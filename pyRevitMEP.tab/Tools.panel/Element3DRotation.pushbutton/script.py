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
from revitutils import doc, uidoc
from scriptutils.userinput import WPFWindow

# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import Transaction, ElementTransformUtils, Line, XYZ, Location, UnitType, UnitUtils
# noinspection PyUnresolvedReferences
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
# noinspection PyUnresolvedReferences
from Autodesk.Revit.UI import IExternalEventHandler, IExternalApplication, Result, ExternalEvent, IExternalCommand
# noinspection PyUnresolvedReferences
from Autodesk.Revit.Exceptions import InvalidOperationException, OperationCanceledException


__doc__ = "Rotate object in any direction"
__title__ = "3D Rotate"
__author__ = "Cyril Waechter"

# Get current project units for angles
angle_unit = doc.GetUnits().GetFormatOptions(UnitType.UT_Angle).DisplayUnits


def xyz_axis(element_id):
    """Input : Element, Output : xyz axis of the element"""
    origin = doc.GetElement(element_id).Location.Point
    xyz_direction = [XYZ(origin.X + 1, origin.Y, origin.Z),
                     XYZ(origin.X, origin.Y + 1, origin.Z),
                     XYZ(origin.X, origin.Y, origin.Z + 1)]
    axis = []
    for direction in xyz_direction:
        axis.append(Line.CreateBound(origin, direction))
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
        try:
            t = Transaction(doc, "Rotate around itself")
            t.Start()
            for elid in self.selection:
                el_axis = xyz_axis(elid)
                for i in range(3):
                    if self.angles[i] == 0:
                        pass
                    else:
                        ElementTransformUtils.RotateElement(doc, elid, el_axis[i], self.angles[i])
            t.Commit()
        except InvalidOperationException:
            import traceback
            traceback.print_exc()
        except:
            import traceback
            traceback.print_exc()

    def around_axis(self):
        """Method used to rotate elements around selected axis"""
        try:
            axis = axis_selection()
            t = Transaction(doc, "Rotate around axis")
            t.Start()
            ElementTransformUtils.RotateElements(doc, self.selection, axis, self.angles)
            t.Commit()
        except InvalidOperationException:
            import traceback
            traceback.print_exc()
        except:
            import traceback
            traceback.print_exc()

rotate_elements = RotateElement()


# Create a subclass of IExternalEventHandler
class RotateElementHandler(IExternalEventHandler):
    """Input : function or method. Execute input in a IExternalEventHandler"""

    # __init__ is used to make function from outside of the class to be executed by the handler. \
    # Instructions could be simply written under Execute method only
    def __init__(self, do_this):
        self.do_this = do_this

    # Execute method run in Revit API environment.
    # noinspection PyPep8Naming, PyUnusedLocal
    def Execute(self, application):
        try:
            self.do_this()
        except InvalidOperationException:
            # If you don't catch this exeption Revit may crash.
            print "InvalidOperationException catched"

    # noinspection PyMethodMayBeStatic, PyPep8Naming
    def GetName(self):
        return "Execute an function or method in a IExternalHandler"

# Create handler instances. Same class (2 instance) is used to call 2 different method.
around_itself_handler = RotateElementHandler(rotate_elements.around_itself)
around_axis_handler = RotateElementHandler(rotate_elements.around_axis)
# Create ExternalEvent instance which pass these handlers
around_itself_event = ExternalEvent.Create(around_itself_handler)
around_axis_event = ExternalEvent.Create(around_axis_handler)


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
            for i in range(3):
                angles[i] = UnitUtils.ConvertToInternalUnits(float(angles[i]), angle_unit)
            rotate_elements.angles = angles
        except ValueError:
            self.warning.Text = "Incorrect angles, input format required '0.0'"
        else:
            self.warning.Text = ""
            around_itself_event.Raise()

    # noinspection PyUnusedLocal
    def around_axis_click(self, sender, e):
        try:
            rotate_elements.angles = UnitUtils.ConvertToInternalUnits(float(self.rotation_angle.Text), angle_unit)
            rotate_elements.selection = uidoc.Selection.GetElementIds()
        except ValueError:
            self.warning.Text = "Incorrect angles, input format required '0.0'"
        else:
            around_axis_event.Raise()


RotateOptions('RotateOptions.xaml').Show()
