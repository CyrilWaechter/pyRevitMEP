"""Rename flow: scope selection, name computation, conflict handling, reporting.

Imports of Revit/pyRevit stay inside functions so the pure parts are unit-tested
locally with fakes.
"""

from . import pattern


class ViewResolver(pattern.Resolver):
    """Resolves pattern references against one view's parameters."""

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
        except Exception:  # noqa: BLE001 - Guid.Parse and get_Parameter raise various types
            return ""
        return self._pick([parameter])

    def _pick(self, parameters):
        from Autodesk.Revit.DB import StorageType

        for parameter in parameters or []:
            if parameter is None:
                continue
            if self.use_definition_name:
                return parameter.Definition.Name
            if not parameter.HasValue:
                continue
            if parameter.StorageType == StorageType.String:
                return parameter.AsString()
            value = parameter.AsValueString()
            if value is not None:
                return value
        return ""


def collect_target_views(doc, patterns, selected_ids):
    """Return (views, skipped, used_selection).

    skipped maps "no_pattern" / "not_view" / "template" to lists of names or ids.
    """
    from Autodesk.Revit import DB

    skipped = {"no_pattern": [], "not_view": [], "template": []}
    candidates = []
    used_selection = False
    for element_id in selected_ids:
        element = doc.GetElement(element_id)
        if element is None:
            continue
        if not isinstance(element, DB.View):
            skipped["not_view"].append(str(element_id))
            continue
        candidates.append(element)
        used_selection = True
    if not candidates:
        for class_name in patterns:
            view_class = getattr(DB, class_name, None)
            if view_class is None:
                continue
            candidates.extend(DB.FilteredElementCollector(doc).OfClass(view_class))

    views = []
    for view in candidates:
        if view.IsTemplate:
            skipped["template"].append(view.Name)
            continue
        if not patterns.get(type(view).__name__):
            skipped["no_pattern"].append(view.Name)
            continue
        views.append(view)
    return views, skipped, used_selection


def compute_renames(views, patterns, resolver_factory=None):
    if resolver_factory is None:
        resolver_factory = ViewResolver
    renames = []
    for view in views:
        current = patterns.get(type(view).__name__)
        if not current:
            continue
        renames.append((view, pattern.apply_pattern(current, resolver_factory(view))))
    return renames


def preview_lines(renames, limit=10):
    lines = [f"{view.Name} -> {new_name}" for view, new_name in renames[:limit]]
    if len(renames) > limit:
        lines.append(f"... and {len(renames) - limit} more")
    return lines


FORBIDDEN_NAME_CHARS = frozenset('\\:{}[]|;<>?`"*')


def _invalid_name_reason(new_name):
    if not new_name.strip():
        return "pattern resolved to an empty name"
    bad = sorted(FORBIDDEN_NAME_CHARS.intersection(new_name))
    if bad:
        return "name contains invalid characters: {}".format(" ".join(bad))
    return None


def rename_views(views_and_names, duplicate_exception):
    """Rename views; must be called inside an open transaction."""
    renamed, failed = [], []
    for view, new_name in views_and_names:
        old_name = view.Name
        if old_name == new_name:
            renamed.append((old_name, new_name))
            continue
        reason = _invalid_name_reason(new_name)
        if reason:
            failed.append((old_name, reason))
            continue
        final, error = None, None
        try:
            view.Name = new_name
            final = new_name
        except duplicate_exception:
            for index in range(1, 1001):
                try:
                    candidate = f"{new_name} {index}"
                    view.Name = candidate
                    final = candidate
                    break
                except duplicate_exception:
                    continue
            else:
                error = f"no unique name found for {new_name}"
        except Exception as exc:  # noqa: BLE001 - one bad view must not abort the batch
            error = str(exc)
        if final is not None:
            renamed.append((old_name, final))
        else:
            failed.append((old_name, error or "unknown error"))
    return renamed, failed


def main(doc, uidoc, patterns, confirm):
    """Run the whole flow; return a report dict, or None when the user cancels."""
    from Autodesk.Revit.Exceptions import ArgumentException
    from pyrevit import revit

    selected_ids = list(uidoc.Selection.GetElementIds())
    views, skipped, used_selection = collect_target_views(doc, patterns, selected_ids)
    renames = compute_renames(views, patterns)
    scope = "selected views" if used_selection else "views in the project"
    if not confirm(renames, scope):
        return None
    with revit.Transaction("ViewRename", doc):
        renamed, failed = rename_views(renames, duplicate_exception=ArgumentException)
    return {
        "scope": scope,
        "cancelled": False,
        "renamed": renamed,
        "failed": failed,
        "skipped": skipped,
    }


def format_report(report):
    lines = [f"ViewRename: renamed {len(report['renamed'])} view(s) (scope: {report.get('scope')})"]
    lines += [f"{old} -> {new}" for old, new in report["renamed"]]
    if report["failed"]:
        lines.append("Failed:")
        lines += [f"{old} -> {error}" for old, error in report["failed"]]
    for key, label in (
        ("no_pattern", "Skipped (no pattern)"),
        ("template", "Skipped (template)"),
        ("not_view", "Skipped (not a view)"),
    ):
        items = report["skipped"].get(key) or []
        if items:
            lines.append(f"{label}: {', '.join(str(item) for item in items)}")
    return "\n".join(lines)
