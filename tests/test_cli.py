"""Smoke test for the CLI entry point."""

import website_converter


def test_main_help_exits_zero(monkeypatch, capsys):
    try:
        website_converter.main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("main(['--help']) must exit via argparse")
    assert "Convert static websites to ZIM archive format" in capsys.readouterr().out
