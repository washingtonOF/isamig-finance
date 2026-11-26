import re

def normalize_cpf(value):
    digits = re.sub(r"[^0-9]", "", str(value or ""))
    if len(digits) != 11 or len(set(digits)) == 1:
        return None
    for size in (9, 10):
        remainder = sum(int(digits[i]) * (size + 1 - i) for i in range(size)) % 11
        if int(digits[size]) != (0 if remainder < 2 else 11 - remainder):
            return None
    return digits

def resolve_registration(cpf, residents):
    normalized = normalize_cpf(cpf)
    if not normalized:
        return {"status": "invalid"}
    matches = [(unit, data) for unit, data in residents.items()
               if normalize_cpf(data.get("cpf")) == normalized]
    if not matches:
        return {"status": "not_found"}
    if len(matches) != 1 or matches[0][0] == "204":
        return {"status": "review"}
    unit, data = matches[0]
    name = str(data.get("responsible") or data.get("owner") or "").strip().split()
    if not name:
        return {"status": "review"}
    # Internal result only. Do not expose unit or name before identity checks.
    return {"status": "matched", "unit": unit, "masked_name": name[0] + " ****"}
