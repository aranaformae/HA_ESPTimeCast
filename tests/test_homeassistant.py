"""Exercise actual HA loading, UI setup, entities and service lifecycle."""

from pathlib import Path
from types import MappingProxyType

import pytest
from homeassistant import loader
from homeassistant.bootstrap import async_load_base_functionality
from homeassistant.config_entries import ConfigEntries, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component


@pytest.fixture
async def hass(tmp_path):
    (tmp_path / "custom_components").symlink_to(
        Path(__file__).resolve().parents[1] / "custom_components", target_is_directory=True
    )
    instance = HomeAssistant(str(tmp_path))
    loader.async_setup(instance)
    instance.config_entries = ConfigEntries(instance, {})
    await async_load_base_functionality(instance)
    await async_setup_component(instance, "network", {})
    await async_setup_component(instance, "homeassistant", {})
    yield instance
    await instance.async_stop(force=True)


async def add_entry(hass, device, title="Test clock"):
    entry = ConfigEntry(
        domain="esptimecast",
        title=title,
        version=1,
        minor_version=1,
        data={"host": device.url},
        options={},
        source="user",
        unique_id=None,
        discovery_keys=MappingProxyType({}),
        subentries_data=None,
    )
    await hass.config_entries.async_add(entry)
    assert entry.state.value == "loaded"
    await hass.async_block_till_done()
    return entry


async def test_setup_entities_services_unload(hass, device):
    entry = await add_entry(hass, device)
    registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(registry, entry.entry_id)
    assert len(entities) >= 60

    def entity(key):
        return next(e.entity_id for e in entities if e.unique_id == f"{entry.entry_id}_{key}")

    assert hass.states.get(entity("firmware")).state == "2.1.14"
    assert hass.states.get(entity("brightness")).state == "10"
    assert hass.states.get(entity("persistent_message")).state == "BASE"
    assert hass.states.get(entity("alarm_4")).state == "off"
    assert hass.states.get(entity("display")).state == "on"
    await hass.services.async_call(
        "light", "turn_off", {"entity_id": entity("display")}, blocking=True
    )
    assert device.calls[-1] == ("/action", {"display_off": ""})
    await hass.services.async_call(
        "light", "turn_on", {"entity_id": entity("display")}, blocking=True
    )
    assert device.calls[-1] == ("/action", {"display_on": ""})
    dev = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)[0]
    await hass.services.async_call(
        "esptimecast", "start_timer", {"device_id": dev.id, "duration": "5M"}, blocking=True
    )
    assert device.calls[-1] == ("/action", {"timer": "5M"})
    device.status_code = 503
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity("display")).state == "unavailable"
    device.status_code = 200
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(entity("display")).state == "on"
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert not hass.services.has_service("esptimecast", "start_timer")


async def test_config_flow_and_duplicate(hass, device):
    result = await hass.config_entries.flow.async_init("esptimecast", context={"source": "user"})
    assert result["type"] == "form"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"host": device.url})
    assert result["type"] == "create_entry"
    await hass.async_block_till_done()
    duplicate = await hass.config_entries.flow.async_init(
        "esptimecast", context={"source": "user"}, data={"host": device.url}
    )
    assert duplicate["type"] == "abort"
    assert duplicate["reason"] == "already_configured"


async def test_invalid_device_selection(hass, device):
    from homeassistant.exceptions import ServiceValidationError

    await add_entry(hass, device)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            "esptimecast", "start_timer", {"device_id": "wrong", "duration": "5M"}, blocking=True
        )


async def test_options_reconfigure_and_multiple_devices(hass, device):
    from types import SimpleNamespace

    first = await add_entry(hass, device)
    # Same firmware hostname must not merge physically distinct device entries.
    second = await add_entry(
        hass, SimpleNamespace(url=device.url.replace("127.0.0.1", "localhost")), "Second clock"
    )
    first_device = dr.async_entries_for_config_entry(dr.async_get(hass), first.entry_id)[0]
    second_device = dr.async_entries_for_config_entry(dr.async_get(hass), second.entry_id)[0]
    assert first_device.id != second_device.id
    result = await hass.config_entries.options.async_init(first.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"scan_interval": 30}
    )
    assert result["type"] == "create_entry"
    await hass.async_block_till_done()
    assert first.runtime_data.update_interval.total_seconds() == 30
    result = await hass.config_entries.flow.async_init(
        "esptimecast", context={"source": "reconfigure", "entry_id": first.entry_id}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"host": device.url})
    assert result["reason"] == "reconfigure_successful"
    await hass.async_block_till_done()
    assert await hass.config_entries.async_unload(first.entry_id)
    assert hass.services.has_service("esptimecast", "start_timer")
    await hass.services.async_call(
        "esptimecast",
        "start_timer",
        {"device_id": second_device.id, "duration": "2M"},
        blocking=True,
    )
    assert device.calls[-1] == ("/action", {"timer": "2M"})


async def test_service_descriptions(hass, device):
    from homeassistant.helpers.service import _load_services_file

    from custom_components.esptimecast.services import SCHEMAS

    await add_entry(hass, device)
    integration = await loader.async_get_integration(hass, "esptimecast")
    descriptions = await hass.async_add_executor_job(_load_services_file, integration)
    assert set(descriptions) == set(SCHEMAS)
    assert (
        descriptions["start_timer"]["fields"]["device_id"]["selector"]["device"]["integration"]
        == "esptimecast"
    )


