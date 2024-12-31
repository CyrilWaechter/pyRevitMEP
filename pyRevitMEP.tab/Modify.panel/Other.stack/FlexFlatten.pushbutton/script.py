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

from System.Collections.Generic import List
from Autodesk.Revit.DB import XYZ
from pyrevit import revit

with revit.Transaction("Aplanize flex objects"):
    for flex_el in revit.get_selection():
        # Make tangents planar
        for tangent_name in ["StartTangent", "EndTangent"]:
            old_tangent = getattr(flex_el, tangent_name)
            setattr(flex_el, tangent_name, XYZ(old_tangent.X, old_tangent.Y, 0))

        # Make a new List of XYZ with same Z as first point
        new_points = List[XYZ]()
        for xyz in list(flex_el.Points)[:-1]:
            try:
                new_z
            except NameError:
                new_z = xyz.Z
            new_points.Add(XYZ(xyz.X, xyz.Y, new_z))
        new_points.Add(list(flex_el.Points)[-1])
        flex_el.Points = new_points
