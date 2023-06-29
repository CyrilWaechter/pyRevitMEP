# coding: utf8
from pyrevit import script, revit
from pyrevitmep.meputils import NoConnectorManagerError, get_connector_manager

__doc__ = """Disconnect all connector of an element"""
__title__ = "Disconnect"
__author__ = "Cyril Waechter"

logger = script.get_logger()
doc = revit.doc
output = script.get_output()


def disconnect_all_connectors(el):
    for connector in get_connector_manager(el).Connectors:
        if not connector.IsConnected:
            continue
        for other_connector in connector.AllRefs:
            if other_connector == connector:
                continue
            connector.DisconnectFrom(other_connector)
        system = connector.MEPSystem
        if not system or not system.IsMultipleNetwork:
            continue
        connector.MEPSystem.DivideSystem(doc)


def disconnect():
    with revit.Transaction("Disconnect elements", doc):
        for el in revit.get_selection():
            try:
                disconnect_all_connectors(el)
            except NoConnectorManagerError:
                print(
                    "No connector manager found for {}: {}".format(
                        el.Category.Name, output.linkify(el.Id)
                    )
                )


disconnect()
