# coding: utf8
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

import ast
from System import Guid

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewPlan,
    ViewSection,
    View3D,
    StorageType,
    InstanceBinding,
    Document,
    BuiltInParameter,
    SpecTypeId,
)
from Autodesk.Revit.Exceptions import (
    ArgumentException,
)

from pyrevitmep.parameter import SharedParameter, ProjectParameter
from pyrevitmep.event import CustomizableEvent

import operator
import re
import collections
from pyrevit.forms import WPFWindow
from pyrevit import script, revit, DB, HOST_APP

__doc__ = "Rename selected views according to a pattern"
__title__ = "Rename\nViews"
__author__ = "Cyril Waechter"

doc = revit.doc  # type: Document
uidoc = revit.uidoc
app = HOST_APP.app


# Create a regular expression to retrieve Guid (including constructor) in a string
parameterGuidRegex = re.compile(
    r"""
Guid\(              # Guid constructor. Example : Guid("F9168C5E-CEB2-4faa-B6BF-329BF39FA1E4")
[\" | \']           # Single or double quote required in Guid constructor
([0-9a-f]{8}        # First 8 hexa
(-?[0-9a-f]{4}){3}  # Optional separator + 4 hexa 3 times
-?[0-9a-f]{12})     # Optional separator + 12 hexa
[\" | \']           # Single or double quote required in Guid constructor
\)                  # Close parenthesis necessary to build a Guid
""",
    re.IGNORECASE | re.VERBOSE,
)

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


def add_parameter_in_pattern(parameter):
    """
    :parameter parameter: a parameter you want to get reference of
    :type parameter: Parameter
    :return: best reference of a parameter formatted to be inserted in the pattern (Guid, BuiltInParameter or Name)
    """
    if parameter.IsShared:
        return "Guid('{guid}')".format(guid=str(parameter.GUID))
    elif str(parameter.Definition.BuiltInParameter) != "INVALID":
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
    result = parameterNameRegex.sub(lambda m: func(getparameters_byname(view, m.group(1)), m.group(1)), pattern)
    result = parameterGuidRegex.sub(lambda m: func(getparameter(view, m.group()), m.group()), result)
    result = parameterBipRegex.sub(
        lambda m: func(getparameter(view, "BuiltInParameter." + m.group(1)), m.group(1)),
        result,
    )
    return result


def rename_views(views_and_names):
    """Rename all views with their associated new name"""
    logger.debug("Start rename function")
    with revit.Transaction("Rename views"):
        logger.debug("Start batch renaming: {}".format(views_and_names))
        for view, newname in views_and_names:
            logger.debug("{}{}".format(view, newname))
            try:
                view.Name = newname
            except ArgumentException:
                i = 1
                while True:
                    logger.debug("ArgumentException catched with newname: {}".format(newname))
                    try:
                        alt_name = newname + " " + str(i)
                        view.Name = alt_name
                    except ArgumentException:
                        logger.debug("ArgumentException catched with newname: {}".format(alt_name))
                        i += 1
                    else:
                        break
            else:
                logger.debug("Successfully renamed views")


customizable_event = CustomizableEvent()


