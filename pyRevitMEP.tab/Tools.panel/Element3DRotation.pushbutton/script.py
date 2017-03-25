# coding=utf-8
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
from scriptutils.userinput import WPFWindow

from Autodesk.Revit.DB import Transaction, ElementTransformUtils, Line, XYZ, Location, UnitType, UnitUtils

__doc__ = "Rotate object in any direction"
__title__ = "3D Rotate"
__author__ = "Cyril Waechter"

# Get project units for angles
angle_unit = doc.GetUnits().GetFormatOptions(UnitType.UT_Angle).DisplayUnits

def xyz_axis(element_id):
    origin = doc.GetElement(element_id).Location.Point
    xyz_direction = [XYZ(origin.X + 1, origin.Y, origin.Z),
                     XYZ(origin.X, origin.Y + 1, origin.Z),
                     XYZ(origin.X, origin.Y, origin.Z + 1)]
    axis = []
    for direction in xyz_direction:
        axis.append(Line.CreateBound(origin, direction))
    return axis


def rotate(element_id, axis, angle):
    try:
        ElementTransformUtils.RotateElement(doc, element_id, axis, angle)
    except:
        raise


class RotateOptions(WPFWindow):
    """
    WPF form for rotation angle input
    """

    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.set_image_source("xyz_img", "XYZ.png")

    def around_itself_click(self, sender, e):
        try:
            angles = [self.x_axis.Text, self.y_axis.Text, self.z_axis.Text]
            for i in range(3):
                angles[i] = UnitUtils.ConvertToInternalUnits(float(angles[i]),angle_unit)
        except ValueError:
            self.warning.Text = "Incorrect angles, input format required '0.0'"
        else:
            self.DialogResult = True
            self.Close()
            t = Transaction(doc, "Rotate around itself")
            t.Start()
            for elid in selection.element_ids:
                el_axis = xyz_axis(elid)
                for i in range(3):
                    if angles[i] == 0:
                        pass
                    else:
                        rotate(elid,el_axis[i],angles[i])
            t.Commit()

RotateOptions('RotateOptions.xaml').ShowDialog()