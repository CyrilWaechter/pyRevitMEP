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

import rpw
# noinspection PyUnresolvedReferences
from System.Collections.Generic import List

__doc__ = "Flatten selected flexible pipe/duct"
__title__ = "Flatten flex pipe/duct"
__author__ = "Cyril Waechter"
__context__ = "Selection"

XYZ = rpw.DB.XYZ
selection = rpw.ui.Selection()

with rpw.db.Transaction('Aplanize flex objects'):
    for flex_el in selection:
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
