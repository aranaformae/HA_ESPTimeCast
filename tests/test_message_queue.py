import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.exceptions import ServiceValidationError

from custom_components.esptimecast.api import BusyError, ESPTimeCastError
from custom_components.esptimecast.message_queue import MessageQueue


async def until(predicate):
    async with asyncio.timeout(4):
        while not predicate():
            await asyncio.sleep(0.005)


@pytest.fixture
async def queue():
    coordinator = SimpleNamespace(
        hass=SimpleNamespace(
            async_create_background_task=lambda coro, name: asyncio.create_task(coro)
        ),
        transaction=asyncio.Lock(),
        async_update_listeners=Mock(),
        client=SimpleNamespace(
            status=AsyncMock(
                return_value={
                    "display": {"displayMode": 0, "allowInterrupt": True},
                    "alarm": {"ringing": False},
                }
            ),
            message=AsyncMock(),
        ),
    )
    queue = MessageQueue(coordinator)
    queue.retry_interval = 0.01
    yield queue
    await queue.clear()


async def test_fifo_and_bounded_duration(queue):
    queue.enqueue("first", 0.01, 10, 80)
    queue.enqueue("second", 0.01, 10, 80)
    await until(lambda: queue.coordinator.client.message.call_count == 1)
    assert queue.active
    assert len(queue.pending) == 1
    await until(lambda: queue.task.done())
    calls = queue.coordinator.client.message.call_args_list
    assert [call.kwargs["message"] for call in calls] == ["first", "second"]
    assert all(call.kwargs["interrupt"] is True and call.kwargs["scrolls"] == 0 for call in calls)
    assert queue.last_result == "delivered"


async def test_protection_expiry_and_capacity(queue):
    queue.coordinator.client.status.return_value["display"]["allowInterrupt"] = False
    queue.enqueue("expires", 1, 0.03, 80)
    await until(lambda: queue.task.done())
    queue.coordinator.client.message.assert_not_called()
    assert queue.expired == 1
    for _ in range(20):
        queue.enqueue("waiting", 1, 10, 80)
    with pytest.raises(ServiceValidationError):
        queue.enqueue("overflow", 1, 10, 80)
    await queue.clear()
    assert not queue.pending


async def test_retries_errors_and_clear(queue):
    queue.coordinator.client.message.side_effect = [BusyError("409"), ESPTimeCastError("503"), None]
    queue.enqueue("retry", 10, 10, 80)
    queue.enqueue("cancel", 1, 10, 80)
    await until(lambda: queue.active)
    assert queue.coordinator.client.message.call_count == 3
    await queue.clear()
    assert queue.task is None
    assert not queue.pending
    assert queue.last_result == "cleared"
    assert queue.coordinator.client.message.call_count == 3


async def test_expiry_after_network_wait(queue):
    async def slow_status():
        await asyncio.sleep(0.04)
        return {"display": {"displayMode": 0, "allowInterrupt": True}}

    queue.coordinator.client.status.side_effect = slow_status
    queue.enqueue("too late", 1, 0.01, 80)
    await until(lambda: queue.task.done())
    queue.coordinator.client.message.assert_not_called()
    assert queue.expired == 1
