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
from pyRevitMEP.parameter import create_shared_parameter_definition, create_project_parameter
from pyRevitMEP.event import CustomizableEvent

import operator
import re
import collections
from rpw import doc, uidoc
from pyrevit.forms import WPFWindow
from pyrevit import script
import rpw
# noinspection PyUnresolvedReferences
from rpw import revit, DB

__doc__ = "Rename selected views according to a pattern"
__title__ = "Rename views"
__author__ = "Cyril Waechter"


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
    :type func: func
    :param func: a function which retrieve a specific attribute of a parameter
    :type pattern: str
    :param pattern: pattern like "bip(PLAN_VIEW_LEVEL)" for batch process
    :type view: View
    :return: a string with pattern applied
    """
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


def rename_views(views_and_names):
    """Rename all views with their associated new name"""
    logger.debug('Start rename function')
    with rpw.db.Transaction("Rename views"):
        logger.debug('Start batch renaming: {}'.format(views_and_names))
        for view, newname in views_and_names:
            logger.debug('{}{}'.format(view, newname))
            try:
                view.Name = newname
            except ArgumentException:
                i = 1
                while True:
                    logger.debug('ArgumentException catched with newname: {}'.format(newname))
                    try:
                        alt_name = newname + ' ' + str(i)
                        view.Name = alt_name
                    except ArgumentException:
                        logger.debug('ArgumentException catched with newname: {}'.format(alt_name))
                        i += 1
                    else:
                        break
            else:
                logger.debug('Successfully renamed views')


customizable_event = CustomizableEvent()


my_config = script.get_config()
logger = script.get_logger()


class ViewRename(WPFWindow):
    """
    GUI used to make a rename pattern and preview the result on a sample view
    Then launch the mass renaming operation
    """

    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.cursorposition = 0
        self.cb_all.IsChecked = True
        self.storage_pattern_parameter = "pyRevitMEP_viewrename_patterns"

        self.view_class_dict = {
            'viewplan': {
                'pattern': "name(ORG_Métier)_name(ORG_Métier_Sous_catégorie)_PE_bip(PLAN_VIEW_LEVEL)_bip("
                           "VIEWER_VOLUME_OF_INTEREST_CROP)",
                'pattern_textbox': self.viewplan_pattern,
                'preview_textbox': self.viewplan_preview,
                'name_preview_textbox': self.viewplan_toname_preview,
                'parameter_combobox': self.cb_viewplan_parameters},
            'view3D': {
                'pattern': "name(ORG_Métier)_name(ORG_Métier_Sous_catégorie)_3D"},
            'viewsection': {
                'pattern': "name(ORG_Métier)_name(ORG_Métier_Sous_catégorie)_CP"}
        }

        # Initialize pattern and parameter list
        for view_class in self.view_class_dict.keys():
            try:
                sample_view = eval('sample{}'.format(view_class))
                pattern_textbox = eval('self.{}_pattern'.format(view_class))
                preview_textbox = eval('self.{}_preview'.format(view_class))
                preview_by_name_textbox = eval('self.{}_toname_preview'.format(view_class))
                parameter_combobox = eval('self.cb_{}_parameters'.format(view_class))

                param_list = list(sample_view.Parameters)
                param_list.sort(key=operator.attrgetter("Definition.Name"))
                parameter_combobox.ItemsSource = param_list
                try:
                    # Try to load patterns from project parameter
                    project_info_param_set = rpw.db.ParameterSet(revit.doc.ProjectInformation)
                    param = project_info_param_set[self.storage_pattern_parameter]
                    pattern_textbox.Text = eval(param.value)[view_class]

                except (rpw.exceptions.RpwParameterNotFound, SyntaxError) as error:
                    try:
                        # Try to load patterns from config file
                        pattern_textbox.Text = getattr(my_config, view_class).decode('utf8')
                    except AttributeError:
                        # Else load default values
                        pattern = self.view_class_dict[view_class]['pattern']
                        pattern_textbox.Text = pattern

                preview_textbox.Text = apply_pattern(sample_view, pattern_textbox.Text, param_display_value)
                preview_by_name_textbox.Text = apply_pattern(sample_view, pattern_textbox.Text, param_name)

            except AttributeError:
                # Disable options and preview for view_class which not exist in the project
                view_class_checkbox = eval('self.cb_{}'.format(view_class))
                view_class_button = eval('self.btn_{}_add_parameter'.format(view_class))
                self.cb_all.IsEnabled = False
                view_class_checkbox.IsChecked = False
                view_class_checkbox.IsEnabled = False
                view_class_button.IsEnabled = False

        # Create a dict with key=View class, value=pattern location
        self.pattern_dict = {ViewPlan: self.viewplan_pattern, View3D: self.view3D_pattern,
                             ViewSection: self.viewsection_pattern}

    # noinspection PyUnusedLocal
    def save_to_parameter_click(self, sender, e):
        customizable_event.raise_event(self.save_to_parameter)

    def save_to_parameter(self):
        project_info_param_set = rpw.db.ParameterSet(revit.doc.ProjectInformation)
        try:
            param = project_info_param_set[self.storage_pattern_parameter]
            pattern_dict = eval(param.value)
        except (rpw.exceptions.RpwParameterNotFound, SyntaxError) as error:
            category_set = revit.app.Create.NewCategorySet()
            category = revit.doc.Settings.Categories.get_Item(DB.BuiltInCategory.OST_ProjectInformation)
            category_set.Insert(category)
            with rpw.db.Transaction("Add pyRevitMEP_viewrename_patterns to project parameters"):
                definition = create_shared_parameter_definition(revit.app, self.storage_pattern_parameter,
                                                                "pyRevitMEP", DB.ParameterType.Text)
                create_project_parameter(revit.app, definition, category_set, DB.BuiltInParameterGroup.PG_PATTERN, True)
                param = project_info_param_set[self.storage_pattern_parameter]
                pattern_dict = {}

        for view_class in self.view_class_dict.keys():
            view_class_checkbox = eval('self.cb_{}'.format(view_class))
            if view_class_checkbox.IsChecked:
                pattern_textbox = eval('self.{}_pattern'.format(view_class))
                pattern_dict[view_class] = pattern_textbox.Text

        with rpw.db.Transaction("Saving configuration to parameter"):
            param.value = str(pattern_dict).encode('utf8')

    # noinspection PyUnusedLocal
    def save_config_click(self, sender, e):
        logger.debug('Start writing config file')
        for view_class in self.view_class_dict.keys():
            view_class_checkbox = eval('self.cb_{}'.format(view_class))
            logger.debug(view_class_checkbox.IsChecked)
            if view_class_checkbox.IsChecked:
                pattern_textbox = eval('self.{}_pattern'.format(view_class))
                logger.debug(type(pattern_textbox.Text))
                setattr(my_config, view_class, pattern_textbox.Text.encode('utf8'))
        script.save_config()
        logger.debug('End writing config file')

    # noinspection PyUnusedLocal
    def btn_add_parameter_click(self, sender, e):
        for view_class in self.view_class_dict.keys():
            if view_class in sender.Name:
                parameters_combobox = eval('self.cb_{}_parameters'.format(view_class))
                param_reference = add_parameter_in_pattern(parameters_combobox.SelectedItem)
                index = self.cursorposition
                pattern_textbox = eval('self.{}_pattern'.format(view_class))
                pattern_textbox.Text = pattern_textbox.Text[:index] + param_reference + pattern_textbox.Text[index:]

    # noinspection PyUnusedLocal
    def pattern_changed(self, sender, e):
        view_class = sender.Name.split('_')[0]
        sample_view = eval("sample{}".format(view_class))
        pattern_textbox = eval("self.{}_pattern".format(view_class))
        parameter_preview = eval('self.{}_preview'.format(view_class))
        name_preview = eval('self.{}_toname_preview'.format(view_class))
        self.cursorposition = sender.SelectionStart
        parameter_preview.Text = apply_pattern(sample_view,
                                               pattern_textbox.Text,
                                               param_display_value)
        name_preview.Text = apply_pattern(sample_view,
                                          pattern_textbox.Text,
                                          param_name)

    # noinspection PyUnusedLocal
    def cb_checked_changed(self, sender, e):
        self.cb_all.IsChecked = None
        if self.cb_viewplan.IsChecked \
                and self.cb_view3D.IsChecked \
                and self.cb_viewsection.IsChecked:
            self.cb_all.IsChecked = True
        if not self.cb_viewplan.IsChecked \
                and not self.cb_view3D.IsChecked \
                and not self.cb_viewsection.IsChecked:
            self.cb_all.IsChecked = False

    # noinspection PyUnusedLocal
    def cb_all_checked_changed(self, sender, e):
        logger.debug(self.cb_all.IsChecked)
        state = self.cb_all.IsChecked
        if state is not None:
            self.cb_viewplan.IsChecked = state
            self.cb_view3D.IsChecked = state
            self.cb_viewsection.IsChecked = state

    # noinspection PyUnusedLocal
    def btn_ok_click(self, sender, e):
        views = []
        if self.radiobtn_selectedviews.IsChecked:
            for elemid in uidoc.Selection.GetElementIds():
                views.append(doc.GetElement(elemid))
        else:
            checked_viewclass_list = []
            if self.cb_viewplan.IsChecked:
                checked_viewclass_list.append(ViewPlan)
            if self.cb_view3D.IsChecked:
                checked_viewclass_list.append(View3D)
            if self.cb_viewsection.IsChecked:
                checked_viewclass_list.append(ViewSection)

            for viewclass in checked_viewclass_list:
                for view in FilteredElementCollector(doc).OfClass(viewclass):
                    if not view.IsTemplate:
                        views.append(view)
        logger.debug(views)
        viewplusname = []

        for view in views:
            pattern = self.pattern_dict[type(view)].Text
            newname = apply_pattern(view, pattern, param_display_value)
            viewplusname.append((view, newname))
        logger.debug('[viewplusname:{}'.format(viewplusname))
        customizable_event.raise_event(rename_views, viewplusname)


wpf_viewrename = ViewRename('ViewRename.xaml')

wpf_viewrename.Show()
