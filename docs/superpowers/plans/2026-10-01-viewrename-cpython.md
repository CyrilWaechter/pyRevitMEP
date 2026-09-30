# ViewRename v2 (CPython) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace ViewRename's IronPython/modeless-WPF implementation with a CPython 3 tool: TaskDialog-confirmed apply flow plus a WinForms pattern editor, targeting Revit 2024–2027.

**Architecture:** Two pyRevit entry points in the bundle — `script.py` (normal click, apply) and `config.py` (Shift+Click, editor). Shared logic lives in the bundle `lib/viewrename/` package: pure `pattern.py` and `codec.py` (locally unit-tested), Revit-facing `apply.py` and `storage.py`, and WinForms `ui.py`. Patterns are stored as JSON in ExtensibleStorage on Project Information, with legacy-parameter and pyRevit-config fallbacks.

**Tech Stack:** CPython 3.12.3 (pyRevit CPython engine), Revit API 2024+, pythonnet, WinForms (`System.Windows.Forms`), pyRevit 6.5.x; pytest for local dev-only unit tests; ruff (line length 120).

**Spec:** `docs/superpowers/specs/2026-10-01-viewrename-cpython-design.md`

## Global Constraints

- Target Revit versions: 2024–2027. Use only 2024+ API (`ForgeTypeId` era): no `ElementId.IntegerValue`, no `ParameterType`, no `BuiltInParameterGroup`.
- Every script first line: `#! python3` (CPython). No IronPython, no WPF, no `pyrevit.forms`, no persistent engine.
- No dependency on `pyrevitmep.parameter`, `rsparam`, or a shared parameter file.
- `eval()` must not appear anywhere in the new code; pattern references are parsed explicitly.
- Pattern semantics to preserve: `name(Param Name)`, `bip(BUILTIN_NAME)`, `Guid('…')`; display value via `AsString()` for String storage else `AsValueString()`; unresolvable reference → empty string.
- Commits: `ViewRename: <description>` (repo convention).
- Remote workflow: use the `remote-revit` skill and `AGENTS.local.md`. Extension path `C:\Users\Marie\AppData\Roaming\pyRevit\Extensions\PyRevitMEP.extension`; pyRevit CLI `C:\Users\Marie\AppData\Roaming\pyRevit-Master\bin\pyrevit.exe`. Remote output must be ASCII.
- Scratch models are copies; never test on originals. `%TEMP%` = `C:\Users\Marie\AppData\Local\Temp`.
- Local test command: `python3 -m pytest tests/viewrename -q` (dev-only tests; not loaded by pyRevit). Formatting: `ruff format` then `ruff check` on touched files.
- Do not commit `AGENTS.md`, `AGENTS.local.md`, or `pyproject.toml` (pre-existing untracked user files).

## Review Focus

Inputs/conditions the spec implies that no test fully pins; each is covered in the task listed.

1. Selection containing views whose class has no pattern (and non-view elements) → those are skipped and reported, other selected views still renamed (Task 4 test, Task 7 integration).
2. Two views resolving to the same name, or to a name already used by a view outside the target set → deterministic ` 1`, ` 2` suffixing, failures reported instead of aborting the batch (Task 4 test, Task 7 integration).
3. Legacy/corrupt stored data: `bytes` config values, single-quoted Python-dict strings, accented values, empty or non-dict payloads → parsed when recognizable, treated as absent when not, never raises (Task 3 tests, Task 5 remote smoke).
4. Pattern references to missing parameters and unbalanced/unknown syntax → empty substitution at apply time; editor refuses to save invalid syntax (Task 2 tests, Task 6 smoke).
5. View templates and non-view elements → never renamed (Task 7 integration).

---

### Task 1: Remote capability probes (throwaway, no commit)

**Files:**
- Create locally (throwaway, not committed): `/tmp/opencode/viewrename-probe/probe.py`
- Create locally (throwaway): `/tmp/opencode/viewrename-probe/probe-extension/ProbeOC.extension/ProbeOC.tab/Probe.panel/Probe.pushbutton/script.py` and `.../lib/probelib/__init__.py`

**Interfaces:**
- Consumes: nothing.
- Produces: go/no-go for WinForms, ExtensibleStorage `Set[str]`/`Get[str]`, `script.get_output()`, `script.get_config()`, TaskDialog properties, and bundle `lib/` import under CPython 3.12. Fallbacks are chosen here if a probe fails (spec "Decision points and fallbacks").

- [ ] **Step 1: Create scratch model copies on the remote**

```bash
ssh -p 2222 Marie@127.0.0.1 'mkdir "%TEMP%\viewrename-test" 2>nul & copy /Y "C:\Users\Marie\Nextcloud\0000_ProjetExemple\Liens\rac_advanced_sample_project_R24.rvt" "%TEMP%\viewrename-test\scratch_r24.rvt" & copy /Y "C:\Users\Marie\Nextcloud\0000_ProjetExemple\Liens\rac_advanced_sample_project_R25.rvt" "%TEMP%\viewrename-test\scratch_r25.rvt"'
```

Expected: exit code 0 and two files in `%TEMP%\viewrename-test` (the copy confirmation text is localized).

- [ ] **Step 2: Write the probe script**

`/tmp/opencode/viewrename-probe/probe.py` — exact content:

