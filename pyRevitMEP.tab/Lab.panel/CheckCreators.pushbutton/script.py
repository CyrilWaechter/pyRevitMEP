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
from Autodesk.Revit.DB import WorksharingUtils, FilteredElementCollector
from revitutils import doc

elem_list = ""
# FilteredElementCollector(doc).WhereElementIsNotElementType() is a way to retrieve all elements in doc
for elem in FilteredElementCollector(doc).WhereElementIsNotElementType():
    elem_creator = WorksharingUtils.GetWorksharingTooltipInfo(doc, elem.Id).Creator
    try:
        name = elem.Name
    except:
        name = ""
    elem_list = elem_list + "{:20},{:20},{:20}\n".format(str(elem.Id), name, elem_creator)

print(elem_list)