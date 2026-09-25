"""Volatile, bounded FIFO using timed messages and expiring retries."""

import asyncio
import time
from collections import deque
from dataclasses import dataclass

from homeassistant.exceptions import ServiceValidationError

from .api import ESPTimeCastError, boolean


@dataclass
class Message:
    text: str
    seconds: int
    speed: int
    expires: float


class MessageQueue:
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self.pending = deque()
        self.task = None
        self.active = False
        self.expired = 0
        self.last_result = "idle"
        self.retry_interval = 5

    def notify(self):
        self.coordinator.async_update_listeners()

    def enqueue(self, text, seconds, ttl, speed):
        if len(self.pending) >= 20:
            raise ServiceValidationError("Message queue is full (20 waiting messages)")
        self.pending.append(Message(text, seconds, speed, time.monotonic() + ttl))
        if self.task is None or self.task.done():
            self.task = self.coordinator.hass.async_create_background_task(
                self.run(), "ESPTimeCast message queue"
            )
        self.notify()

    async def clear(self):
        self.pending.clear()
        if self.task is not None:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        self.active = False
        self.last_result = "cleared"
        self.notify()

    async def run(self):
        try:
            while self.pending:
                item = self.pending[0]
                if time.monotonic() >= item.expires:
                    self.pending.popleft()
                    self.expired += 1
                    self.last_result = "expired"
                    self.notify()
                    continue
                sent = False
                try:
                    async with self.coordinator.transaction:
                        status = await self.coordinator.client.status()
                        display = status["display"]
                        blocked = (
                            display.get("displayMode") in (7, 8)
                            or boolean(status.get("alarm", {}).get("ringing"))
                            or not boolean(display.get("allowInterrupt", True))
                        )
                        # Recheck expiry after network/lock waits, before delivery.
                        if not blocked and time.monotonic() < item.expires:
                            await self.coordinator.client.message(
                                message=item.text,
                                seconds=item.seconds,
                                scrolls=0,
                                speed=item.speed,
                                interrupt=True,
                            )
                            sent = True
                except ESPTimeCastError:
                    # Includes 409 and temporary network errors; never force interruption.
                    pass
                if not sent:
                    self.last_result = "waiting"
                    self.notify()
                    await asyncio.sleep(
                        min(self.retry_interval, max(0, item.expires - time.monotonic()))
                    )
                    continue
                self.pending.popleft()
                self.active = True
                self.last_result = "displaying"
                self.notify()
                # Firmware clears after the requested duration; wait a small guard interval.
                await asyncio.sleep(item.seconds + 1)
                self.active = False
                self.last_result = "delivered"
                self.notify()
        finally:
            self.active = False
            self.notify()
