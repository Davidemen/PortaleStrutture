import pytest

from strutture.web import config


@pytest.mark.unit
def test_from_env_defaults_when_unset() -> None:
    settings = config.from_env({})
    assert settings.rate_limit_per_minute == 600
    assert settings.max_body_bytes == 8_000_000  # sized for a 20 000-row reactions table
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000


@pytest.mark.unit
def test_from_env_reads_overrides() -> None:
    settings = config.from_env(
        {
            "STRUTTURE_WEB_RATE_LIMIT": "5",
            "STRUTTURE_WEB_MAX_BODY_BYTES": "2048",
            "STRUTTURE_WEB_HOST": "0.0.0.0",
            "STRUTTURE_WEB_PORT": "9000",
        }
    )
    assert settings.rate_limit_per_minute == 5
    assert settings.max_body_bytes == 2048
    assert settings.host == "0.0.0.0"
    assert settings.port == 9000


@pytest.mark.unit
def test_from_env_ignores_invalid_or_non_positive_values() -> None:
    settings = config.from_env({"STRUTTURE_WEB_RATE_LIMIT": "not-a-number", "STRUTTURE_WEB_PORT": "-1"})
    assert settings.rate_limit_per_minute == 600
    assert settings.port == 8000
