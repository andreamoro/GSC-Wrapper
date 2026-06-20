"""Tests for the ``Query`` builder (no network: ``execute``/``get`` excluded)."""
from datetime import date

import pytest
from dateutil.relativedelta import relativedelta

import gsc_wrapper
from gsc_wrapper import country, data_state, dimension, operator, search_type


def test_requires_webproperty():
    with pytest.raises(TypeError):
        gsc_wrapper.Query(None)


def test_default_state(query):
    # Defaults: yesterday/day-before, final data, auto aggregation, 25k rows.
    assert query.raw["dataState"] == "final"
    assert query.raw["aggregationType"] == "auto"
    assert query.raw["startRow"] == 0
    assert query.raw["rowLimit"] == 25000
    assert query.startDate == date.today() - relativedelta(days=2)
    assert query.endDate == date.today() - relativedelta(days=1)


def test_equality_and_repr(site):
    a = gsc_wrapper.Query(site)
    b = gsc_wrapper.Query(site)
    assert a == b
    a.limit(10)
    assert a != b
    assert "gsc_wrapper.query.Query" in repr(a)


# --- range -----------------------------------------------------------------
# Dates are chosen relative to today so they always sit inside the 16-month
# window the API (and __range_build) enforces.

START = date.today() - relativedelta(days=40)
END = date.today() - relativedelta(days=30)


def test_range_days_offset(query):
    query.range(startDate=START, days=1, months=0)
    assert query.startDate == START
    assert query.endDate == START + relativedelta(days=1)
    assert query.raw["startDate"] == START.isoformat()


def test_range_negative_offset_swaps(query):
    # A negative span swaps the dates so start < end is preserved.
    query.range(startDate=START, days=-5, months=0)
    assert query.startDate == START - relativedelta(days=5)
    assert query.endDate == START


def test_range_two_dates(query):
    query.range(startDate=START, endDate=END)
    assert query.startDate == START
    assert query.endDate == END


def test_range_string_dates(query):
    query.range(startDate=START.isoformat(), endDate=END.isoformat())
    assert query.startDate == START
    assert query.endDate == END


def test_range_start_after_end_is_swapped(query):
    query.range(startDate=END, endDate=START)
    assert query.startDate == START
    assert query.endDate == END


def test_range_future_clamped_to_yesterday(query):
    # With FINAL data, future dates are pulled back to yesterday.
    query.range(startDate=date.today() + relativedelta(days=10),
                endDate=date.today() + relativedelta(days=20))
    yesterday = date.today() - relativedelta(days=1)
    assert query.startDate == yesterday
    assert query.endDate == yesterday


def test_range_clamped_to_16_months(query):
    # A start date older than 16 months is pulled forward to the boundary;
    # the recent end date keeps the range the right way round.
    query.range(startDate=date.today() - relativedelta(years=3),
                endDate=date.today() - relativedelta(days=1))
    max_old = date.today() + relativedelta(months=-16, days=-1)
    assert query.startDate == max_old


def test_range_invalid_string_raises(query):
    # The positional string overload validates the ISO format.
    with pytest.raises(ValueError):
        query.range("not-a-date", 1, 0)


# --- dimensions ------------------------------------------------------------

def test_dimensions_multiple(query):
    query.dimensions(dimension.DATE, dimension.PAGE)
    assert query.raw["dimensions"] == ["date", "page"]


def test_dimensions_single(query):
    query.dimensions(dimension.QUERY)
    assert query.raw["dimensions"] == ["query"]


def test_search_appearance_alone(query):
    query.dimensions(dimension.SEARCH_APPEARANCE)
    assert query.raw["dimensions"] == ["search_appearance"]


# --- filters ---------------------------------------------------------------

def test_filter_country(query):
    query.filter(country.ITALY, operator.EQUALS)
    assert query.filters == [
        {"dimension": "country", "expression": "ITA", "operator": "equals"}
    ]


def test_filter_dimension(query):
    query.filter(dimension.PAGE, "/blog", operator.CONTAINS)
    assert query.filters == [
        {"dimension": "page", "expression": "/blog", "operator": "contains"}
    ]


def test_filter_replaces_same_key_by_default(query):
    query.filter(country.ITALY)
    query.filter(country.SPAIN)
    assert query.filters == [
        {"dimension": "country", "expression": "ESP", "operator": "equals"}
    ]


def test_filter_append_keeps_both(query):
    query.filter(country.ITALY)
    query.filter(dimension.PAGE, "/blog", operator.CONTAINS, append=True)
    assert len(query.filters) == 2


def test_filter_remove_country(query):
    query.filter(country.ITALY)
    query.filter(dimension.PAGE, "/blog", operator.CONTAINS, append=True)
    query.filter_remove(country.ITALY)
    assert query.filters == [
        {"dimension": "page", "expression": "/blog", "operator": "contains"}
    ]


def test_filter_remove_dimension(query):
    query.filter(dimension.PAGE, "/blog", operator.CONTAINS)
    query.filter_remove(dimension.PAGE, "/blog")
    assert query.filters == []


def test_filter_search_appearance_is_noop(query):
    # SEARCH_APPEARANCE is only valid at the metric level, so filtering on it
    # must leave the query untouched.
    result = query.filter(dimension.SEARCH_APPEARANCE, "x", operator.EQUALS)
    assert result is query
    assert query.filters == []


def test_filter_invalid_operator_raises(query):
    # A non-enum operator matches no registered overload signature.
    with pytest.raises(Exception):
        query.filter(country.ITALY, "equals")


# --- misc builders ---------------------------------------------------------

def test_limit_caps_at_25000(query):
    query.limit(99999)
    assert query.raw["rowLimit"] == 25000


def test_limit_with_offset(query):
    query.limit(100, 50)
    assert query.raw["startRow"] == 100
    assert query.raw["rowLimit"] == 50


def test_data_state(query):
    query.data_state(data_state.ALL)
    assert query.raw["dataState"] == "all"


def test_data_state_invalid_raises(query):
    with pytest.raises(ValueError):
        query.data_state("all")


def test_search_type(query):
    query.search_type(search_type.IMAGE)
    assert query.raw["type"] == "image"


def test_search_type_invalid_raises(query):
    with pytest.raises(ValueError):
        query.search_type("image")


def test_method_chaining_returns_query(query):
    result = (
        query.range(startDate=date(2022, 10, 10), days=5, months=0)
        .dimensions(dimension.DATE)
        .filter(country.ITALY)
        .limit(10)
    )
    assert result is query


def test_search_appearance_combined_is_stripped(query):
    # SEARCH_APPEARANCE must be dropped when combined with other dimensions,
    # since the API does not allow it alongside anything else.
    query.dimensions(dimension.SEARCH_APPEARANCE, dimension.DATE)
    assert query.raw["dimensions"] == ["date"]


def test_search_appearance_combined_stripped_regardless_of_order(query):
    query.dimensions(dimension.PAGE, dimension.SEARCH_APPEARANCE)
    assert query.raw["dimensions"] == ["page"]
    assert "search_appearance" not in query.raw["dimensions"]
