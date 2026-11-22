"""Path resolution helpers for ZIM main-page selection."""

from pathlib import Path
from urllib.parse import unquote


def resolve_main_page(main_page: str, site_path: Path) -> str:
    """Resolve main_page to an actual file that exists in site_path.

    URL-decodes the input first (handles %20, %26, etc.) so the path
    can be matched against the real filesystem paths used as ZIM item keys.
    Tries candidates in order: exact path, + .html, + /index.html
    (a trailing slash is trimmed before appending /index.html).
    Falls back to index.html.
    """
    decoded = unquote(main_page)
    candidates = [
        decoded,
        decoded + ".html",
        decoded.rstrip('/') + "/index.html",
    ]
    for candidate in candidates:
        if (site_path / candidate).is_file():
            return candidate
    return "index.html"
