"""Tests for the shared validation/sanitization helpers."""

import pytest

from converter.validation import (
    sanitize_filename,
    validate_filename,
    validate_language_code,
)
from create_config import (
    sanitize_filename as config_sanitize_filename,
    validate_language_code as config_validate_language_code,
)


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("eng", True),
        ("fra", True),
        ("ENG", True),
        ("en", False),
        ("e3g", False),
        ("", False),
        (None, False),
    ],
)
def test_validate_language_code(code, expected):
    assert validate_language_code(code) is expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("my-site_1", True),
        ("my site", True),
        ("a/b", False),
        ("a:b", False),
        ("", False),
    ],
)
def test_validate_filename(name, expected):
    assert validate_filename(name) is expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("my site", "my-site"),
        ("a:b?c", "abc"),
        ("a/b\\c", "abc"),
        ("", ""),
    ],
)
def test_sanitize_filename(name, expected):
    assert sanitize_filename(name) == expected


def test_config_builder_uses_canonical_language_validator():
    assert config_validate_language_code("ENG") is True


def test_config_builder_uses_canonical_filename_sanitizer():
    assert config_sanitize_filename("a:b?c") == "abc"
