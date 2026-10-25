import pytest

from app.config import is_configured


@pytest.mark.parametrize("value", ["", " ", "YOUR_KEY", "your-secret-key", "YOUR_SUPABASE_KEY"])
def test_placeholder_credentials_are_not_configured(value: str) -> None:
    assert not is_configured(value)


def test_realistic_credential_is_configured() -> None:
    assert is_configured("sk-example")
