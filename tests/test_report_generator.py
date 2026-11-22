"""Tests for the HTML validation report."""

from converter.report_generator import generate_link_validation_report


def test_report_keeps_css_and_renders_counts(tmp_path):
    report = generate_link_validation_report(
        ["a.html -> Link '/x/' has no index.html"],
        ["xyz"],
        ["b.html (OSError)"],
        tmp_path,
    )

    assert report == tmp_path / "conversion_report.html"
    text = report.read_text(encoding="utf-8")
    assert "font-family: Arial" in text
    assert "Missing Index Pages (1)" in text
    assert "<code>.xyz</code>" in text
    assert "b.html (OSError)" in text
    assert "{missing_links_count}" not in text
