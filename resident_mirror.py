"""Merge imported payer suggestions with local overrides without bank writes."""
EDITABLE = frozenset(("name","cpf","phone","email","address"))
def effective_profile(source, overrides):
    return {key: overrides[key] if key in overrides else source.get(key, "") for key in EDITABLE}

def refresh_source(previous, incoming):
    result = {key: previous[key] for key in EDITABLE if key in previous}
    for key in EDITABLE:
        value = incoming.get(key)
        if isinstance(value, str) and value.strip():
            result[key] = value.strip()
    return result
