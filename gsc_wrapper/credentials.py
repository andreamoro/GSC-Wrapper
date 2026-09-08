"""Optional helpers for building the credentials ``Account`` expects.

Nothing in this module is required. :class:`~gsc_wrapper.account.Account` and
:class:`~gsc_wrapper.aio.account.AsyncAccount` keep accepting exactly what they
always have - a ``dict`` of OAuth user credentials or an already-built
``google.auth`` credentials object - and the authentication *flow* is still
external to the wrapper by design. These helpers only spare you from
re-implementing the fiddly parts of the three non-interactive routes:

* **Service account key** - a JSON key file on disk, optionally with Workspace
  domain-wide delegation (``subject``). See :func:`from_service_account_file`.
* **Application Default Credentials (ADC) with impersonation** - name a service
  account by email and let ADC sign the token request, so no key for the target
  is held anywhere. See :func:`impersonate`. This is the route that works where
  organisation policy forbids creating service-account keys
  (``constraints/iam.disableServiceAccountKeyCreation``).
* **Environment-driven** - resolve either of the above from ``GSC_*``
  environment variables. See :func:`from_env`.

Whichever route is taken, the identity that ends up calling the API must be
added as a user on each property in the Search Console UI. IAM says who you may
act *as*; it says nothing about which properties that identity can read - and
impersonating does not inherit the source identity's Search Console access.

Usage:
>>> from gsc_wrapper import Account, credentials
>>> account = Account(credentials.impersonate("me@project.iam.gserviceaccount.com"))
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from google.auth.credentials import Credentials as GoogleCredentials

# Read-only Search Analytics access, which is all a reporting client needs.
READONLY_SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

# Add this when a write action is required (e.g. submitting a sitemap).
READWRITE_SCOPES = ["https://www.googleapis.com/auth/webmasters"]

# Impersonation is authorised by the IAM Credentials API, which is gated on
# cloud-platform - NOT on the Search Console scope. The source identity is
# therefore built with this, and only the token it mints for the target carries
# the Search Console scopes. Getting the two the wrong way round yields a 403
# from iamcredentials.googleapis.com that reads like a permissions problem.
IMPERSONATION_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

# Environment variables read by ``from_env``.
SERVICE_ACCOUNT_EMAIL_ENV = "GSC_SERVICE_ACCOUNT_EMAIL"
CREDENTIALS_PATH_ENV = "GSC_CREDENTIALS_PATH"
SUBJECT_ENV = "GSC_SUBJECT"


class CredentialsError(Exception):
    """Raised when credentials cannot be resolved or built.

    Every failure in this module is deliberately loud: a misconfigured
    environment should stop the run rather than quietly authenticate as some
    other principal.
    """


def from_service_account_file(
    key_file: str | Path,
    *,
    scopes: list[str] | None = None,
    subject: str | None = None,
) -> GoogleCredentials:
    """Build service-account credentials from a JSON key file.

    By default the calls are made *as the service account itself*, so its email
    must be granted access to the property in Search Console. Pass ``subject``
    to impersonate a real user instead, via Google Workspace domain-wide
    delegation - which requires a Workspace domain and does not work on a
    personal Google account.

    Args:
        key_file: Path to the service account JSON key.
        scopes: OAuth scopes to request. Defaults to ``READONLY_SCOPES``.
        subject: Email of the Workspace user to impersonate through
            domain-wide delegation. Omit to act as the service account.

    Returns:
        A ``google.oauth2.service_account.Credentials`` instance, ready to be
        handed to ``Account`` or ``AsyncAccount``.

    Raises:
        CredentialsError: If the path does not point to an existing file.
    """
    from google.oauth2 import service_account

    path = Path(key_file).expanduser()
    if not path.is_file():
        raise CredentialsError(
            f"The service account key file '{path}' does not exist."
        )

    credentials = service_account.Credentials.from_service_account_file(
        str(path), scopes=scopes or READONLY_SCOPES
    )
    return credentials.with_subject(subject) if subject else credentials


def from_file(
    credentials_file: str | Path,
    *,
    scopes: list[str] | None = None,
    subject: str | None = None,
) -> dict | GoogleCredentials:
    """Load credentials from a JSON file, whatever shape Google wrote it in.

    Three shapes are recognised, distinguished by the ``type`` key:

    * ``"service_account"`` - a downloaded service-account key, built exactly
      as :func:`from_service_account_file` would.
    * ``"authorized_user"`` - the file ``gcloud auth application-default
      login`` writes, or any stored OAuth user credential.
    * anything else - returned as the raw ``dict``, which is the historical
      flat mapping (``token``, ``refresh_token``, ``client_id``, ...) that
      ``Account`` already knows how to build from.

    Args:
        credentials_file: Path to the JSON file.
        scopes: OAuth scopes to request. Defaults to ``READONLY_SCOPES``. Only
            meaningful for the service-account and authorized-user shapes; a
            raw dict carries whatever scopes its token was minted with.
        subject: Domain-wide delegation subject. Service-account shape only.

    Returns:
        Either a ``google.auth`` credentials object or the raw ``dict``. Both
        are accepted by ``Account`` and ``AsyncAccount``.

    Raises:
        CredentialsError: If the file is missing or is not valid JSON.
    """
    path = Path(credentials_file).expanduser()
    if not path.is_file():
        raise CredentialsError(
            f"The credentials file '{path}' does not exist."
        )

    try:
        info = json.loads(path.read_text())
    except ValueError as e:
        raise CredentialsError(
            f"The credentials file '{path}' is not valid JSON.\n{e}"
        ) from e

    kind = info.get("type") if isinstance(info, dict) else None

    if kind == "service_account":
        return from_service_account_file(path, scopes=scopes, subject=subject)

    if kind == "authorized_user":
        from google.oauth2.credentials import Credentials

        return Credentials.from_authorized_user_info(
            info, scopes=scopes or READONLY_SCOPES
        )

    return info


def impersonate(
    target_principal: str,
    *,
    scopes: list[str] | None = None,
    source: GoogleCredentials | None = None,
    delegates: list[str] | None = None,
    lifetime: int = 3600,
) -> GoogleCredentials:
    """Impersonate a service account, without holding a key for it.

    An email is an identity, not a credential, so something still has to sign
    the token request. That signer is ``source`` when given, and otherwise
    Application Default Credentials - an attached service account on GCE or
    Cloud Run, or a local ``gcloud auth application-default login``. Only the
    ADC case removes the key file entirely; off GCP compute an explicit
    ``source`` usually means swapping one key for another.

    Three prerequisites live outside this library, all on Google's side:

    * the IAM Credentials API (``iamcredentials.googleapis.com``) enabled on
      the quota project;
    * the source identity holding ``roles/iam.serviceAccountTokenCreator`` on
      the target account;
    * the **target** email added as a user on each property in the Search
      Console UI.

    ADC silently uses whichever account was last logged in, so a 403 here is as
    often the wrong source identity as it is a missing grant.

    Args:
        target_principal: Email of the service account to impersonate.
        scopes: Scopes for the *minted* token. Defaults to
            ``READONLY_SCOPES``.
        source: Credentials that sign the impersonation request. Defaults to
            Application Default Credentials, scoped to
            ``IMPERSONATION_SCOPES``.
        delegates: Intermediate service accounts for a delegation chain, when
            the source cannot mint for the target directly.
        lifetime: Lifetime of the minted access token, in seconds.

    Returns:
        A ``google.auth.impersonated_credentials.Credentials`` instance.

    Raises:
        CredentialsError: If no target is given, or if no Application Default
            Credentials could be found to impersonate *from*.
    """
    import google.auth
    from google.auth import impersonated_credentials
    from google.auth.exceptions import DefaultCredentialsError

    if not target_principal:
        raise CredentialsError(
            "A target service account email is required to impersonate."
        )

    if source is None:
        try:
            source, _project = google.auth.default(scopes=IMPERSONATION_SCOPES)
        except DefaultCredentialsError as e:
            raise CredentialsError(
                f"Impersonation of '{target_principal}' was requested, but no "
                "Application Default Credentials were found to impersonate "
                "FROM.\nRun `gcloud auth application-default login` as a "
                "principal holding roles/iam.serviceAccountTokenCreator on "
                "that account, run on a box with an attached service account, "
                "or pass an explicit `source` credential.\n"
                f"{e}"
            ) from e

    return impersonated_credentials.Credentials(
        source_credentials=source,
        target_principal=target_principal,
        target_scopes=scopes or READONLY_SCOPES,
        delegates=delegates,
        lifetime=lifetime,
    )


def from_env(
    *,
    scopes: list[str] | None = None,
) -> dict | GoogleCredentials:
    """Resolve credentials from the environment.

    Two routes, and ``GSC_SERVICE_ACCOUNT_EMAIL`` wins whenever it is set:

    * ``GSC_SERVICE_ACCOUNT_EMAIL`` - impersonate that service account off
      Application Default Credentials, as :func:`impersonate` does.
    * ``GSC_CREDENTIALS_PATH`` - a *path* to a JSON credentials file, read by
      :func:`from_file`. Used only when no email is set. A path rather than
      inlined JSON because environment values have no escaping standard and
      Google's own libraries expect a file anyway.

    ``GSC_SUBJECT`` is honoured on the file route only, for Workspace
    domain-wide delegation.

    The key file is deliberately **not** a fallback signer for impersonation.
    Naming an account by email is a statement that this machine holds no key
    for it; quietly signing with some other key that happens to be on disk
    would authenticate as a principal nobody named, and would make a
    misconfigured environment look like it worked. Pass ``source`` to
    :func:`impersonate` directly when that is genuinely what you want.

    Reading a ``.env`` file is the application's job, not the library's: load
    it (e.g. with ``python-dotenv``) before calling this.

    Args:
        scopes: OAuth scopes to request. Defaults to ``READONLY_SCOPES``.

    Returns:
        Credentials for whichever route was configured, ready for ``Account``.

    Raises:
        CredentialsError: If neither variable is set, so that a missing
            configuration fails here rather than at the first API call.
    """
    email = os.environ.get(SERVICE_ACCOUNT_EMAIL_ENV, "").strip()
    if email:
        return impersonate(email, scopes=scopes)

    path = os.environ.get(CREDENTIALS_PATH_ENV, "").strip()
    if path:
        subject = os.environ.get(SUBJECT_ENV, "").strip() or None
        return from_file(path, scopes=scopes, subject=subject)

    raise CredentialsError(
        f"No credentials configured. Set {SERVICE_ACCOUNT_EMAIL_ENV} to "
        f"impersonate a service account through Application Default "
        f"Credentials, or {CREDENTIALS_PATH_ENV} to the path of a JSON "
        f"credentials file."
    )
