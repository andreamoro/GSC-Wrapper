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

There are two ways to satisfy that access requirement. Pick **one**.

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
site = Authenticate(method="service")
# or pass an explicit key path:
#   authenticate_service_account("/path/to/key.json")
```

Done — no browser, no consent screen.

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

Delegation does not *bypass* the access requirement — it shifts it from "the
service account has access" to "the user it impersonates has access."

---

## Configuration in this repo's tests

`tests/standalone_sync.py` exposes a small dispatcher so you can switch flows
without touching the rest of the code:

```python
site = Authenticate(method="service")   # programmatic service account
site = Authenticate(method="oauth")     # interactive user login (Selenium)
site = Authenticate(method="test")      # offline fake account
```

By default the service-account flow reads the key path from a `key_file`
entry under `[credentials.service]` in `tests/config.toml`:

```toml
[credentials.service]
key_file = "/absolute/path/to/key.json"
# subject = "you@yourdomain.com"   # optional: domain-wide delegation
```

If no path is provided (neither as an argument nor in `config.toml`), or the
file does not exist, authentication fails loudly with a clear error rather
than silently falling back.

---

## Troubleshooting

| Symptom | Cause / Fix |
| --- | --- |
| **"Invalid scope"** in the Admin console | You used the short name. Use the full `https://www.googleapis.com/auth/webmasters.readonly` URL. |
| `account[...]` returns `None` / empty list | The calling identity has no access to the property. Grant the service account (Option A) or impersonate a user with access (Option B). |
| `403 / insufficient permissions` | Wrong scope authorized, or write action attempted with a read-only scope. |
| Delegation page won't accept the Client ID | Use the service account's numeric **Unique ID**, not its email; ensure delegation is enabled on the service account. |
| Delegation doesn't work at all | You're on a personal Google account — domain-wide delegation requires Google Workspace. Use Option A instead. |
