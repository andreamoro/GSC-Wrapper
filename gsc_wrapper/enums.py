from enum import Enum, EnumMeta


class MyEnumMeta(EnumMeta):
    def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            try:
                cls.__members__.get(item)
            except ValueError:
                return False
            else:
                return True
        else:
            return True


class country(Enum, metaclass=MyEnumMeta):
    AFGHANISTAN = "AFG"
    ALAND_ISLANDS = "ALA"
    ALBANIA = "ALB"
    ALGERIA = "DZA"
    AMERICAN_SAMOA = "ASM"
    ANDORRA = "AND"
    ANGOLA = "AGO"
    ANGUILLA = "AIA"
    ANTARCTICA = "ATA"
    ANTIGUA_AND_BARBUDA = "ATG"
    ARGENTINA = "ARG"
    ARMENIA = "ARM"
    ARUBA = "ABW"
    AUSTRALIA = "AUS"
    AUSTRIA = "AUT"
    AZERBAIJAN = "AZE"
    BAHAMAS = "BHS"
    BAHRAIN = "BHR"
    BANGLADESH = "BGD"
    BARBADOS = "BRB"
    BELARUS = "BLR"
    BELGIUM = "BEL"
    BELIZE = "BLZ"
    BENIN = "BEN"
    BERMUDA = "BMU"
    BHUTAN = "BTN"
    BOLIVIA = "BOL"
    BONAIRE_SINT_EUSTATIUS_AND_SABA = "BES"
    BOSNIA_AND_HERZEGOVINA = "BIH"
    BOTSWANA = "BWA"
    BOUVET_ISLAND = "BVT"
    BRAZIL = "BRA"
    BRITISH_INDIAN_OCEAN_TERRITORY = "IOT"
    BRUNEI_DARUSSALAM = "BRN"
    BULGARIA = "BGR"
    BURKINA_FASO = "BFA"
    BURUNDI = "BDI"
    CABO_VERDE = "CPV"
    CAMBODIA = "KHM"
    CAMEROON = "CMR"
    CANADA = "CAN"
    CAYMAN_ISLANDS = "CYM"
    CENTRAL_AFRICAN_REPUBLIC = "CAF"
    CHAD = "TCD"
    CHILE = "CHL"
    CHINA = "CHN"
    CHRISTMAS_ISLAND = "CXR"
    COCOS_KEELING_ISLANDS = "CCK"
    COLOMBIA = "COL"
    COMOROS = "COM"
    CONGO_DEMOCRATIC_REPUBLIC = "COD"
    CONGO = "COG"
    COOK_ISLANDS = "COK"
    COSTA_RICA = "CRI"
    CROATIA = "HRV"
    CUBA = "CUB"
    CURAÇAO = "CUW"
    CYPRUS = "CYP"
    CZECHIA = "CZE"
    DENMARK = "DNK"
    DJIBOUTI = "DJI"
    DOMINICA = "DMA"
    DOMINICAN_REPUBLIC = "DOM"
    ECUADOR = "ECU"
    EGYPT = "EGY"
    EL_SALVADOR = "SLV"
    EQUATORIAL_GUINEA = "GNQ"
    ERITREA = "ERI"
    ESTONIA = "EST"
    ESWATINI = "SWZ"
    ETHIOPIA = "ETH"
    FALKLAND_ISLANDS = "FLK"
    FAROE_ISLANDS = "FRO"
    FIJI = "FJI"
    FINLAND = "FIN"
    FRANCE = "FRA"
    FRENCH_GUIANA = "GUF"
    FRENCH_POLYNESIA = "PYF"
    FRENCH_SOUTHERN_TERRITORIES = "ATF"
    GABON = "GAB"
    GAMBIA = "GMB"
    GEORGIA = "GEO"
    GERMANY = "DEU"
    GHANA = "GHA"
    GIBRALTAR = "GIB"
    GREECE = "GRC"
    GREENLAND = "GRL"
    GRENADA = "GRD"
    GUADELOUPE = "GLP"
    GUAM = "GUM"
    GUATEMALA = "GTM"
    GUERNSEY = "GGY"
    GUINEA = "GIN"
    GUINEA_BISSAU = "GNB"
    GUYANA = "GUY"
    HAITI = "HTI"
    HEARD_ISLAND_AND_MCDONALD_ISLANDS = "HMD"
    HOLY_SEE = "VAT"
    HONDURAS = "HND"
    HONG_KONG = "HKG"
    HUNGARY = "HUN"
    ICELAND = "ISL"
    INDIA = "IND"
    INDONESIA = "IDN"
    IRAN = "IRN"
    IRAQ = "IRQ"
    IRELAND = "IRL"
    ISLE_OF_MAN = "IMN"
    ISRAEL = "ISR"
    ITALY = "ITA"
    IVORY_COST = "CIV"
    JAMAICA = "JAM"
    JAPAN = "JPN"
    JERSEY = "JEY"
    JORDAN = "JOR"
    KAZAKHSTAN = "KAZ"
    KENYA = "KEN"
    KIRIBATI = "KIR"
    KOREA_DEMOCRATIC_PEOPLE_REPUBLIC = "PRK"
    KOREA_REPUBLIC_OF = "KOR"
    KUWAIT = "KWT"
    KYRGYZSTAN = "KGZ"
    LAO_REPUBLIC = "LAO"
    LATVIA = "LVA"
    LEBANON = "LBN"
    LESOTHO = "LSO"
    LIBERIA = "LBR"
    LIBYA = "LBY"
    LIECHTENSTEIN = "LIE"
    LITHUANIA = "LTU"
    LUXEMBOURG = "LUX"
    MACAO = "MAC"
    MADAGASCAR = "MDG"
    MALAWI = "MWI"
    MALAYSIA = "MYS"
    MALDIVES = "MDV"
    MALI = "MLI"
    MALTA = "MLT"
    MARSHALL_ISLANDS = "MHL"
    MARTINIQUE = "MTQ"
    MAURITANIA = "MRT"
    MAURITIUS = "MUS"
    MAYOTTE = "MYT"
    MEXICO = "MEX"
    MICRONESIA = "FSM"
    MOLDOVA = "MDA"
    MONACO = "MCO"
    MONGOLIA = "MNG"
    MONTENEGRO = "MNE"
    MONTSERRAT = "MSR"
    MOROCCO = "MAR"
    MOZAMBIQUE = "MOZ"
    MYANMAR = "MMR"
    NAMIBIA = "NAM"
    NAURU = "NRU"
    NEPAL = "NPL"
    NETHERLANDS = "NLD"
    NEW_CALEDONIA = "NCL"
    NEW_ZEALAND = "NZL"
    NICARAGUA = "NIC"
    NIGER = "NER"
    NIGERIA = "NGA"
    NIUE = "NIU"
    NORFOLK_ISLAND = "NFK"
    NORTHERN_MARIANA_ISLANDS = "MNP"
    NORWAY = "NOR"
    OMAN = "OMN"
    PAKISTAN = "PAK"
    PALAU = "PLW"
    PALESTINE = "PSE"
    PANAMA = "PAN"
    PAPUA_NEW_GUINEA = "PNG"
    PARAGUAY = "PRY"
    PERU = "PER"
    PHILIPPINES = "PHL"
    PITCAIRN = "PCN"
    POLAND = "POL"
    PORTUGAL = "PRT"
    PUERTO_RICO = "PRI"
    QATAR = "QAT"
    REPUBLIC_OF_NORTH_MACEDONIA = "MKD"
    ROMANIA = "ROU"
    RUSSIAN_FEDERATION = "RUS"
    RWANDA = "RWA"
    RÉUNION = "REU"
    SAINT_BARTHELEMY = "BLM"
    SAINT_HELENA = "SHN"
    SAINT_KITTS_AND_NEVIS = "KNA"
    SAINT_LUCIA = "LCA"
    SAINT_MARTIN = "MAF"
    SAINT_PIERRE_AND_MIQUELON = "SPM"
    SAINT_VINCENT_AND_THE_GRENADINES = "VCT"
    SAMOA = "WSM"
    SAN_MARINO = "SMR"
    SAO_TOME_AND_PRINCIPE = "STP"
    SAUDI_ARABIA = "SAU"
    SENEGAL = "SEN"
    SERBIA = "SRB"
    SEYCHELLES = "SYC"
    SIERRA_LEONE = "SLE"
    SINGAPORE = "SGP"
    SINT_MAARTEN = "SXM"
    SLOVAKIA = "SVK"
    SLOVENIA = "SVN"
    SOLOMON_ISLANDS = "SLB"
    SOMALIA = "SOM"
    SOUTH_AFRICA = "ZAF"
    SOUTH_GEORGIA_AND_THE_SOUTH_SANDWICH_ISLANDS = "SGS"
    SOUTH_SUDAN = "SSD"
    SPAIN = "ESP"
    SRI_LANKA = "LKA"
    SUDAN = "SDN"
    SURINAME = "SUR"
    SVALBARD_AND_JAN_MAYEN = "SJM"
    SWEDEN = "SWE"
    SWITZERLAND = "CHE"
    SYRIAN_ARAB_REPUBLIC = "SYR"
    TAIWAN = "TWN"
    TAJIKISTAN = "TJK"
    TANZANIA = "TZA"
    THAILAND = "THA"
    TIMOR_LESTE = "TLS"
    TOGO = "TGO"
    TOKELAU = "TKL"
    TONGA = "TON"
    TRINIDAD_AND_TOBAGO = "TTO"
    TUNISIA = "TUN"
    TURKEY = "TUR"
    TURKMENISTAN = "TKM"
    TURKS_AND_CAICOS_ISLANDS = "TCA"
    TUVALU = "TUV"
    UGANDA = "UGA"
    UKRAINE = "UKR"
    UNITED_ARAB_EMIRATES = "ARE"
    UNITED_KINGDOM = "GBR"
    UNITED_STATES_MINOR_OUTLYING_ISLANDS = "UMI"
    UNITED_STATES = "USA"
    URUGUAY = "URY"
    UZBEKISTAN = "UZB"
    VANUATU = "VUT"
    VENEZUELA = "VEN"
    VIET_NAM = "VNM"
    VIRGIN_ISLANDS_BRITISH = "VGB"
    VIRGIN_ISLANDS_US = "VIR"
    WALLIS_AND_FUTUNA = "WLF"
    WESTERN_SAHARA = "ESH"
    YEMEN = "YEM"
    ZAMBIA = "ZMB"
    ZIMBABWE = "ZWE"


