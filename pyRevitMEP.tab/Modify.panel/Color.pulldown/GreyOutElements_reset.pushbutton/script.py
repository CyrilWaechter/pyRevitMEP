from Autodesk.Revit.DB import (
    OverrideGraphicSettings,
)
from pyrevit import revit

doc = __revit__.ActiveUIDocument.Document

ogs = OverrideGraphicSettings()

with revit.Transaction("Grey out elements"):
    for element in revit.get_selection():
        doc.ActiveView.SetElementOverrides(element.Id, ogs)
