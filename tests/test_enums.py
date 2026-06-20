"""Tests for the enumerations and the custom ``MyEnumMeta`` metaclass."""
import pytest

from gsc_wrapper import enums


def test_value_lookup():
    assert enums.country.ITALY.value == "ITA"
    assert enums.search_type.WEB.value == "web"
    assert enums.dimension.SEARCH_APPEARANCE.value == "search_appearance"
    assert enums.operator.NOT_EQUALS.value == "not_equal"
    assert enums.data_state.FINAL.value == "final"


def test_contains_by_value():
    # MyEnumMeta.__contains__ accepts the underlying value.
    assert "ITA" in enums.country
    assert "web" in enums.search_type
    assert "page" in enums.dimension


def test_contains_by_member():
    # An actual member is also reported as contained.
    assert enums.dimension.DATE in enums.dimension
    assert enums.country.SPAIN in enums.country


def test_contains_by_name():
    # Membership also accepts the member name, not just its value.
    assert "ITALY" in enums.country
    assert "WEB" in enums.search_type


def test_not_contains_unknown_value():
    assert "NOT_A_COUNTRY" not in enums.country
    assert "ftp" not in enums.search_type
    assert "italy" not in enums.country  # names are case-sensitive


def test_not_contains_unhashable():
    assert ["ITA"] not in enums.country


def test_indexing_state_alias():
    # BLOCKED_DUE_TO_NOINDEX is declared as an alias of BLOCKED_BY_META_TAG.
    assert (
        enums.indexingState.BLOCKED_DUE_TO_NOINDEX
        is enums.indexingState.BLOCKED_BY_META_TAG
    )


@pytest.mark.parametrize(
    "member, value",
    [
        (enums.verdict.PASS, "Page is in GSC"),
        (enums.robotsTxtState.ALLOWED, "Allowed"),
        (enums.pageFetchState.SUCCESSFUL, "Success"),
        (enums.crawlerAgent.MOBILE, "Mobile"),
        (enums.severity.ERROR, "Error"),
    ],
)
def test_inspection_enum_values(member, value):
    assert member.value == value
