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

from revitutils import doc, selection

# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import Element, Transaction, MEPModel, ConnectorManager, MEPSystem

__doc__ = "Delete MEP system of selected objects"
__title__ = "System delete"
__author__ = "Cyril Waechter"

# Find systems id and delete it
s = []
for el in selection.elements:
    try:
        s.append(el.MEPSystem.Id)
    except AttributeError:
        try:
            connectors = el.MEPModel.ConnectorManager.Connectors
            for connector in connectors:
                if connector.MEPSystem is not None:
                    elid = Element.Id.GetValue(connector.MEPSystem)
                    s.append(elid)
        except AttributeError:
            pass

t = Transaction(doc, "delete selected objects system")
t.Start()
for elid in s:
    doc.Delete(elid)
t.Commit()
