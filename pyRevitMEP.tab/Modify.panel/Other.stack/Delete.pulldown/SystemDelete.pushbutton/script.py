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
from pyrevit import revit
from Autodesk.Revit.DB import Element, ElementId
from System.Collections.Generic import List

doc = revit.doc
uidoc = revit.uidoc


__doc__ = "Delete MEP system of selected objects"
__title__ = "System delete"
__author__ = "Cyril Waechter"
__context__ = "Selection"

# Find systems id and delete it
system_list = List[ElementId]()
for element_id in uidoc.Selection.GetElementIds():
    el = doc.GetElement(element_id)
    try:
        system_list.Add(el.MEPSystem.Id)
    except AttributeError:
        try:
            connectors = el.MEPModel.ConnectorManager.Connectors
            for connector in connectors:
                if connector.MEPSystem is not None:
                    elid = Element.Id.GetValue(connector.MEPSystem)
                    system_list.Add(elid)
        except AttributeError:
            pass

with revit.Transaction("delete selected objects system"):
    doc.Delete(system_list)
