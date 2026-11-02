import pytest
from fastapi import HTTPException

from app.config import DEFAULT_API_KEY, settings
from app.security import check_api_key_configured, verify_api_key


def test_correct_key_is_accepted(monkeypatch):
    monkeypatch.setattr(settings, "app_api_key", "s3cret-key")

    assert verify_api_key("s3cret-key") is None


@pytest.mark.parametrize("sent", [None, "", "wrong", "s3cret-ke", "s3cret-keyX"])
def test_missing_or_wrong_key_is_rejected(monkeypatch, sent):
    monkeypatch.setattr(settings, "app_api_key", "s3cret-key")

    with pytest.raises(HTTPException) as error:
        verify_api_key(sent)

    assert error.value.status_code == 401


def test_default_key_is_refused_outside_local(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "app_api_key", DEFAULT_API_KEY)

    with pytest.raises(RuntimeError):
        check_api_key_configured()


def test_default_key_is_allowed_locally_and_custom_key_anywhere(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "local")
    monkeypatch.setattr(settings, "app_api_key", DEFAULT_API_KEY)
    check_api_key_configured()

    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "app_api_key", "a-private-key")
    check_api_key_configured()
