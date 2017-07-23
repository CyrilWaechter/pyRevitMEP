# coding: utf8
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
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import Transaction, Element, BuiltInParameter, FilteredElementCollector, \
    ViewPlan, ViewSection, View3D, StorageType
# noinspection PyUnresolvedReferences
from Autodesk.Revit.Exceptions import InvalidOperationException, OperationCanceledException, ArgumentException
# noinspection PyUnresolvedReferences
from Autodesk.Revit.UI import IExternalEventHandler, IExternalApplication, Result, ExternalEvent, IExternalCommand
# noinspection PyUnresolvedReferences
from System import Guid

import operator
import re
import rpw
import collections
from revitutils import doc, uidoc
from scriptutils.userinput import WPFWindow

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

# Create a regular expression to retrieve Guid (including constructor) in a string
parameterGuidRegex = re.compile(r'''
Guid\(              # Guid constructor. Example : Guid("F9168C5E-CEB2-4faa-B6BF-329BF39FA1E4")
[\" | \']           # Single or double quote required in Guid constructor
([0-9a-f]{8}        # First 8 hexa
(-?[0-9a-f]{4}){3}  # Optional separator + 4 hexa 3 times
-?[0-9a-f]{12})     # Optional separator + 12 hexa
[\" | \']           # Single or double quote required in Guid constructor
\)                  # Close parenthesis necessary to build a Guid
''', re.IGNORECASE | re.VERBOSE)

# Create a regular expression to retrieve BuiltInParameter in a string
parameterBipRegex = re.compile(r"bip\((\w+)\)")

# Create a regular expression to retrieve named parameters in a string
parameterNameRegex = re.compile(r"name\(([\w\s]+)\)")  # Retrieve group(1)


def get_sampleviewfromclass(viewclass):
    """Return a sample of the desired view class to see available parameters"""
    for view in FilteredElementCollector(doc).OfClass(viewclass):
        if view.IsTemplate:
            continue
        else:
            return view

# Retrieve a sample view for each view class
sampleviewplan = get_sampleviewfromclass(ViewPlan)
sampleview3D = get_sampleviewfromclass(View3D)
sampleviewsection = get_sampleviewfromclass(ViewSection)


def add_parameter_in_pattern(parameter):
    """
    :parameter parameter: a parameter you want to get reference of
    :type parameter: Parameter
    :return: best reference of a parameter formatted to be inserted in the pattern (Guid, BuiltInParameter or Name)
    """
    if parameter.IsShared:
        # print("{guid[",str(parameter.GUID),"]}")
        return "Guid('{guid}')".format(guid=str(parameter.GUID))
    elif str(parameter.Definition.BuiltInParameter) != "INVALID":
        # print("{bip[",parameter.Definition.BuiltInParameter,"]}")
        return "bip({bip_name})".format(bip_name=parameter.Definition.BuiltInParameter)
    else:
        return "name({param_name})".format(param_name=parameter.Definition.Name)


def getparameter(view, biporguid):
    """
    :param view: View class object
    :param biporguid: BuiltInParameter or Guid
    :return: Parameter class object or None if not found
    """
    try:
        if view is None:
            return None
        param = view.get_Parameter(eval(biporguid))
        return param
    except AttributeError:
        return None


def getparameters_byname(view, name):
    """
    :param view: View class object
    :param name: Parameter name (Definition.Name)
    :return: A list of parameters with the corresponding name
    """
    return view.GetParameters(name)


def param_display_value(parameters, default=""):
    """
    :type default: str
    :param parameters: Parameter or a list of Parameters
    :param default: default value if no suitable value found
    :return: suitable display value or default value
    """
    if not parameters:
        return default
    if not isinstance(parameters, collections.Iterable):
        parameters = [parameters]
    for param in parameters:
        if not param.HasValue:
            continue
        elif param.StorageType == StorageType.String:
            return param.AsString()
        elif param.AsValueString() is not None:
            return param.AsValueString()
        else:
            continue
    return default


def param_name(parameters, default=""):
    """
    :type default: str
    :param parameters: Parameter or a list of Parameters
    :param default: default value if no suitable value found
    :return: first Parameter.Definition.Name found or default value
    """
    if not parameters:
        return default
    if not isinstance(parameters, collections.Iterable):
        parameters = [parameters]
    for param in parameters:
        return param.Definition.Name


def guid(parameters, default=""):
    """
    :param parameters: Parameter or a list of Parameters
    :param default: default value if no suitable value found
    :return: first Parameter.GUID found or default value
    """
    if not parameters:
        return default
    for param in list(parameters):
        if param.IsShared:
            return param.GUID
    return default


def apply_pattern(view, pattern, func):
    """
    apply a pattern to a string using a regular expression
    :type func: function
    :param func: a function which retrieve a specific attribute of a parameter
    :type pattern: str
    :param pattern: pattern like "bip(PLAN_VIEW_LEVEL)" for batch process
    :type view: View
    :return: a string with pattern applied
    """
    try:
        result = parameterNameRegex.sub(lambda m: func(getparameters_byname(view, m.group(1)),
                                                       m.group(1)),
                                        pattern)
        result = parameterGuidRegex.sub(lambda m: func(getparameter(view, m.group()),
                                                       m.group()),
                                        result)
        result = parameterBipRegex.sub(lambda m: func(getparameter(view, "BuiltInParameter." + m.group(1)),
                                                      m.group(1)),
                                       result)
        return result
    except:
        import traceback
        traceback.print_exc()
        return "Something goes wrong in apply_pattern"


