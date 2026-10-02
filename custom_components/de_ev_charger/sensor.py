from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass,
)
from homeassistant.const import (
    EntityCategory, UnitOfElectricCurrent, UnitOfElectricPotential, UnitOfEnergy,
    UnitOfPower, UnitOfTime,
)

from .const import (
    CP_LEVELS, CP_TOLERANCE, JSON_DPS, METRICS_SCALE, PHASES, WORK_STATES, flatten, parse_json,
)
from .entity import EvEntity

RAW_SENSORS = {
    # code: (translation_key, категория / category)
    "x_work_state": ("work_state", None),
    "x_charge_mode": ("charge_mode", None),
    "x_metrics": ("metrics_raw", EntityCategory.DIAGNOSTIC),
    "x_charger_info": ("charger_info", EntityCategory.DIAGNOSTIC),
    "x_debug": ("debug", EntityCategory.DIAGNOSTIC),
    "x_lang_cfg": ("language", EntityCategory.DIAGNOSTIC),
}


def _num(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _metrics(data):
    """x_metrics с ключами в нижнем регистре (облако шлёт "L1", "L2", "L3").
    x_metrics with lower-case keys (the cloud sends "L1", "L2", "L3")."""
    return {str(k).lower(): v for k, v in (parse_json(data.get("x_metrics")) or {}).items()}


def _metric(data, field, scale=METRICS_SCALE):
    """Поле x_metrics / scale.
    x_metrics field / scale."""
    val = _num(_metrics(data).get(field))
    return None if val is None else val / scale


def _phases(data, idx):
    """{'l1': V|A|kW, ...} по фазам, которые есть в x_metrics.
    {'l1': V|A|kW, ...} for the phases present in x_metrics."""
    metrics = _metrics(data)
    out = {}
    for phase in PHASES:
        arr = metrics.get(phase)
        if isinstance(arr, list) and len(arr) > idx and _num(arr[idx]) is not None:
            out[phase] = arr[idx] / METRICS_SCALE
    return out


def _cp(data):
    try:
        return float((parse_json(data.get("x_charger_info")) or {}).get("cp"))
    except (TypeError, ValueError):
        return None


def _vehicle(data):
    """Состояние машины по напряжению CP: 12.1 / 9 / 6 В (±7%).
    Vehicle state from CP voltage: 12.1 / 9 / 6 V (±7%)."""
    cp = _cp(data)
    if cp is None:
        return None
    for state, level in CP_LEVELS:
        if abs(cp - level) <= level * CP_TOLERANCE:
            return state
    return None


def _work_code(data):
    try:
        return int(str(data.get("x_work_state")))
    except (TypeError, ValueError):
        return None


def _status(data):
    code = _work_code(data)
    return None if code is None else WORK_STATES.get(code, "other")


def _duration(data):
    # d - десятые доли секунды (подтверждено: 11890 -> 19:49)
    # d - tenths of a second (confirmed: 11890 -> 19:49)
    val = _metric(data, "d")
    return None if val is None else int(val)


def _l1(idx):
    return lambda data: _phases(data, idx).get("l1")


def _phase_attrs(idx):
    return lambda data: _phases(data, idx) or None


def _power(data):
    """Суммарная мощность по фазам, кВт.
    Total power over phases, kW."""
    vals = _phases(data, 2)
    return round(sum(vals.values()), 2) if vals else None


@dataclass(frozen=True, kw_only=True)
class EvSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict], Any]
    attrs_fn: Callable[[dict], dict | None] | None = None


V, A = UnitOfElectricPotential.VOLT, UnitOfElectricCurrent.AMPERE
MEASUREMENT = SensorStateClass.MEASUREMENT

