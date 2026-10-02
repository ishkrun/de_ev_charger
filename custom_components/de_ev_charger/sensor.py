from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import EntityCategory

from .const import JSON_DPS, flatten, parse_json
from .entity import EvEntity

RAW_SENSORS = {
    "x_work_state": ("Work state", None),
    "x_charge_mode": ("Charge mode", None),
    "x_metrics": ("Metrics raw", EntityCategory.DIAGNOSTIC),
    "x_charger_info": ("Charger info", EntityCategory.DIAGNOSTIC),
    "x_debug": ("Debug", EntityCategory.DIAGNOSTIC),
    "x_lang_cfg": ("Language", EntityCategory.DIAGNOSTIC),
}


async def async_setup_entry(hass, entry, async_add_entities):
    coord = entry.runtime_data
    data = coord.data or {}
    entities = [
        EvRawSensor(coord, code, name, cat)
        for code, (name, cat) in RAW_SENSORS.items()
        if code in data
    ]
    # Автоматически создаём сенсоры из числовых полей JSON-строк
    for code in JSON_DPS:
        for field, value in flatten(parse_json(data.get(code))).items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                entities.append(EvJsonSensor(coord, code, field))
    async_add_entities(entities)


class EvRawSensor(EvEntity, SensorEntity):
    def __init__(self, coord, key, name, category):
        super().__init__(coord, key, name)
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
        super().__init__(coord, f"{code}_{field}", f"{code[2:]} {field}")
        self._code = code
        self._field = field

    @property
    def native_value(self):
        data = flatten(parse_json((self.coordinator.data or {}).get(self._code)))
        return data.get(self._field)
