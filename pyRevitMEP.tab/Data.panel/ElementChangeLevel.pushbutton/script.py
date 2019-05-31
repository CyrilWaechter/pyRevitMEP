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
    , FilteredElementCollector
from pyrevit.forms import WPFWindow
import rpw
from rpw import revit
from pyrevitmep.event import CustomizableEvent

__doc__ = "Change selected elements level without moving it"
__title__ = "Change Level"
__author__ = "Cyril Waechter"

doc = revit.doc
uidoc = revit.uidoc


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
                el_param_offset = el.get_Parameter(BuiltInParameter.INSTANCE_FREE_HOST_OFFSET_PARAM)
                el_newoffset = el_param_offset.AsDouble() + el_level.Elevation - ref_level.Elevation
                el_param_offset.Set(el_newoffset)
                el_level_param.Set(ref_level.Id)
            # Ignore other objects
            else:
                print "Warning. Following element was ignored. It is probably an hosted element."
                print el


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


ReferenceLevelSelection('ReferenceLevelSelection.xaml').Show()
