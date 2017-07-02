"""
Copyright (c) 2017 Cyril Waechter
Python scripts for Autodesk Revit

This file is part of pyRevitMEP repository at https://github.com/CyrilWaechter/pyRevitMEP

pyRevitMEP is an extension for pyRevit. It contain free set of scripts for Autodesk Revit:
you can redistribute it and/or modify it under the terms of the GNU General Public License
version 3, as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

See this link for a copy of the GNU General Public License protecting this package.
https://github.com/CyrilWaechter/pyRevitMEP/blob/master/LICENSE
"""

# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import Transaction, BuiltInParameter, Element, Level, MEPCurve, ElementId, FamilyInstance\
    , FilteredElementCollector
from scriptutils.userinput import WPFWindow
from revitutils import doc, selection

__doc__ = "Change selected elements level without moving it"
__title__ = "Change Level"
__author__ = "Cyril Waechter"

t = Transaction(doc, "Change reference level")


def get_level_from_object():
    """Ask user to select an object and retrieve its associated level"""
    try:
        ref_object = selection.utils.pick_element("Select reference object")
        if isinstance(ref_object, MEPCurve):
            level = ref_object.ReferenceLevel
        else:
            level = doc.GetElement(ref_object.LevelId)
        return level
    except:
        print("Unable to retrieve reference level from this object")


def change_level(ref_level):
    try:
        t.Start()

        # Change reference level and relative offset for each selected object in order to change reference plane without
        # moving the object
        for el in selection.elements:

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

        t.Commit()

    except:  # print a stack trace and error messages for debugging
        import traceback
        traceback.print_exc()
        t.RollBack()


class ReferenceLevelSelection(WPFWindow):
    """
    GUI used to select a reference level from a list or an object
    """

    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)

        levels_dict = {}
        self.levels_list = FilteredElementCollector(doc).OfClass(Level)
        self.combobox_levels.ItemsSource = self.levels_list

    def button_levelfromlist_click(self, sender, e):
        self.Close()
        level = self.combobox_levels.SelectedItem
        change_level(level)

    def button_levelfromrefobject_click(self, sender, e):
        self.Close()
        level = get_level_from_object()
        change_level(level)

ReferenceLevelSelection('ReferenceLevelSelection.xaml').ShowDialog()
