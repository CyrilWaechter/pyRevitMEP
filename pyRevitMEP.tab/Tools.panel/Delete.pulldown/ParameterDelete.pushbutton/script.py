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

from revitutils import doc

# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import Transaction, FilteredElementCollector, ParameterElement

__doc__ = "Delete project parameters including hidden ones"
__title__ = "Project Parameter delete"
__author__ = "Cyril Waechter"

#Retrieve all parameters in the document
params = FilteredElementCollector(doc).OfClass(ParameterElement)
filteredparams = []

#Store parameters which has a name starting with "magi" or "MC"
for param in params:
    if param.Name.startswith(("magi", "MC")): #startswith method accept tuple
        filteredparams.append(param)
        print param.Name

#Delete all parameters in the list
t = Transaction(doc, "Delete parameters")
t.Start()
for param in filteredparams:
    doc.Delete(param.Id)
t.Commit()

