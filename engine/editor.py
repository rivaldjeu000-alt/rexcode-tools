import re


def find_value(xml: str, name: str):
    pattern = rf'<Var\b[^>]*name="{re.escape(name)}"[^>]*v="([^"]*)"'
    match = re.search(pattern, xml)
    return match.group(1) if match else None


def replace_value(xml: str, name: str, new_value: str):
    esc = re.escape(name)
    pattern = rf'<Var\b[^>]*name="{esc}"[^>]*v="[^"]*"[^>]*/>'
    count = 0

    def _replace(match):
        nonlocal count
        count += 1
        return re.sub(r'v="[^"]*"', f'v="{new_value}"', match.group(0), count=1)

    out = re.sub(pattern, _replace, xml)
    return (out, True) if count > 0 else (xml, False)


def insert_var_typed(xml: str, name: str, value: str, var_type: str = "i") -> str:
    tag = f'<Var name="{name}" v="{value}" t="{var_type}"/>'
    match = re.search(r'</Global\s*>', xml, re.IGNORECASE)
    if match:
        return xml[:match.start()] + tag + "\n" + xml[match.start():]
    match = re.search(r'</root\s*>', xml, re.IGNORECASE)
    if match:
        return xml[:match.start()] + tag + "\n" + xml[match.start():]
    return xml + tag


def set_stat(xml: str, var_name: str, value):
    value_str = str(value)
    out, success = replace_value(xml, var_name, value_str)
    if success:
        return out, True, f"OK {var_name} = {value_str}"
    out = insert_var_typed(xml, var_name, value_str, "i")
    return out, True, f"OK {var_name} = {value_str} (baru)"


STATS_VARS = {
    "Level": "PlayerLevel",
    "M3 Level": "M3Level",
    "1st Win": "FirstAttemptM3Levels",
    "Lives Sent": "LivesSent",
    "Help Given": "Achievement_Teamwork",
    "Cards": "FullCardCollections",
    "Regatta": "RegataTasksCompleted",
    "Year": "AccYear",
    "Golden Pass": "GoldenPass",
}

CURRENCY_VARS = {
    "T-Cash": "Cash",
    "Coins": "Coins",
    "Event Token": "EventToken",
    "Gems": "Gems",
    "Barn Cap": "WareHouseCashUpgrade",
}

RESOURCE_VARS = {
    "XP": "sexpx",
    "Exp Energy": "expeditionEnergy",
}


def read_category(xml: str, kategori: dict) -> dict:
    result = {}
    for label, var_name in kategori.items():
        value = find_value(xml, var_name)
        result[label] = value if value else "0"
    return result


def read_stats(xml: str) -> dict:
    return read_category(xml, STATS_VARS)


def read_currency(xml: str) -> dict:
    return read_category(xml, CURRENCY_VARS)


def read_resource(xml: str) -> dict:
    return read_category(xml, RESOURCE_VARS)


def apply_edits(xml: str, edits: dict):
    messages = []
    for var_name, new_value in edits.items():
        if new_value is None or new_value == "":
            continue
        xml, ok, msg = set_stat(xml, var_name, new_value)
        messages.append(msg)
    return xml, messages
