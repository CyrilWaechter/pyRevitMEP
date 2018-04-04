# coding: utf8
from math import pi
from Autodesk.Revit.DB import Line, XYZ, InsulationLiningBase
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
from Autodesk.Revit import Exceptions
from pyrevit.script import get_logger
import rpw

__doc__ = """Connect an object to an other.
Select first object to connect (pick a location close to the desired connector)
Select second object to be connected (pick a location close to the desired connector)"""
__title__ = "ConnectTo"
__author__ = "Cyril Waechter"


logger = get_logger()
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


class NoInsulation(ISelectionFilter):
    def AllowElement(self, elem):
        if isinstance(elem, InsulationLiningBase):
            return False
        else:
            return True

    def AllowReference(self, reference, position):
        return True


# Prompt user to select elements and points to connect
try:
    reference = uidoc.Selection.PickObject(ObjectType.Element, NoInsulation(), "Pick element to move")
    moved_element = doc.GetElement(reference)
    moved_point = reference.GlobalPoint
    reference = uidoc.Selection.PickObject(ObjectType.Element, NoInsulation(), "Pick element to be connected to")
    target_element = doc.GetElement(reference)
    target_point = reference.GlobalPoint
except Exceptions.OperationCanceledException:
    import sys
    sys.exit()


# Get associated unused connectors
moved_connector = get_connector_closest_to(get_connector_manager(moved_element).UnusedConnectors,
                                           moved_point)
target_connector = get_connector_closest_to(get_connector_manager(target_element).UnusedConnectors,
                                            target_point)

# Retrieves connectors direction and catch attribute error like when there is no unused connector available
try:
    moved_direction = moved_connector.CoordinateSystem.BasisZ
    target_direction = target_connector.CoordinateSystem.BasisZ
except AttributeError:
    rpw.ui.forms.Alert("It looks like one of the objects have no unused connector", header="AttributeError")
    import sys
    sys.exit()

# Move and connect
with rpw.db.Transaction("Connect elements"):
    # If connector direction is same, rotate it
    angle = moved_direction.AngleTo(target_direction)
    if angle != pi:
        if angle == 0:
            vector = moved_connector.CoordinateSystem.BasisY
        else:
            vector = moved_direction.CrossProduct(target_direction)
        try:
            line = Line.CreateBound(moved_point, moved_point+vector)
            moved_element.Location.Rotate(line, angle - pi)
        except Exceptions.ArgumentsInconsistentException:
            logger.debug("Vector : {} ; Angle : {}".format(vector, angle))
    # Move element in order match connector position
    moved_element.Location.Move(target_connector.Origin - moved_connector.Origin)
    # Connect connectors
    moved_connector.ConnectTo(target_connector)
