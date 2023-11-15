import logging
import configparser
import time

from google_auth_oauthlib.flow import Flow
from dateutil.relativedelta import relativedelta
from datetime import date
from pathlib import Path

import sys

# import os
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, str(Path(__file__).parent.parent))
import gsc_wrapper


if __name__ == "__main__":
    test = False

    # sys.addaudithook(print)
    # import webbrowser
    # webbrowser.open("https://www.google.com")

    if not test:
        config = configparser.ConfigParser()
        config.read("./tests/config.ini")
        client_id = config["credentials"]["client_id"]
        client_secret = config["credentials"]["client_secret"]

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
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
            redirect_uri="urn:ietf:wg:oauth:2.0:oob",
        )

        auth_url, b = flow.authorization_url(prompt="consent")

        # The next following lines facilitate the authentication process with
        # Google Auth form.
        from selenium.webdriver import Chrome, Keys, ChromeOptions
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By

        brave_path = f"{Path.home()}/.config/BraveSoftware/Brave-Browser/"

        options = ChromeOptions()
        options.binary_location = "/opt/brave.com/brave/brave"
        options.add_argument(f"--user-data-dir={Path.home()}/Downloads")
        options.add_argument("--extension-process")
        # This implies a manually launched browser with the --remote-debugging-port=9222 option
        # options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
        # options.add_argument("--no-sandbox")
        # options.add_argument("--disable-extensions")
        # options.add_argument("disable-infobars")
        # options.add_argument("start-maximized")

        browser = Chrome(options=options)
        browser.get(auth_url)
        time.sleep(2)

        if browser.current_url != auth_url:
            # Login is required again
            username = browser.find_element(By.ID, "identifierId")
            username.send_keys(config["web_authentication"]["email"])
            username.send_keys(Keys.ENTER)

            time.sleep(2)

            password = browser.find_element(By.XPATH, "//form//input[@name='Passwd']")
            password.send_keys(config["web_authentication"]["password"])
            password.send_keys(Keys.ENTER)

            time.sleep(2)
            # Here we need the verification to continue with human interaction
            pass

            button = browser.find_element(By.CSS_SELECTOR, "#submit_approve_access")
            button.click()

        token = browser.find_element(By.CLASS_NAME, "fD1Pid").text
        browser.close()

        f = flow.fetch_token(code=token)

        credentials = {
            "token": token,
            "refresh_token": f["refresh_token"],
            "client_id": client_id,
            "client_secret": client_secret,
            "token_uri": gsc_wrapper.GOOGLE_TOKEN_URI,
            "scopes": ["https://www.googleapis.com/auth/webmasters.readonly"],
        }

        account = gsc_wrapper.Account(credentials)
        # Retrieving the sites list is implicitely done inside
        # the get_item method in the account, but if needed
        # this can be done with the following
        # site_list = account.webproperties()
        site = account["https://www.andreamoro.eu/"]

    else:
        # Build a fake object to test the rest of the code only.
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

        site_list = [gsc_wrapper.WebProperty(raw, account) for raw in web_properties]
        account._webproperties = site_list
        site = account["www.test1.com"]
    pass
    query = gsc_wrapper.Query(site)

    data = query.range(startDate=date(2022, 10, 10), endDate=date(2022, 11, 10))
    print(query.raw)
    assert query.startDate < query.endDate, "Error"
    print()

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
    # data = query.range(startDate='2022-12-10', endDate='2022-11-10')
    # print(query.raw)
    # assert query.startDate < query.endDate, "Error. Start date is lower than end date."
    # print()

    # # Expected endDate 1 day from startdate 2022-11-10 = 2022-11-11
    # data = query.range(startDate=date(2022, 11, 10), days=1, months=0)
    # assert query.startDate == date(2022, 11, 10) and query.endDate == date(2022, 11, 11), "Error"
    # print(query.raw)
    # print()

    # # Expected + 1 days + 1 month with startdate 2022-10-10 = 2022-11-11
    # data = query.range(startDate=date(2022, 10, 10), days=1, months=1)
    # assert query.startDate == date(2022, 10, 10) and query.endDate == date(2022, 11, 11), "Error"
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

    data = query.range(startDate=date.today(), days=1, months=0)
    data = query.filter(
        country=gsc_wrapper.country.ITALY,
        operator=gsc_wrapper.operator.EQUALS,
        append=False,
    )
    assert query.filters == [
        {"dimension": "country", "expression": "ITA", "operator": "equals"}
    ], "Error"

    data = query.filter_remove(gsc_wrapper.country.ITALY)
    data = query.search_type(gsc_wrapper.search_type.WEB)

    data = (
        query.filter(gsc_wrapper.country.ITALY)
        .range(date.today(), months=-1)
        .dimensions(gsc_wrapper.dimension.DATE, gsc_wrapper.dimension.PAGE)
    )
    # At this stage the country should contain again ITALY
    data = query.filter(gsc_wrapper.country.ALBANIA, append=True).search_type(
        gsc_wrapper.search_type.IMAGE
    )
    # At this stage the country should contain also ALBANIA

    assert query.filters == [
        {"dimension": "country", "expression": "ITA", "operator": "equals"},
        {"dimension": "country", "expression": "ALB", "operator": "equals"},
    ], "Error"

    pass
    # *** Execute a query and return the whole dataset
    report = data.get()

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
    report = gsc_wrapper.Report.from_disk("https_www_andreamoro_eu.pck")
    pass
