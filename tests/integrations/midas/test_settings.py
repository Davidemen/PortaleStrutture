"""Rule 2 (key resolution) and rule 3 (no SSRF) — docs/integrations/MIDAS.md."""
import pytest

from strutture.integrations.midas import MidasSettings
from strutture.integrations.midas.settings import has_server_key, resolve_key, validate_base_url

VALID_URL = "https://moa-engineers.midasit.com:443/gen"


@pytest.mark.unit
@pytest.mark.parametrize(
    "url",
    [
        "http://moa-engineers.midasit.com/gen",  # not https
        "https://1.2.3.4/gen",  # IP literal
        "https://moa-engineers.midasit.com.evil.org/gen",  # subdomain trick
        "https://user@moa-engineers.midasit.com/gen",  # userinfo
        "https://moa-engineers.midasit.com:8443/gen",  # wrong port
        "https://moa-engineers.midasit.com/other",  # wrong path
        "https://evil.com/gen",  # unrelated host entirely
    ],
)
def test_validate_base_url_rejects_ssrf_candidates(url: str) -> None:
    with pytest.raises(ValueError):
        validate_base_url(url)


@pytest.mark.unit
@pytest.mark.parametrize("url", [VALID_URL, "https://moa-engineers.midasit.com/gen", "https://moa-engineers-gb.midasit.com/civil"])
def test_validate_base_url_accepts_legit_relays(url: str) -> None:
    assert validate_base_url(url).startswith("https://moa-engineers")


@pytest.mark.unit
def test_allowed_hosts_escape_hatch_permits_a_fake_relay_over_http() -> None:
    fake = "http://127.0.0.1:9443/gen"
    with pytest.raises(ValueError):
        validate_base_url(fake)
    assert validate_base_url(fake, allowed_hosts=("127.0.0.1:9443",)) == fake


@pytest.mark.unit
def test_allowed_hosts_escape_hatch_still_requires_a_valid_path() -> None:
    with pytest.raises(ValueError):
        validate_base_url("http://127.0.0.1:9443/other", allowed_hosts=("127.0.0.1:9443",))


@pytest.mark.unit
def test_resolve_key_prefers_header_over_env() -> None:
    assert resolve_key(" header-key ", env={"MIDAS_MAPI_KEY": "env-key"}) == "header-key"


@pytest.mark.unit
def test_resolve_key_falls_back_to_env() -> None:
    assert resolve_key(None, env={"MIDAS_MAPI_KEY": "env-key"}) == "env-key"
    assert resolve_key("", env={"MIDAS_MAPI_KEY": "env-key"}) == "env-key"


@pytest.mark.unit
def test_resolve_key_returns_none_when_neither_present() -> None:
    assert resolve_key(None, env={}) is None


@pytest.mark.unit
def test_has_server_key_reflects_env_only() -> None:
    assert has_server_key(env={"MIDAS_MAPI_KEY": "x"}) is True
    assert has_server_key(env={}) is False


@pytest.mark.unit
def test_settings_from_env_reads_optional_defaults() -> None:
    settings = MidasSettings.from_env(
        env={"MIDAS_BASE_URL": VALID_URL, "MIDAS_PRODUCT": "civil", "MIDAS_ALLOWED_HOSTS": "a:1, b:2"}
    )
    assert settings.base_url == VALID_URL
    assert settings.product == "civil"
    assert settings.allowed_hosts == ("a:1", "b:2")


@pytest.mark.unit
def test_settings_from_env_defaults_are_none_and_empty() -> None:
    settings = MidasSettings.from_env(env={})
    assert settings.base_url is None
    assert settings.product is None
    assert settings.allowed_hosts == ()


@pytest.mark.unit
def test_settings_from_env_ignores_invalid_product() -> None:
    settings = MidasSettings.from_env(env={"MIDAS_PRODUCT": "not-a-product"})
    assert settings.product is None


@pytest.mark.unit
def test_out_of_range_port_gives_an_italian_message_not_a_python_traceback() -> None:
    """LOW 3: urlsplit().port raises its own English ValueError for an out-of-range port; that
    must never reach the caller unfiltered."""
    with pytest.raises(ValueError) as exc_info:
        validate_base_url("https://moa-engineers.midasit.com:99999/gen")
    message = str(exc_info.value)
    assert "porta" in message.lower()
    assert "out of range" not in message.lower()


@pytest.mark.unit
def test_canonical_base_url_lowercases_the_host() -> None:
    """LOW 4: the canonical URL must not echo back the caller's original letter case."""
    assert validate_base_url("https://MOA-ENGINEERS.MIDASIT.COM/gen") == "https://moa-engineers.midasit.com/gen"
    assert validate_base_url("https://Moa-Engineers-Gb.MidasIT.com:443/civil") == "https://moa-engineers-gb.midasit.com:443/civil"