class search_type(Enum, metaclass=MyEnumMeta):
    WEB = "web"
    IMAGE = "image"
    VIDEO = "video"
    NEWS = "news"
    DISCOVER = "discover"
    GOOGLE_NEWS = "google_news"


class data_state(Enum, metaclass=MyEnumMeta):
    ALL = "all"
    FINAL = "final"


class dimension(Enum, metaclass=MyEnumMeta):
    DATE = "date"
    QUERY = "query"
    PAGE = "page"
    COUNTRY = "country"
    DEVICE = "device"
    SEARCH_APPEARANCE = "search_appearance"


class operator(Enum, metaclass=MyEnumMeta):
    EQUALS = "equals"
    NOT_EQUALS = "not_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    INCLUDING_REGEX = "including_regex"
    EXCLUDING_REGEX = "excluding_regex"


class verdict(Enum, metaclass=MyEnumMeta):
    VERDICT_UNSPECIFIED = "unspecified"
    PASS = "Page is in GSC"
    FAIL = "Page is not in GSC"
    NEUTRAL = "Excluded from GSC"


class robotsTxtState(Enum, metaclass=MyEnumMeta):
    ROBOTS_TXT_STATE_UNSPECIFIED = "State unknown, page not fetched"
    ALLOWED = "Allowed"
    DISALLOWED = "Disallowed"


