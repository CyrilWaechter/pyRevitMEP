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


def confirm(renames, scope):
    dialog = TaskDialog("ViewRename")
    dialog.MainInstruction = f"Rename {len(renames)} view(s)?"
    dialog.MainContent = f"Scope: {scope}\n\n" + "\n".join(apply.preview_lines(renames))
    dialog.AddCommandLink(TaskDialogCommandLinkId.CommandLink1, "Rename")
    dialog.CommonButtons = TaskDialogCommonButtons.Cancel
    return dialog.Show() == TaskDialogResult.CommandLink1


if doc is None:
    TaskDialog.Show("ViewRename", "Open a document first.")
else:
    patterns = storage.read_patterns(doc)
    if not patterns:
        TaskDialog.Show(
            "ViewRename",
            "No rename pattern configured.\nShift+Click this button to edit patterns.",
        )
    else:
        report = apply.main(doc, uidoc, patterns, confirm)
        if report is None:
            output.print("ViewRename: cancelled.")
        else:
            output.print(apply.format_report(report))
