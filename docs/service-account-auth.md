# Authenticating with a Service Account

This guide covers the **programmatic, non-interactive** way to authenticate
against the Google Search Console API using a *service account*, as an
alternative to the interactive OAuth user flow.

A service account is best suited to automation: scheduled jobs, servers, CI,
etc. — anywhere a human is not present to click through a consent screen.

> **Key concept:** a service account is a *distinct identity* with its own
> email address (`...@....iam.gserviceaccount.com`). It is **not** your Google
> account. Whatever identity makes the API call must have access to the
> property in Search Console.

There are three ways to satisfy that access requirement. Pick **one**.

| | Route | Holds a key? | Requires |
| --- | --- | --- | --- |
| **A** | Service account added to the property | yes, a JSON key | any Google account |
| **B** | Domain-wide delegation (impersonate a user) | yes, a JSON key | Google Workspace + super admin |
| **C** | ADC impersonation of the service account | **no** | Google Cloud IAM |

Option C is the one to reach for when organisation policy forbids creating
service-account keys at all (`constraints/iam.disableServiceAccountKeyCreation`),
which is common on corporate projects.

---

## Option A — Grant the service account directly (simplest)

Works with **any** Google account (personal or Workspace).

### 1. Create the service account & key

1. Open the [Google Cloud Console → Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts).
2. Select (or create) the project that has the **Search Console API** enabled
   ([enable it here](https://console.cloud.google.com/apis/library/searchconsole.googleapis.com)).
3. Click **Create service account**, give it a name, and finish.
4. Open the service account → **Keys** tab → **Add key** → **Create new key** →
   **JSON**. A `.json` key file downloads — keep it safe and **out of version
   control**.
5. Copy the service account's **email** (`...@....iam.gserviceaccount.com`).

### 2. Grant it access in Search Console

1. Open [Google Search Console](https://search.google.com/search-console).
2. Select your property → **Settings** → **Users and permissions**.
3. Click **Add user**, paste the service account **email**, set a permission
   level (Full or Restricted), and save.

### 3. Authenticate in code

```python
from gsc_wrapper import Account, credentials

account = Account(credentials.from_service_account_file("/path/to/key.json"))
site = account["https://www.yourdomain.com/"]
```

Done — no browser, no consent screen.

In this repo's manual scripts the same flow is reachable through the
dispatcher:

```python
site = Authenticate(method="service")
# or pass an explicit key path:
#   authenticate_service_account("/path/to/key.json")
```

---

## Option B — Domain-wide delegation / impersonation (Google Workspace only)

Use this when you do **not** want to add the bare service account to the
property, and instead let it *impersonate a real user* who already has access.

> **Requirements:**
> - A **Google Workspace** domain (this does **not** work on personal
>   `@gmail.com` accounts).
> - **Super admin** rights to the Workspace.
> - The impersonated user must be a member of your domain **and** already have
>   access to the Search Console property.

### 1. Enable delegation on the service account

In the [Cloud Console → Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts),
open the service account and make sure **domain-wide delegation** is enabled
(under *Advanced settings* / *Show domain-wide delegation*). Note its
**Unique ID** (a long number, also called the OAuth 2 Client ID) — you'll need
it next.

### 2. Authorize the scope in the Admin console

1. Go to **[admin.google.com/ac/owl/domainwidedelegation](https://admin.google.com/ac/owl/domainwidedelegation)**
   (signed in as a super admin).
   - Menu equivalent: **Security → Access and data control → API controls →
     Domain-wide delegation → Manage Domain Wide Delegation**.
2. Click **Add new**.
3. **Client ID** → paste the service account's **Unique ID** (the number, *not*
   the email).
4. **OAuth scopes** → paste the **full scope URL** (comma-delimited if more
   than one):

   ```
   https://www.googleapis.com/auth/webmasters.readonly
   ```

   > ⚠️ Entering just `webmasters.readonly` gives an **"Invalid scope"** error.
   > It must be the complete `https://www.googleapis.com/auth/...` URL.
   >
   > Add `https://www.googleapis.com/auth/webmasters` as well if you need write
   > access (e.g. submitting URL inspection requests).

5. Click **Authorise**.

### 3. Authenticate in code (impersonating a user)

```python
from google.oauth2 import service_account

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

credentials = service_account.Credentials.from_service_account_file(
    "/path/to/key.json", scopes=SCOPES,
).with_subject("you@yourdomain.com")   # the user being impersonated

account = gsc_wrapper.Account(credentials)
site = account["https://www.yourdomain.com/"]
```

Or, equivalently, with the helper — `subject` is what turns Option A into
Option B:

```python
from gsc_wrapper import Account, credentials

account = Account(credentials.from_service_account_file(
    "/path/to/key.json", subject="you@yourdomain.com",
))
```

Delegation does not *bypass* the access requirement — it shifts it from "the
service account has access" to "the user it impersonates has access."

---

## Option C — Application Default Credentials + impersonation (keyless)

Use this when you do not want to hold a key for the service account *at all* —
either because organisation policy forbids creating service-account keys, or
because you would simply rather not have one on disk.

You name the service account by **email**, and something else signs the token
request on its behalf. An email is an identity, not a credential: the signer is
[Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials)
(ADC) — an attached service account on GCE/Cloud Run/GKE, or your own login
locally.

> **Requirements:**
> - The IAM Credentials API (`iamcredentials.googleapis.com`) enabled on the
>   ADC quota project.
> - The **source** identity (your ADC) holding
>   `roles/iam.serviceAccountTokenCreator` on the target service account.
> - The **target** email added as a user on each Search Console property.
>   Impersonating does *not* inherit the source identity's Search Console
>   access — IAM says who you may act *as*, and nothing about which properties
>   that identity can read.

### 1. Get Application Default Credentials on the machine

On GCE, Cloud Run or GKE the attached service account already *is* ADC —
nothing to do. Locally:

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
```

ADC silently uses whichever Google account the browser was already signed into,
so a later 403 is as often the wrong identity as it is a missing grant. Check
which one you actually got:

```bash
curl -s -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  https://www.googleapis.com/oauth2/v3/userinfo
```

### 2. Grant the impersonation right

On the **target** service account, grant your ADC principal
`roles/iam.serviceAccountTokenCreator`:

```bash
gcloud iam service-accounts add-iam-policy-binding \
  TARGET@PROJECT.iam.gserviceaccount.com \
  --member="user:you@yourdomain.com" \
  --role="roles/iam.serviceAccountTokenCreator"
```

### 3. Add the target to Search Console

Exactly as in Option A step 2, but using the **target** service account's
email — the identity that ends up making the call.

### 4. Authenticate in code

```python
from gsc_wrapper import Account, credentials

account = Account(
    credentials.impersonate("presence@your-project.iam.gserviceaccount.com")
)
site = account["https://www.yourdomain.com/"]
```

No key file is read, anywhere.

> **The scope split that trips people up.** Impersonation is authorised by the
> IAM Credentials API, which is gated on `cloud-platform` — *not* on the Search
> Console scope. So the **source** identity is built with `cloud-platform`, and
> only the token it mints for the **target** carries
> `webmasters.readonly`. `impersonate()` does this for you; getting the two the
> wrong way round by hand yields a 403 from `iamcredentials.googleapis.com`
> that reads like an ordinary permissions problem.

### Deploying it elsewhere

`gcloud auth application-default login` writes
`~/.config/gcloud/application_default_credentials.json`. Copy that file to the
target machine and point `GOOGLE_APPLICATION_CREDENTIALS` at it — the gcloud
SDK creates the file but is never needed to *use* it. Note that it is a **user**
credential: your identity, broad scope, audited as you, and dead the day your
account is disabled. On GCP compute, prefer an attached service account.

---

## The `gsc_wrapper.credentials` helpers

Building credentials is still **external to the wrapper** by design — `Account`
and `AsyncAccount` accept any `google.auth` credentials object, or the OAuth
dict, exactly as they always have, and you are free to keep building them
yourself. The `gsc_wrapper.credentials` module is an *optional* convenience that
saves re-implementing the fiddly parts of the routes above.

| Helper | Route |
| --- | --- |
| `from_service_account_file(key_file, *, scopes, subject)` | Option A, or Option B with `subject` |
| `impersonate(target, *, scopes, source, delegates, lifetime)` | Option C |
| `from_file(path, *, scopes, subject)` | Any JSON on disk — shape auto-detected |
| `from_env(*, scopes)` | Either route, resolved from the environment |

Every helper defaults to `credentials.READONLY_SCOPES`
(`webmasters.readonly`); pass `scopes=credentials.READWRITE_SCOPES` when you
need write access. Failures raise `credentials.CredentialsError` with an
actionable message rather than returning `None`.

`from_file` recognises the three JSON shapes Google writes, by their `type`
key — a `service_account` key, an `authorized_user` blob, or the historical
flat mapping (`token`, `refresh_token`, `client_id`, …) — so you can point it
at whatever you happen to have and let it work out the rest.

The credentials all work identically with the asynchronous API:

```python
from gsc_wrapper import AsyncAccount, credentials

async with AsyncAccount(credentials.impersonate(TARGET_EMAIL)) as account:
    site = await account.webproperty("https://www.yourdomain.com/")
```

### Resolving from the environment

`from_env()` reads two variables, and **`GSC_SERVICE_ACCOUNT_EMAIL` wins
whenever it is set**:

```bash
# Option C — keyless impersonation
GSC_SERVICE_ACCOUNT_EMAIL=presence@your-project.iam.gserviceaccount.com

# Options A / B — a PATH to the JSON, never the JSON itself
GSC_CREDENTIALS_PATH=/home/youruser/.secrets/gsc_key.json
GSC_SUBJECT=you@yourdomain.com   # optional, Option B only
```

```python
from gsc_wrapper import Account, credentials

account = Account(credentials.from_env())
```

Two deliberate choices worth knowing about:

- **A path, not inlined JSON.** Environment values have no escaping standard,
  so nested quotes in a JSON blob are fragile — and Google's libraries expect a
  file anyway.
- **The key file is not a fallback signer.** When the email is set, the path is
  not read *at all*. Naming an account by email is a statement that this machine
  holds no key for it; quietly signing with some other key that happens to be on
  disk would authenticate as a principal nobody named, and would make a
  misconfigured environment look like it worked. If you genuinely want a key to
  sign the impersonation, say so explicitly:
  `impersonate(target, source=from_service_account_file(path, scopes=credentials.IMPERSONATION_SCOPES))`.

Loading a `.env` file is the application's job, not the library's — `from_env()`
reads the process environment, so load your `.env` (with `python-dotenv` or
otherwise) before calling it. Keep both `.env` and any JSON key git-ignored and
`chmod 600`; environment variables are plaintext-on-disk obfuscation, not
encryption. That is proportionate for a single operator on their own box — move
to a secrets manager (Vault, SOPS, a cloud secret store) if this ever becomes
team-operated or multi-tenant.

---

## Configuration in this repo's tests

`tests/standalone_sync.py` exposes a small dispatcher so you can switch flows
without touching the rest of the code:

```python
site = Authenticate(method="service")   # programmatic service account (A / B)
site = Authenticate(method="adc")       # ADC impersonation, no key file (C)
site = Authenticate(method="oauth")     # interactive user login (Selenium)
site = Authenticate(method="test")      # offline fake account
```

By default the service-account flow reads the key path from a `key_file`
entry under `[credentials.service]` in `tests/config.toml`:

```toml
[credentials.service]
key_file = "/absolute/path/to/key.json"
# subject = "you@yourdomain.com"   # optional: domain-wide delegation

[credentials.adc]
# Option C: the service account to impersonate off Application Default
# Credentials. No key file is involved.
service_account_email = "presence@your-project.iam.gserviceaccount.com"
```

If no path is provided (neither as an argument nor in `config.toml`), or the
file does not exist, authentication fails loudly with a clear error rather
than silently falling back. The `adc` flow behaves the same way: it falls back
to the `GSC_SERVICE_ACCOUNT_EMAIL` environment variable and, failing that,
raises rather than guessing at an identity.

---

## Troubleshooting

| Symptom | Cause / Fix |
| --- | --- |
| **"Invalid scope"** in the Admin console | You used the short name. Use the full `https://www.googleapis.com/auth/webmasters.readonly` URL. |
| `account[...]` returns `None` / empty list | The calling identity has no access to the property. Grant the service account (Option A) or impersonate a user with access (Option B). |
| `403 / insufficient permissions` | Wrong scope authorized, or write action attempted with a read-only scope. |
| Delegation page won't accept the Client ID | Use the service account's numeric **Unique ID**, not its email; ensure delegation is enabled on the service account. |
| Delegation doesn't work at all | You're on a personal Google account — domain-wide delegation requires Google Workspace. Use Option A instead. |
| `DefaultCredentialsError` / "no Application Default Credentials" | Option C with nothing to impersonate *from*. Run `gcloud auth application-default login`, or pass an explicit `source=` to `impersonate()`. |
| `403` from `iamcredentials.googleapis.com` | Either the IAM Credentials API is not enabled on the quota project, or your ADC principal lacks `roles/iam.serviceAccountTokenCreator` on the **target**. Check *which* identity your ADC actually is before assuming the grant is missing. |
| Option C authenticates, but the property list is empty | The **target** email is not a user on the property. Impersonating does not inherit the source's Search Console access. |
| `Could not automatically determine credentials` on a server | ADC is absent on that box. Copy `application_default_credentials.json` over and set `GOOGLE_APPLICATION_CREDENTIALS`, or attach a service account to the instance. |
| `CredentialsError: No credentials configured` | `from_env()` found neither `GSC_SERVICE_ACCOUNT_EMAIL` nor `GSC_CREDENTIALS_PATH`. If they are in a `.env`, load it first — the library reads the process environment, not the file. |
