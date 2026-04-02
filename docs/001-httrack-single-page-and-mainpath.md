# 001 — HTTrack: Single-Page Mode and Dynamic Mainpath

## Goal

Two improvements to the HTTrack download workflow:

1. **Single-page mode** — let users download only the exact URL they provide, without following any links.
2. **Dynamic ZIM entrypoint** — correctly set the ZIM mainpath when the entry URL is not at the site root (e.g. `domain.com/pages/article.html`).

## Value

- Before, downloading a single article required knowing the httrack flag `-r1` and passing it via `--httrack-args`. Now there is a dedicated `--single-page` flag.
- Before, any site whose entry URL was not at the root (e.g. a tutorial page at `/docs/intro.html`) would open Kiwix on a blank or wrong page, because the mainpath was hardcoded to `index.html`. Now the correct path is derived automatically from the URL.

## Changes

### `httrack_wrapper.py`

- Added `derive_main_page_from_url(url)` — strips the scheme/domain and normalises the path:
  - Root URL → `"index.html"`
  - Trailing-slash URL → `"path/to/index.html"`
  - File URL → `"path/to/file.html"` (as-is)
- Added `--single-page` CLI flag. When set, prepends `-r1` to the httrack arguments so only the given URL is fetched.
- `create_config_file()` now accepts `single_page` (bool) and writes two new fields to the JSON:
  - `"main_page"` — relative path of the entry point
  - `"single_page"` — whether the download was a single-page capture

### `converter/config.py`

- Added `"main_page": "index.html"` to `CONFIG_DEFAULTS` so existing configs without this field continue to work.

### `website_converter.py`

- Line 203: replaced `creator.set_mainpath("index.html")` with `creator.set_mainpath(config.get("main_page", "index.html"))`.

## Usage

```bash
# Single page (no link following)
python3 httrack_wrapper.py https://example.com/docs/intro.html --single-page

# Recursive (default, unchanged)
python3 httrack_wrapper.py https://example.com/
```

Generated config will include:
```json
{
  "main_page": "docs/intro.html",
  "single_page": true
}
```
