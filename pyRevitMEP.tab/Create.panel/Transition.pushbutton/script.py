# coding: utf8

from Autodesk.Revit import Exceptions
from Autodesk.Revit.DB import InsulationLiningBase, Document, FamilyInstance
from Autodesk.Revit.UI.Selection import ISelectionFilter, ObjectType

from pyrevit import script, forms, revit
from pyrevitmep.meputils import get_connector_closest_to, get_connector_manager

__doc__ = """Create a MEP transition between 2 open ends.
Select first object (pick a location close to the desired connector)
Select second object (pick a location close to the desired connector)"""
__title__ = "Transition"
__author__ = "Cyril Waechter"

logger = script.get_logger()
uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document  # type: Document


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


class NoInsulationNoFamilyInstance(ISelectionFilter):
    def AllowElement(self, elem):
        if isinstance(elem, InsulationLiningBase) or isinstance(elem, FamilyInstance):
            return False
        try:
            get_connector_manager(elem)
            return True
        except AttributeError:
            return False

    def AllowReference(self, reference, position):
        return True


def new_transition():
    # Prompt user to select elements and points to connect
    try:
        message = "Pick element 1 (the connector moves depending on transition length)"
        with forms.WarningBar(title=message):
            reference = uidoc.Selection.PickObject(
                ObjectType.Element, NoInsulationNoFamilyInstance(), message
            )
    except Exceptions.OperationCanceledException:
        return False

    try:
        element1 = doc.GetElement(reference)
        xyz1 = reference.GlobalPoint

        message = "Pick element 2 (static)"
        with forms.WarningBar(title=message):
            reference = uidoc.Selection.PickObject(
                ObjectType.Element, NoInsulation(), message
            )
        element2 = doc.GetElement(reference)
        xyz2 = reference.GlobalPoint
    except Exceptions.OperationCanceledException:
        return True

    # Get associated unused connectors
    connector1 = get_connector_closest_to(
        get_connector_manager(element1).UnusedConnectors, xyz1
    )
    connector2 = get_connector_closest_to(
        get_connector_manager(element2).UnusedConnectors, xyz2
    )

    try:
        if connector1.Domain != connector2.Domain:
            forms.alert(
                "You picked 2 connectors of different domain. Please retry.",
                title="Domain Error",
            )
            return True
    except AttributeError:
        forms.alert(
            "It looks like one of the objects have no unused connector",
            title="AttributeError",
        )
        return True

    if not connector1 and not connector2:
        forms.alert(
            "It looks like one of the objects have no unused connector",
            title="AttributeError",
        )
        return True

    with revit.Transaction("Create transition"):
        try:
            doc.Create.NewTransitionFitting(connector1, connector2)
        except Exceptions.InvalidOperationException:
            cmd_link1_msg = "Show exemple image"
            result = forms.alert(
                "Unable to connect.",
                sub_msg="Make sure you click near connectors you want to make a transition between.",
                options=[cmd_link1_msg]
            )
            if result == cmd_link1_msg:
                import os; os.startfile(os.path.join(__commandpath__, "WhereToClick.png"))
    return True


while new_transition():
    pass
