# coding: utf8
from math import pi
from Autodesk.Revit.DB import Line, XYZ
from Autodesk.Revit.UI.Selection import ObjectType, ObjectSnapTypes
import rpw

uidoc = rpw.revit.uidoc
doc = rpw.revit.doc


def get_connector_manager(element):
    """Get element's connector manager"""
    try:
        return element.ConnectorManager
    except AttributeError:
        pass

    try:
        return element.MEPModel.ConnectorManager
    except AttributeError:
        raise AttributeError("Cannot find connector manager in given element")


def get_connector_closest_to(connectors, xyz):
    """Get connector from connector set iterable closest to an XYZ point"""
    min_distance = float("inf")
    closest_connector = None
    for connector in connectors:
        distance = connector.Origin.DistanceTo(xyz)
        if distance < min_distance:
            min_distance = distance
            closest_connector = connector
    return closest_connector


# Prompt user to select elements and points to connect
moved_element = doc.GetElement(
    uidoc.Selection.PickObject(ObjectType.Element, "Pick element to move"))
moved_point = uidoc.Selection.PickPoint(ObjectSnapTypes.Points, "Pick point to connect")
target_element = doc.GetElement(
    uidoc.Selection.PickObject(ObjectType.Element, "Pick element to be connected to"))
target_point = uidoc.Selection.PickPoint(ObjectSnapTypes.Points, "Pick point to be connected to")


# Get associated connectors
moved_connector = get_connector_closest_to(get_connector_manager(moved_element).UnusedConnectors,
                                           moved_point)
target_connector = get_connector_closest_to(get_connector_manager(target_element).UnusedConnectors,
                                            target_point)

# Check
moved_direction = moved_connector.CoordinateSystem.BasisZ
target_direction = target_connector.CoordinateSystem.BasisZ


with rpw.db.Transaction("Connect elements"):
    # If connector direction is same, rotate it
    angle = moved_direction.AngleTo(target_direction)
    if angle != pi:
        cross_product = moved_direction.CrossProduct(target_direction)
        line = Line.CreateBound(moved_point, moved_point+cross_product)
        moved_element.Location.Rotate(line, angle - pi)
    # Move element in order match connector position
    moved_element.Location.Move(target_connector.Origin - moved_connector.Origin)
    # Connect connectors
    moved_connector.ConnectTo(target_connector)
