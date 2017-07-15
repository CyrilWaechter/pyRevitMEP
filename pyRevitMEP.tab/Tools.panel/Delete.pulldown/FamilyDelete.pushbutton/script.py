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
from Autodesk.Revit.DB import Transaction, FamilySymbol

__doc__ = "Delete selected families from project"
__title__ = "Family delete"
__author__ = "Cyril Waechter"

t = Transaction(doc, "Delete families from project")
t.Start()

try:
    # Find families of selected object and delete it
    for el in selection.elements:
        family_id = el.Symbol.Family.Id
        doc.Delete(family_id)

except:  # print a stack trace and error messages for debugging
    import traceback
    traceback.print_exc()
    t.RollBack()

else:
    t.Commit()
