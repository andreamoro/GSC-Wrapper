from gsc_wrapper.account import Account, WebProperty
from gsc_wrapper.query import Query
from gsc_wrapper.inspection import InspectURL
from gsc_wrapper.enums import country, data_state, dimension, search_type, operator

__all__ = (
    "Account",
    "WebProperty",
    "Query",
    "InspectURL",
    "country",
    "data_state",
    "dimension",
    "search_type",
    "operator",
)
__version__ = "2.0.0"

GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_REVOKE_URI = "https://oauth2.googleapis.com/revoke"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
