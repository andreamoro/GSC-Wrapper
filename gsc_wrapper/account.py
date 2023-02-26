import json

from typing import Type
from oauth2client import client
from apiclient import discovery
from .query import Query


class Account:
    """
    An account can be associated with a number of web
    properties.
    You should navigate to a web property to run queries.
    
    Args:
        service
    
    Usage:
    >>> import gsc_wrapper
    >>> account = Account(credentials)
    >>> account
    <gsc_wrapper.account>
    >>> account[0]
    <gsc_wrapper.account.WebProperty(url='...')>
    >>> account['www_webproperty_com']
    <gsc_wrapper.account.WebProperty(url='...')>
    """

    def __init__(self, credentials: json = None):
        if credentials is None:
            raise Exception("A credential JSON object is required.\nClass can't be initialised.")
        
        self.service = self.__authenticate(credentials)
        self._webproperties = None
        
    def __authenticate(self, credentials: json):
        cred = client.OAuth2Credentials(**credentials)
        
        return discovery.build(
            serviceName="webmasters",
            version="v3",
            credentials=cred,
            cache_discovery=False,
        )

    def webproperties(self) -> Type['WebProperty']:
        """
        A list of all web properties associated with this account. You may
        select a specific web property using an index or by indexing the
        account directly with the properties exact URI.
        
        Usage:
        >>> account.webproperties[0]
        <gsc_wrapper.account.WebProperty(url='...')>
        """
        if self._webproperties is None:
            web_properties = self.service.sites().list().execute().get('siteEntry', [])  
            self._webproperties = [WebProperty(raw, self) for raw in web_properties]

        return self._webproperties

    def __getitem__(self, item):
        if self._webproperties is None:
            self._webproperties = self.webproperties()
            
        if isinstance(item, str):
            properties = [p for p in self._webproperties if p.url == item]
            web_property = properties[0] if properties else None
        else:
            web_property = self._webproperties[item]

        return web_property

    def __repr__(self):
        return f"<gsc_wrapper.account(credentials='{self.cred}')>"


class WebProperty:
    """
    in Google Search Console. You will use a web property
    A web property is a particular website you're tracking
    to make your Search Analytics queries.
    Usage:
    >>> webproperty = account[www_webproperty_com]
    >>> webproperty.query.range(start='today', days=-7).dimension('date').get()
    <gsc_wrapper.query.Report(rows=...)>
    """

    permission_levels = {
        'siteFullUser': 1,
        'siteOwner': 2,
        'siteRestrictedUser': 3,
        'siteUnverifiedUser': 4
    }

    def __init__(self, raw, account: Account):
        self.account = account
        self.raw = raw
        self.url = raw['siteUrl']
        self.permission = raw['permissionLevel']
        self.query = Query(self)

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return self.__dict__ == other.__dict__
        return False

    def __repr__(self):
        return f"<gsc_wrapper.account.WebProperty(url='{self.url}', permission='{self.permission}')>"