async def test_brightness_changes_report_latest_device_value_immediately(hass, device):
    """Rapid consecutive writes must not leave the UI showing an older level."""
    entry = await add_entry(hass, device)
    entities = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    number = next(e.entity_id for e in entities if e.unique_id == f"{entry.entry_id}_brightness")
    light = next(e.entity_id for e in entities if e.unique_id == f"{entry.entry_id}_display")
    for level in (3, 12, 0, 15, 7):
        await hass.services.async_call(
            "number", "set_value", {"entity_id": number, "value": level}, blocking=True
        )
        assert device.state["display"]["brightness"] == level
        assert hass.states.get(number).state == str(level)
        assert hass.states.get(light).attributes["brightness"] == round((level + 1) * 255 / 16)
    for requested in (32, 240, 128):
        await hass.services.async_call(
            "light", "turn_on", {"entity_id": light, "brightness": requested}, blocking=True
        )
        actual = device.state["display"]["brightness"]
        assert hass.states.get(number).state == str(actual)
        assert hass.states.get(light).attributes["brightness"] == round((actual + 1) * 255 / 16)


async def test_alarm_controls_and_timer_presets(hass, device):
    import copy

    entry = await add_entry(hass, device)
    entities = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)

    def eid(key):
        return next(e.entity_id for e in entities if e.unique_id == f"{entry.entry_id}_{key}")

    old = copy.deepcopy(device.state["alarm"]["alarms"])
    await hass.services.async_call(
        "time", "set_value", {"entity_id": eid("alarm_2_time"), "time": "08:35:00"}, blocking=True
    )
    assert hass.states.get(eid("alarm_2_time")).state == "08:35:00"
    assert device.state["alarm"]["alarms"][0] == old[0]
    assert device.state["alarm"]["alarms"][1]["days"] == old[1]["days"]
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": eid("alarm_2_day_1")}, blocking=True
    )
    assert device.state["alarm"]["alarms"][1]["days"] == [True, False, True, True, True, True, True]
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": eid("alarm_2_snoozeMinutes"), "value": 8},
        blocking=True,
    )
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": eid("alarm_2_sound"), "option": "Chirp"},
        blocking=True,
    )
    assert device.state["alarm"]["alarms"][1]["snoozeMinutes"] == 8
    assert device.state["alarm"]["alarms"][1]["sound"] == 2
    await hass.services.async_call(
        "number", "set_value", {"entity_id": eid("timer_duration"), "value": 17}, blocking=True
    )
    await hass.services.async_call(
        "button", "press", {"entity_id": eid("start_timer")}, blocking=True
    )
    assert device.calls[-1] == ("/action", {"timer": "17M"})
    for preset in (5, 10, 25):
        await hass.services.async_call(
            "button", "press", {"entity_id": eid(f"timer_{preset}_minutes")}, blocking=True
        )
        assert device.calls[-1] == ("/action", {"timer": f"{preset}M"})


async def test_queue_services_and_unload_cancel_worker(hass, device):
    import asyncio

    entry = await add_entry(hass, device)
    device.state["display"]["allowInterrupt"] = False
    dev = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)[0]
    await hass.services.async_call(
        "esptimecast",
        "queue_message",
        {"device_id": dev.id, "message": "Wait for display", "ttl": 60},
        blocking=True,
    )
    queue = entry.runtime_data.messages
    assert len(queue.pending) == 1
    await asyncio.sleep(0.01)
    assert not device.calls
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert queue.task is None
    assert not queue.pending


@pytest.mark.parametrize(
    "filename,inputs",
    [
        ("doorbell.yaml", {"sensor": "binary_sensor.doorbell"}),
        ("appliance_finished.yaml", {"power": "sensor.washer_power"}),
        ("waste_reminder.yaml", {"sensor": "sensor.waste"}),
        ("calendar_reminder.yaml", {"calendar": "calendar.family"}),
    ],
)
async def test_blueprints_validate_in_homeassistant(hass, filename, inputs):
    from homeassistant.components.automation.config import (
        AUTOMATION_BLUEPRINT_SCHEMA,
        async_validate_config_item,
    )
    from homeassistant.components.blueprint.models import Blueprint, BlueprintInputs
    from homeassistant.util.yaml import load_yaml_dict

    path = Path(__file__).resolve().parents[1] / "blueprints/automation/esptimecast" / filename
    blueprint = Blueprint(
        load_yaml_dict(str(path)), schema=AUTOMATION_BLUEPRINT_SCHEMA, expected_domain="automation"
    )
    configured = BlueprintInputs(
        blueprint, {"use_blueprint": {"path": filename, "input": {"device": "test", **inputs}}}
    )
    configured.validate()
    expanded = configured.async_substitute()
    validated = await async_validate_config_item(hass, "automation", expanded)
    assert validated is not None


async def test_dashboard_entity_references(hass, device):
    import yaml

    entry = await add_entry(hass, device, title="esptimecast")
    known = {
        e.entity_id for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    }
    dashboard = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / "examples/dashboard.yaml").read_text()
    )
    for card in dashboard["views"][0]["cards"]:
        for entity_id in card.get("entities", []):
            assert entity_id in known or entity_id in (
                "input_text.esptimecast_message",
                "script.esptimecast_send_message",
            )


async def test_dashboard_message_helper_delivers_to_selected_device(hass, device):
    import asyncio

    import yaml

    await add_entry(hass, device, title="esptimecast")
    package = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / "examples/message_helpers.yaml").read_text()
    )
    assert await async_setup_component(hass, "input_text", {"input_text": package["input_text"]})
    assert await async_setup_component(hass, "script", {"script": package["script"]})
    await hass.services.async_call(
        "input_text",
        "set_value",
        {"entity_id": "input_text.esptimecast_message", "value": "Dashboard test"},
        blocking=True,
    )
    await hass.services.async_call("script", "esptimecast_send_message", {}, blocking=True)
    async with asyncio.timeout(2):
        while not device.calls:
            await asyncio.sleep(0.01)
    assert device.calls[-1][1]["message"] == "Dashboard test"
    assert device.calls[-1][1]["interrupt"] == "1"
