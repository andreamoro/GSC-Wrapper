"""Tests for ``gsc_wrapper.inspection.Report`` (URL-inspection report)."""
import pytest

from gsc_wrapper.inspection import Report


@pytest.fixture
def raw_rows():
    return [
        {
            "inspectionResultLink": "https://search.google.com/x",
            "inspectionUrl": "https://www.test1.com/",
            "indexStatusResult": {
                "verdict": "PASS",
                "robotsTxtState": "ALLOWED",
                "indexingState": "INDEXING_ALLOWED",
                "pageFetchState": "SUCCESSFUL",
                "crawledAs": "MOBILE",
            },
            "mobileUsabilityResult": {"verdict": "PASS"},
        },
    ]


@pytest.fixture
def report(raw_rows):
    return Report("https://www.test1.com/", raw_rows)


def test_len_and_repr(report):
    assert len(report) == 1
    assert repr(report) == "<gsc_wrapper.inspection.Report(rows=1)>"


def test_nested_namedtuple_access(report):
    assert report.first.indexStatusResult.verdict == "PASS"
    assert report.first.mobileUsabilityResult.verdict == "PASS"


def test_first_last_on_single_row(report):
    assert report.first is report.last


def test_to_dataframe_maps_enums(report):
    df = report.to_dataframe()
    # Flattened, dotted column names with enum values translated to labels.
    assert df["indexStatusResult.verdict"][0] == "Page is in GSC"
    assert df["indexStatusResult.robotsTxtState"][0] == "Allowed"
    assert df["indexStatusResult.pageFetchState"][0] == "Success"
    assert df["indexStatusResult.crawledAs"][0] == "Mobile"


def test_disk_roundtrip(report, tmp_path):
    target = tmp_path / "inspection.pck"
    saved = report.to_disk(str(target))
    assert saved == str(target)

    restored = Report.from_disk(str(target))
    assert len(restored) == len(report)
    assert restored.first.indexStatusResult.verdict == "PASS"


def test_from_disk_empty_filename_returns_none():
    assert Report.from_disk("") is None


def test_datastream_roundtrip(report):
    import pickle

    blob = pickle.dumps([{"url": report.webproperty}, report.raw])
    restored = Report.from_datastream(blob)
    assert len(restored) == 1
    assert restored.first.inspectionUrl == "https://www.test1.com/"
