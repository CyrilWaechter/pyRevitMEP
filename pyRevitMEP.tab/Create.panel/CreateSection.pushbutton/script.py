# coding: utf8

__doc__ = """Create sections from selected linear objects (eg. walls)
SHIFT-CLICK to display options"""
__title__ = "CreateSectionFrom"
__author__ = "Cyril Waechter"
__context__ = "selection"


from Autodesk.Revit.DB import (
    Document,
    Line,
    FilteredElementCollector,
    ViewFamilyType,
    ViewFamily,
    Element,
    ViewSection,
    Transform,
    BoundingBoxXYZ,
    XYZ,
    BuiltInParameter,
)
from Autodesk.Revit.UI import UIDocument
from Autodesk.Revit import Exceptions

from pyrevit import script, forms, revit

uidoc = revit.uidoc  # type: UIDocument
doc = revit.doc  # type: Document
logger = script.get_logger()

section_types = {
    Element.Name.__get__(vt): vt
    for vt in FilteredElementCollector(doc).OfClass(ViewFamilyType)
    if vt.ViewFamily == ViewFamily.Section
}

section_type = section_types.get(
    forms.ask_for_one_item(
        section_types.keys(),
        section_types.keys()[0],
        prompt="Select view section type to use for generated sections",
        title="Select section type",
    )
)


# Retrieve parameters from config file
_config = script.get_config()
prefix = _config.get_option("prefix", "Mur")
depth_offset = float(_config.get_option("depth_offset", "1"))
height_offset = float(_config.get_option("height_offset", "1"))
width_offset = float(_config.get_option("width_offset", "1"))

sections = []

for element_id in uidoc.Selection.GetElementIds():
    element = doc.GetElement(element_id)  # type: Element

    # Determine if element can be used to create a section
    try:
        curve = element.Location.Curve
        if not isinstance(curve, Line):
            raise AttributeError
    except AttributeError:
        logger.info("{} has no Line Curve to guide section creation".format(element))
        continue

    # Create a BoundingBoxXYZ oriented parallel to the element
    curve_transform = curve.ComputeDerivatives(0.5, True)

    origin = curve_transform.Origin
    wall_direction = curve_transform.BasisX.Normalize()  # type: XYZ
    up = XYZ.BasisZ
    section_direction = wall_direction.CrossProduct(up)
    right = up.CrossProduct(section_direction)

    transform = Transform.Identity
    transform.Origin = origin
    transform.BasisX = wall_direction
    transform.BasisY = up
    transform.BasisZ = section_direction

    section_box = BoundingBoxXYZ()
    section_box.Transform = transform

    # Try to retrieve element height, width and lenght
    try:
        el_depth = element.WallType.Width
    except AttributeError:
        el_depth = 2

    el_width = curve.Length

    el_bounding_box = element.get_BoundingBox(None)
    z_min = el_bounding_box.Min.Z
    z_max = el_bounding_box.Max.Z
    el_height = z_max - z_min

    # Get Wall Offset Params if Element is Wall
    try:
        base_offset = element.Parameter[BuiltInParameter.WALL_BASE_OFFSET].AsDouble()
    except AttributeError:
        base_offset = 0

    # Set BoundingBoxXYZ's boundaries
    section_box.Min = XYZ(
        -el_width / 2 - width_offset,
        -height_offset + base_offset,
        -el_depth / 2 - depth_offset,
    )
    section_box.Max = XYZ(
        el_width / 2 + width_offset,
        el_height + height_offset + base_offset,
        el_depth / 2 + depth_offset,
    )

    # Append necessary parameters to create sections in a list
    suffix_param = element.get_Parameter(BuiltInParameter.DOOR_NUMBER)
    sections.append(
        {
            "box": section_box,
            "suffix": suffix_param.AsString() if suffix_param.HasValue else None,
        }
    )

with revit.Transaction("Create sections", doc):
    fallback_suffix = 1
    for section in sections:
        section_view = ViewSection.CreateSection(doc, section_type.Id, section["box"])
        base_suffix = section["suffix"]
        if base_suffix:
            try:
                section_view.Name = "{} {}".format(prefix, base_suffix)
            except Exceptions.ArgumentException:
                print(
                    "Failed to rename view {}. Desired name already exist.".format(
                        section_view.Name
                    )
                )
        else:
            while fallback_suffix < 10000:
                try:
                    section_view.Name = "{} {}".format(prefix, fallback_suffix)
                except Exceptions.ArgumentException:
                    fallback_suffix += 1
                    continue
                break
