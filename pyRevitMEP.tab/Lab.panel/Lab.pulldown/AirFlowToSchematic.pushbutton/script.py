# coding: utf8
import rpw
from pyrevit import script, forms
from pyrevit.forms import WPFWindow
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Document, BuiltInParameter

__title__ = "AirFlowToSchematic"
__author__ = "Cyril Waechter"
__doc__ = "Description"

doc = __revit__.ActiveUIDocument.Document  # type: Document

logger = script.get_logger()

def get_spaces_flows_by_appartement(doc):
    zones_dict = dict()
    for space in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_MEPSpaces):
        zone = space.LookupParameter("ARC_Cage d'escalier").AsString()
        number = space.LookupParameter("ARC_Appartement").AsString()
        fou = space.get_Parameter(
            BuiltInParameter.ROOM_ACTUAL_SUPPLY_AIRFLOW_PARAM
        ).AsDouble()
        rep = space.get_Parameter(
            BuiltInParameter.ROOM_ACTUAL_RETURN_AIRFLOW_PARAM
        ).AsDouble()
        zones_dict.setdefault(zone, dict()).setdefault(number, []).append((fou, rep))
    return zones_dict


def set_spaces_flows_by_appartement(doc, zone_dict):
    for space in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_MEPSpaces):
        zone = space.LookupParameter("ARC_Cage d'escalier").AsString()
        number = space.get_Parameter(BuiltInParameter.ROOM_NUMBER).AsString()
        try:
            fou = sum(room[0] for room in zone_dict[zone][number])
            rep = sum(room[1] for room in zone_dict[zone][number])
            space.get_Parameter(BuiltInParameter.ROOM_DESIGN_SUPPLY_AIRFLOW_PARAM).Set(
                fou
            )
            space.get_Parameter(BuiltInParameter.ROOM_BASE_RETURN_AIRFLOW_ON_PARAM).Set(0)
            space.get_Parameter(BuiltInParameter.ROOM_DESIGN_RETURN_AIRFLOW_PARAM).Set(
                rep
            )
        except KeyError:
            logger.info("{} {} not found in source document".format(zone, number))


class Room:
    def __init__(self, space):
        self.zone = space.LookupParameter("ARC_Cage d'escalier").AsString()
        self.number = space.LookupParameter("ARC_Appartement").AsString()
        self.fou = space.get_Parameter(
            BuiltInParameter.ROOM_ACTUAL_SUPPLY_AIRFLOW_PARAM
        ).AsDouble()
        self.rep = space.get_Parameter(
            BuiltInParameter.ROOM_ACTUAL_RETURN_AIRFLOW_PARAM
        ).AsDouble()
    

class DocSelection(WPFWindow):
    """
    GUI used to select pipe type to copy
    """

    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.source_docs.DataContext = rpw.revit.docs
        self.target_docs.DataContext = rpw.revit.docs

    # noinspection PyUnusedLocal
    def source_doc_selection_changed(self, sender, e):
        try:
            self.source_doc = self.source_docs.SelectedItem
            self.target_doc = self.target_docs.SelectedItem
        except:
            pass

    # noinspection PyUnusedLocal
    def button_copy_click(self, sender, e):
        self.Close()
        with rpw.db.Transaction("Copy flow to schematic", self.target_doc):
            zone_dict = get_spaces_flows_by_appartement(self.source_doc)
            set_spaces_flows_by_appartement(self.target_doc, zone_dict)



DocSelection('DocsSelection.xaml').ShowDialog()


