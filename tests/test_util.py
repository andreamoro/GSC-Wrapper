"""Tests for the ``Util`` helper."""
from gsc_wrapper.util import Util


def test_get_filename_when_absent(tmp_path):
    # When the target does not exist, the path is returned unchanged.
    result = Util.get_filename(tmp_path, "report.pck")
    assert result == tmp_path / "report.pck"


def test_get_filename_returns_pathlike(tmp_path):
    result = Util.get_filename(tmp_path, "data.pck")
    # The returned value joins destination and filename.
    assert str(result).endswith("data.pck")
    assert str(tmp_path) in str(result)