```python
#! python3
"""Throwaway CPython capability probe for ViewRename v2. ASCII output only."""
import traceback


def report(tag, ok, detail=""):
    print("PROBE {} {} {}".format(tag, "OK" if ok else "FAIL", detail))


def failure(tag, exc):
    report(tag, False, str(exc).encode("ascii", "replace").decode("ascii"))


# 1. pyRevit CPython basics
try:
    from pyrevit import revit, script
    doc = revit.doc
    report("doc", doc is not None, doc.Title if doc else "no-doc")
    output = script.get_output()
    report("output", True, type(output).__name__)
    config = script.get_config()
    setattr(config, "ProbeKey", "probe-value")
    report("config", getattr(config, "ProbeKey") == "probe-value", str(getattr(config, "ProbeKey")))
except Exception as exc:
    failure("pyrevit", exc)
    traceback.print_exc()

# 2. WinForms with an event and a modal dialog
try:
    import clr

    clr.AddReference("System.Windows.Forms")
    clr.AddReference("System.Drawing")
    from System.Drawing import Point
    from System.Windows.Forms import Form, TextBox, Timer

    form = Form()
    box = TextBox()
    box.Location = Point(10, 10)
    form.Controls.Add(box)
    fired = {"value": False}

    def on_text(sender, args):
        fired["value"] = True

    box.TextChanged += on_text
    box.Text = "hello"
    timer = Timer()
    timer.Interval = 1200
    timer.Tick += lambda sender, args: form.Close()
    timer.Start()
    form.ShowDialog()
    report("winforms", fired["value"], "TextChanged fired")
except Exception as exc:
    failure("winforms", exc)
    traceback.print_exc()

# 3. ExtensibleStorage round-trip (product schema; scratch model only)
try:
    from System import Guid
    from Autodesk.Revit.DB import AccessLevel, ExtensibleStorage, Schema, SchemaBuilder

    schema_guid = Guid("62444aa5-69f7-4aa6-9b0e-238dd1309f83")
    schema = Schema.Lookup(schema_guid)
    if schema is None:
        builder = SchemaBuilder(schema_guid, "pyRevitMEP.ViewRename")
        builder.SetReadAccessLevel(AccessLevel.Public)
        builder.SetWriteAccessLevel(AccessLevel.Public)
        builder.AddSimpleField("Patterns", str)
        schema = builder.Finish()
    entity = ExtensibleStorage.Entity(schema)
    entity.Set[str]("Patterns", '{"ViewPlan": "probe"}')
    with revit.Transaction("ViewRename probe"):
        doc.ProjectInformation.SetEntity(entity)
    read_back = doc.ProjectInformation.GetEntity(schema).Get[str]("Patterns")
    report("extensible", read_back == '{"ViewPlan": "probe"}', read_back)
except Exception as exc:
    failure("extensible", exc)
    traceback.print_exc()

# 4. TaskDialog construction (never shown; Show blocks on a human click)
try:
    from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons

    dialog = TaskDialog("Probe")
    dialog.MainInstruction = "probe"
    dialog.MainContent = "probe"
    dialog.CommonButtons = TaskDialogCommonButtons.Cancel
    report("taskdialog", True)
except Exception as exc:
    failure("taskdialog", exc)

print("PROBE done")
```

- [ ] **Step 3: Write the bundle-lib probe extension**

`ProbeOC.pushbutton/script.py`:

```python
#! python3
import probelib

print("PROBE bundle-lib OK " + probelib.ping())
```

`lib/probelib/__init__.py`:

```python
def ping():
    return "pong"
```

- [ ] **Step 4: Sync probes to the remote**

```bash
scp -P 2222 /tmp/opencode/viewrename-probe/probe.py 'Marie@127.0.0.1:C:/Users/Marie/AppData/Local/Temp/viewrename-test/probe.py'
tar czf - -C /tmp/opencode/viewrename-probe/probe-extension ProbeOC.extension \
  | ssh -p 2222 Marie@127.0.0.1 "tar xzf - -C C:/Users/Marie/AppData/Roaming/pyRevit/Extensions"
```

- [ ] **Step 5: Run the probe on Revit 2024 and 2025**

One Revit instance per run; allow several minutes each. Run sequentially, not in parallel.

```bash
ssh -p 2222 Marie@127.0.0.1 'C:\Users\Marie\AppData\Roaming\pyRevit-Master\bin\pyrevit.exe run "C:\Users\Marie\AppData\Local\Temp\viewrename-test\probe.py" --revit=2024 --models="C:\Users\Marie\AppData\Local\Temp\viewrename-test\scratch_r24.rvt" --allowdialogs'
```

Then the same with `--revit=2025` and `scratch_r25.rvt`.

Expected: every `PROBE <tag> OK`; `PROBE done`. For the bundle-lib check:

```bash
ssh -p 2222 Marie@127.0.0.1 'C:\Users\Marie\AppData\Roaming\pyRevit-Master\bin\pyrevit.exe run "C:\Users\Marie\AppData\Roaming\pyRevit\Extensions\ProbeOC.extension\ProbeOC.tab\Probe.panel\Probe.pushbutton\script.py" --revit=2024'
```

Expected: `PROBE bundle-lib OK pong`.

- [ ] **Step 6: Decide fallbacks and report**

