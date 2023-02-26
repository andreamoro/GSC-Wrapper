import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import gsc_wrapper
import logging
import configparser

from google_auth_oauthlib.flow import Flow
from oauth2client import GOOGLE_REVOKE_URI, GOOGLE_TOKEN_URI, GOOGLE_AUTH_URI

from dateutil.relativedelta import relativedelta

def explore_paths():
    # need to identify the leaf of the path
    # need to identify the nodes of the path
    
    
    # what I want is a ctr on a per directory basis
    
    # SOme ideas
    #https://stackoverflow.com/questions/55114008/python-group-elements-together-in-list
    #https://stackoverflow.com/questions/49975482/how-to-group-list-of-lists-in-python
    
    
    # URLs list
    #https://stackoverflow.com/questions/49975482/how-to-group-list-of-lists-in-python (leaf)
    #https://stackoverflow.com/questions/49975482/
    #https://stackoverflow.com/questions/
    #https://stackoverflow.com/
    #https://stackoverflow.com/tags
    #https://stackoverflow.com/questions/tagged/javascript
    #https://stackoverflow.com/questions/tagged/
    
    # On a first pass
    # - Order by alphabetically (Not sure this is required)
    # - Removing duplicates (shouldn't exist, but safer) - can use a python set
    # - Remove the domain (at the end this function process one at a time)
    # - Identify the leaf
    # - Count the levels
    # - Split the URLs into levels (here I'm going to have a nx matrix)
    # - Group by chunks
    pass

def get_unique_urls_list(source: dict, domain: str) -> dict:
    """Get a dict containing a unique list of URLs 
    deprived by the domain name.
    """
    
    # Using a set to remove duplicates
    res = {item.replace(domain, "") for item in source}
    
    # Add the homepage that at this stage was remove
    res.add("/")
    
    # Remove the empty node
    res.remove("")
    
    return list(res)

def get_folder_structure(url: str):
    """Get a single URL and return as variable list of items
    depending of how many folder it exists."""
    previous = ""
    for item in url.split("/"):
        previous += item + "/"
        yield previous
    
    # previous += item
    # yield previous
    # list_ = item


