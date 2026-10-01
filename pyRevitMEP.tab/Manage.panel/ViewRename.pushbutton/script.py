#! python3
"""Rename selected views according to a pattern. Shift+Click to edit patterns."""

from Autodesk.Revit.UI import (
    TaskDialog,
    TaskDialogCommandLinkId,
    TaskDialogCommonButtons,
    TaskDialogResult,
)
from pyrevit import revit, script
from viewrename import apply, storage

doc = revit.doc
uidoc = revit.uidoc
output = script.get_output()


def confirm(renames, scope, using_defaults=False):
    dialog = TaskDialog("ViewRename")
    dialog.MainInstruction = f"Rename {len(renames)} view(s)?"
    content = f"Scope: {scope}\n\n" + "\n".join(apply.preview_lines(renames))
    if using_defaults:
        content = "Using built-in default patterns.\n\n" + content
    dialog.MainContent = content
    dialog.AddCommandLink(TaskDialogCommandLinkId.CommandLink1, "Rename")
    dialog.CommonButtons = TaskDialogCommonButtons.Cancel
    return dialog.Show() == TaskDialogResult.CommandLink1


if doc is None:
    TaskDialog.Show("ViewRename", "Open a document first.")
else:
    patterns, source = storage.read_patterns_with_source(doc)
    if not patterns:
        TaskDialog.Show(
            "ViewRename",
            "No rename pattern configured.\nShift+Click this button to edit patterns.",
        )
    else:
        using_defaults = source == "defaults"
        report = apply.main(doc, uidoc, patterns, lambda renames, scope: confirm(renames, scope, using_defaults))
        if report is not None:
            output.print_code(apply.format_report(report))
