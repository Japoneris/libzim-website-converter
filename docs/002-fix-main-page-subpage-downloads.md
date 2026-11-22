# 002 — Fix: Main Page Resolution for Sub-page Downloads

## Goal

When a ZIM file is built from a blog post or sub-page download (e.g. `https://site.com/p/my-article`), Kiwix was opening to an empty or irrelevant page instead of the actual article.

## Problem

HTTrack saves pages without a URL extension as `<path>.html` on disk (e.g. `p/dna-sequencing.html`). But `derive_main_page_from_url()` returned the raw URL path (`p/dna-sequencing`) with no extension. So `set_mainpath()` pointed to a ZIM entry that did not exist, causing Kiwix to show an empty page even though the content was correctly included in the archive.

A secondary issue: older configs created without a `main_page` field fell back to `"index.html"`, which is HTTrack's auto-generated directory listing — not the article.

## Changes

### `website_converter.py`

Added `resolve_main_page(main_page, site_path)` function (just above the `Creator` usage). It tries candidates in order:
1. `main_page` as-is
2. `main_page + ".html"`
3. `main_page + "/index.html"`
4. `main_page.rstrip('/') + "/index.html"`
5. Fallback: `"index.html"`

Before calling `creator.set_mainpath()`, the configured value is now resolved against the actual files on disk. A warning is logged if a fallback was used.

### `httrack_wrapper.py`

In `create_config_file()`, after deriving the URL path, the downloaded `site_path` directory is scanned to find the real file matching the URL. The config is then written with the correct, disk-verified path (e.g. `"p/dna-sequencing.html"` instead of `"p/dna-sequencing"`).

## Impact

- All existing configs (including old ones without a `main_page` key) now open to the correct page at ZIM load time.
- Newly generated configs also get the correct path written in from the start.
- No re-download required to benefit from the fix.
