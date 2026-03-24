# 000 - Config-file-first CLI refactor

## Goal

Simplify the CLI workflow by making the JSON config file the **single required argument** to `website_converter.py`. Previously, users had to provide a positional `site_path`, an optional `--config` file (metadata only), and feature flags as CLI args. Now all project settings live in one config file.

A new `create_config.py` tool helps users build config files interactively.

## Value

- **Simpler usage**: `python3 website_converter.py config/my-site.json` — one argument, done.
- **Reproducible builds**: the config file is a complete, self-contained description of the project.
- **No more interactive prompts in the converter**: the converter is now fully non-interactive.
- **Easier onboarding**: `create_config.py` guides new users through config creation.

## New workflow

```bash
# 1. Download a website (creates config automatically)
python3 httrack_wrapper.py https://example.com/article

# 2. Review/edit the config
cat config/article.json

# 3. Convert to ZIM
python3 website_converter.py config/article.json

# Or create a config from scratch:
python3 create_config.py
```

## Config file format

```json
{
  "site_path": "downloads/my-site/example.com",
  "output_path": "zim_files",
  "icon": "icons/my-icon.png",

  "name": "my-site",
  "title": "My Site Title",
  "creator": "John Doe",
  "publisher": "You",
  "description": "Offline copy of example.com",
  "language": "eng",

  "resolve_external": false,
  "cleanup": false,
  "optimize_images": false,
  "max_image_width": 1920,
  "image_quality": 85
}
```

**Required fields**: `site_path`, `name`, `title`, `creator`, `description`, `language`

**Optional fields** (with defaults): `output_path` (`zim_files`), `icon` (`icons/comment.png`), `publisher` (`You`), `resolve_external` (`false`), `cleanup` (`false`), `optimize_images` (`false`), `max_image_width` (`1920`), `image_quality` (`85`)

## CLI flags

`website_converter.py` now only accepts runtime flags:

| Flag | Description |
|------|-------------|
| `--verbose` | DEBUG-level logging |
| `--quiet` | Errors only |
| `--dry-run` | Analyze without creating ZIM |
| `--report` | Generate HTML validation report |
| `--no-progress` | Disable progress bar |

Removed flags: `--name`, `--title`, `--creator`, `--publisher`, `--description`, `--language`, `--config`, `--non-interactive`, `--resolve-external`, `--cleanup`, `--optimize-images`, `--max-image-width`, `--image-quality`, `--icon`, `--output_path`, and the positional `site_path`.

## Files modified

- **`converter/config.py`** — added `validate_config()`, `CONFIG_DEFAULTS`, `REQUIRED_FIELDS`. `load_config()` now exits on error instead of returning empty dict.
- **`converter/__init__.py`** — exported `validate_config`.
- **`website_converter.py`** — rewrote argparse (single positional `config_file` + runtime flags). Replaced interactive metadata prompts with config-driven flow. Uses `SimpleNamespace` to pass config values to `file_processor`.
- **`httrack_wrapper.py`** — `create_config_file()` now auto-detects and writes `site_path`. Updated "Next steps" message.
- **`create_config.py`** — new interactive config builder script.
- **`config/*.json`** — all config files updated with `site_path` field.