my_config = script.get_config()
logger = script.get_logger()
customizable_event.logger = logger


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
            ViewPlan: {
                "pattern": "name(ORG_Métier)_name(ORG_Métier_Sous_catégorie)_PE_bip(PLAN_VIEW_LEVEL)_bip("
                "VIEWER_VOLUME_OF_INTEREST_CROP)",
                "sample_view": None,
            },
            View3D: {
                "pattern": "name(ORG_Métier)_name(ORG_Métier_Sous_catégorie)_3D",
                "sample_view": None,
            },
            ViewSection: {
                "pattern": "name(ORG_Métier)_name(ORG_Métier_Sous_catégorie)_CP",
                "sample_view": None,
            },
        }

        # Initialize pattern and parameter list
        for view_class, view_class_dict in self.view_class_dict.items():
            name = view_class.__name__
            sample_view = view_class_dict[sample_view] = get_sampleviewfromclass(view_class)
            if not sample_view:
                # Disable options and preview for view_class which not exist in the project
                view_class_checkbox = getattr(self, "cb_{}".format(name))
                view_class_button = getattr(self, "btn_{}_add_parameter".format(name))
                self.cb_all.IsEnabled = False
                view_class_checkbox.IsChecked = False
                view_class_checkbox.IsEnabled = False
                view_class_button.IsEnabled = False
                continue
            pattern_textbox = getattr(self, "{}_pattern".format(name))
            preview_textbox = getattr(self, "{}_preview".format(name))
            preview_by_name_textbox = getattr(self, "{}_toname_preview".format(name))
            parameter_combobox = getattr(self, "cb_{}_parameters".format(name))

            param_list = list(sample_view.Parameters)
            param_list.sort(key=operator.attrgetter("Definition.Name"))
            parameter_combobox.ItemsSource = param_list
            pattern = None
            param = revit.doc.ProjectInformation.LookupParameter(self.storage_pattern_parameter)
            if param and param.AsString():
                pattern = ast.literal_eval(param.AsString())[name]
            if not pattern:
                # Try to load patterns from config file
                pattern = getattr(my_config, name, None)
                if pattern:
                    pattern = pattern.decode("utf8")
            if not pattern:
                pattern = view_class_dict["pattern"]
            pattern_textbox.Text = pattern

            preview_textbox.Text = apply_pattern(sample_view, pattern_textbox.Text, param_display_value)
            preview_by_name_textbox.Text = apply_pattern(sample_view, pattern_textbox.Text, param_name)

    # noinspection PyUnusedLocal
    def save_to_parameter_click(self, sender, e):
        customizable_event.raise_event(self.save_to_parameter)

    def save_to_parameter(self):
        param = revit.doc.ProjectInformation.LookupParameter(self.storage_pattern_parameter)
        if not param:
            # create a project parameter to store patterns
            logger.debug("Param do not exist. Creating parameter.")
            category_set = app.Create.NewCategorySet()
            category = revit.doc.Settings.Categories.get_Item(DB.BuiltInCategory.OST_ProjectInformation)
            category_set.Insert(category)
            # if no parameter with given name exist, create a temporary one
            definition = SharedParameter.get_definition_by_name(self.storage_pattern_parameter)
            if not definition:
                shared_param = SharedParameter(self.storage_pattern_parameter, SpecTypeId.String)
                definition = shared_param.write_to_definition_file()
                shared_param.delete_from_definition_file()
            binding = InstanceBinding(category_set)
            project_param = ProjectParameter(definition, binding)
            project_param.group = DB.GroupTypeId.Pattern
            with revit.Transaction("Add {} to project parameters".format(self.storage_pattern_parameter)):
                project_param.save_to_revit_doc()
            param = revit.doc.ProjectInformation.LookupParameter(self.storage_pattern_parameter)
        pattern_dict = {}

        for view_class in self.view_class_dict.keys():
            name = view_class.__name__
            view_class_checkbox = getattr(self, "cb_{}".format(name))
            if view_class_checkbox.IsChecked:
                pattern_textbox = getattr(self, "{}_pattern".format(name))
                pattern_dict[name] = pattern_textbox.Text

        with revit.Transaction("Saving configuration to parameter"):
            param.Set(str(pattern_dict).encode("utf8"))

    # noinspection PyUnusedLocal
    def save_config_click(self, sender, e):
        logger.debug("Start writing config file")
        for view_class in self.view_class_dict.keys():
            name = view_class.__name__
            view_class_checkbox = getattr(self, "cb_{}".format(name))
            logger.debug(view_class_checkbox.IsChecked)
            if view_class_checkbox.IsChecked:
                pattern_textbox = getattr(self, "{}_pattern".format(name))
                logger.debug(type(pattern_textbox.Text))
                setattr(my_config, name, pattern_textbox.Text.encode("utf8"))
        script.save_config()
        logger.debug("End writing config file")

    # noinspection PyUnusedLocal
    def btn_add_parameter_click(self, sender, e):
        for view_class in self.view_class_dict.keys():
            if view_class in sender.Name:
                name = view_class.__name__
                parameters_combobox = getattr(self, "cb_{}_parameters".format(name))
                param_reference = add_parameter_in_pattern(parameters_combobox.SelectedItem)
                index = self.cursorposition
                pattern_textbox = getattr(self, "{}_pattern".format(name))
                pattern_textbox.Text = pattern_textbox.Text[:index] + param_reference + pattern_textbox.Text[index:]

    # noinspection PyUnusedLocal
    def pattern_changed(self, sender, e):
        view_class = getattr(DB, sender.Name.split("_")[0])
        name = view_class.__name__
        sample_view = self.view_class_dict[view_class]["sample_view"]
        if not sample_view:
            return
        pattern_textbox = getattr(self, "{}_pattern".format(name))
        parameter_preview = getattr(self, "{}_preview".format(name))
        name_preview = getattr(self, "{}_toname_preview".format(name))
        self.cursorposition = sender.SelectionStart
        parameter_preview.Text = apply_pattern(sample_view, pattern_textbox.Text, param_display_value)
        name_preview.Text = apply_pattern(sample_view, pattern_textbox.Text, param_name)

    # noinspection PyUnusedLocal
    def cb_checked_changed(self, sender, e):
        self.cb_all.IsChecked = None
        if self.cb_ViewPlan.IsChecked and self.cb_View3D.IsChecked and self.cb_ViewSection.IsChecked:
            self.cb_all.IsChecked = True
        if not self.cb_ViewPlan.IsChecked and not self.cb_View3D.IsChecked and not self.cb_ViewSection.IsChecked:
            self.cb_all.IsChecked = False

    # noinspection PyUnusedLocal
    def cb_all_checked_changed(self, sender, e):
        logger.debug(self.cb_all.IsChecked)
        state = self.cb_all.IsChecked
        if state is not None:
            self.cb_ViewPlan.IsChecked = state
            self.cb_View3D.IsChecked = state
            self.cb_ViewSection.IsChecked = state

    # noinspection PyUnusedLocal
    def btn_ok_click(self, sender, e):
        views = []
        if self.radiobtn_selectedviews.IsChecked:
            for elemid in uidoc.Selection.GetElementIds():
                views.append(doc.GetElement(elemid))
        else:
            checked_viewclass_list = []
            if self.cb_ViewPlan.IsChecked:
                checked_viewclass_list.append(ViewPlan)
            if self.cb_View3D.IsChecked:
                checked_viewclass_list.append(View3D)
            if self.cb_ViewSection.IsChecked:
                checked_viewclass_list.append(ViewSection)

            for viewclass in checked_viewclass_list:
                for view in FilteredElementCollector(doc).OfClass(viewclass):
                    if not view.IsTemplate:
                        views.append(view)
        logger.debug(views)
        viewplusname = []

        for view in views:
            pattern = getattr(self, "{}_pattern".format(type(view).__name__)).Text
            newname = apply_pattern(view, pattern, param_display_value)
            viewplusname.append((view, newname))
        logger.debug("[viewplusname:{}".format(viewplusname))
        customizable_event.raise_event(rename_views, viewplusname)


wpf_viewrename = ViewRename("ViewRename.xaml")

wpf_viewrename.Show()
