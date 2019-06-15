# coding: utf8
from System.Collections.Generic import List
from Autodesk.Revit.DB import Document, Categories, BuiltInCategory, Category, GraphicsStyleType, Color, \
    FilteredElementCollector, LinePatternElement, LinePattern, ElementId, LinePatternSegment, LinePatternSegmentType, \
    Element
from Autodesk.Revit.DB.Plumbing import PipingSystemType
from Autodesk.Revit.DB.Mechanical import MechanicalSystemType
from Autodesk.Revit import Exceptions
from pyrevit import script
import rpw

# __doc__ = "TODO: "
# __title__ = "TODO: "
__author__ = "Cyril Waechter"
# __context__ = "selection"

doc = __revit__.ActiveUIDocument.Document  # type: Document
uidoc = __revit__.ActiveUIDocument  # type: UIDocument

logger = script.get_logger()

categories = doc.Settings.Categories  # type: Categories
line_category = categories.__getitem__(BuiltInCategory.OST_Lines)  # type: Category
plain_line_pattern_id = ElementId(-3000010)


def create_line_pattern():
    # type: () -> LinePatternElement
    """Create a line pattern not configurable at the moment"""
    line_pattern = LinePattern("Default")
    segment_list = List[LinePatternSegment]()
    segment_list.Add(LinePatternSegment(LinePatternSegmentType.Dash, 1))
    segment_list.Add(LinePatternSegment(LinePatternSegmentType.Space, 1))
    line_pattern.SetSegments(segment_list)
    return LinePatternElement.Create(doc, line_pattern)


def new_line_style(name="NewLine", pattern_id=plain_line_pattern_id, color=None, weight=1):
    # type: (str, ElementId, Color, int) -> Category
    """Create a new line style which is actually a new subcategory of OST_Lines

    """
    line = categories.NewSubcategory(line_category, name)  # type: Category

    if not color:
        color = Color(0, 0, 0)
    line.LineColor = color

    line.SetLinePatternId(pattern_id, GraphicsStyleType.Projection)

    line.SetLineWeight(weight, GraphicsStyleType.Projection)

    return line


def create_system_type_lines(system_type):
    for system in FilteredElementCollector(doc).OfClass(system_type):  # type: PipingSystemType
        color = system.LineColor
        pattern_id = system.LinePatternId
        abbreviation = system.Abbreviation
        name = Element.Name.__get__(system)
        weight = system.LineWeight
        if weight == -1:
            weight = system.Category.GetLineWeight(GraphicsStyleType.Projection)


        try:
            new_line_style(name, pattern_id, color, weight)
        except Exceptions.ArgumentException:
            existing_cat = line_category.SubCategories[name]  # type: Category
            existing_cat.LineColor = color
            existing_cat.SetLinePatternId(ElementId)
            existing_cat.SetLineWeight(weight)


with rpw.db.Transaction("Create line style for each piping system type"):
    create_system_type_lines(PipingSystemType)

with rpw.db.Transaction("Create line style for each ventilation system type"):
    create_system_type_lines(MechanicalSystemType)