class ElementParametersDicts(object):
    """
    Create an object which contain dictionnaries for parameters
    Each dictionnary reference element parameters by their GUID, BuiltInParameter and Name
    """
    def __init__(self, view, attribute):
        self.test = 1
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

# Make a static dictionnaries for each view class to use it in preview fields
viewplan_namedicts = ElementParametersDicts(get_sampleviewfromclass(ViewPlan), "name")
viewplan_valuedicts = ElementParametersDicts(get_sampleviewfromclass(ViewPlan), "value")
view3D_namedicts = ElementParametersDicts(get_sampleviewfromclass(View3D), "name")
view3D_valuedicts = ElementParametersDicts(get_sampleviewfromclass(View3D), "value")
viewsection_namedicts = ElementParametersDicts(get_sampleviewfromclass(ViewSection), "name")
viewsection_valuedicts = ElementParametersDicts(get_sampleviewfromclass(ViewSection), "value")

list_dict = [view3D_namedicts, view3D_namedicts, viewsection_namedicts]


class RenameViews(object):
    """Simple class intended to be used in ExternalEvent"""
    def __init__(self):
        self.viewsandnames = []

    def rename(self):
        """Rename all views with their associated new name"""
        t = Transaction(doc, "Rename views")
        t.Start()
        for view, newname in self.viewsandnames:
            view.Name = newname
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


# Create an handler instance and his associated ExternalEvent
rename_view_handler = ViewRenameHandler(rename_view.rename)
rename_view_event = ExternalEvent.Create(rename_view_handler)


class ViewRename(WPFWindow):
    """
    GUI used to make a rename pattern and preview the result on a sample view
    Then launch the mass renaming operation
    """

    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        # Initialize ViewPlan pattern and parameter list
        viewplan_paramlist = list(sampleviewplan.Parameters)
        viewplan_paramlist.sort(key=operator.attrgetter("Definition.Name"))
        self.cb_viewplan_parameters.ItemsSource = viewplan_paramlist
        self.pattern.Text = "name(ORG_Métier)_name(ORG_Métier_Sous_catégorie)_PE_bip(PLAN_VIEW_LEVEL)_" \
                            "bip(VIEWER_VOLUME_OF_INTEREST_CROP)"
        self.preview.Text = apply_pattern(sampleviewplan,
                                          self.pattern.Text,
                                          param_display_value)
        self.pattern_paramname_preview.Text = apply_pattern(sampleviewplan,
                                                            self.pattern.Text,
                                                            param_name)
        self.cursorposition = 0
        self.cb_all.IsChecked = None
        self.pattern_dict = {ViewPlan:"pattern", View3D:"pattern_view3D", ViewSection:"pattern_viewsection"}

    def btn_viewplan_addparameter_click(self, sender, e):
        param_reference = add_parameter_in_pattern(self.cb_viewplan_parameters.SelectedItem)
        index = self.cursorposition
        self.pattern.Text = self.pattern.Text[:index] + param_reference + self.pattern.Text[index:]

    def pattern_selection_changed(self, sender, e):
        self.cursorposition = sender.SelectionStart
        self.preview.Text = apply_pattern(sampleviewplan,
                                          self.pattern.Text,
                                          param_display_value)
        self.pattern_paramname_preview.Text = apply_pattern(sampleviewplan,
                                                            self.pattern.Text,
                                                            param_name)

    def cb_checked_changed(self, sender, e):
        self.cb_all.IsChecked = None
        if self.cb_viewplan.IsChecked == True\
                and self.cb_view3D.IsChecked == True\
                and self.cb_viewsection.IsChecked == True:
            self.cb_all.IsChecked = True
        if self.cb_viewplan.IsChecked == False\
                and self.cb_view3D.IsChecked == False\
                and self.cb_viewsection.IsChecked == False:
            self.cb_all.IsChecked = False

    def cb_all_checked_changed(self, sender, e):
        checked = self.cb_all.IsChecked
        self.cb_viewplan.IsChecked = checked
        self.cb_view3D.IsChecked = checked
        self.cb_viewsection.IsChecked = checked

    def btn_ok_click(self, sender, e):
        views = []
        if self.radiobtn_selectedviews.IsChecked:
            for elemid in uidoc.Selection.GetElementIds():
                views.append(doc.GetElement(elemid))
        else:
            checked_viewclass_list = []
            if self.cb_viewplan.IsCheked:
                checked_viewclass_list.append(ViewPlan)
            if self.cb_view3D.IsChecked:
                checked_viewclass_list.append(View3D)
            if self.cb_viewsection.IsChecked:
                checked_viewclass_list.append(ViewSection)
            for viewclass in checked_viewclass_list:
                for view in FilteredElementCollector(doc).OfClass(viewclass):
                    if not view.IsTemplate:
                        views.append(view)
        viewplusname = []
        for view in views:
            pattern = getattr(self, self.pattern_dict[view.__class__])
            newname = apply_pattern(view, pattern.Text, param_display_value)
            viewplusname.append((view, newname))
            rename_view.viewsandnames = viewplusname
            rename_view_event.Raise()


wpf_viewrename = ViewRename('ViewRename.xaml')
wpf_viewrename.Show()
