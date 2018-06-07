# coding: utf8
from Autodesk.Revit.DB import ElementTransformUtils, Line, UnitType, UnitUtils, ElementId, ViewSection, XYZ, \
    FilteredElementCollector, Grid, ReferencePlane, FamilyInstance
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
from Autodesk.Revit import Exceptions

import rpw
from pyrevit import forms, script

uidoc = rpw.revit.uidoc
doc = rpw.revit.doc
logger = script.get_logger()

def element_selection():
    try:
        with forms.WarningBar(title="Pick element to move and connect"):
            reference = uidoc.Selection.PickObject(ObjectType.Element, "Pick element to move")
    except Exceptions.OperationCanceledException:
        return False

    try:
        element1 = doc.GetElement(reference)
        with forms.WarningBar(title="Pick reference element"):
            reference = uidoc.Selection.PickObject(ObjectType.Element, "Pick target element")
        element2 = doc.GetElement(reference)

        logger.debug("ELEMENTS \n 1: {} \n 2: {}".format(element1, element2))

        angle = direction(element1).AngleTo(direction(element2))
        axis = Line.CreateBound(origin(element2), origin(element2) + XYZ.BasisZ)
        with rpw.db.Transaction("Make parallel", doc):
            element2.Location.Rotate(axis, angle)

        return True
    except Exceptions.OperationCanceledException:
        return True


def section_direction(element):
    # type: (ViewSection) -> XYZ
    for view in FilteredElementCollector(doc).OfClass(ViewSection):  # type: ViewSection
        if view.Name == element.Name:
            return view.RightDirection
    else:
        raise AttributeError


def grid_direction(element):
    # type: (Grid) -> XYZ
    return element.Curve.Direction


def plane_direction(element):
    # type: (ReferencePlane) -> XYZ
    return element.Direction


def line_direction(element):
    return element.Location.Curve.Direction


def family_direction(element):
    # type: (FamilyInstance) -> XYZ
    return element.FacingOrientation


def direction(element):
    direction_funcs = (grid_direction, plane_direction, family_direction, line_direction, section_direction)

    for func in direction_funcs:
        try:
            return func(element)
        except AttributeError:
            pass
    else:
        logger.debug("DIRECTION : type {}".format(type(element)))


def section_origin(element):
    # type: (ViewSection) -> XYZ
    for view in FilteredElementCollector(doc).OfClass(ViewSection):  # type: ViewSection
        if view.Name == element.Name:
            return view.Origin
    else:
        raise AttributeError


def grid_origin(element):
    # type: (Grid) -> XYZ
    return element.Curve.Origin


def plane_origin(element):
    # type: (ReferencePlane) -> XYZ
    return element.GetPlane().Origin


def line_origin(element):
    return element.Location.Curve.Origin


def family_origin(element):
    # type: (FamilyInstance) -> XYZ
    return element.GetTransform().Origin


def origin(element):
    origin_funcs = (grid_origin, plane_origin, family_origin, line_origin, section_origin)

    for func in origin_funcs:
        try:
            return func(element)
        except AttributeError:
            continue
    else:
        logger.debug("ORIGIN : type {}".format(type(element)))


while element_selection():
    pass
