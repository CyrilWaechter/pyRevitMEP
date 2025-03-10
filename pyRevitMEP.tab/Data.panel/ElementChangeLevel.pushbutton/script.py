"""
Copyright (c) 2017 Cyril Waechter
Python scripts for Autodesk Revit

This file is part of pyrevitmep repository at https://github.com/CyrilWaechter/pyrevitmep

pyrevitmep is an extension for pyRevit. It contain free set of scripts for Autodesk Revit:
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
from Autodesk.Revit.DB import (
    BuiltInParameter,
    Level,
    MEPCurve,
    FamilyInstance,
    FilteredElementCollector,
    BuiltInCategory,
    Category,
    UV,
    StorageType,
)
from Autodesk.Revit.DB.Mechanical import Space
from pyrevit import revit
from pyrevit import script, HOST_APP
from pyrevit.forms import WPFWindow
from pyrevitmep.event import CustomizableEvent

doc = revit.doc
uidoc = revit.uidoc

logger = script.get_logger()

is_revit_2020_or_above = int(HOST_APP.version) >= 2020
logger.debug(is_revit_2020_or_above)


class Offset:
    def __init__(self):
        # Modified category for Revit 2020 and above. When you change level, object doesn't move. eg. fittings.
        to_offset = {
            BuiltInCategory.OST_DuctAccessory,
            BuiltInCategory.OST_DuctFitting,
            BuiltInCategory.OST_PipeAccessory,
            BuiltInCategory.OST_PipeFitting,
            BuiltInCategory.OST_CableTrayFitting,
            BuiltInCategory.OST_ConduitFitting,
            BuiltInCategory.OST_DuctTerminal,
            BuiltInCategory.OST_PlumbingFixtures,
            BuiltInCategory.OST_GenericModel,
            BuiltInCategory.OST_MechanicalEquipment,
        }
        no_offset_from_2020 = {
            BuiltInCategory.OST_DuctAccessory,
            BuiltInCategory.OST_DuctFitting,
            BuiltInCategory.OST_PipeAccessory,
            BuiltInCategory.OST_PipeFitting,
            BuiltInCategory.OST_CableTrayFitting,
            BuiltInCategory.OST_ConduitFitting,
        }
        if is_revit_2020_or_above:
            self.category_ids_to_offset = self.get_category_ids(to_offset.difference(no_offset_from_2020))
        else:
            self.category_ids_to_offset = self.get_category_ids(to_offset)
        logger.debug(self.category_ids_to_offset)

    def is_required(self, element):
        return element.Category.Id in self.category_ids_to_offset

    def get_category_ids(self, categories):
        return tuple(Category.GetCategory(doc, cat).Id for cat in categories)


def get_level_from_object():
    """Ask user to select an object and retrieve its associated level"""
    try:
        ref_object = revit.pick_element("Select reference object")
        if isinstance(ref_object, MEPCurve):
            level = ref_object.ReferenceLevel
        else:
            level = doc.GetElement(ref_object.LevelId)
        return level
    except:
        print("Unable to retrieve reference level from this object")


def get_param_value(param):
    if param.StorageType == StorageType.Double:
        return param.AsDouble()
    elif param.StorageType == StorageType.ElementId:
        return param.AsElementId()
    elif param.StorageType == StorageType.Integer:
        return param.AsInteger()
    elif param.StorageType == StorageType.String:
        return param.AsString()


def change_level(ref_level):
    with revit.Transaction("Change reference level", doc):
        # Change reference level and relative offset for each selected object in order to change reference plane without
        # moving the object
        selection_ids = uidoc.Selection.GetElementIds()

        offset = Offset()
        for id in selection_ids:
            el = doc.GetElement(id)
            # Change reference level of objects like ducts, pipes and cable trays
            if isinstance(el, MEPCurve):
                el.ReferenceLevel = ref_level

            # Change reference level of family objects like fittings, accessories, air terminal
            elif isinstance(el, FamilyInstance) and el.Host is None:
                el_level = doc.GetElement(el.LevelId)
                el_level_param = el.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM)
                if offset.is_required(el):
                    el_param_offset = el.get_Parameter(BuiltInParameter.INSTANCE_FREE_HOST_OFFSET_PARAM)
                    el_newoffset = el_param_offset.AsDouble() + el_level.Elevation - ref_level.Elevation
                    el_param_offset.Set(el_newoffset)
                el_level_param.Set(ref_level.Id)
            elif isinstance(el, Space):
                point = el.Location.Point
                newspace = doc.Create.NewSpace(ref_level, UV(point.X, point.Y))
                for param in el.Parameters:
                    if param.IsReadOnly:
                        continue
                    value = get_param_value(param)
                    if not value:
                        continue
                    newspace.LookupParameter(param.Definition.Name).Set(value)
                newspace.get_Parameter(BuiltInParameter.ROOM_UPPER_LEVEL).Set(ref_level.Id)
                upper_offset = newspace.get_Parameter(BuiltInParameter.ROOM_UPPER_OFFSET)
                if upper_offset.AsDouble() <= 0:
                    upper_offset.Set(1 / 0.3048)
                doc.Delete(el.Id)

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
    ReferenceLevelSelection("ReferenceLevelSelection.xaml").Show()
