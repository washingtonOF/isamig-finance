"""Pure helpers for resident import staging; never grants access."""
import re

UNITS = frozenset(str(floor * 100 + unit)
                  for floor in range(1, 7)
                  for unit in range(1, 3 if floor == 6 else 5))
ROLES = frozenset({"master", "administrative", "resident"})

def identify_unit(*fields):
    """Return a unique explicitly labelled apartment, otherwise None."""
    candidates = set()
    for field in fields:
        if not isinstance(field, str):
            continue
        value = field.strip()
        if value in UNITS:
            candidates.add(value)
        for match in re.finditer(r"\b(?:ap(?:to)?\.?|apartamento|unidade)\s*[-:#]?\s*(\d{3})\b", value, re.I):
            candidates.add(match.group(1))
    return next(iter(candidates)) if len(candidates) == 1 and candidates <= UNITS else None

def stage_resident(name, email, *unit_fields):
    """Build a pending candidate from normalized billing data."""
    unit = identify_unit(name, *unit_fields)
    return {"name": name, "email": email.strip().lower() if isinstance(email, str) else "",
            "unit": unit, "status": "pending_review", "role": "resident"}
