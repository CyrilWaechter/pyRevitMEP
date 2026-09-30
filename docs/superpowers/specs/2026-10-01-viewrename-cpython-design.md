# ViewRename v2 — CPython migration and GUI removal

Date: 2026-10-01
Status: Design approved; implementation plan pending

## Context

pyRevitMEP is a pyRevit extension for Autodesk Revit. This spec covers the first
sub-project of a larger, tool-by-tool effort to audit and sanitize the extension:
migrate scripts to CPython (Python 3) where possible, drop WPF dialogs that block the
migration, and support the four newest Revit versions (2024–2027).

### Current ViewRename implementation

- IronPython 2.7 (no shebang), modeless WPF window (`ViewRename.xaml`), persistent
  engine, and `pyrevitmep.event.CustomizableEvent` (an `IExternalEventHandler`) to run
  the rename in a valid Revit API context.
- One window per view class (`ViewPlan`, `View3D`, `ViewSection`) with a pattern text
  box, live previews, a parameter picker (Name / BuiltInParameter / GUID), and
  "add parameter at cursor".
- Patterns stored in the project parameter `pyRevitMEP_viewrename_patterns`
  (created through the extension's shared-parameter machinery), with a pyRevit config
  file fallback.

### Problems this design fixes

- Under CPython, `pyrevit.forms` is a stub: every UI symbol raises
  `PyRevitCPythonNotSupported` (verified on the target machine, pyRevit 6.5.5 /
  CPython 3.12.3). The modeless WPF window is what forces IronPython.
- Pattern parameter creation is broken: `delete_from_definition_file()` is called
  without its required argument, and the shared `pyrevitmep.parameter` module imports
  an `rsparam` package that is not vendored in this repository. Creation also depends
  on a configured shared parameter file.
- `getparameter()` uses `eval()` on pattern text — unsafe input handling.
- Pattern serialization (`str(dict).encode("utf8")`) and config writes
  (`str.encode("utf8")`) are IronPython-2 idioms and produce fragile values.
- Inline metadata (`__doc__`, `__title__`, `__author__`) duplicates `bundle.yaml`;
  pyRevit is deprecating inline metadata.

### Target environment (verified remotely)

- pyRevit 6.5.5; engines available: IronPython 2.7.12 (active), IronPython 3.4.2,
  CPython 3.12.3.
- Revit 2022–2025 installed on the test machine (2026/2027 not installed).
- Per-button engine selection works (`#! python3` hashbang); push-button bundles may
  contain a `config.py` that pyRevit runs on Shift+Click and that adds a ● marker on
  the button.

## Goal

ViewRename runs under CPython 3, on Revit 2024–2027, with no WPF and no persistent
engine, while preserving the useful parts of its workflow: configurable per-class
patterns, a live preview, and a parameter picker for building patterns.

Success criteria:

- Normal click applies patterns to selected views, or to all non-template views of
  configured classes when no view is selected, after an explicit confirmation with a
  preview.
- Shift+Click opens a pattern editor in which the user can build patterns from a
  parameter list, see previews, and save to the model or to user config.
- Existing users' patterns (legacy project parameter or config file) keep working and
  are migrated to the new model storage on first editor save.
- Nothing in the tool requires `pyrevit.forms`, WPF, IronPython, `rsparam`, or a
  shared parameter file.

## Product design

### One button, two modes

- **Normal click → Apply patterns.**
  1. Determine scope (see below).
  2. Resolve every target view's new name from the configured patterns.
  3. Show a native `TaskDialog` preview: scope in plain words, target count, first
     ~10 `old → new` lines; buttons **Rename** / **Cancel**.
  4. On confirm, rename everything in one transaction; disambiguate conflicts by
     appending ` 1`, ` 2`, … (current behavior).
  5. Write the full report to the pyRevit output window: renamed views (old → new,
     including auto-disambiguated names), views skipped because their class has no
     pattern, views skipped because they are templates, and failures.
- **Shift+Click → Edit patterns** (`config.py`). The button shows pyRevit's automatic
  ● marker; `bundle.yaml` tooltips mention SHIFT-CLICK.

### Scope rules

- Selection contains at least one view → rename those views only; non-view elements in
  the selection are ignored.
- Otherwise → all non-template views whose class has a configured pattern.
- The confirmation dialog always states the scope explicitly, so mass renames are
  never silent. If the tool is run with no patterns configured, show a `TaskDialog`
  explaining that Shift+Click opens the editor, and do nothing.

### Pattern syntax and resolution

Patterns are a `{view class name: pattern}` map. Resolution keeps the current
mini-language and semantics, with explicit parsing instead of `eval()`:

- `name(Some Parameter)` → first parameter with that definition name;
  editor previews definition names (secondary preview).
- `bip(BUILTIN_NAME)` → `BuiltInParameter` looked up with `getattr`.
- `Guid('xxxxxxxx-…')` → shared parameter resolved by GUID (`Guid.Parse`, not `eval`).
- Unresolvable references resolve to the empty string (current behavior).
- Rename values use the display value (`AsValueString`) like the current apply path.

Supported classes are extensible: anything present in the stored map is applied. The
editor offers **ViewPlan, View3D, ViewSection, ViewSheet, ViewDrafting**. Patterns for
classes with no views in the model are ignored.

### Pattern storage

Read order:

1. **ExtensibleStorage** on `ProjectInformation` — schema `pyRevitMEP.ViewRename`
   (fixed GUID), single string field holding JSON. Primary storage; travels with the
   model and needs no shared parameter file or parameter.
2. Legacy project parameter `pyRevitMEP_viewrename_patterns` (only if ExtensibleStorage
   is empty), parsed safely with `ast.literal_eval` (the old tool stored `str(dict)`,
   with single quotes) instead of `eval`.
3. pyRevit user config attributes (`ViewPlan`, `View3D`, …), decoding `bytes` values
   written by the old tool.

Editor save buttons write to ExtensibleStorage ("Save to model") and/or user config
("Save to config"). The first model save migrates whatever was read from the legacy
sources. The legacy parameter itself is left untouched; deleting it is a separate
cleanup the user can do with the existing ParameterDelete tool.

### Editor (`config.py`, WinForms)

- One tab per offered view class, each with:
  - pattern text box;
  - live primary preview (resolved name) and secondary preview (definition names);
  - parameter list for a sample view of that class, columns Name / BuiltInParameter /
    GUID, with **Insert at cursor**;
  - disabled tab with a note when the model has no view of that class.
- Old hardcoded defaults are pre-filled as starting suggestions only, and only when a
  class has no stored pattern; they are never applied implicitly.
- Buttons: **Save to model**, **Save to config**, **Close**. Empty pattern boxes are
  saved as absent entries (removing the class from storage). The window is modal;
  transactions run after it closes. No external event, no persistent engine.
- Invalid pattern syntax is reported in the window, not silently saved.

Note: the old hardcoded defaults produce names like `_PE_…` for models without the
company parameters, which is why the new apply path never uses implicit defaults.

## Technical design

### Bundle layout

```
pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/
├── script.py          # apply mode, CPython (#! python3)
├── config.py          # editor mode, CPython (#! python3), runs on Shift+Click
├── bundle.yaml        # persistent engine removed; tooltips mention SHIFT-CLICK
├── icon.png           # unchanged
└── lib/
    └── viewrename/
        ├── __init__.py
        ├── pattern.py # syntax parsing and application (no eval)
        ├── storage.py # ExtensibleStorage, legacy parameter, config, migration
        └── ui.py      # WinForms editor window
```

`ViewRename.xaml` is deleted. Inline `__doc__` / `__title__` / `__author__` are removed
from `script.py`. pyRevit adds a bundle `lib/` folder to `sys.path` automatically
(verified in pyRevit documentation and loader behavior); the probe below confirms it
under CPython 3.12 before product code is written.

### Probes (first implementation step, throwaway)

Run on the remote machine against a scratch model, on Revit 2024 and 2025, via
`pyrevit run --allowdialogs`:

1. **WinForms under CPython**: reference `System.Windows.Forms`, build a small form
   with a text box and a button, wire an event, `ShowDialog` auto-closed by a timer.
2. **ExtensibleStorage under pythonnet**: `SchemaBuilder`, `Entity.Set[str]` and
   `Get[str]` on `ProjectInformation`, read back in a transaction.
3. **pyRevit CPython basics**: bundle `lib/` import, `script.get_output()`,
   `script.get_config()` / `save_config()`, `revit.Transaction`, `TaskDialog` with
   buttons.

Decision points and fallbacks:

- WinForms fails → the editor remains a separate IronPython WPF button (old
  `ViewRename.xaml` kept) until a later decision; `script.py` still ships as CPython.
- ExtensibleStorage generics fail → store the JSON in a reimplemented project
  parameter (robust creation, no shared parameter file dependency if avoidable) or
  fall back to config-only, decided with the user before proceeding.
- Bundle `lib/` import fails → flatten the modules into `script.py` / `config.py` or
  use the extension `lib/` directory.

### Version support

Only APIs present in Revit 2024–2027 are used (ForgeTypeId era; no
`ElementId.IntegerValue`, no `ParameterType` / `BuiltInParameterGroup`). There is no
version-conditional code expected. Revit 2026/2027 cannot be tested on the available
machine; this limitation is recorded and accepted at design time.

### Removed machinery

Modeless WPF window, `CustomizableEvent` for this tool, persistent engine,
`pyrevitmep.parameter` dependency (and therefore `rsparam` and the shared parameter
file), `eval()` on pattern text, `SpecTypeId` import fragility.

## Verification

Manual, on the remote Revit 2024 and 2025:

- No patterns configured → explanatory dialog, no changes.
- Patterns from: ExtensibleStorage; legacy project parameter; pyRevit config.
- Scope: views selected; nothing selected; selection with non-view elements.
- Conflict handling: two views resolving to the same name; name colliding with an
  existing untouched view.
- Missing parameter in a pattern → empty substitution.
- Template views excluded; classes without patterns skipped and reported.
- Editor: parameter list populated, insert at cursor, previews match applied results,
  save to model and to config, invalid syntax reporting.
- Migration: model with legacy parameter gets patterns into ExtensibleStorage after
  the first editor save.
- `ruff format` (line length 120) on every touched file.

## Program sequencing

This sub-project is Phase 1. The remaining phases each get their own spec and plan:

- **Phase 0 — audit inventory** (can run in parallel with Phase 1): categorize all 71 scripts by
  engine, GUI kind, lib dependencies, version-sensitive APIs, Python-2 idioms, and
  bugs; write `docs/audit/tool-inventory.md`; use it to order later migrations.
- **Phase 2 — shared lib modernization**: make `lib/pyrevitmep` usable from CPython
  and Python 3 clean while keeping IronPython 2 compatibility for not-yet-migrated
  tools; remove the `rsparam` dependency; simplify version guards to Revit 2024+;
  delete unused `lib/lxml` (vendored for CPython 3.8 and imported nowhere).
- **Phase 3 — non-GUI tools to CPython** in verified batches.
- **Phase 4 — GUI tools**: one design per tool (WinForms or no-GUI redesign).

Out of scope: `Samples.panel` (pyRevit samples); `Lab.panel` is migrated
opportunistically only. Upstream pyRevit's eventual CPython WPF support is not relied
upon; if it lands, the WinForms editor can be revisited.