- WinForms FAIL → editor stays a separate IronPython WPF button (keep `ViewRename.xaml`); continue with `script.py` CPython.
- ExtensibleStorage FAIL → stop and choose the storage fallback with the user before Task 5.
- Bundle lib FAIL → flatten `viewrename` modules into `script.py`/`config.py` (Tasks 2–6 adapt).
- `script.get_output()` FAIL → report via `script.get_logger()` plus a `TaskDialog` summary in Task 7.

Delete the probe extension and probe files afterwards:

```bash
ssh -p 2222 Marie@127.0.0.1 'rmdir /s /q "C:\Users\Marie\AppData\Roaming\pyRevit\Extensions\ProbeOC.extension" & del /q "%TEMP%\viewrename-test\probe.py"'
```

Report the probe matrix (tag → OK/FAIL, Revit version, chosen fallback) in chat. No commit: probe artifacts are throwaway.

---

### Task 2: `lib/viewrename/pattern.py` (pure pattern engine)

**Files:**
- Create: `pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/lib/viewrename/__init__.py`
- Create: `pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/lib/viewrename/pattern.py`
- Create: `tests/viewrename/conftest.py`
- Test: `tests/viewrename/test_pattern.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `viewrename.CLASS_NAMES = ("ViewPlan", "View3D", "ViewSection", "ViewSheet", "ViewDrafting")` in `__init__.py`
  - `pattern.apply_pattern(pattern: str, resolver) -> str` where `resolver` has `by_name(name: str) -> str`, `by_bip(name: str) -> str`, `by_guid(guid: str) -> str`
  - `pattern.validate_pattern(pattern: str) -> list[str]` (empty list = valid)

- [ ] **Step 1: Write the failing tests**

`tests/viewrename/conftest.py`:

```python
import pathlib
import sys

LIB = (
    pathlib.Path(__file__).resolve().parents[2]
    / "pyRevitMEP.tab"
    / "Manage.panel"
    / "ViewRename.pushbutton"
    / "lib"
)
sys.path.insert(0, str(LIB))
```

`tests/viewrename/test_pattern.py`:

```python
from viewrename import pattern


class FakeResolver:
    def __init__(self, values):
        self.values = values

    def by_name(self, name):
        return self.values.get("name:" + name, "")

    def by_bip(self, name):
        return self.values.get("bip:" + name, "")

    def by_guid(self, guid):
        return self.values.get("guid:" + guid, "")


def test_substitutes_name_bip_and_guid():
    resolver = FakeResolver(
        {
            "name:ORG_Métier": "CVC",
            "bip:PLAN_VIEW_LEVEL": "L1",
            "guid:62444aa5-69f7-4aa6-9b0e-238dd1309f83": "Partagé",
        }
    )
    result = pattern.apply_pattern(
        "name(ORG_Métier)_bip(PLAN_VIEW_LEVEL)_Guid('62444aa5-69f7-4aa6-9b0e-238dd1309f83')",
        resolver,
    )
    assert result == "CVC_L1_Partagé"


def test_unknown_references_resolve_to_empty_string():
    resolver = FakeResolver({})
    assert pattern.apply_pattern("pre_name(Missing)_post", resolver) == "pre__post"


def test_plain_text_passes_through_with_parentheses():
    resolver = FakeResolver({})
    assert pattern.apply_pattern("Plan (niveau)name(Level)", resolver) == "Plan (niveau)"


def test_validate_accepts_valid_pattern():
    assert pattern.validate_pattern("name(ORG_Métier)_bip(PLAN_VIEW_LEVEL)") == []


def test_validate_rejects_unbalanced_parentheses():
    assert pattern.validate_pattern("name(Level") != []


def test_validate_rejects_unknown_reference():
    assert pattern.validate_pattern("foo(bar)") != []


