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
import rpw, operator

# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import Transaction, Element, BuiltInParameter, FilteredElementCollector, ViewPlan
# noinspection PyUnresolvedReferences
from Autodesk.Revit.UI import IExternalEventHandler, IExternalApplication, Result, ExternalEvent, IExternalCommand
# noinspection PyUnresolvedReferences
from Autodesk.Revit.Exceptions import InvalidOperationException, OperationCanceledException, ArgumentException

__doc__ = "Rename selected views according to a pattern"
__title__ = "Rename views"
__author__ = "Cyril Waechter"

# try:
#     t = Transaction(doc, "Rename views")
#     t.Start()
#     for view in selection.elements:  # Loop trough selected views
#         view_typeid = doc.GetElement(view.GetTypeId())  # Get ViewFamilyType Id
#         view_typename = Element.Name.GetValue(view_typeid)  # Get ViewFamilyType Name
#
#         # Get Scope Box name if it exist
#         try:
#             view_scopebox = view.get_Parameter(BuiltInParameter.VIEWER_VOLUME_OF_INTEREST_CROP)
#             view_scopebox_name = "" if view_scopebox.Value() is None else "_" + view_scopebox.AsValueString()
#         except AttributeError:
#             view_scopebox_name = ""
#
#         # Get view reference level if it exist
#         view_genlevel = "" if view.GenLevel is None else view.GenLevel.Name
#
#         # Future view name
#         view_name = "{c}_{a}{b}".format(a=view_genlevel, b=view_scopebox_name, c=view_typename, )
#
#         # Rename view
#         i = 0
#         while True:
#             try:
#                 view.Name = view_name if i == 0 else view_name + str(i)
#             except ArgumentException:
#                 i += 1
#             except:
#                 raise
#             else:
#                 break
#     t.Commit()
# except:  # print a stack trace and error messages for debugging
#     import traceback
#
#     traceback.print_exc()
#     t.RollBack()


# def get_viewparameters(view):
#     for view in FilteredElementCollector(doc).OfClass(viewclass):
#         if view.IsTemplate:
#             continue
#         else:
#             viewparams = view.Parameters
#     return viewparams


def get_sampleviewfromclass(viewclass):
    for view in FilteredElementCollector(doc).OfClass(viewclass):
        if view.IsTemplate:
            continue
        else:
            return view


def add_parameter_in_pattern(parameter):
    if parameter.IsShared:
        # print("{guid[",str(parameter.GUID),"]}")
        return "{guid[" + str(parameter.GUID) + "]}"
    elif str(parameter.Definition.BuiltInParameter) != "INVALID":
        # print("{bip[",parameter.Definition.BuiltInParameter,"]}")
        return "{bip[" + str(parameter.Definition.BuiltInParameter) + "]}"
    else:
        return "{name[" + parameter.Definition.Name + "]}"


def apply_pattern(pattern, viewparametersdicts):
    try:
        vpd = viewparametersdicts
        return pattern.format(guid=vpd.guid_dict, bip=vpd.bip_dict, name=vpd.name_dict)
    except:
        pass


class ViewParametersDicts(object):
    def __init__(self, view, attribute):
        guid_dict = {}
        bip_dict = {}
        name_dict = {}
        for param in view.Parameters:
            bip = str(param.Definition.BuiltInParameter)
            if param.StorageType.ToString() == "None":
                continue
            elif param.IsShared:
                guid_dict[str(param.GUID)] = getattr(rpw.db.Parameter(param), attribute)
            elif bip != "INVALID":
                bip_dict[bip] = getattr(rpw.db.Parameter(param), attribute)
            name_dict[param.Definition.Name] = getattr(rpw.db.Parameter(param), attribute)
        self.guid_dict = guid_dict
        self.bip_dict = bip_dict
        self.name_dict = name_dict

ViewPlanNameDicts = ViewParametersDicts(get_sampleviewfromclass(ViewPlan), "name")
ViewPlanValueDicts = ViewParametersDicts(get_sampleviewfromclass(ViewPlan), "value")


class RenameViews(object):
    def __init__(self):
        self.views = []
        self.newname = ""

    def rename(self):
        for view in self.views:

            t = Transaction(doc, "Rename views")
            t.Start()
            self.view.Name = ViewRename.pattern.Text
            t.Commit()

rename_view = RenameViews()

# Create a subclass of IExternalEventHandler
class ViewRenameHandler(IExternalEventHandler):
    """Input : function or method. Execute input in a IExternalEventHandler"""

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

def apply_pattern_views(viewselection):
    pass

# Create handler instances. Same class (2 instance) is used to call 2 different method.
rename_view_handler = ViewRenameHandler(rename_view.rename)
# # Create ExternalEvent instance which pass these handlers
rename_view_event = ExternalEvent.Create(rename_view_handler)
# around_axis_event = ExternalEvent.Create(around_axis_handler)

class ViewRename(WPFWindow):
    """
    GUI used to select a reference level from a list or an object
    """

    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.cb_viewplan_parameters.ItemsSource = get_sampleviewfromclass(ViewPlan).Parameters
        self.pattern.Text = "COO_GEN_PE_E0"
        self.preview.Text = apply_pattern(self.pattern.Text, ViewPlanValueDicts)
        self.pattern_paramname_preview.Text = apply_pattern(self.pattern.Text, ViewPlanNameDicts)
        self.cursorposition = 0
        self.cb_all.IsChecked = None

    def btn_addparameter_click(self, sender, e):
        parameter = add_parameter_in_pattern(self.cb_viewplan_parameters.SelectedItem)
        index = self.cursorposition
        self.pattern.Text = self.pattern.Text[:index] + parameter + self.pattern.Text[index:]

    def pattern_selection_changed(self, sender, e):
        self.cursorposition = sender.SelectionStart
        self.preview.Text = apply_pattern(self.pattern.Text, ViewPlanValueDicts)
        self.pattern_paramname_preview.Text = apply_pattern(self.pattern.Text, ViewPlanNameDicts)

    def cb_checked_changed(self, sender, e):
        self.cb_all.IsChecked = None
        if self.cb_viewplan.IsChecked == True and self.cb_view3D.IsChecked == True and self.cb_viewsection.IsChecked == True:
            self.cb_all.IsChecked = True
        if self.cb_viewplan.IsChecked == False and self.cb_view3D.IsChecked == False and self.cb_viewsection.IsChecked == False:
            self.cb_all.IsChecked = False

    def cb_all_checked_changed(self, sender, e):
        checked = self.cb_all.IsChecked
        self.cb_viewplan.IsChecked = checked
        self.cb_view3D.IsChecked = checked
        self.cb_viewsection.IsChecked = checked

    def btn_ok_click(self, sender, e):
        for view in selection:
            if self.cb_viewplan.IsChecked and isinstance(view, ViewPlan):
                vpd = ViewParametersDicts(view, "value")
                # view.Definition.Name = apply_pattern(self.pattern.Text, vpd)



ViewRename('ViewRename.xaml').Show()
