# coding: utf8
from Autodesk.Revit.DB import Reference, ReferenceArray, XYZ, Line, Options, FamilyInstance, Point, \
    FamilyInstanceReferenceType, Edge
from Autodesk.Revit import Exceptions
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter

from pyrevit import script, forms

import rpw
from rpw import revit

__doc__ = """"
Quick dimension selected elements
Warning : Full support for line base elements only (eg. pipes, walls, lines, grids). 
Don't currently fully work with family instance.
"""
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


class CurveLineFilter(ISelectionFilter):
    def AllowElement(self, elem):
        try:
            if isinstance(elem.Location.Curve, Line):
                return True
            else:
                return False
        except AttributeError:
            return False

    def AllowReference(self, reference, position):
        try:
            if isinstance(doc.GetElement(reference).Location.Curve, Line):
                return True
            else:
                return False
        except AttributeError:
            return False


if not selection:
    try:
        selection = [doc.GetElement(reference) for reference in uidoc.Selection.PickObjects(
            ObjectType.Element, CustomFilter(), "Pick")]
    except Exceptions.OperationCanceledException:
        import sys
        sys.exit()

# All reference in reference will be dimensioned
reference_array = ReferenceArray()

options = Options(ComputeReferences=True, IncludeNonVisibleObjects=True)


def family_origin_reference(family_instance):
    family_origin = family_instance.Location.Point
    for geom in family_instance.get_Geometry(options):
        if isinstance(geom, Point) and geom.Coord == family_origin:
            return geom.Reference
    else:
        try:
            for type in FamilyInstanceReferenceType.GetValues(FamilyInstanceReferenceType):
                for reference in family_instance.GetReferences(type):
                    return reference
                    geom = family_instance.GetGeometryObjectFromReference(reference)
                    if isinstance(geom, Point) and geom.Coord == family_instance.Location.Point:
                        return reference

                    if isinstance(geom, Edge):
                        curve = geom.AsCurve()
                        if (
                                isinstance(curve, Line) and
                                curve.Direction.CrossProduct(direction).IsZeroLength()
                        ):
                            logger.debug("{} {}".format(geom.Origin, geom.Direction))
                            return reference
        except NameError:
            raise
            logger.info("Some part of the function (FamilyInstanceReferenceType) is only available from Revit 2018")


def get_reference(element):
    if isinstance(element, FamilyInstance):
        return family_origin_reference(element)
    else:
        try:
            el_curve = element.Location.Curve
        except AttributeError:
            el_curve = element.Curve
        if el_curve.Direction.CrossProduct(direction).IsAlmostEqualTo(XYZ()):
            return Reference(element)
        else:
            for geom in element.get_Geometry(options):
                for edge in geom.Edges:
                    curve = edge.AsCurve()
                    if isinstance(curve, Line):
                        el_origin = el_curve.Origin
                        ed_origin = curve.Origin
                        if (el_origin.X, el_origin.Y) == (ed_origin.X, ed_origin.Y):
                            if curve.GetEndPoint(0) - pt1 < curve.GetEndPoint(1) - pt1:
                                return edge.GetEndPointReference(0)
                            else:
                                return edge.GetEndPointReference(1)


for element in selection:
    try:
        direction = element.Location.Curve.Direction
        break
    except AttributeError:
        continue
else:
    with forms.WarningBar(title="Unable to find a lead direction. Please pick a parallel line."):
        ref = uidoc.Selection.PickObject(ObjectType.Element, CurveLineFilter())
        direction = doc.GetElement(ref).Location.Curve.Direction

pt1 = uidoc.Selection.PickPoint()  # type: XYZ
pt2 = pt1 + XYZ(-direction.Y, direction.X, 0)
line = Line.CreateBound(pt1,pt2)

for element in selection:
    reference_array.Append(get_reference(element))

with rpw.db.Transaction("QuickDimensionPipe"):
    logger.debug([reference for reference in reference_array])
    dim = doc.Create.NewDimension(doc.ActiveView, line, reference_array)
