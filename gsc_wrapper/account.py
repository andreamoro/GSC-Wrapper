from __future__ import annotations
from googleapiclient import discovery
from google.oauth2.credentials import Credentials


class Account:
    """An account can be associated with a number of web
    properties.
    You should navigate to a web property to run queries
    or to pull information about the indexation status
    of a given URL.


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

    def __init__(self, credentials: dict):
        if not credentials:
            raise Exception(
                "A credential JSON object is required.\n\
                    Class can't be initialised."
            )

        self.service: discovery.Resource = self.__authenticate(credentials)
        self._webproperties: list[WebProperty] = []

    def __authenticate(self, credentials: dict) -> discovery.Resource:
        self.cred = Credentials(**credentials)

        API_SERVICE_NAME = "searchconsole"
        API_VERSION = "v1"

        try:
            return discovery.build(
                API_SERVICE_NAME,
                API_VERSION,
                credentials=self.cred
            )
        except Exception as e:
            raise Exception(
                f"An errorr occurred during the authentication\
                            process.\n{e}"
            )

    def webproperties(self) -> list["WebProperty"]:
        """
        A list of all web properties associated with this account. You may
        select a specific web property using an index or by exact URI.


        Usage:
        >>> account.webproperties[0]
        <gsc_wrapper.account.WebProperty(url='...')>
        """
        if len(self._webproperties) == 0:
            web_properties = self.service.sites().list().execute().get("siteEntry", [])
            self._webproperties = [WebProperty(raw, self)
                                   for raw in web_properties]

        return self._webproperties

    def __getitem__(self, item) -> WebProperty | None:
        if len(self._webproperties) == 0:
            self._webproperties = self.webproperties()

        if isinstance(item, str):
            properties = [p for p in self._webproperties if p.url == item]
            web_property = properties[0] if properties else None
        else:
            web_property = self._webproperties[item]

        return web_property

    def __repr__(self):
        return f"<gsc_wrapper.account(credentials='{self.cred.client_id}')>"


class WebProperty:
    """
    A web property is a website tracked in Google Search Console
    that can be queried via the Search Analytics.

    Usage:
    >>> webproperty = account[www_webproperty_com]
    >>> webproperty.query.range(start='today', days=-7).dimension('date').get()
    <gsc_wrapper.query.Report(rows=...)>
    """

    permission_levels = {
        "siteFullUser": 1,
        "siteOwner": 2,
        "siteRestrictedUser": 3,
        "siteUnverifiedUser": 4,
    }

    def __init__(self, raw, account: Account):
        self.account = account
        self.raw = raw
        self.url = raw["siteUrl"]
        self.permission = raw["permissionLevel"]

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return self.__dict__ == other.__dict__
        return False

    def __repr__(self):
        return (
            f"<gsc_wrapper.account.WebProperty(url='{self.url}', "
            f"permission='{self.permission}')>"
        )
