# coding=utf-8
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

from revitutils import doc, uidoc, selection
from math import pi

# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import Transaction, ElementTransformUtils, Line, XYZ, Location

__doc__ = "Rotate object in any direction"
__title__ = "3D Rotate"
__author__ = "Cyril Waechter"

getselection = uidoc.Selection.GetElementIds

try:
    t = Transaction(doc, "Rotation axe x")
    t.Start()
    # Look for selected family origin and rotate it around x axis
    for elid in selection.element_ids:
        o = doc.GetElement(elid).Location.Point
        z = XYZ(o.X + 1, o.Y, o.Z)
        axis = Line.CreateBound(o, z)
        ElementTransformUtils.RotateElement(doc, elid, axis, pi / 2)
    t.Commit()
except:
    raise