class indexingState(Enum, metaclass=MyEnumMeta):
    INDEXING_STATE_UNSPECIFIED = "State unknown"
    INDEXING_ALLOWED = "Indexing allowed"
    BLOCKED_BY_META_TAG = "Noindex detected in robots meta tag"
    BLOCKED_DUE_TO_NOINDEX = BLOCKED_BY_META_TAG
    BLOCKED_BY_HTTP_HEADER = "Noindex detected in X-Robots-Tag"
    BLOCKED_DUE_TO_EXPIRED_UNAVAILABLE_AFTER = "Indexing not allowed due to 'unavailable_after' date expired"


class pageFetchState(Enum, metaclass=MyEnumMeta):
    PAGE_FETCH_STATE_UNSPECIFIED = "State unknown"
    SUCCESSFUL = "Success"
    BLOCKED_ROBOTS_TXT = "Blocked by robots.txt"
    REDIRECT_ERROR = "Redirection error"
    ACCESS_DENIED = "Access denied (401)"
    NOT_FOUND = "Page Not found (404)"
    ACCESS_FORBIDDEN = "Access forbidden (403)"
    BLOCKED_4XX = "Other 4xx issue (not 403, 404)"
    SOFT_404 = "Soft 404"
    SERVER_ERROR = "Server error (5xx)"
    INTERNAL_CRAWL_ERROR = "Internal error"
    INVALID_URL = "Invalid URL"


class crawlerAgent(Enum, metaclass=MyEnumMeta):
    CRAWLING_USER_AGENT_UNSPECIFIED = "Unknown"
    DESKTOP = "Desktop"
    MOBILE = "Mobile"


class severity(Enum, metaclass=MyEnumMeta):
    SEVERITY_UNSPECIFIED = "Unknown severity"
    WARNING = "Warning"
    ERROR = "Error"


class mobileUsabilityIssueType(Enum, metaclass=MyEnumMeta):
    MOBILE_USABILITY_ISSUE_TYPE_UNSPECIFIED = "Unknown issue"
    USES_INCOMPATIBLE_PLUGINS = "Site uses incompatible plugins for mobile devices"
    CONFIGURE_VIEWPORT = "Viewport is not specified"
    FIXED_WIDTH_VIEWPORT = "Viewport defined to a fixed width"
    SIZE_CONTENT_TO_VIEWPORT = "Content not sized to viewport"
    USE_LEGIBLE_FONT_SIZES = "Font size is too small for mobile devices"
    TAP_TARGETS_TOO_CLOSE = "Touch elements are too close"