# Расчётные сенсоры: key = часть unique_id, translation_key = имя (ru/en/es) и ключ для карточки
# Computed sensors: key = part of unique_id, translation_key = name (ru/en/es) and the card lookup key
SENSORS = (
    EvSensorDescription(
        key="status", translation_key="status", icon="mdi:ev-station",
        device_class=SensorDeviceClass.ENUM, options=[*WORK_STATES.values(), "other"],
        value_fn=_status, attrs_fn=lambda d: {"code": _work_code(d)},
    ),
    EvSensorDescription(
        key="vehicle", translation_key="vehicle", icon="mdi:car-electric",
        device_class=SensorDeviceClass.ENUM, options=[s for s, _ in CP_LEVELS],
        value_fn=_vehicle, attrs_fn=lambda d: {"cp": _cp(d)},
    ),
    EvSensorDescription(
        key="voltage", translation_key="voltage", device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=V, state_class=MEASUREMENT, suggested_display_precision=0,
        value_fn=_l1(0), attrs_fn=_phase_attrs(0),
    ),
    EvSensorDescription(
        key="current", translation_key="current", device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=A, state_class=MEASUREMENT, suggested_display_precision=1,
        value_fn=_l1(1), attrs_fn=_phase_attrs(1),
    ),
    EvSensorDescription(
        key="power", translation_key="power", device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT, state_class=MEASUREMENT,
        suggested_display_precision=1, value_fn=_power, attrs_fn=_phase_attrs(2),
    ),
    EvSensorDescription(
        key="session_energy", translation_key="session_energy", device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING, suggested_display_precision=1,
        value_fn=lambda d: _metric(d, "e"),
    ),
    EvSensorDescription(
        key="session_duration", translation_key="session_duration",
        device_class=SensorDeviceClass.DURATION, native_unit_of_measurement=UnitOfTime.SECONDS,
        icon="mdi:timer-outline", suggested_display_precision=0, value_fn=_duration,
    ),
    EvSensorDescription(
        key="cp_voltage", translation_key="cp_voltage", device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=V, state_class=MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC, value_fn=_cp,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    coord = entry.runtime_data
    data = coord.data or {}
    entities = [
        EvRawSensor(coord, code, tkey, cat)
        for code, (tkey, cat) in RAW_SENSORS.items()
        if code in data
    ]
    # Сенсоры из числовых полей JSON-строк (старые, для совместимости с прежними карточками)
    # Sensors from numeric fields of JSON strings (legacy, kept for older cards)
    for code in JSON_DPS:
        for field, value in flatten(parse_json(data.get(code))).items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                entities.append(EvJsonSensor(coord, code, field))
    # Расчётные сенсоры создаются всегда (даже если облако пока не отдало данные)
    # Computed sensors are always created (even if the cloud has no data yet)
    entities.extend(EvSensor(coord, desc) for desc in SENSORS)
    async_add_entities(entities)


class EvRawSensor(EvEntity, SensorEntity):
    """Сырое значение DP; JSON разворачивается в атрибуты.
    Raw DP value; JSON is flattened into attributes."""

    def __init__(self, coord, key, translation_key, category):
        super().__init__(coord, key, translation_key)
        self._attr_entity_category = category

    @property
    def native_value(self):
        val = self.dp
        if isinstance(val, str):
            return val[:255]
        return val

    @property
    def extra_state_attributes(self):
        parsed = parse_json(self.dp)
        return flatten(parsed) if parsed else None


class EvJsonSensor(EvEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coord, code, field):
        # Имя без перевода: поле JSON меняется от прошивки
        # Untranslated name: the JSON field depends on firmware
        super().__init__(coord, f"{code}_{field}", name=f"{code[2:]} {field}")
        self._code = code
        self._field = field

    @property
    def native_value(self):
        data = flatten(parse_json((self.coordinator.data or {}).get(self._code)))
        return data.get(self._field)


class EvSensor(EvEntity, SensorEntity):
    entity_description: EvSensorDescription

    def __init__(self, coord, description: EvSensorDescription):
        super().__init__(coord, description.key, description.translation_key)
        self.entity_description = description

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.coordinator.data or {})

    @property
    def extra_state_attributes(self):
        fn = self.entity_description.attrs_fn
        return fn(self.coordinator.data or {}) if fn else None
