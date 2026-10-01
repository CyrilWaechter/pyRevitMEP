# AGENTS.md

pyRevit extension that adds MEP tools to Autodesk Revit. There is no build step and no CLI: scripts execute inside Revit via pyRevit (Windows only) and cannot be imported or run from this checkout.

## Repository layout

- `extension.json` — pyRevit extension manifest; the repo root is the extension root (installed as `pyRevitMEP.extension`, see README / `bash/`).
- `pyRevitMEP.tab/` — Revit UI tree. Directory suffixes define the element type (`*.panel`, `*.stack`, `*.pulldown`, `*.pushbutton`); unrecognized suffixes such as `*.nobutton` are hidden. Tab order comes from `layout:` in `pyRevitMEP.tab/bundle.yaml`.
- `<tool>/script.py` — button entrypoint. Optional siblings: `bundle.yaml` (localized `fr_fr`/`en_us` title and tooltip; shared values such as `author` and `youtube` are defined once in the parent `bundle.yaml` and referenced as `{{author}}`), `icon.png`, `*.xaml` for WPF UI. Older tools put metadata in `__title__`/`__doc__` instead of `bundle.yaml`.
- `lib/` — extension library, automatically added to `sys.path` by pyRevit; scripts import it as `from pyrevitmep...`. The `pyrevit` package itself is provided by the host, it is not vendored here.
- `lib/pyrevitmep/` — shared code of this extension (parameters, events, Excel, plumbing, …).
- `lib/materialsdb/`, `lib/lxml/` — vendored third-party code (materialsdb.org; lxml is compiled for CPython 3.8 on Windows). `materialsdb/classes.py` is generated — do not edit it directly.
- New tools go in the matching functional panel; `Lab.panel` is for experiments and `Samples.panel` for pyRevit/API samples.

## Python and pyRevit conventions

- The engine is chosen per script by its first line: `#! python3` selects CPython, no shebang means the default IronPython 2.7 engine. Tools using Python 3 features or vendored libs declare `#! python3` (MaterialsDB, PySide2 samples, f-strings); other scripts must stay IronPython-compatible (no f-strings, py2 idioms such as `collections.Iterable`). Check line 1 before editing and keep the code valid for that engine.
- Use pyRevit APIs instead of raw entrypoints: `from pyrevit import revit, DB, script, forms, HOST_APP`; `revit.doc`, `revit.uidoc`, `revit.Transaction("...")`; `script.get_config()`, `script.get_logger()`, `script.get_output()`.
- Support multiple Revit versions via `HOST_APP.is_older_than(...)` (see `lib/pyrevitmep/parameter/__init__.py`: `ParameterType` vs `SpecTypeId`, `BuiltInParameterGroup` vs `GroupTypeId`) instead of assuming the newest API.
- Modeless WPF windows (`pyrevit.forms.WPFWindow` + XAML) must push model changes through `pyrevitmep.event.CustomizableEvent`, with the transaction opened inside the callback, not before; those buttons need `engine: persistent: true` in `bundle.yaml` or the handler stops when the script ends.

## Verification and workflow

- No CI and no automated tests; verification is manual: load/update the extension in Revit through pyRevit and run the tool. The only test (`pyRevitMEP.tab/unittest.panel/...`) also runs inside Revit.
- Formatting: `ruff format` with line length 120 (config in `pyproject.toml`); run it on files you edit. Vendored `lib/lxml`/`lib/materialsdb` and two Python 2 Lab scripts are excluded.
- Remote Revit workflow: before any remote work, load the `remote-revit` skill (machine-wide); this project's remote path and sync commands are in `AGENTS.local.md` when present.
- Expected update flow is `bash/pyrevit_update.sh` → `git checkout -f && git pull`; local modifications are expected to be discarded.
- Commit messages look like `ToolName: description` (e.g. `ViewRename: Fixe save to parameter`); contributions are forks with PRs against `master` (see CONTRIBUTING.md).
