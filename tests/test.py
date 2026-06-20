import configparser
import time

from google_auth_oauthlib.flow import Flow
from google.oauth2 import service_account
from datetime import date
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import gsc_wrapper
from gsc_wrapper.query import Report as ReportQuery
from gsc_wrapper.inspection import Report as ReportInspection


SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
SITE_URL = "https://www.andreamoro.eu/"


def AuthenticationSteps(browser, config):
    from selenium.webdriver import Keys
    from selenium.webdriver.common.by import By

    if "opparams" in browser.current_url:
        # Login is required again
        username = browser.find_element(By.ID, "identifierId")
        username.send_keys(config["web_authentication"]["email"])
        username.send_keys(Keys.ENTER)
        return

        # while "opparams" in browser.current_url:
        #     time.sleep(2)

    if "/pwd" in browser.current_url:
        password = browser.find_element(
            By.XPATH, "//form//input[@type='password']"
        )
        password.send_keys(config["web_authentication"]["password"])
        password.send_keys(Keys.ENTER)
        return

        # while "pwd" in browser.current_url: # challenge
        #     time.sleep(2)

    if "oauthchooseaccount" in browser.current_url:
        button = browser.find_element(
            By.XPATH, "//*/ul[@class='OVnw0d']/li[1]/div"
        )
        button.click()
        return

        # while "oauthchooseaccount" in browser.current_url:
        #     time.sleep(2)

    if "consent" in browser.current_url and \
        "/pwd" not in browser.current_url:
        # This is the "Screen consent with the Allow button"
        button = browser.find_element(By.CSS_SELECTOR, "#submit_approve_access")
        button.click()

def authenticate_oauth() -> gsc_wrapper.WebProperty | None:
    """Interactive OAuth user flow.

    A client_id / client_secret pair is read from config.ini and the
    consent screen is driven automatically through Selenium to retrieve
    the authorisation token. Suited to acting on behalf of a human user.
    """
    config = configparser.ConfigParser()
    config.read(str(Path(__file__).parent / "config.ini"))
    client_id = config["credentials.oauth"]["client_id"]
    client_secret = config["credentials.oauth"]["client_secret"]

    credentials = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uris": [],
            "auth_uri": gsc_wrapper.GOOGLE_AUTH_URI,
            "token_uri": gsc_wrapper.GOOGLE_TOKEN_URI,
        }
    }

    flow = Flow.from_client_config(
        credentials,
        scopes=SCOPES,
        redirect_uri="urn:ietf:wg:oauth:2.0:oob",
    )

    auth_url, b = flow.authorization_url(prompt="consent")

    # The next following lines facilitate the authentication process with
    # Google Auth form.
    from selenium.webdriver import Chrome, ChromeOptions
    from selenium.webdriver.common.by import By

    # brave_path = f"{Path.home()}/.config/BraveSoftware/Brave-Browser/"

    options = ChromeOptions()
    options.binary_location = "/opt/brave.com/brave/brave"
    options.add_argument(f"--user-data-dir={Path.home()}/Downloads/GSCWrapperBraveAutomation")
    options.add_argument("--extension-process")
    # This implies a manually launched browser with the --remote-debugging-port=9222 option
    # options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    # options.add_argument("--no-sandbox")
    # options.add_argument("--disable-extensions")
    # options.add_argument("disable-infobars")
    # options.add_argument("start-maximized")

    with Chrome(options=options) as browser:
        browser.get(auth_url)
        time.sleep(2)

        while "approvalnativeapp" not in browser.current_url:
            time.sleep(2)
            AuthenticationSteps(browser, config)

        token = browser.find_element(By.CLASS_NAME, "fD1Pid").text
        browser.close()

    if token is None or len(token) == 0:
        raise Exception('The authentication token was not retrieved.')

    f = flow.fetch_token(code=token)

    credentials = {
        "token": token,
        "refresh_token": f["refresh_token"],
        "client_id": client_id,
        "client_secret": client_secret,
        "token_uri": gsc_wrapper.GOOGLE_TOKEN_URI,
        "scopes": SCOPES,
    }

    account = gsc_wrapper.Account(credentials)
    # Retrieving the sites list is implicitely done inside
    # the get_item method in the account, but if needed
    # this can be done with the following
    # site_list = account.webproperties()
    return account[SITE_URL]


