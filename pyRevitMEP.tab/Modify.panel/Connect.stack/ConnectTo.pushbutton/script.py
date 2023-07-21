# coding: utf8
from math import pi

from Autodesk.Revit.DB import Line, InsulationLiningBase
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
from Autodesk.Revit import Exceptions

from pyrevit import script, revit, forms
from pyrevitmep.meputils import get_connector_manager, get_connector_closest_to

__doc__ = """Connect an object to an other.
Select first object to connect (pick a location close to the desired connector)
Select second object to be connected (pick a location close to the desired connector)"""
__title__ = "ConnectTo"
__author__ = "Cyril Waechter"

logger = script.get_logger()
uidoc = revit.uidoc
doc = revit.doc


class NoInsulation(ISelectionFilter):
    def AllowElement(self, elem):
        if isinstance(elem, InsulationLiningBase):
            return False
        try:
            get_connector_manager(elem)
            return True
        except AttributeError:
            return False

    def AllowReference(self, reference, position):
        return True


def connect_to():
    # Prompt user to select elements and points to connect
    try:
        with forms.WarningBar(title="Pick element to move and connect"):
            reference = uidoc.Selection.PickObject(
                ObjectType.Element, NoInsulation(), "Pick element to move"
            )
    except Exceptions.OperationCanceledException:
        return False

    try:
        moved_element = doc.GetElement(reference)
        moved_point = reference.GlobalPoint
        with forms.WarningBar(title="Pick element to be connected to"):
            reference = uidoc.Selection.PickObject(
                ObjectType.Element, NoInsulation(), "Pick element to be connected to"
            )
        target_element = doc.GetElement(reference)
        target_point = reference.GlobalPoint
    except Exceptions.OperationCanceledException:
        return True
    except Exceptions.InvalidObjectException:
        with forms.WarningBar(title="Oops, it looks like you chose an invalid object"):
            import time

            time.sleep(2)

    # Check if user has selected same element twice to prevent errors and unintended movements
    if target_element.Id == moved_element.Id:
        forms.alert(
            msg="Oops, it looks like you've selected the same object twice.",
            title="Attribute Error",
        )
        return True

    # Get associated unused connectors
    moved_connector = get_connector_closest_to(
        get_connector_manager(moved_element).UnusedConnectors, moved_point
    )
    target_connector = get_connector_closest_to(
        get_connector_manager(target_element).UnusedConnectors, target_point
    )
    try:
        if moved_connector.Domain != target_connector.Domain:
            forms.alert(
                msg="You picked 2 connectors of different domain. Please retry.",
                title="Domain Error",
            )
            return True
    except AttributeError:
        forms.alert(
            msg="It looks like one of the objects have no unused connector",
            title="AttributeError",
        )
        return True

    # Retrieves connectors direction and catch attribute error like when there is no unused connector available
    try:
        moved_direction = moved_connector.CoordinateSystem.BasisZ
        target_direction = target_connector.CoordinateSystem.BasisZ
    except AttributeError:
        forms.alert(
            msg="It looks like one of the objects have no unused connector",
            title="AttributeError",
        )
        return True

    # Move and connect
    with revit.Transaction("Connect elements"):
        # If connector direction is same, rotate it
        angle = moved_direction.AngleTo(target_direction)
        if angle != pi:
            if angle == 0:
                vector = moved_connector.CoordinateSystem.BasisY
            else:
                vector = moved_direction.CrossProduct(target_direction)
            try:
                line = Line.CreateBound(moved_point, moved_point + vector)
                moved_element.Location.Rotate(line, angle - pi)
            # Revit don't like angle and distance too close to 0
            except Exceptions.ArgumentsInconsistentException:
                logger.debug("Vector : {} ; Angle : {}".format(vector, angle))
        # Move element in order match connector position
        moved_element.Location.Move(target_connector.Origin - moved_connector.Origin)
        # Connect connectors
        moved_connector.ConnectTo(target_connector)
    return True


while connect_to():
    pass
