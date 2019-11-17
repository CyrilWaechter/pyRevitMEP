"""
Copyright (c) 2017 Cyril Waechter
Python scripts for Autodesk Revit

This file is part of pypevitmep repository at https://github.com/CyrilWaechter/pypevitmep

pypevitmep is an extension for pyRevit. It contain free set of scripts for Autodesk Revit:
you can redistribute it and/or modify it under the terms of the GNU General Public License
version 3, as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

See this link for a copy of the GNU General Public License protecting this package.
https://github.com/CyrilWaechter/pypevitmep/blob/master/LICENSE
"""

# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import Transaction, BuiltInParameter, Element, Level, MEPCurve, ElementId, FamilyInstance\
    , FilteredElementCollector, BuiltInCategory, Category
from pyrevit import script, HOST_APP
from pyrevit.forms import WPFWindow, alert
import rpw
from rpw import revit
from pyrevitmep.event import CustomizableEvent

__doc__ = "Change selected elements level without moving it"
__title__ = "Change Level"
__author__ = "Cyril Waechter"
__persistentengine__ = True

doc = revit.doc
uidoc = revit.uidoc

logger = script.get_logger()

is_revit_2020 = int(HOST_APP.version) >= 2020
logger.debug(is_revit_2020)


def get_enhanced_ids():
    # Modified category for Revit 2020 and above. When you change level, object doesn't move. eg. fittings.
    enhanced_cat = (
        BuiltInCategory.OST_DuctAccessory,
        BuiltInCategory.OST_DuctFitting,
        BuiltInCategory.OST_PipeAccessory,
        BuiltInCategory.OST_PipeFitting,
        BuiltInCategory.OST_CableTrayFitting,
        BuiltInCategory.OST_ConduitFitting
    )
    return (Category.GetCategory(doc, cat).Id for cat in enhanced_cat)


enhanced_cat_ids = get_enhanced_ids()
logger.debug([cat_id for cat_id in enhanced_cat_ids])


def get_level_from_object():
    """Ask user to select an object and retrieve its associated level"""
    try:
        ref_id = rpw.ui.Pick.pick_element("Select reference object").ElementId
        ref_object = doc.GetElement(ref_id)
        if isinstance(ref_object, MEPCurve):
            level = ref_object.ReferenceLevel
        else:
            level = doc.GetElement(ref_object.LevelId)
        return level
    except:
        print("Unable to retrieve reference level from this object")


def change_level(ref_level):
    with rpw.db.Transaction("Change reference level"):
        # Change reference level and relative offset for each selected object in order to change reference plane without
        # moving the object
        selection_ids = uidoc.Selection.GetElementIds()

        for id in selection_ids:
            el = doc.GetElement(id)
            # Change reference level of objects like ducts, pipes and cable trays
            if isinstance(el, MEPCurve):
                el.ReferenceLevel = ref_level

            # Change reference level of objects like ducts, pipes and cable trays
            elif isinstance(el, FamilyInstance) and el.Host is None:
                el_level = doc.GetElement(el.LevelId)
                el_level_param = el.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM)
                logger.debug("Category is in enhanced categories ? {}".format(el.Category.Id in enhanced_cat_ids))
                if not(is_revit_2020 or el.Category.Id in enhanced_cat_ids):
                    el_param_offset = el.get_Parameter(BuiltInParameter.INSTANCE_FREE_HOST_OFFSET_PARAM)
                    el_newoffset = el_param_offset.AsDouble() + el_level.Elevation - ref_level.Elevation
                    el_param_offset.Set(el_newoffset)
                el_level_param.Set(ref_level.Id)

            # Ignore other objects
            else:
                logger.info("Warning. Following element was ignored. It is probably an hosted element.")
                logger.info(el)


customizable_event = CustomizableEvent()


class ReferenceLevelSelection(WPFWindow):
    """
    GUI used to select a reference level from a list or an object
    """

    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)

        self.levels = FilteredElementCollector(doc).OfClass(Level)
        self.combobox_levels.DataContext = self.levels

    # noinspection PyUnusedLocal
    def from_list_click(self, sender, e):
        level = self.combobox_levels.SelectedItem
        customizable_event.raise_event(change_level, level)

    # noinspection PyUnusedLocal
    def from_object_click(self, sender, e):
        selection = uidoc.Selection.GetElementIds()
        level = get_level_from_object()
        uidoc.Selection.SetElementIds(selection)
        customizable_event.raise_event(change_level, level)


if __forceddebugmode__:
    selection = uidoc.Selection.GetElementIds()
    level = get_level_from_object()
    uidoc.Selection.SetElementIds(selection)
    change_level(level)
else:
    ReferenceLevelSelection('ReferenceLevelSelection.xaml').Show()
