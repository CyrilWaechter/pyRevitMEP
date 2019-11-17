# coding: utf8
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Transaction,
    Document,
    BuiltInParameter,
)

import rpw
from pyrevit import script, forms

__title__ = "AirFlowTerminalToSpace"
__author__ = "Cyril Waechter"
__doc__ = "Copy actual air flow (total terminals air flow) to Space design flow"

doc = __revit__.ActiveUIDocument.Document  # type: Document

logger = script.get_logger()


def create_terminal_space_dict():
    d = dict()
    for air_terminal in FilteredElementCollector(doc).OfCategory(
        BuiltInCategory.OST_DuctTerminal
    ):
        space = doc.GetSpaceAtPoint(air_terminal.Location.Point)
        if space:
            d.setdefault(space, []).append(air_terminal)
        else:
            logger.info("{} is not in any space".format(air_terminal.Id))

    return d


def space_to_air_terminals():
    for space, air_terminals in create_terminal_space_dict():
        flow = space.get_Parameter(
            BuiltInParameter.ROOM_DESIGN_SUPPLY_AIRFLOW_PARAM
        ).AsDouble()
        quantity = len(air_terminals)
        for air_terminal in air_terminals:
            air_terminal.get_Parameter(BuiltInParameter.RBS_DUCT_FLOW_PARAM).Set(
                flow / quantity
            )


def air_terminals_to_space():
    with rpw.db.Transaction(doc=doc, name="Store AirTerminals flow to Spaces"):
        for space in FilteredElementCollector(doc).OfCategory(
            BuiltInCategory.OST_MEPSpaces
        ):
            fou = space.get_Parameter(
                BuiltInParameter.ROOM_ACTUAL_SUPPLY_AIRFLOW_PARAM
            ).AsDouble()
            rep = space.get_Parameter(
                BuiltInParameter.ROOM_ACTUAL_RETURN_AIRFLOW_PARAM
            ).AsDouble()

            space.get_Parameter(BuiltInParameter.ROOM_DESIGN_SUPPLY_AIRFLOW_PARAM).Set(
                fou
            )
            space.get_Parameter(BuiltInParameter.ROOM_BASE_RETURN_AIRFLOW_ON_PARAM).Set(0)
            space.get_Parameter(BuiltInParameter.ROOM_DESIGN_RETURN_AIRFLOW_PARAM).Set(
                rep
            )

if __name__ == "__main__":
    air_terminals_to_space()
