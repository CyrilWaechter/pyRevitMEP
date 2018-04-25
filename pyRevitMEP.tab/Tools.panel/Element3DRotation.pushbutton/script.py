# coding=utf-8
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
import rpw
from rpw import revit
from pyrevit.forms import WPFWindow
from pypevitmep.event import CustomizableEvent

# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import Transaction, ElementTransformUtils, Line, XYZ, Location, UnitType, UnitUtils, ElementId
# noinspection PyUnresolvedReferences
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
# noinspection PyUnresolvedReferences
from Autodesk.Revit.UI import IExternalEventHandler, IExternalApplication, Result, ExternalEvent, IExternalCommand
# noinspection PyUnresolvedReferences
from Autodesk.Revit.Exceptions import InvalidOperationException, OperationCanceledException


__doc__ = "Rotate object in any direction"
__title__ = "3D Rotate"
__author__ = "Cyril Waechter"

doc = revit.doc
uidoc = revit.uidoc

# Get current project units for angles
angle_unit = doc.GetUnits().GetFormatOptions(UnitType.UT_Angle).DisplayUnits


def xyz_axis(element_id):
    """Input : Element, Output : xyz axis of the element
    :type element_id: ElementId
    """
    transform = doc.GetElement(element_id).GetTransform()
    axis = [Line.CreateBound(transform.Origin, transform.Origin + transform.Basis[i]) for i in range(3)]
    return axis


class AxisISelectionFilter(ISelectionFilter):
    """ISelectionFilter that allow only which have an axis (Line)"""

    # noinspection PyMethodMayBeStatic, PyPep8Naming
    def AllowElement(self, element):
        if isinstance(element.Location.Curve, Line):
            return True
        else:
            return False


def axis_selection():
    """Ask user to select an element, return the axis of the element"""
    try:
        reference = uidoc.Selection.PickObject(ObjectType.Element, AxisISelectionFilter(), "Select an axis")
    except OperationCanceledException:
        pass
    else:
        axis = doc.GetElement(reference).Location.Curve
        return axis


class RotateElement(object):
    """class used to store rotation parameters. Methods then rotate elements."""
    def __init__(self):
        self.selection = uidoc.Selection.GetElementIds()
        self.angles = [0]

    def around_itself(self):
        """Method used to rotate elements on themselves"""
        with rpw.db.Transaction("Rotate around itself", doc):
            for elid in self.selection:
                el_axis = xyz_axis(elid)
                for i in range(3):
                    if self.angles[i] == 0:
                        pass
                    else:
                        ElementTransformUtils.RotateElement(doc, elid, el_axis[i], self.angles[i])

    def around_axis(self):
        """Method used to rotate elements around selected axis"""
        with rpw.db.Transaction("Rotate around axis", doc):
            axis = axis_selection()
            ElementTransformUtils.RotateElements(doc, self.selection, axis, self.angles)
        uidoc.Selection.SetElementIds(rotate_elements.selection)


rotate_elements = RotateElement()

customizable_event = CustomizableEvent()


class RotateOptions(WPFWindow):
    """
    Modeless WPF form used for rotation angle input
    """

    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.set_image_source("xyz_img", "XYZ.png")
        self.set_image_source("plusminus_img", "PlusMinusRotation.png")

    # noinspection PyUnusedLocal
    def around_itself_click(self, sender, e):
        try:
            rotate_elements.selection = uidoc.Selection.GetElementIds()
            angles = [self.x_axis.Text, self.y_axis.Text, self.z_axis.Text]
            internal_angles = [UnitUtils.ConvertToInternalUnits(float(i), angle_unit) for i in angles]
            rotate_elements.angles = internal_angles
        except ValueError:
            self.warning.Text = "Incorrect angles, input format required '0.0'"
        else:
            self.warning.Text = ""
            customizable_event.raise_event(rotate_elements.around_itself)

    # noinspection PyUnusedLocal
    def around_axis_click(self, sender, e):
        try:
            rotate_elements.angles = UnitUtils.ConvertToInternalUnits(float(self.rotation_angle.Text), angle_unit)
            rotate_elements.selection = uidoc.Selection.GetElementIds()
        except ValueError:
            self.warning.Text = "Incorrect angles, input format required '0.0'"
        else:
            customizable_event.raise_event(rotate_elements.around_axis)

RotateOptions('RotateOptions.xaml').Show()