if __name__ == '__main__':
    test = False
    
    
    # url = "/questions/196017/splitting-urls-into-hierarchy-level-directories"
    # boh = get_folder_structure(url)
    
    # for i in boh:
    #     print(i)

    # # import operator   
    # # boh = get_folder_structure(url)      
    # # for i in itertools.accumulate(boh, operator.iadd(i, '/')):
    # #     print(i)        
        
    
    if not test:
        config = configparser.ConfigParser()
        config.read("./tests/config.ini")
        client_id = config['credentials']['client_id']
        client_secret = config['credentials']['client_secret']
        
        credentials = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uris": [],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://accounts.google.com/o/oauth2/token",
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
            'access_token': token,
            'refresh_token': f['refresh_token'],
            'client_id': client_id,
            'client_secret': client_secret,
            'token_uri': GOOGLE_TOKEN_URI,
            'scopes': 'https://www.googleapis.com/auth/webmasters.readonly',
            'user_agent': None,
            'token_expiry': None,
            'revoke_uri': GOOGLE_REVOKE_URI,
        }    

        account = gsc_wrapper.Account(credentials)
        site_list = account.webproperties()    
        # site = account['https://www.andreamoro.eu/']
        site = account['https://www.evensi.it/']

    else:
        credentials = {
            'access_token': None,
            'refresh_token': None,
            'client_id': None,
            'client_secret': None,
            'token_uri': GOOGLE_TOKEN_URI,
            'scopes': 'https://www.googleapis.com/auth/webmasters.readonly',
            'user_agent': None,
            'token_expiry': None,
            'revoke_uri': GOOGLE_REVOKE_URI,
        }    
        account = gsc_wrapper.Account(credentials)
        
        web_properties = [{'siteUrl': 'www.test1.com', 'permissionLevel': '1'}, 
                            {'siteUrl': 'www.test2.com', 'permissionLevel': '1'}, 
                            {'siteUrl': 'subdomain.google.com', 'permissionLevel': '1'}]
        site_list = [gsc_wrapper.WebProperty(raw, account) for raw in web_properties]
        account._webproperties = site_list
        site = account['www.test1.com']
        
    from datetime import date
    # data = site.query.range(startDate=date(2022, 10, 10), endDate=date(2022, 11, 10))
    # print(site.query.raw)
    # assert site.query.startDate < site.query.endDate, "Error"
    # print()
    
    # # End data lower than starting date, expected correction
    # data = site.query.range(startDate=date(2022, 11, 10), endDate=date(2022, 10, 10))
    # print(site.query.raw)
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
    
    # # Expected adjustments on the startDate going over the 16 months allowance
    # data = site.query.range(startDate=date.today(), days=0, months=-20)
    # print(site.query.raw)    
    # assert site.query.endDate == date.today() + relativedelta(days=-1 if site.query.data_state().raw['dataState'] == 'final' else 0) and \
    #         site.query.startDate == date.today() + relativedelta(months=-16, days=-1 if site.query.data_state().raw['dataState'] == 'final' else 0), "Error"
    # print()
    
    # # Expected endDate +1 month = 2022-11-10
    # data = site.query.range(startDate='2022-10-10', days=0, months=1)
    # assert site.query.endDate == date(2022, 11, 10), "Error"
    # print(site.query.raw)    
    
    # # Expected Startdate adjusted to 2022-09-10 enddate to 2022-10-10 
    # data = site.query.range(startDate='2022-10-10', days=0, months=-1)
    # assert site.query.endDate == date(2022, 10, 10) and site.query.startDate == date(2022,9,10), "Error"
    # print(site.query.raw)    
    
    data = site.query.range(startDate=date.today(), days=-5, months=0)\
                .search_type(gsc_wrapper.search_type.WEB)\
                .dimensions(gsc_wrapper.dimension.DATE)\
                .filter(country=gsc_wrapper.country.ITALY, operator=gsc_wrapper.operator.EQUALS, append=False)\
                .execute()

    logging.warning(site.query.raw)
    logging.info(data.get('rows'))
    
    report = site.query.range(startDate=date.today(), days=-10, months=0)\
                     .dimensions(gsc_wrapper.dimension.DATE).get()
    
    # data = site.query.range(startDate=date.today(), days=1, months=0)
    # data = site.query.filter(country=gsc_wrapper.country.ITALY, operator=gsc_wrapper.operator.EQUALS, append=False)
    # data = site.query.search_type(gsc_wrapper.search_type.WEB)
    
   
    # data = site.query.filter(gsc_wrapper.country.ALBANIA,append=True).search_type(gsc_wrapper.search_type.IMAGE)
    
    # data = site.query.filter(gsc_wrapper.country.ITALY)
    # .range(date.today(), months=-1)\
    #         .dimensions(gsc_wrapper.dimension.DATE, gsc_wrapper.dimension.PAGE)

    data = site.query.filter(gsc_wrapper.country.ITALY).range(date.today(), months=-1)\
            .dimensions(gsc_wrapper.dimension.DATE, gsc_wrapper.dimension.PAGE)
    report = data.get()

    # *** Execute a query against a sliced set of data
    data = site.query.filter(gsc_wrapper.country.ITALY).range(date.today(), months=-1)\
            .dimensions(gsc_wrapper.dimension.DATE, gsc_wrapper.dimension.PAGE).execute()
    
    # report = gsc_wrapper.Report(site.url, site.query.raw, data.get('rows'))

    # *** Execute a query and return the whole dataset
    # data = site.query.filter(gsc_wrapper.country.ITALY).range(date.today(), months=-1)\
    #         .dimensions(gsc_wrapper.dimension.DATE, gsc_wrapper.dimension.PAGE)
    
    # report = data.get()
    # report.to_disk('20230109_https_www_evensi_it_.pck')
    
    # *** Restore a report persisted on disk
    # report = gsc_wrapper.Report.from_disk('20230109_https_www_evensi_it_002.pck')
