from datetime import datetime, timezone, timedelta
from registration_activation import issue_activation, verify_activation

CPF = "52998224725"
RESIDENTS = {"302": {"cpf": CPF, "responsible": "Maria Teste"}}
NOW = datetime(2026, 11, 26, tzinfo=timezone.utc)

def test_activation_valid():
    token, record = issue_activation(CPF, RESIDENTS, NOW)
    assert token not in str(record)
    assert verify_activation(CPF, token, record, RESIDENTS, NOW) == {
        "unit": "302", "masked_name": "Maria ****", "masked_cpf": "***.***.***-25"}

def test_activation_rejects_wrong_token_or_cpf():
    token, record = issue_activation(CPF, RESIDENTS, NOW)
    assert verify_activation(CPF, "x"*32, record, RESIDENTS, NOW) is None
    assert verify_activation("11111111111", token, record, RESIDENTS, NOW) is None

def test_activation_expired_or_used():
    token, record = issue_activation(CPF, RESIDENTS, NOW)
    assert verify_activation(CPF, token, record, RESIDENTS, NOW+timedelta(hours=48)) is None
    assert verify_activation(CPF, token, dict(record, used=True), RESIDENTS, NOW) is None

def test_activation_rejects_changed_unit():
    token, record = issue_activation(CPF, RESIDENTS, NOW)
    assert verify_activation(CPF, token, record, {"303": RESIDENTS["302"]}, NOW) is None
