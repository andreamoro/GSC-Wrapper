"""Tests for the optional ``gsc_wrapper.credentials`` helpers.

Offline like the rest of the suite: no Google credentials, no network. The one
call that genuinely needs a valid RSA key - Google's own
``service_account.Credentials.from_service_account_file`` - is stubbed at the
boundary, so what is exercised here is this package's dispatch, precedence and
error handling rather than google-auth itself.
"""
import json

import pytest
from google.auth.exceptions import DefaultCredentialsError

from gsc_wrapper import credentials as creds


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Never let the developer's own GSC_* variables leak into a test."""
    for name in (
        creds.SERVICE_ACCOUNT_EMAIL_ENV,
        creds.CREDENTIALS_PATH_ENV,
        creds.SUBJECT_ENV,
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def write_json(tmp_path):
    """Write a JSON payload to a temp file and return its path."""
    def _write(payload, name="credentials.json"):
        path = tmp_path / name
        path.write_text(json.dumps(payload))
        return path
    return _write


class FakeSource:
    """A stand-in for the credentials that sign an impersonation request."""

    requires_scopes = False
    valid = True
    token = "fake-source-token"
    universe_domain = "googleapis.com"


# --- from_file -------------------------------------------------------------

def test_from_file_returns_flat_dict_untouched(write_json):
    """The historical shape ``Account`` already builds from is passed through."""
    payload = {
        "token": None,
        "refresh_token": "refresh",
        "client_id": "client",
        "client_secret": "secret",
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": ["https://www.googleapis.com/auth/webmasters.readonly"],
    }
    assert creds.from_file(write_json(payload)) == payload


def test_from_file_builds_authorized_user(write_json):
    path = write_json({
        "type": "authorized_user",
        "client_id": "client.apps.googleusercontent.com",
        "client_secret": "secret",
        "refresh_token": "refresh",
    })

    credentials = creds.from_file(path)

    assert credentials.client_id == "client.apps.googleusercontent.com"
    assert credentials.scopes == creds.READONLY_SCOPES


def test_from_file_delegates_service_account_shape(write_json, monkeypatch):
    path = write_json({"type": "service_account", "client_email": "sa@p.iam"})
    seen = {}

    def fake_builder(key_file, *, scopes=None, subject=None):
        seen.update(key_file=key_file, scopes=scopes, subject=subject)
        return "built"

    monkeypatch.setattr(creds, "from_service_account_file", fake_builder)

    assert creds.from_file(path, subject="user@example.com") == "built"
    assert seen["key_file"] == path
    assert seen["subject"] == "user@example.com"


def test_from_file_missing_path_raises(tmp_path):
    with pytest.raises(creds.CredentialsError, match="does not exist"):
        creds.from_file(tmp_path / "absent.json")


def test_from_file_invalid_json_raises(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{not json")

    with pytest.raises(creds.CredentialsError, match="not valid JSON"):
        creds.from_file(path)


def test_from_service_account_file_missing_path_raises(tmp_path):
    with pytest.raises(creds.CredentialsError, match="does not exist"):
        creds.from_service_account_file(tmp_path / "absent.json")


# --- impersonate -----------------------------------------------------------

def test_impersonate_defaults_to_readonly_scopes():
    credentials = creds.impersonate(
        "target@project.iam.gserviceaccount.com", source=FakeSource()
    )

    assert credentials.service_account_email == \
        "target@project.iam.gserviceaccount.com"
    assert credentials._target_scopes == creds.READONLY_SCOPES


def test_impersonate_honours_explicit_scopes():
    credentials = creds.impersonate(
        "target@project.iam.gserviceaccount.com",
        scopes=creds.READWRITE_SCOPES,
        source=FakeSource(),
    )

    assert credentials._target_scopes == creds.READWRITE_SCOPES


def test_impersonate_uses_adc_when_no_source(monkeypatch):
    """ADC is the default signer, and it is scoped to cloud-platform."""
    seen = {}

    def fake_default(scopes=None):
        seen["scopes"] = scopes
        return FakeSource(), "project"

    monkeypatch.setattr("google.auth.default", fake_default)

    creds.impersonate("target@project.iam.gserviceaccount.com")

    assert seen["scopes"] == creds.IMPERSONATION_SCOPES


def test_impersonate_without_adc_raises_actionable_error(monkeypatch):
    def fake_default(scopes=None):
        raise DefaultCredentialsError("no ADC here")

    monkeypatch.setattr("google.auth.default", fake_default)

    with pytest.raises(creds.CredentialsError, match="application-default login"):
        creds.impersonate("target@project.iam.gserviceaccount.com")


def test_impersonate_requires_a_target():
    with pytest.raises(creds.CredentialsError, match="required"):
        creds.impersonate("")


# --- from_env --------------------------------------------------------------

def test_from_env_without_configuration_raises():
    with pytest.raises(creds.CredentialsError, match="No credentials configured"):
        creds.from_env()


def test_from_env_uses_credentials_path(monkeypatch, write_json):
    path = write_json({"token": None, "client_id": "client"})
    monkeypatch.setenv(creds.CREDENTIALS_PATH_ENV, str(path))

    assert creds.from_env() == {"token": None, "client_id": "client"}


def test_from_env_passes_subject_on_the_file_route(monkeypatch, write_json):
    path = write_json({"type": "service_account"})
    monkeypatch.setenv(creds.CREDENTIALS_PATH_ENV, str(path))
    monkeypatch.setenv(creds.SUBJECT_ENV, "user@example.com")
    seen = {}

    monkeypatch.setattr(
        creds, "from_service_account_file",
        lambda key_file, *, scopes=None, subject=None: seen.update(subject=subject),
    )

    creds.from_env()

    assert seen["subject"] == "user@example.com"


def test_from_env_email_wins_and_never_reads_the_key_path(monkeypatch, tmp_path):
    """The documented rule: naming an account means no key on disk is consulted.

    A path is set *and* points at a real file, so a fallback would silently
    succeed as the wrong principal instead of impersonating the named one.
    """
    stray = tmp_path / "stray-key.json"
    stray.write_text(json.dumps({"type": "service_account"}))
    monkeypatch.setenv(creds.CREDENTIALS_PATH_ENV, str(stray))
    monkeypatch.setenv(
        creds.SERVICE_ACCOUNT_EMAIL_ENV, "target@project.iam.gserviceaccount.com"
    )
    monkeypatch.setattr(
        creds, "from_file",
        lambda *a, **kw: pytest.fail("the key path must not be read"),
    )
    monkeypatch.setattr("google.auth.default", lambda scopes=None: (FakeSource(), "p"))

    credentials = creds.from_env()

    assert credentials.service_account_email == \
        "target@project.iam.gserviceaccount.com"


def test_from_env_ignores_blank_values(monkeypatch, write_json):
    """A commented-out or emptied variable must not shadow the other route."""
    path = write_json({"client_id": "client"})
    monkeypatch.setenv(creds.SERVICE_ACCOUNT_EMAIL_ENV, "   ")
    monkeypatch.setenv(creds.CREDENTIALS_PATH_ENV, str(path))

    assert creds.from_env() == {"client_id": "client"}
