# coding: utf8
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Transaction,
    Document,
    BuiltInParameter,
    Category,
    Connector,
)
from Autodesk.Revit.DB.Mechanical import DuctFlowConfigurationType

import rpw
from pyrevit import script, forms

__title__ = "AirFlowSpaceToAirTerminal"
__author__ = "Cyril Waechter"
__doc__ = "Copy actual air flow (total terminals air flow) to Space design flow"

doc = __revit__.ActiveUIDocument.Document  # type: Document
uidoc = __revit__.ActiveUIDocument  # type: UIDocument

logger = script.get_logger()


def create_terminal_space_dict():
    selection = get_terminals_in_selection()
    if not selection:
        selection = FilteredElementCollector(doc).OfCategory(
            BuiltInCategory.OST_DuctTerminal
        )

    d = dict()
    for air_terminal in selection:
        connector = [c for c in air_terminal.MEPModel.ConnectorManager.Connectors][0]  # type: Connector
        if connector.AssignedDuctFlowConfiguration != DuctFlowConfigurationType.Preset:
            continue
        space = doc.GetSpaceAtPoint(air_terminal.Location.Point)
        system_type = air_terminal.get_Parameter(
            BuiltInParameter.RBS_SYSTEM_CLASSIFICATION_PARAM
        ).AsString()
        if space:
            d.setdefault(space.Id, dict()).setdefault(system_type, []).append(
                air_terminal
            )
        else:
            logger.info("{} is not in any space".format(air_terminal.Id))

    logger.debug(d)

    return d


def get_terminals_in_selection():
    terminals = []
    terminal_cat_id = Category.GetCategory(doc, BuiltInCategory.OST_DuctTerminal).Id
    for id in uidoc.Selection.GetElementIds():
        element = doc.GetElement(id)
        if element.Category.Id == terminal_cat_id:
            terminals.append(element)
    return terminals


def space_to_air_terminals():
    with rpw.db.Transaction(doc=doc, name="Store Spaces flow to AirTerminals"):
        for space_id, system_types in create_terminal_space_dict().items():
            space = doc.GetElement(space_id)
            fou = space.get_Parameter(
                BuiltInParameter.ROOM_DESIGN_SUPPLY_AIRFLOW_PARAM
            ).AsDouble()
            rep = space.get_Parameter(
                BuiltInParameter.ROOM_DESIGN_RETURN_AIRFLOW_PARAM
            ).AsDouble()

            try:
                fou_terminals = system_types["Soufflage"]
                set_terminals_flow(fou_terminals, fou)
            except KeyError:
                pass
            try:
                rep_terminals = system_types["Reprise"]
                set_terminals_flow(rep_terminals, rep)
            except KeyError:
                pass


def set_terminals_flow(air_terminals, total_flow):
    quantity = len(air_terminals)
    for air_terminal in air_terminals:
        for air_terminal in air_terminals:
            air_terminal.get_Parameter(BuiltInParameter.RBS_DUCT_FLOW_PARAM).Set(
                total_flow / quantity
            )


if __name__ == "__main__":
    space_to_air_terminals()
