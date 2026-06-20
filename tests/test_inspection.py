"""Tests for ``InspectURL`` (the URL-inspection builder, offline)."""
import pytest

import gsc_wrapper

URL_A = "https://www.test1.com/"
URL_B = "https://www.test1.com/blog"
URL_C = "https://www.test1.com/contact"


def test_requires_webproperty():
    with pytest.raises(TypeError):
        gsc_wrapper.InspectURL(None)


def test_initial_state(inspect, site):
    assert inspect.urls == []
    assert inspect.urls_to_inspect == 0
    assert inspect.raw["siteUrl"] == site.url
    assert "InspectURL" in repr(inspect)


def test_add_single_url(inspect):
    inspect.add_url(URL_A)
    assert inspect.urls == [URL_A]
    assert inspect.urls_to_inspect == 1
    assert inspect.raw["inspectionUrl"] == URL_A


def test_add_url_list(inspect):
    inspect.add_url([URL_A, URL_B, URL_C])
    assert inspect.urls == [URL_A, URL_B, URL_C]
    assert inspect.urls_to_inspect == 3


def test_add_url_chaining(inspect):
    result = inspect.add_url(URL_A).add_url(URL_B)
    assert result is inspect
    assert inspect.urls == [URL_A, URL_B]


def test_duplicate_url_ignored(inspect):
    inspect.add_url(URL_A)
    inspect.add_url(URL_A)
    assert inspect.urls_to_inspect == 1


def test_add_url_overwrite_refreshes_entry(inspect):
    inspect.add_url(URL_A)
    inspect.add_url(URL_B)
    inspect.add_url(URL_A, overwrite=True)
    # Overwriting removes and re-appends, so the URL stays unique.
    assert inspect.urls_to_inspect == 2
    assert inspect.urls.count(URL_A) == 1


def test_add_url_invalid_type_raises(inspect):
    # An int matches neither the str nor the list overload.
    with pytest.raises(Exception):
        inspect.add_url(123)


def test_remove_url_by_index(inspect):
    inspect.add_url([URL_A, URL_B])
    inspect.remove_url(0)
    # Removing by index drops the entry and refreshes the cached url list.
    assert URL_A not in inspect.urls
    assert inspect.urls == [URL_B]
    assert inspect.urls_to_inspect == 1


def test_remove_url_by_index_out_of_range_raises(inspect):
    inspect.add_url(URL_A)
    with pytest.raises(ValueError):
        inspect.remove_url(5)


def test_remove_url_by_string(inspect):
    inspect.add_url([URL_A, URL_B, URL_C])
    inspect.remove_url(URL_B)
    assert inspect.urls == [URL_A, URL_C]
    assert inspect.urls_to_inspect == 2


def test_remove_url_by_list(inspect):
    inspect.add_url([URL_A, URL_B, URL_C])
    inspect.remove_url([URL_A, URL_C])
    assert inspect.urls == [URL_B]
    assert inspect.urls_to_inspect == 1


def test_remove_all_urls(inspect):
    inspect.add_url([URL_A, URL_B, URL_C])
    assert inspect.urls  # prime the cached_property
    inspect.remove_all_urls()
    assert inspect.urls_to_inspect == 0
    assert inspect._urls_bag == []
    assert inspect.urls == []  # cache was invalidated
