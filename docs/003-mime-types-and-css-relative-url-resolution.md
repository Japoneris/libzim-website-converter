# 003 — MIME types + CSS relative URL resolution

## Goal

Two improvements to make offline ZIM files render more completely:

1. Add missing audio/video MIME types so those files are stored with correct types in the ZIM.
2. Download fonts and images referenced via relative paths in downloaded CSS files (e.g. Font Awesome webfonts).

## Problem

### MIME types
`converter/mime_types.py` was missing common audio/video formats: `mp3`, `ogg`, `opus`, `aac`, `flac`, `m4a`, `webm`, `weba`, `avi`, `mov`. Files with these extensions fell through to the unknown-extension path.

### CSS relative URLs
When `resolve_external_dependencies()` downloads a CSS file (e.g. Font Awesome's `all.min.css` from cdnjs), that CSS references its webfonts via relative paths like `url(../webfonts/fa-solid-900.woff2)`. The existing code only scanned for absolute/protocol-relative URLs (`https://` or `//`), so the fonts were never downloaded. Font Awesome icons were always broken.

The fix is clean because `_external/` preserves the full domain+path directory structure: the relative path from the CSS file to the fonts remains valid automatically — no URL rewriting is needed, just downloading the files.

## Changes

### `converter/mime_types.py`
Added 10 audio/video entries: `mp3`, `ogg`, `opus`, `aac`, `flac`, `m4a`, `webm`, `weba`, `avi`, `mov`.

### `converter/external_deps.py`
- Added `urljoin` to imports.
- Added `_RE_CSS_RELATIVE_URL` regex matching relative `url()` references in CSS (excludes `https://`, `//`, `data:`).
- Added `find_relative_urls_in_css(content)` helper function.
- Modified `resolve_external_dependencies()` phase 2: CSS entries in `downloaded_css` now also carry the original absolute URL (3-tuple instead of 2-tuple) so relative references can be resolved.
- Modified phase 3: after scanning for absolute URLs, also resolves relative `url()` references using `urljoin(css_url, rel)`, downloads the result, and recurses into any relative-referenced CSS files.
