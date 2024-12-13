from Autodesk.Revit.DB import (
    OverrideGraphicSettings,
    Color,
    ElementId,
    FilteredElementCollector,
    FillPatternElement,
)
from pyrevit import revit

doc = __revit__.ActiveUIDocument.Document

ogs = OverrideGraphicSettings()
color = Color(192, 192, 192)
ogs.SetProjectionLineColor(color)

def get_solid_fill_pattern_id(doc):
    for pattern in FilteredElementCollector(doc).OfClass(FillPatternElement):
        if pattern.GetFillPattern().IsSolidFill:
            return pattern.Id

pattern_id = get_solid_fill_pattern_id(doc)

ogs.SetSurfaceForegroundPatternColor(color)
ogs.SetSurfaceForegroundPatternId(pattern_id)


with revit.Transaction("Grey out elements"):
    for element in revit.get_selection():
        doc.ActiveView.SetElementOverrides(element.Id, ogs)