def test_validate_ignores_parentheses_without_leading_word():
    assert pattern.validate_pattern("Plan (sans reference)") == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/viewrename/test_pattern.py -q`
Expected: collection error / `ModuleNotFoundError` for `viewrename`.

- [ ] **Step 3: Implement the modules**

`__init__.py`:

```python
CLASS_NAMES = ("ViewPlan", "View3D", "ViewSection", "ViewSheet", "ViewDrafting")
```

`pattern.py` — exact regexes and substitution order (name, then Guid, then bip, as the old tool did):

```python
NAME_RE = re.compile(r"name\(([^)]+)\)")
BIP_RE = re.compile(r"bip\((\w+)\)")
GUID_RE = re.compile(r"""Guid\(\s*['"]([0-9a-fA-F-]{36})['"]\s*\)""")
REFERENCE_WORD_RE = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z]\w*\(")
KNOWN_REFERENCES = ("name(", "bip(", "Guid(")


class Resolver(object):
    """Duck-typed interface: by_name/by_bip/by_guid return a string, "" when absent."""

    def by_name(self, name):
        raise NotImplementedError

    def by_bip(self, name):
        raise NotImplementedError

    def by_guid(self, guid):
        raise NotImplementedError


def apply_pattern(pattern, resolver):
    result = NAME_RE.sub(lambda match: resolver.by_name(match.group(1)), pattern)
    result = GUID_RE.sub(lambda match: resolver.by_guid(match.group(1)), result)
    return BIP_RE.sub(lambda match: resolver.by_bip(match.group(1)), result)


def validate_pattern(pattern):
    errors = []
    if pattern.count("(") != pattern.count(")"):
        errors.append("Unbalanced parentheses")
    for match in REFERENCE_WORD_RE.finditer(pattern):
        word = match.group(0)
        if word not in KNOWN_REFERENCES:
            errors.append("Unknown reference: {}".format(word))
    return errors
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/viewrename -q`
Expected: 7 passed.

- [ ] **Step 5: Format and commit**

```bash
ruff format pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/lib/viewrename tests/viewrename
git add pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/lib/viewrename tests/viewrename
git commit -m "ViewRename: Add pure pattern engine"
```

---

### Task 3: `lib/viewrename/codec.py` (storage serialization)

**Files:**
- Create: `pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/lib/viewrename/codec.py`
- Test: `tests/viewrename/test_codec.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `codec.encode_patterns(patterns: dict) -> str` (JSON, non-empty values only, sorted keys)
  - `codec.decode_patterns(text) -> dict` (JSON first, then `ast.literal_eval` for the legacy `str(dict)` form; `{}` on any failure)
  - `codec.normalize_config_value(value) -> str` (`bytes` decoded UTF-8, `None` → `""`)

- [ ] **Step 1: Write the failing tests**

`tests/viewrename/test_codec.py`:

```python
from viewrename import codec


def test_encode_decode_round_trip_with_accents():
    patterns = {"ViewPlan": "PE_name(ORG_Métier)", "View3D": "name(Sous-catégorie)_3D"}
    assert codec.decode_patterns(codec.encode_patterns(patterns)) == patterns


def test_encode_skips_empty_values_and_sorts_keys():
    assert codec.encode_patterns({"View3D": "B", "ViewPlan": "", "ViewSheet": "A"}) == (
        '{"View3D": "B", "ViewSheet": "A"}'
    )


def test_decode_legacy_single_quoted_dict():
    legacy = "{'ViewPlan': 'PE_name(ORG_Métier)', 'View3D': 'name(X)_3D'}"
    assert codec.decode_patterns(legacy) == {
        "ViewPlan": "PE_name(ORG_Métier)",
        "View3D": "name(X)_3D",
    }


def test_decode_bytes_value():
    assert codec.decode_patterns(b"{'ViewPlan': 'A'}") == {"ViewPlan": "A"}


def test_decode_garbage_returns_empty_dict():
    assert codec.decode_patterns("not a dict") == {}
    assert codec.decode_patterns("") == {}
    assert codec.decode_patterns(None) == {}
    assert codec.decode_patterns([1, 2]) == {}


def test_decode_filters_non_string_and_empty_entries():
    assert codec.decode_patterns('{"ViewPlan": "A", "View3D": "", "ViewSheet": null}') == {
        "ViewPlan": "A"
    }


def test_normalize_config_value():
    assert codec.normalize_config_value(b"name(Level)") == "name(Level)"
    assert codec.normalize_config_value(None) == ""
    assert codec.normalize_config_value(42) == "42"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/viewrename/test_codec.py -q`
Expected: `ModuleNotFoundError` / missing `codec`.

- [ ] **Step 3: Implement `codec.py`**

```python
import ast
import json


def encode_patterns(patterns):
    cleaned = {key: value for key, value in patterns.items() if value}
    return json.dumps(cleaned, ensure_ascii=False, sort_keys=True)


def decode_patterns(text):
    if isinstance(text, bytes):
        try:
            text = text.decode("utf8")
        except UnicodeDecodeError:
            return {}
    if not text or not isinstance(text, str):
        return {}
    data = None
    try:
        data = json.loads(text)
    except ValueError:
        try:
            data = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            return {}
    if not isinstance(data, dict):
        return {}
    return {str(key): str(value) for key, value in data.items() if isinstance(value, str) and value}


def normalize_config_value(value):
    if isinstance(value, bytes):
        try:
            return value.decode("utf8")
        except UnicodeDecodeError:
            return ""
    if value is None:
        return ""
    return str(value)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/viewrename -q`
Expected: all tests pass (7 pattern + 7 codec).

- [ ] **Step 5: Format and commit**

```bash
ruff format pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/lib/viewrename tests/viewrename
git add pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/lib/viewrename/codec.py tests/viewrename/test_codec.py
git commit -m "ViewRename: Add pattern serialization codec"
```

---

### Task 4: `lib/viewrename/apply.py` (rename flow)

**Files:**
- Create: `pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/lib/viewrename/apply.py`
- Test: `tests/viewrename/test_apply.py`

**Interfaces:**
- Consumes: `pattern.apply_pattern` (Task 2); `codec` not needed here.
- Produces:
  - `apply.ViewResolver(view, use_definition_name=False)` — Revit-backed resolver (imports inside methods so the module imports without Revit).
  - `apply.collect_target_views(doc, patterns, selected_ids) -> (views, skipped, used_selection)`; `skipped = {"no_pattern": [str], "not_view": [str], "template": [str]}`.
  - `apply.compute_renames(views, patterns, resolver_factory=ViewResolver) -> list[(view, new_name)]`
  - `apply.preview_lines(renames, limit=10) -> list[str]`
  - `apply.rename_views(views_and_names, duplicate_exception) -> (renamed, failed)`; must run inside an open transaction; `renamed = list[(old, final)]`, `failed = list[(old, error_text)]`.
  - `apply.main(doc, uidoc, patterns, confirm) -> dict | None` (None = user cancelled); `confirm(renames, scope_label) -> bool`; opens one `revit.Transaction("ViewRename")`.
  - `apply.format_report(report) -> str`

- [ ] **Step 1: Write the failing tests**

`tests/viewrename/test_apply.py`:

```python
from viewrename import apply


class FakeDuplicate(Exception):
    pass


class FakeResolver:
    def __init__(self, values):
        self.values = values

    def by_name(self, name):
        return self.values.get(name, "")

    def by_bip(self, name):
        return ""

    def by_guid(self, guid):
        return ""


class FakeView:
    taken = None  # set of already-used names when conflict simulation is on

    def __init__(self, name, class_name):
        self._name = name
        self._class_name = class_name

    @property
    def Name(self):
        return self._name

    @Name.setter
    def Name(self, value):
        if FakeView.taken is not None:
            if value in FakeView.taken:
                raise FakeDuplicate(value)
            FakeView.taken.add(value)
        self._name = value


def make_view(name, class_name):
    return type(class_name, (FakeView,), {})(name, class_name)


def test_compute_renames_uses_pattern_per_class():
    view = make_view("old", "ViewPlan")
    renames = apply.compute_renames(
        [view], {"ViewPlan": "P_name(Level)"}, resolver_factory=lambda v: FakeResolver({"Level": "L1"})
    )
    assert renames == [(view, "P_L1")]


def test_compute_renames_skips_unconfigured_class():
    view = make_view("old", "View3D")
    assert apply.compute_renames([view], {"ViewPlan": "P"}, resolver_factory=FakeResolver) == []


def test_rename_views_disambiguates_duplicates():
    FakeView.taken = set()
    try:
        first = make_view("a", "ViewPlan")
        second = make_view("b", "ViewPlan")
        renamed, failed = apply.rename_views(
            [(first, "X"), (second, "X")], duplicate_exception=FakeDuplicate
        )
        assert renamed == [("a", "X"), ("b", "X 1")]
        assert failed == []
    finally:
        FakeView.taken = None


def test_rename_views_suffixes_around_names_outside_the_batch():
    FakeView.taken = {"X"}
    try:
        first = make_view("a", "ViewPlan")
        second = make_view("b", "ViewPlan")
        renamed, failed = apply.rename_views(
            [(first, "X"), (second, "X")], duplicate_exception=FakeDuplicate
        )
        assert renamed == [("a", "X 1"), ("b", "X 2")]
        assert failed == []
    finally:
        FakeView.taken = None


def test_rename_views_reports_failures_and_continues():
    class AlwaysFails:
        @property
        def Name(self):
            return "a"

        @Name.setter
        def Name(self, value):
            raise FakeDuplicate(value)

    renamed, failed = apply.rename_views([(AlwaysFails(), "X")], duplicate_exception=FakeDuplicate)
    assert renamed == []
    assert failed and failed[0][0] == "a"


def test_preview_lines_truncates():
    views = [make_view(str(i), "ViewPlan") for i in range(15)]
    lines = apply.preview_lines([(v, "n" + v.Name) for v in views], limit=3)
    assert lines == ["0 -> n0", "1 -> n1", "2 -> n2", "... and 12 more"]


def test_format_report_lists_sections():
    report = {
        "scope": "selected views",
        "cancelled": False,
        "renamed": [("old", "new")],
        "failed": [("bad", "boom")],
        "skipped": {"no_pattern": ["X"], "template": [], "not_view": []},
    }
    text = apply.format_report(report)
    assert "renamed 1" in text
    assert "old -> new" in text
    assert "bad -> boom" in text
    assert "X" in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/viewrename/test_apply.py -q`
Expected: `ModuleNotFoundError` / missing `apply`.

- [ ] **Step 3: Implement `apply.py`**

Key decisions to encode:

```python
from . import pattern


class ViewResolver(pattern.Resolver):
    def __init__(self, view, use_definition_name=False):
        self.view = view
        self.use_definition_name = use_definition_name

    def by_name(self, name):
        return self._pick(self.view.GetParameters(name))

    def by_bip(self, name):
        from Autodesk.Revit.DB import BuiltInParameter

        bip = getattr(BuiltInParameter, name, None)
        if bip is None:
            return ""
        return self._pick([self.view.get_Parameter(bip)])

    def by_guid(self, guid):
        from System import Guid

        try:
            parameter = self.view.get_Parameter(Guid.Parse(guid))
        except Exception:
            return ""
        return self._pick([parameter])

    def _pick(self, parameters):
        for parameter in parameters or []:
            if parameter is None:
                continue
            if self.use_definition_name:
                return parameter.Definition.Name
            if not parameter.HasValue:
                continue
            from Autodesk.Revit.DB import StorageType

            if parameter.StorageType == StorageType.String:
                return parameter.AsString()
            value = parameter.AsValueString()
            if value is not None:
                return value
        return ""
```

`collect_target_views`, `compute_renames`, `preview_lines`, `rename_views`, `main`, `format_report` per the Interfaces block, with these pinned behaviors:

- `collect_target_views`: Revit imports inside the function; selected non-view elements go to `skipped["not_view"]`; views collected from selection set `used_selection=True`; when no selected view exists, iterate `patterns` keys and collect each class with `FilteredElementCollector(doc).OfClass(getattr(DB, class_name))`; templates go to `skipped["template"]`; views whose `type(view).__name__` is not in `patterns` go to `skipped["no_pattern"]`.
- `compute_renames`: skip views whose class is not in `patterns`; new name = `pattern.apply_pattern(patterns[class_name], resolver_factory(view))`.
- `preview_lines`: `"{} -> {}".format(view.Name, new_name)`; if `len(renames) > limit`, append `"... and {} more".format(len(renames) - limit)`.
- `rename_views`: skip when `view.Name == new_name` (report as renamed but unchanged); on `duplicate_exception`, try `"{} {}".format(new_name, i)` for i in 1..1000, stop on success; if all attempts fail, add to `failed` and continue with the next view; catch any `Exception` per view → `failed`, batch continues.
- `main`: `selected_ids = list(uidoc.Selection.GetElementIds())`; `scope = "selected views" if used_selection else "views in the project"`; call `confirm(renames, scope)` before opening the transaction; on cancel return `None`; call `rename_views(renames, duplicate_exception=ArgumentException)` (import inside `main`) inside `with revit.Transaction("ViewRename")`; return the report dict with keys `scope`, `cancelled`, `renamed`, `failed`, `skipped`.
- `format_report`: header `ViewRename: renamed N view(s) (scope: ...)`, one `old -> new` line per rename, `Failed:` lines, then `Skipped (no pattern): ...`, `Skipped (template): ...`, `Skipped (not a view): ...` sections for non-empty lists only.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/viewrename -q`
Expected: all tests pass.

- [ ] **Step 5: Format and commit**

```bash
ruff format pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/lib/viewrename/apply.py tests/viewrename/test_apply.py
git add pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/lib/viewrename/apply.py tests/viewrename/test_apply.py
git commit -m "ViewRename: Add rename flow module"
```

---

### Task 5: `lib/viewrename/storage.py` + remote smoke

**Files:**
- Create: `pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/lib/viewrename/storage.py`
- Create locally (throwaway, not committed): `/tmp/opencode/viewrename-probe/probe_storage.py`

**Interfaces:**
- Consumes: `codec` (Task 3); `viewrename.CLASS_NAMES` (Task 2).
- Produces:
  - `storage.SCHEMA_GUID = "62444aa5-69f7-4aa6-9b0e-238dd1309f83"`, `SCHEMA_NAME = "pyRevitMEP.ViewRename"`, `FIELD_NAME = "Patterns"`, `LEGACY_PARAM_NAME = "pyRevitMEP_viewrename_patterns"`
  - `storage.read_patterns(doc) -> dict` (ExtensibleStorage → legacy parameter → config)
  - `storage.read_legacy_parameter(doc) -> dict`
  - `storage.write_to_model(doc, patterns)` (own `revit.Transaction("ViewRename: save patterns")`)
  - `storage.read_from_config() -> dict`, `storage.write_to_config(patterns)`

- [ ] **Step 1: Implement `storage.py`**

Pinned details:

- `_get_schema(doc, create)`: `Schema.Lookup(Guid(SCHEMA_GUID))`; when `create` and missing, `SchemaBuilder(Guid(SCHEMA_GUID), SCHEMA_NAME)` with `set([Read,Write])AccessLevel(AccessLevel.Public)`, `AddSimpleField(FIELD_NAME, str)`, `Finish()`.
- `_read_entity(doc)`: missing schema / invalid entity → `""`; else `doc.ProjectInformation.GetEntity(schema).Get[str](FIELD_NAME)`.
- If `Entity.Set[str]` / `Get[str]` syntax from Task 1 differs, use the syntax validated by the probe.
- `read_from_config`: `script.get_config()`, values via `getattr(config, name, "")` for `CLASS_NAMES`, `codec.normalize_config_value`, drop empties.
- `write_to_config`: set every `CLASS_NAMES` attribute (empty string clears), then `script.save_config()`.
- All Revit/pyRevit imports inside functions (module must import without Revit so tests keep running).

- [ ] **Step 2: Sync and smoke-test on the remote**

Copy the bundle, then run the smoke against the R24 and R25 scratch copies:

```bash
cd /home/cyril/git/pyRevitMEP
tar czf - --exclude=.git --exclude=__pycache__ --exclude=.idea . \
  | ssh -p 2222 Marie@127.0.0.1 "tar xzf - -C C:/Users/Marie/AppData/Roaming/pyRevit/Extensions/PyRevitMEP.extension"
```

`/tmp/opencode/viewrename-probe/probe_storage.py` (throwaway; imports the bundle lib explicitly so it works even without bundle context):

```python
#! python3
import sys
from os.path import dirname

sys.path.insert(0, dirname(__file__))
sys.path.insert(0, dirname(__file__) + r"\lib")

from pyrevit import revit, script
from viewrename import storage

doc = revit.doc
patterns = {"ViewPlan": "VR_name(Level)", "View3D": "name(Sous-catégorie)_3D"}
storage.write_to_model(doc, patterns)
assert storage.read_patterns(doc) == patterns, storage.read_patterns(doc)
storage.write_to_config(patterns)
assert storage.read_from_config() == patterns, storage.read_from_config()
output = script.get_output()
output.print("STORAGE-SMOKE-OK")
```

Sync it into the bundle, run, then delete it remotely:

```bash
scp -P 2222 /tmp/opencode/viewrename-probe/probe_storage.py 'Marie@127.0.0.1:C:/Users/Marie/AppData/Roaming/pyRevit/Extensions/PyRevitMEP.extension/pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/_probe_storage.py'
ssh -p 2222 Marie@127.0.0.1 'C:\Users\Marie\AppData\Roaming\pyRevit-Master\bin\pyrevit.exe run "C:\Users\Marie\AppData\Roaming\pyRevit\Extensions\PyRevitMEP.extension\pyRevitMEP.tab\Manage.panel\ViewRename.pushbutton\_probe_storage.py" --revit=2024 --models="C:\Users\Marie\AppData\Local\Temp\viewrename-test\scratch_r24.rvt"'
```

Repeat for `--revit=2025` / `scratch_r25.rvt`; expected `STORAGE-SMOKE-OK` both times. Then:

```bash
ssh -p 2222 Marie@127.0.0.1 'del /q "C:\Users\Marie\AppData\Roaming\pyRevit\Extensions\PyRevitMEP.extension\pyRevitMEP.tab\Manage.panel\ViewRename.pushbutton\_probe_storage.py"'
```

- [ ] **Step 3: Commit**

```bash
ruff format pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/lib/viewrename/storage.py
git add pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/lib/viewrename/storage.py
git commit -m "ViewRename: Add ExtensibleStorage and config storage"
```

---

### Task 6: `lib/viewrename/ui.py` + `config.py` editor

**Files:**
- Create: `pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/lib/viewrename/ui.py`
- Create: `pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/config.py`
- Create locally (throwaway, not committed): `/tmp/opencode/viewrename-probe/probe_ui.py`

**Interfaces:**
- Consumes: `storage.read_patterns` (Task 5), `pattern.apply_pattern`/`validate_pattern` (Task 2), `viewrename.CLASS_NAMES`.
- Produces: `ui.show_editor(doc) -> (action, patterns)` with `action` in `("model", "config", None)`, `ui.DEFAULT_PATTERNS` (old hardcoded patterns for the three original classes), and `ui.run_smoke(doc)` (dev-aid that opens the editor, auto-closes it, and prints `UI-SMOKE-OK`).

- [ ] **Step 1: Implement `ui.py`**

Pinned behaviors:

- WinForms imports at module top (`System.Windows.Forms`, `System.Drawing`); no `pyrevit.forms`.
- `show_editor(doc)` builds a fixed-dialog `Form` titled `ViewRename patterns`, `StartPosition.CenterScreen`, `TopMost = True`, one `TabPage` per `CLASS_NAMES`. Structure it as a `PatternEditor` class (`__init__(doc)`, `collect_patterns()`) plus module-level `show_editor(doc)` and `run_smoke(doc)`.
- Each tab: pattern `TextBox`; primary preview label (resolved name); secondary preview label (definition names); parameter `ListView` (`View.Details`, columns `Name`, `Built-in`, `GUID`); `Insert at cursor` button (`textBox.SelectedText = reference`); a note label when the class has no sample view (controls disabled).
- Sample view: first non-template `FilteredElementCollector(doc).OfClass(getattr(DB, class_name))`.
- Parameter reference rules: shared → `Guid('<GUID>')`; non-INVALID built-in → `bip(<NAME>)`; else `name(<Definition.Name>)`.
- Previews recompute on `TextChanged`; use `pattern.validate_pattern` and show errors in a red label.
- Pre-fill a class only when no stored pattern exists for it, using `DEFAULT_PATTERNS`.
- Buttons `Save to model` and `Save to config` set `self._action` and close the form; `Close` sets `None`. If a pattern is invalid, show a `MessageBox` and do not close.
- Collect patterns from text boxes on save (empty → omitted).
- No Revit transactions inside the dialog; only API reads.
- `config.py`:

```python
#! python3
from pyrevit import revit
from viewrename import storage, ui

doc = revit.doc
if doc is None:
    from Autodesk.Revit.UI import TaskDialog

    TaskDialog.Show("ViewRename", "Open a document first.")
else:
    action, patterns = ui.show_editor(doc)
    if action == "model":
        storage.write_to_model(doc, patterns)
    elif action == "config":
        storage.write_to_config(patterns)
```

`DEFAULT_PATTERNS` (spec: suggestions only):

```python
DEFAULT_PATTERNS = {
    "ViewPlan": "name(ORG_Métier)_name(ORG_Métier_Sous_catégorie)_PE_bip(PLAN_VIEW_LEVEL)_bip(VIEWER_VOLUME_OF_INTEREST_CROP)",
    "View3D": "name(ORG_Métier)_name(ORG_Métier_Sous_catégorie)_3D",
    "ViewSection": "name(ORG_Métier)_name(ORG_Métier_Sous_catégorie)_CP",
}
```

- [ ] **Step 2: Remote smoke — window builds, controls populate, closes cleanly**

`/tmp/opencode/viewrename-probe/probe_ui.py` (throwaway; explicit lib path like Task 5):

```python
#! python3
import sys
from os.path import dirname

sys.path.insert(0, dirname(__file__))
sys.path.insert(0, dirname(__file__) + r"\lib")

from pyrevit import revit, script
from viewrename import ui

doc = revit.doc
ui.run_smoke(doc)  # helper in ui.py: builds the editor, asserts tabs/controls, closes via Timer, prints "UI-SMOKE-OK"
```

Add to `ui.py` a small `run_smoke(doc)` helper (dev aid, harmless in production): builds the editor, `Timer` closes it after 1200 ms, prints `UI-SMOKE-OK`. Sync `probe_ui.py` into the bundle, run on 2024 and 2025 with `--allowdialogs` (same commands as Task 5, plus the flag), delete afterwards. Expected `UI-SMOKE-OK`.

- [ ] **Step 3: Interactive manual check (user)**

Ask the user to open the scratch model in Revit 2024 and Shift+Click the button. Checklist to report back: tabs present; parameter list populated; insert at cursor works; previews update; invalid syntax is refused; `Save to model` and `Save to config` both persist (verify by reopening the editor).

- [ ] **Step 4: Format and commit**

```bash
ruff format pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/lib/viewrename/ui.py pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/config.py
git add pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/lib/viewrename/ui.py pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/config.py
git commit -m "ViewRename: Add WinForms pattern editor"
```

---

### Task 7: `script.py` apply entry, bundle wiring, remote integration tests

**Files:**
- Modify: `pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/script.py` (full rewrite)
- Modify: `pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/bundle.yaml`
- Delete: `pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/ViewRename.xaml`
- Create locally (throwaway, not committed): `/tmp/opencode/viewrename-probe/probe_int.py`

**Interfaces:**
- Consumes: `storage.read_patterns`/`write_to_model` (Task 5), `apply.main`/`format_report`/`preview_lines` (Task 4).
- Produces: the shipped entry point.

- [ ] **Step 1: Rewrite `script.py`**

Pinned flow: guard `revit.doc is None`; `patterns = storage.read_patterns(doc)`; if empty, `TaskDialog` explaining Shift+Click and stop; `confirm(renames, scope)` builds a `TaskDialog` (`MainInstruction` `Rename N view(s)?`, `MainContent` with scope + `apply.preview_lines`, `CommandLink1` = `Rename`, `CommonButtons.Cancel`); `report = apply.main(...)`; cancelled → `output.print("ViewRename: cancelled.")`; else `output.print(apply.format_report(report))`. First line `#! python3`; no inline `__doc__`/`__title__`/`__author__`.

- [ ] **Step 2: Update `bundle.yaml` and delete the XAML**

- Remove `engine: persistent: true`.
- Tooltips (fr/en) mention `SHIFT-CLIC`/`SHIFT-CLICK` for patterns; keep title/help_url/author.
- `git rm pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/ViewRename.xaml`.

- [ ] **Step 3: Write the integration probe**

`/tmp/opencode/viewrename-probe/probe_int.py` (throwaway) runs inside the bundle context. It must:

1. Import `from System.Collections.Generic import List`, `from Autodesk.Revit.DB import ElementId`, and `from viewrename import apply, storage`.
2. Seed patterns: `storage.write_to_model(doc, {"ViewPlan": "ZZVR_name(Level)"})`.
3. **All scope**: clear selection (`uidoc.Selection.SetElementIds(List[ElementId]())`), run `apply.main(doc, uidoc, patterns, confirm=lambda renames, scope: True)`; assert every non-template `ViewPlan` name starts with `ZZVR_`, `View3D` names unchanged, and `skipped["no_pattern"]` is non-empty.
4. **Selected scope**: select one `ViewPlan` (`uidoc.Selection.SetElementIds(List[ElementId]([view_id]))`), run again; assert only that view's name changed.
5. **Conflicts**: pick two plans, set patterns so both resolve to the same name, run; assert the second got a ` 1` suffix and `failed` is empty.
6. **Templates**: assert no template view appears in `renamed`.
7. Print `INT-SCOPE-OK`, `INT-SELECTED-OK`, `INT-CONFLICT-OK`, `INT-TEMPLATE-OK`, `INTEGRATION-OK`.

Sync the bundle, sync the probe into the bundle, run on 2024 and 2025, delete the probe afterwards. Do not save the scratch models.

- [ ] **Step 4: Run the apply entry point end-to-end (user + agent)**

Run `script.py` itself via `pyrevit run --allowdialogs` on the scratch models (TaskDialog appears; requires the user to click Rename). Confirm the output report and the names afterwards with a read-only probe. Then ask the user to run the button normally in Revit 2024 and 2025 and confirm the dialog/report UX.

- [ ] **Step 5: Format and commit**

```bash
ruff format pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/script.py pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/config.py
git add pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/script.py pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton/bundle.yaml
git commit -m "ViewRename: Run on CPython with editor on Shift+Click"
```

---

### Task 8: Final verification pass

**Files:**
- Verify: all files above.
- Maybe modify: notes in the spec if a fallback was taken.

- [ ] **Step 1: Full local checks**

Run: `python3 -m pytest tests/viewrename -q` and `ruff format --check` + `ruff check` on all touched Python files. Expected: tests pass, no format diffs.

- [ ] **Step 2: Manual verification matrix on Revit 2024 + 2025 (ask the user where interaction is needed)**

From the spec: no patterns configured; patterns from ExtensibleStorage / legacy parameter / config; selection with views, with only non-views, empty; conflicts; missing parameters; templates excluded; editor save/load; migration of a legacy model. Record results in chat; fix any failures before declaring done.

- [ ] **Step 3: Update spec and commit if needed**

If a probe fallback was chosen or behavior differed, update `docs/superpowers/specs/2026-10-01-viewrename-cpython-design.md` accordingly, then:

```bash
git add -A pyRevitMEP.tab/Manage.panel/ViewRename.pushbutton docs/superpowers/specs/2026-10-01-viewrename-cpython-design.md tests/viewrename
git commit -m "ViewRename: Finalize CPython migration"
```
