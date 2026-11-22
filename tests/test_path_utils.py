"""Tests for main-page path resolution."""

from converter.path_utils import resolve_main_page


def test_exact_page_wins(tmp_path):
    (tmp_path / "about.html").write_text("ok", encoding="utf-8")
    (tmp_path / "about").mkdir()
    (tmp_path / "about" / "index.html").write_text("ok", encoding="utf-8")
    assert resolve_main_page("about.html", tmp_path) == "about.html"


def test_url_encoded_path_is_decoded(tmp_path):
    (tmp_path / "my file").mkdir()
    (tmp_path / "my file" / "index.html").write_text("ok", encoding="utf-8")
    assert resolve_main_page("my%20file/", tmp_path) == "my file/index.html"


def test_directory_falls_back_to_index(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.html").write_text("ok", encoding="utf-8")
    assert resolve_main_page("docs", tmp_path) == "docs/index.html"


def test_unknown_page_falls_back_to_root_index(tmp_path):
    (tmp_path / "index.html").write_text("ok", encoding="utf-8")
    assert resolve_main_page("missing", tmp_path) == "index.html"
