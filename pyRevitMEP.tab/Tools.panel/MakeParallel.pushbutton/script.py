# coding: utf8
from math import pi, acos

from Autodesk.Revit.DB import ElementTransformUtils, Line, UnitType, UnitUtils, ElementId, ViewSection, XYZ, \
    FilteredElementCollector, Grid, ReferencePlane, FamilyInstance
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
from Autodesk.Revit import Exceptions

import rpw
from pyrevit import forms, script

__doc__ = """Make 2 elements parallel. First element selected is reference. Second element selected rotate."""
__title__ = "Make Parallel (XY)"
__author__ = "Cyril Waechter"

uidoc = rpw.revit.uidoc
doc = rpw.revit.doc
logger = script.get_logger()


def element_selection():
    try:
        with forms.WarningBar(title="Pick reference element"):
            reference = uidoc.Selection.PickObject(ObjectType.Element, "Pick reference element")
    except Exceptions.OperationCanceledException:
        return False

    try:
        element1 = doc.GetElement(reference)
        with forms.WarningBar(title="Pick target element"):
            reference = uidoc.Selection.PickObject(ObjectType.Element, "Pick target element")
        element2 = doc.GetElement(reference)

        logger.debug("ELEMENTS \n 1: {} \n 2: {}".format(element1, element2))

        v1 = direction(element1)
        v2 = direction(element2)

        xy_v1 = XYZ(v1.X, v1.Y, 0)  # type: XYZ
        xy_v2 = XYZ(v2.X, v2.Y, 0)  # type: XYZ

        angle = xy_v2.AngleTo(xy_v1)
        if angle > pi/2:
            angle = angle - pi
        normal = xy_v2.CrossProduct(xy_v1)

        logger.debug("ANGLE : {}".format(angle))
        logger.debug("NORMAL : {}".format(normal))
        logger.debug("DIRECTION \n 1: {} \n 2: {}".format(direction(element1), direction(element2)))

        axis = Line.CreateBound(origin(element2), origin(element2) + normal)
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
