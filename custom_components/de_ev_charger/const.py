"""Константы и хелперы."""
import json

DOMAIN = "de_ev_charger"
PANEL_URL = "ev-charger"  # панель «Зарядка»: /ev-charger

CONF_ACCESS_ID = "access_id"
CONF_ACCESS_SECRET = "access_secret"
CONF_DEVICE_ID = "device_id"
CONF_REGION = "region"

SCAN_INTERVAL = 30  # секунд
REFRESH_DELAYS = (3, 10)  # секунд от команды: 1-й через 3, 2-й ещё через 7
COMMAND_COOLDOWN = 5  # секунд: не чаще 1 команды от одной кнопки/переключателя

REGIONS = {
    "eu": "https://openapi.tuyaeu.com",
    "eu_west": "https://openapi-weaz.tuyaeu.com",
    "us": "https://openapi.tuyaus.com",
    "cn": "https://openapi.tuyacn.com",
    "in": "https://openapi.tuyain.com",
}

# Строковые DP, которые могут содержать JSON
JSON_DPS = ("x_metrics", "x_charger_info")

# x_charge_mode: {"m":0|2,"dt":0,"ss":"HH:MM","se":"HH:MM"}
# m=0 - расписание выкл, m=2 - расписание вкл
MODE_OFF = 0
MODE_SCHEDULE = 2
DEFAULT_CHARGE_MODE = {"m": 0, "dt": 0, "ss": "00:00", "se": "08:00"}

# x_work_state -> ключ статуса (остальные коды -> "other")
WORK_STATES = {202: "scheduled", 300: "charging"}

# x_metrics: {"L1":[V*10, A*10, kW*10], "L2":[...], "L3":[...], "t":?, "p":?, "e": kWh*10, "d": сек}
METRICS_SCALE = 10
PHASES = ("l1", "l2", "l3")

# x_charger_info.cp - напряжение Control Pilot, В (±7%)
CP_LEVELS = (("disconnected", 12.1), ("connected", 9.0), ("charging", 6.0))
CP_TOLERANCE = 0.07


def parse_json(value):
    """Вернуть dict, если значение - JSON-объект, иначе None."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip().startswith(("{", "[")):
        try:
            data = json.loads(value)
        except ValueError:
            return None
        if isinstance(data, list):
            return {str(i): v for i, v in enumerate(data)}
        return data if isinstance(data, dict) else None
    return None


def flatten(data, prefix=""):
    """{'a': {'b': 1}, 'c': [2, 3]} -> {'a_b': 1, 'c_0': 2, 'c_1': 3}"""
    out = {}
    for key, val in (data or {}).items():
        name = f"{prefix}{key}"
        if isinstance(val, dict):
            out.update(flatten(val, f"{name}_"))
        elif isinstance(val, list):
            for i, item in enumerate(val):
                if isinstance(item, dict):
                    out.update(flatten(item, f"{name}_{i}_"))
                else:
                    out[f"{name}_{i}"] = item
        else:
            out[name] = val
    return out