def authenticate_service_account(
    key_file: str | None = None,
    subject: str | None = None,
) -> gsc_wrapper.WebProperty | None:
    """Programmatic, non-interactive flow using a service account.

    The service account JSON key is loaded and a credentials object is
    handed straight to the Account class (no browser / consent screen).

    By default the call is made *as the service account itself*, so you
    must grant the service account email access to the property in Google
    Search Console first (otherwise the web properties list comes back
    empty even though authentication succeeds).

    Alternatively, pass ``subject`` to impersonate a real user via
    domain-wide delegation. This requires a Google Workspace domain with
    delegation configured for this service account; it does NOT work on a
    personal Google account.

    Args:
        key_file: Path to the service account JSON key. When omitted, the
            ``key_file`` entry under ``[credentials.service]`` in config.ini
            is used.
        subject: Email of the Workspace user to impersonate. When omitted,
            the optional ``subject`` entry under ``[credentials.service]``
            in config.ini is used, if present.

    Raises:
        Exception: If no key file is provided and none is configured, or if
            the resolved path does not point to an existing file.
    """
    config = configparser.ConfigParser()
    config.read(str(Path(__file__).parent / "config.ini"))

    if key_file is None:
        if not config.has_option("credentials.service", "key_file"):
            raise Exception(
                "No service account key file was provided and no "
                "'key_file' entry was found under [credentials.service] "
                "in config.ini."
            )
        key_file = config.get("credentials.service", "key_file")

    if subject is None and config.has_option(
        "credentials.service", "subject"
    ):
        subject = config.get("credentials.service", "subject")

    if not Path(key_file).is_file():
        raise Exception(
            f"The service account key file '{key_file}' does not exist."
        )

    credentials = service_account.Credentials.from_service_account_file(
        key_file,
        scopes=SCOPES,
    )

    # Domain-wide delegation: act on behalf of a real Workspace user who
    # already has access to the property, rather than as the bare service
    # account identity.
    if subject:
        credentials = credentials.with_subject(subject)

    account = gsc_wrapper.Account(credentials)
    return account[SITE_URL]


def authenticate_test() -> gsc_wrapper.WebProperty | None:
    """Offline flow building a fake account to exercise the rest of the
    code without hitting Google."""
    credentials = {
        "token": None,
        "refresh_token": None,
        "client_id": None,
        "client_secret": None,
        "token_uri": gsc_wrapper.GOOGLE_TOKEN_URI,
        "scopes": "https://www.googleapis.com/auth/webmasters.readonly",
    }

    account = gsc_wrapper.Account(credentials)

    web_properties = [
        {"siteUrl": "www.test1.com", "permissionLevel": "1"},
        {"siteUrl": "www.test2.com", "permissionLevel": "1"},
        {"siteUrl": "subdomain.google.com", "permissionLevel": "1"},
    ]

    site_list = [
        gsc_wrapper.WebProperty(raw, account) for raw in web_properties
    ]
    account._webproperties = site_list
    return account["www.test1.com"]


def Authenticate(
    method: str = "oauth",
) -> gsc_wrapper.WebProperty | None:
    """Dispatch to the desired authentication flow.

    Args:
        method: One of ``"oauth"`` (interactive user login), ``"service"``
            (programmatic service account) or ``"test"`` (offline fake).
    """
    flows = {
        "oauth": authenticate_oauth,
        "service": authenticate_service_account,
        "test": authenticate_test,
    }

    if method not in flows:
        raise ValueError(
            f"Unknown authentication method '{method}'. "
            f"Choose one of: {', '.join(flows)}."
        )

    return flows[method]()


