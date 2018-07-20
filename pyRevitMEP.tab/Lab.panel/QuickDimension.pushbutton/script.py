# coding: utf8
from Autodesk.Revit.DB import Reference, ReferenceArray, XYZ, Line, Options, FamilyInstance, Point, \
    FamilyInstanceReferenceType
from Autodesk.Revit import Exceptions
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter

from pyrevit import script

import rpw
from rpw import revit

__doc__ = "Quick dimension selected elements"
__title__ = "QuickDimension"
__author__ = "Cyril Waechter"

doc = revit.doc
uidoc = revit.uidoc
logger = script.get_logger()

selection = [doc.GetElement(id) for id in uidoc.Selection.GetElementIds()]


class CustomFilter(ISelectionFilter):
    def AllowElement(self, elem):
        return True

    def AllowReference(self, reference, position):
        return True


if not selection:
    uidoc.Selection.PickObjects(ObjectType.Edge, CustomFilter(), "Pick")

reference_array = ReferenceArray()

options = Options(ComputeReferences=True, IncludeNonVisibleObjects=True)


def family_origin_reference(family_instance):
    for geom in family_instance.get_Geometry(options):
        if isinstance(geom, Point) and geom.Coord == family_instance.Location.Point:
            return geom.Reference
    else:
        try:
            for type in FamilyInstanceReferenceType.GetValues(FamilyInstanceReferenceType):
                reference = family_instance.GetReferences(type)
                return reference
        except NameError:
            logger.info("Some part of the function (FamilyInstanceReferenceType) is only available from Revit 2018")


for element in selection:
    if isinstance(element, FamilyInstance):
        reference = family_origin_reference(element)
    else:
        reference = Reference(element)
    logger.debug(reference)
    reference_array.Append(reference)

pt1 = uidoc.Selection.PickPoint()
pt2 = pt1 + XYZ.BasisX
line = Line.CreateBound(pt1,pt2)

with rpw.db.Transaction("QuickDimensionPipe"):
    logger.debug([reference for reference in reference_array])
    dim = doc.Create.NewDimension(doc.ActiveView, line, reference_array)
