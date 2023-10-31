import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import gsc_wrapper
import logging
import configparser

from google_auth_oauthlib.flow import Flow

# from google.oauth2 import
# import google.oauth2.credentials

# from google_auth_oauthlib.flow import InstalledAppFlow
from dateutil.relativedelta import relativedelta
from datetime import date


if __name__ == "__main__":
    test = True

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
        token = ""
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
        site_list = account.webproperties()
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

    # data = site.query.range(startDate=date(2022, 10, 10), endDate=date(2022, 11, 10))
    # print(site.query.raw)
    # assert site.query.startDate < site.query.endDate, "Error"
    # print()

    # End data lower than starting date, expected correction
    # data = site.query.range(startDate=date(2022, 11, 10), endDate=date(2022, 10, 10))
    # print(site.query.raw)
    # print(site.query.filters)
    # assert site.query.startDate < site.query.endDate, "Error"
    # print()

    # # String date arguments, date are valid, no problems are expected
    # data = site.query.range(startDate='2022-10-10', endDate='2022-11-10')
    # print(site.query.raw)
    # assert site.query.startDate == date(2022, 10, 10) and site.query.endDate == date(2022, 11, 10), "Error"
    # print()

    # # Start date greater than ending date, expected correction
    # # In fact, as the startDate is in the future, the date is expected to be reset to today's date (26/11)
    # data = site.query.range(startDate='2022-12-10', endDate='2022-11-10')
    # print(site.query.raw)
    # assert site.query.startDate < site.query.endDate, "Error. Start date is lower than end date."
    # print()

    # # Expected endDate 1 day from startdate 2022-11-10 = 2022-11-11
    # data = site.query.range(startDate=date(2022, 11, 10), days=1, months=0)
    # assert site.query.startDate == date(2022, 11, 10) and site.query.endDate == date(2022, 11, 11), "Error"
    # print(site.query.raw)
    # print()

    # # Expected + 1 days + 1 month with startdate 2022-10-10 = 2022-11-11
    # data = site.query.range(startDate=date(2022, 10, 10), days=1, months=1)
    # assert site.query.startDate == date(2022, 10, 10) and site.query.endDate == date(2022, 11, 11), "Error"
    # print(site.query.raw)
    # print()

    # # Expected a today endDate as end date as I'm passing a future date
    # data = site.query.range(startDate=date.today(), days=0, months=1)
    # assert site.query.startDate == site.query.endDate, "Error"
    # print(site.query.raw)
    # print()

    # # Expected adjustments on the startDate going over the
    # # 16 months allowance
    # data = site.query.range(startDate=date.today(), days=0, months=-20)
    # print(site.query.raw)
    # assert site.query.endDate == date.today() + relativedelta(days=-1 if site.query.raw.get('dataState') == 'final' else 0) and \
    #         site.query.startDate == date.today() + relativedelta(months=-16, days=-1 if site.query.raw.get('dataState') == 'final' else 0), "Error"
    # print()

    # # Expected endDate +1 month = 2022-11-10
    # data = site.query.range(startDate='2022-10-10', days=0, months=1)
    # assert site.query.endDate == date(2022, 11, 10), "Error"
    # print(site.query.raw)

    # # Expected Startdate adjusted to 2022-09-10 enddate to 2022-10-10
    # data = site.query.range(startDate='2022-10-10', days=0, months=-1)
    # assert site.query.endDate == date(2022, 10, 10) and site.query.startDate == date(2022,9,10), "Error"
    # print(site.query.raw)

    # data = (
    #     site.query.range(startDate=date.today(), days=-5, months=0)
    #     .search_type(gsc_wrapper.search_type.WEB)
    #     .dimensions(gsc_wrapper.dimension.DATE)
    #     .filter(
    #         country=gsc_wrapper.country.ITALY,
    #         operator=gsc_wrapper.operator.EQUALS,
    #         append=False,
    #     )
    #     .execute()
    # )

    # logging.warning(site.query.raw)
    # logging.info(data.get('rows'))

    # report = (
    #     site.query.range(startDate=date.today(), days=-10, months=0)
    #     .dimensions(gsc_wrapper.dimension.DATE)
    #     .get()
    # )

    data = site.query.range(startDate=date.today(), days=1, months=0)
    data = site.query.filter(
        country=gsc_wrapper.country.ITALY,
        operator=gsc_wrapper.operator.EQUALS,
        append=False,
    )
    assert site.query.filters == [
        {"dimension": "country", "expression": "ITA", "operator": "equals"}
    ], "Error"

    data = site.query.filter_remove(gsc_wrapper.country.ITALY)
    data = site.query.search_type(gsc_wrapper.search_type.WEB)

    data = (
        site.query.filter(gsc_wrapper.country.ITALY)
        .range(date.today(), months=-1)
        .dimensions(gsc_wrapper.dimension.DATE, gsc_wrapper.dimension.PAGE)
    )
    # At this stage the country should contain again ITALY
    data = site.query.filter(gsc_wrapper.country.ALBANIA, append=True).search_type(
        gsc_wrapper.search_type.IMAGE
    )
    # At this stage the country should contain also ALBANIA

    assert site.query.filters == [
        {"dimension": "country", "expression": "ITA", "operator": "equals"},
        {"dimension": "country", "expression": "ALB", "operator": "equals"},
    ], "Error"

    pass
    # *** Execute a query and return the whole dataset
    # report = data.get()

    # *** Execute a query against a sliced set of data
    # Here you can reuse the same object as before.
    # Retrieved data are copied at a report level as opposed to Carty's library
    # where the whole class and every change where deeply copied
    # data = site.query.filter(gsc_wrapper.country.UNITED_KINGDOM).range(date.today(), months=-1)\
    #         .dimensions(gsc_wrapper.dimension.DATE, gsc_wrapper.dimension.PAGE).execute()
    # report2 = gsc_wrapper.Report(site.url, site.query.raw, data.get('rows'))

    # data = site.query.filter(gsc_wrapper.country.ITALY).range(date.today(), months=-1)\
    #         .dimensions(gsc_wrapper.dimension.DATE, gsc_wrapper.dimension.PAGE)
    # report = data.get()

    # *** Persist data on disk
    # report.to_disk('https_www_andreamoro_eu.pck')
    # pass
    # *** Restore a report persisted on disk
    report = gsc_wrapper.Report.from_disk("https_www_andreamoro_eu.pck")
    pass
