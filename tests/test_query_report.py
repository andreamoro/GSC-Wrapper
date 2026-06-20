"""Tests for ``gsc_wrapper.query.Report`` (search-analytics report)."""
import pytest

from gsc_wrapper.query import Report


@pytest.fixture
def raw_rows():
    return [
        {"keys": ["2022-11-10"], "clicks": 5, "impressions": 100,
         "ctr": 0.05, "position": 3.2},
        {"keys": ["2022-11-11"], "clicks": 2, "impressions": 50,
         "ctr": 0.04, "position": 4.0},
    ]


@pytest.fixture
def report(raw_rows):
    query = {"dimensions": ["date"], "startRow": 0, "rowLimit": 2}
    return Report("https://www.test1.com/", query, raw_rows)


def test_columns_combine_dimensions_and_metrics(report):
    assert report.columns == ["date", "clicks", "impressions", "ctr", "position"]


def test_len_and_indexing(report):
    assert len(report) == 2
    assert report[0].date == "2022-11-10"
    assert report[1].clicks == 2


def test_first_and_last(report):
    assert report.first.date == "2022-11-10"
    assert report.last.date == "2022-11-11"


def test_iteration(report):
    dates = [row.date for row in report]
    assert dates == ["2022-11-10", "2022-11-11"]


def test_contains(report):
    assert report.first in report


def test_to_dict(report):
    assert report.to_dict()[0] == {
        "date": "2022-11-10", "clicks": 5, "impressions": 100,
        "ctr": 0.05, "position": 3.2,
    }


def test_repr(report):
    assert repr(report) == "<gsc_wrapper.query.Report(rows=2)>"


def test_empty_report_first_last_none():
    report = Report("https://www.test1.com/", {"dimensions": ["date"]}, [])
    assert report.first is None
    assert report.last is None
    assert len(report) == 0


def test_to_dataframe(report):
    df = report.to_dataframe()
    assert df.shape == (2, 5)
    assert list(df.columns) == ["date", "clicks", "impressions", "ctr",
                                "position"]


def test_disk_roundtrip(report, tmp_path):
    target = tmp_path / "report.pck"
    saved = report.to_disk(str(target))
    assert saved == str(target)
    assert target.exists()

    restored = Report.from_disk(str(target))
    assert restored.to_dict() == report.to_dict()


def test_from_disk_empty_filename_returns_none():
    assert Report.from_disk("") is None


def test_datastream_roundtrip(report):
    import pickle

    blob = pickle.dumps(
        [{"url": report.webproperty, "query": report.query}, report.raw]
    )
    restored = Report.from_datastream(blob)
    assert restored.to_dict() == report.to_dict()
