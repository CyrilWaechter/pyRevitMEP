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

from Autodesk.Revit.UI import TaskDialog

TaskDialog.Show("This is the title","Welcome to your first dialog!")

from Autodesk.Revit.DB import Transaction

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

t = Transaction(doc, 'convert text')
t.Start()

for elId in uidoc.Selection.GetElementIds():
    el = doc.GetElement(elId)
    el.Text = el.Text.lower()

t.Commit()