# 005 - Ruff lint gate

## Goal

Add Ruff as a project lint gate so that style and correctness regressions are caught with one command before committing.

## Value

- One command (`my_env/bin/ruff check .`) reports unused imports, undefined names, import-order drift and common bug patterns across the Python sources.
- The rule set is pinned in `ruff.toml` instead of relying on Ruff's defaults, which changed to a much broader set in recent versions (the installed 0.17.6 reported 67 issues with no config, versus 29 with the project config).
- The baseline is clean: all current sources pass, so any future error is new.

## Code changes

- **`requirements.txt`** - Added `ruff>=0.17` as a dev dependency.
- **`ruff.toml`** (new) - Explicit configuration: Python 3.12 target, line length 100, exclusions for `downloads/`, `zim_files/`, `my_env/`, `.hermes/`, `.ipynb_checkpoints/` and `__pycache__/`. Enabled rules: `E4`, `E7`, `E9`, `F`, `I` (import order), `B` (bugbear) and `UP` (pyupgrade). Operational rules such as `BLE001` (broad `except Exception`), `S` (bandit) and `LOG015` (root logger) are deliberately excluded: the converter intentionally catches broad exceptions per file so one bad asset does not abort a whole archive, and several library modules use the root logger by design.
- **Source files** - Applied Ruff's safe fixes across `converter/`, the three root scripts and `tests/`: sorted imports, removed unnecessary `f` prefixes and redundant `r` open modes, removed an unused `logging` import.
- **`website_converter.py`** - Replaced the `try: from tqdm import tqdm` availability probe (flagged as an unused import) with `find_spec("tqdm") is not None`; behavior is unchanged because tqdm is actually imported where used, in `converter/file_processor.py` and `converter/external_deps.py`.
- **`readme.md`**, **`MODULES.md`** - Documented the lint command and the config file.

## Relevant information

The formatter is available (`my_env/bin/ruff format .`) but is not enforced: adopting it would reformat every source file and produce a large diff unrelated to behavior. It can be enabled in a separate change if the project wants a single canonical style.

## Verification

```bash
cd /home/japoneris/Code/Python/ZimSite
my_env/bin/ruff check .
my_env/bin/python -m pytest -q
```

Expected: `All checks passed!` and `30 passed`.
