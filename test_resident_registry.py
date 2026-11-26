from resident_registry import UNITS, identify_unit, stage_resident

def test_units():
    assert len(UNITS) == 22
    assert "602" in UNITS and "603" not in UNITS

def test_matching():
    assert identify_unit("Maria - AP 203") == "203"
    assert identify_unit("Maria", "602") == "602"
    assert identify_unit("AP 203", "AP 204") is None
    assert identify_unit("AP 603") is None
    assert identify_unit("CPF 123.203.456-00") is None

def test_pending():
    assert stage_resident("Maria AP 101", " M@example.com ") == {
        "name": "Maria AP 101", "email": "m@example.com",
        "unit": "101", "status": "pending_review", "role": "resident"}
