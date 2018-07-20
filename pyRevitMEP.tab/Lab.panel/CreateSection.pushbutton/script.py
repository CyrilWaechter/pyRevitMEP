# coding: utf8

__doc__ = "Quick dimension selected elements"
__title__ = "QuickDimension"
__author__ = "Cyril Waechter"

from Autodesk.Revit.DB import Wall, Document, Line, FilteredElementCollector, ViewFamilyType, ViewFamily, Element, \
    ViewSection, Transform, BoundingBoxXYZ, XYZ, BuiltInParameter
from Autodesk.Revit.UI import UIDocument
from Autodesk.Revit import Exceptions

from pyrevit import script, forms
import rpw

uidoc = rpw.revit.uidoc  # type: UIDocument
doc = rpw.revit.doc  # type: Document
logger = script.get_logger()


section_type = forms.SelectFromList.show(
    [vt for vt in FilteredElementCollector(doc).OfClass(ViewFamilyType) if vt.ViewFamily == ViewFamily.Section],
    "Select view type to create section"
)[0]
width_offset = 1
height_offset = 1
lenght_offset = 1

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
        el_width =  element.WallType.Width
    except AttributeError:
        el_width = 2

    el_length = curve.Length

    el_bounding_box = element.get_BoundingBox(None)
    z_min = el_bounding_box.Min.Z
    z_max = el_bounding_box.Max.Z
    el_height = z_max - z_min

    # Set BoundingBoxXYZ's boundaries
    section_box.Min = XYZ(-el_length / 2 - lenght_offset,
                          -height_offset,
                          -el_width / 2 - width_offset)
    section_box.Max = XYZ(el_length / 2 + lenght_offset,
                          el_height + height_offset,
                          el_width / 2 + width_offset)

    # Append necessary parameters to create sections in a list
    sections.append({"box": section_box,
                     "suffix": element.get_Parameter(BuiltInParameter.DOOR_NUMBER).AsString()
                     })

with rpw.db.Transaction("Create sections", doc):
    for section in sections:
        section_view = ViewSection.CreateSection(doc, section_type.Id, section["box"])
        try:
            section_view.Name = "Mur {}".format(section["suffix"])
        except Exceptions.ArgumentException:
            logger.info("Failed to rename view {}. Desired name already exist.".format(section_view.Name))