def test_search_analytics(query: gsc_wrapper.Query):
    # data = query.range(startDate=date(2022, 10, 10), endDate=date(2022, 11, 10))
    # print(query.raw)
    # assert query.startDate < query.endDate, "Error"
    # print()

    # End data lower than starting date, expected correction
    # data = query.range(startDate=date(2022, 11, 10), endDate=date(2022, 10, 10))
    # print(query.raw)
    # print(query.filters)
    # assert query.startDate < query.endDate, "Error"
    # print()

    # # String date arguments, date are valid, no problems are expected
    # data = query.range(startDate='2022-10-10', endDate='2022-11-10')
    # print(query.raw)
    # assert query.startDate == date(2022, 10, 10) and query.endDate == date(2022, 11, 10), "Error"
    # print()

    # # Start date greater than ending date, expected correction
    # # In fact, as the startDate is in the future, the date is expected to be reset to today's date (26/11)
    # data = query.range(
    #   startDate='2022-12-10',
    #   endDate='2022-11-10'
    # )
    # print(query.raw)
    # assert query.startDate < query.endDate, "Error. Start date is lower than end date."
    # print()

    # Expected endDate 1 day from startdate 2022-11-10 = 2022-11-11
    query.range(startDate=date(2022, 11, 10), days=1, months=0)
    assert \
        query.startDate == date(2022, 11, 10) and \
        query.endDate == date(2022, 11, 11), "Error"
    print(query.raw)
    print()

    # # Expected + 1 days + 1 month with startdate 2022-10-10 = 2022-11-11
    # data = query.range(startDate=date(2022, 10, 10), days=1, months=1)
    # assert \
    #   query.startDate == date(2022, 10, 10) and \
    #   query.endDate == date(2022, 11, 11), "Error"
    # print(query.raw)
    # print()

    # # Expected a today endDate as end date as I'm passing a future date
    # data = query.range(startDate=date.today(), days=0, months=1)
    # assert query.startDate == query.endDate, "Error"
    # print(query.raw)
    # print()

    # # Expected adjustments on the startDate going over the
    # # 16 months allowance
    # data = query.range(startDate=date.today(), days=0, months=-20)
    # print(query.raw)
    # assert query.endDate == date.today() + relativedelta(days=-1 if query.raw.get('dataState') == 'final' else 0) and \
    #         query.startDate == date.today() + relativedelta(months=-16, days=-1 if query.raw.get('dataState') == 'final' else 0), "Error"
    # print()

    # # Expected endDate +1 month = 2022-11-10
    # data = query.range(startDate='2022-10-10', days=0, months=1)
    # assert query.endDate == date(2022, 11, 10), "Error"
    # print(query.raw)

    # # Expected Startdate adjusted to 2022-09-10 enddate to 2022-10-10
    # data = query.range(startDate='2022-10-10', days=0, months=-1)
    # assert query.endDate == date(2022, 10, 10) and query.startDate == date(2022,9,10), "Error"
    # print(query.raw)

    # data = (
    #     query.range(startDate=date.today(), days=-5, months=0)
    #     .search_type(gsc_wrapper.search_type.WEB)
    #     .dimensions(gsc_wrapper.dimension.DATE)
    #     .filter(
    #         country=gsc_wrapper.country.ITALY,
    #         operator=gsc_wrapper.operator.EQUALS,
    #         append=False,
    #     )
    #     .execute()
    # )

    # logging.warning(query.raw)
    # logging.info(data.get('rows'))

    # report = (
    #     query.range(startDate=date.today(), days=-10, months=0)
    #     .dimensions(gsc_wrapper.dimension.DATE)
    #     .get()
    # )

    # data = query.range(startDate=date.today(), days=-10, months=0)
    # data = query.filter(
    #     country=gsc_wrapper.country.ITALY,
    #     operator=gsc_wrapper.operator.EQUALS,
    #     append=False,
    # ).dimensions(gsc_wrapper.dimension.PAGE)
    # assert query.filters == [
    #     {"dimension": "country", "expression": "ITA", "operator": "equals"}
    # ], "Error"

    # data = query.filter_remove(gsc_wrapper.country.ITALY)
    # data = query.search_type(gsc_wrapper.search_type.WEB)

    # data = (
    #     query.filter(gsc_wrapper.country.ITALY)
    #     .range(date.today(), months=-1)
    #     .dimensions(gsc_wrapper.dimension.DATE, gsc_wrapper.dimension.PAGE)
    # )
    # # At this stage the country should contain again ITALY
    # data = query.filter(gsc_wrapper.country.ALBANIA, append=True).search_type(
    #     gsc_wrapper.search_type.IMAGE
    # )
    # # At this stage the country should contain also ALBANIA

    # assert query.filters == [
    #     {"dimension": "country", "expression": "ITA", "operator": "equals"},
    #     {"dimension": "country", "expression": "ALB", "operator": "equals"},
    # ], "Error"

    # pass
    # *** Execute a query and return the whole dataset in a Report
    # report = data.get()

    # *** Execute a query against a sliced set of data
    # Here you can reuse the same object as before.
    # Retrieved data are copied at a report level as opposed to Carty's library
    # where the whole class and every change where deeply copied
    # data = query.filter(gsc_wrapper.country.UNITED_KINGDOM).range(date.today(), months=-1)\
    #         .dimensions(gsc_wrapper.dimension.DATE, gsc_wrapper.dimension.PAGE).execute()
    # report2 = gsc_wrapper.Report(site.url, query.raw, data.get('rows'))

    # data = query.filter(gsc_wrapper.country.ITALY).range(date.today(), months=-1)\
    #         .dimensions(gsc_wrapper.dimension.DATE, gsc_wrapper.dimension.PAGE)
    # report = data.get()

    # *** Persist data on disk
    # report.to_disk('https_www_andreamoro_eu.pck')
    # pass
    # *** Restore a report persisted on disk
    # report = ReportQuery.from_disk("https_www_andreamoro_eu.pck")
    # pass


def test_url_inspection(site):
    inspect = gsc_wrapper.InspectURL(site)
    inspect.add_url(["https://www.andreamoro.eu/"])
    inspect.add_url("https://www.andreamoro.eu/contattami").add_url('https://www.andreamoro.eu/blog/')

    Report = inspect.get()
    # data = inspect.execute()
    df = Report.to_dataframe()
    df.head()

    # Testing the cache
    # At this stage, by calling something different should invalidate the cache
    inspect.add_url("https://www.andreamoro.eu/contattami").add_url('https://www.andreamoro.eu/blog/')
    inspect.add_url("https://www.andreamoro.eu/contattami", True)
    Report = inspect.get()
    df2 = Report.to_dataframe()
    df2.head()

    # Report.to_disk()

    Report = ReportInspection.from_disk('20231203_https_www_andreamoro_eu__inspection.pck')
    Report.to_dataframe()

    pass
    # inspect.remove_url("url")
    # inspect.remove_url(0)

if __name__ == "__main__":
    site = ''
    # method="oauth" -> interactive user login (Selenium-driven consent)
    # method="service" -> programmatic service account (no browser)
    # method="test" -> offline fake account
    site = Authenticate(method="service")

    # Test the Search Analytics part
    # query = gsc_wrapper.Query(site)
    # test_search_analytics(query)

    # Test the URL Inspection part
    test_url_inspection(site)

    pass
