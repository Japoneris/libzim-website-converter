"""Tests for HTML path rewriting and index-link validation."""

from pathlib import Path

from converter.file_processor import process_html_content


def _site(tmp_path: Path) -> Path:
    (tmp_path / "about").mkdir()
    (tmp_path / "about" / "index.html").write_text("ok", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "page.html").write_text("ok", encoding="utf-8")
    return tmp_path


def test_absolute_link_to_existing_index_is_rewritten(tmp_path):
    root = _site(tmp_path)
    warnings = []
    out = process_html_content(
        '<a href="/about/">About</a>', 0, root / "index.html", root, warnings, "index.html"
    )
    assert out == '<a href="about/index.html">About</a>'
    assert warnings == []


def test_missing_index_warns_once_and_keeps_valid_html(tmp_path):
    root = _site(tmp_path)
    warnings = []
    out = process_html_content(
        '<a href="/missing/">A</a><a href="/missing/">B</a>',
        0, root / "index.html", root, warnings, "index.html",
    )
    assert out == '<a href="missing/">A</a><a href="missing/">B</a>'
    assert warnings == ["index.html -> Link 'missing/' has no index.html"]


def test_relative_link_at_depth_one_resolves_against_file_directory(tmp_path):
    root = _site(tmp_path)
    warnings = []
    out = process_html_content(
        '<a href="../about/">Up</a>', 1, root / "sub" / "page.html",
        root, warnings, "sub/page.html",
    )
    assert out == '<a href="../about/index.html">Up</a>'
    assert warnings == []


def test_css_url_at_depth_two_is_prefixed(tmp_path):
    root = _site(tmp_path)
    warnings = []
    out = process_html_content(
        '<link rel="stylesheet" href="/style.css">', 2,
        root / "a" / "b" / "page.html", root, warnings, "a/b/page.html",
    )
    assert out == '<link rel="stylesheet" href="../../style.css">'
