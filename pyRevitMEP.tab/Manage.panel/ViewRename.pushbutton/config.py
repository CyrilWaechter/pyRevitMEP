#! python3
"""ViewRename pattern editor (Shift+Click). Saves patterns to the model or to pyRevit config."""

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
