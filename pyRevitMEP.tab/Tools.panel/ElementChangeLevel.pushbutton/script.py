"""
Copyright (c) 2017 Cyril Waechter
Python scripts for Autodesk Revit

This file is part of pyRevitMEP repository at https://github.com/Nahouhak/pyRevitMEP

pyRevitMEP is an extension for pyRevit. It contain free set of scripts for Autodesk Revit:
you can redistribute it and/or modify it under the terms of the GNU General Public License
version 3, as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

See this link for a copy of the GNU General Public License protecting this package.
https://github.com/Nahouhak/pyRevitMEP/blob/master/LICENSE
"""

# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import Transaction, BuiltInParameter, Element, Level, MEPCurve, ElementId, FamilyInstance

from revitutils import doc, selection

__doc__ = "Change selected elements level without moving it"
__title__ = "Change Level"
__author__ = "Cyril Waechter"

t = Transaction(doc, "Change reference level")

try:
    # Retrieve needed information from reference object
    ref_object = selection.utils.pick_element("Select reference object")
    ref_level = ref_object.ReferenceLevel

    t.Start()

    # Change reference level and relative offset for each selected object in order to change reference plane without
    # moving the object
    for el in selection.elements:

        # Change reference level of objects like ducts, pipes and cable trays
        if el is MEPCurve:
            el.ReferenceLevel = ref_level

        # Change reference level of objects like ducts, pipes and cable trays
        elif el is FamilyInstance and el.Host is None:
            el_level = doc.GetElement(el.LevelId)
            el_level_param = el.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM)
            el_param_offset = el.get_Parameter(BuiltInParameter.INSTANCE_FREE_HOST_OFFSET_PARAM)
            el_newoffset = el_param_offset.AsDouble() + el_level.Elevation - ref_level.Elevation
            el_param_offset.Set(el_newoffset)
            el_level_param.Set(ref_level.Id)
        # Ignore other objects
        else:
            continue

    t.Commit()

except:  # print a stack trace and error messages for debugging
    import traceback
    traceback.print_exc()
    t.RollBack()
