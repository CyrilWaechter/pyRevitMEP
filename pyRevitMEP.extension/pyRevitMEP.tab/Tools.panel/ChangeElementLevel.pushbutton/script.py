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

__doc__ = "Change selected elements level without moving it"
__title__ = "Change Level"
__author__ = "Cyril Waechter"

__window__.Hide()

from Autodesk.Revit.DB import *

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

#Ask user to pick an object which has the desired reference level
def pickobject():
    from Autodesk.Revit.UI.Selection import ObjectType
    __window__.Hide()
    picked = uidoc.Selection.PickObject(ObjectType.Element, "Sélectionnez la référence")
    __window__.Show()
    return picked

#Retrieve needed information from reference object
ref_object = doc.GetElement(pickobject().ElementId)
ref_level = ref_object.ReferenceLevel 
ref_levelid = ref_level.Id

t = Transaction(doc, "Change reference level")

t.Start()

#Change reference level and relative offset for each selected object in order to change reference plane without moving the object
for e in selection:
	object = doc.GetElement(e)
	object_param_level = object.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM)
	object_Level = doc.GetElement(object_param_level.AsElementId())
	object_param_offset = object.get_Parameter(BuiltInParameter.INSTANCE_FREE_HOST_OFFSET_PARAM)
	object_newoffset = object_param_offset.AsDouble() + object_Level.Elevation - ref_level.Elevation
	object_param_level.Set(ref_levelid)
	object_param_offset.Set(object_newoffset)
	
t.Commit()