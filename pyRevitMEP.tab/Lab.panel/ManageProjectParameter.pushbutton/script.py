# coding: utf8
import rpw
# noinspection PyUnresolvedReferences
from rpw import revit, DB, UI
# noinspection PyUnresolvedReferences
from Autodesk.Revit.Exceptions import InvalidOperationException
from pyrevit import script
from pyrevit.forms import WPFWindow
from pypevitmep.parameter import SharedParameter, ProjectParameter, BoundAllowedCategory
# noinspection PyUnresolvedReferences
from System.Collections.ObjectModel import ObservableCollection

__doc__ = "Batch create project parameters"
__title__ = "ProjectParameter"
__author__ = "Cyril Waechter"

doc = rpw.revit.doc
uidoc = rpw.uidoc
logger = script.get_logger()

# text_box = TextBox("parameters_text",text_text, Height=400, Width=400)
# components = [text_box]
#
# form = rpw.ui.forms.FlexForm("Parameters to create check", components)
# form.ShowDialog()
#
# parameters_text = text_box.Text.split("\n")
#
# for parameter in parameters_text:
#     print parameter
#
# with rpw.db.Transaction("Batch create shared parameters from file"):
#      for parameter_name in parameters_text:
#         SharedParameter(revit.app, parameter_name, "MCR", DB.ParameterType.Text)


class Gui(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.data_grid_content = ObservableCollection[object]()
        self.datagrid.ItemsSource = self.data_grid_content
        self.set_image_source("plus_img", "icons8-plus-32.png")
        self.set_image_source("minus_img", "icons8-minus-32.png")
        self.set_image_source("import_revit_img", "icons8-import-32.png")
        self.set_image_source("ok_img", "icons8-checkmark-32.png")
        self.set_image_source("save_img", "icons8-save-32.png")
        self.set_image_source("delete_img", "icons8-trash-32.png")
        self.set_image_source("duplicate_img", "icons8-copy-32.png")
        self.set_image_source("copy_img", "icons8-copy-32.png")
        self.set_image_source("paste_img", "icons8-paste-32.png")

        self.headerdict = {"name": "Name",
                           "parameter_type": "ParameterType",
                           "unit_type": "UnitType"}

        self.binding_headerdict = {"name": "Name",
                                   "category_type": "CategoryType",
                                   "unit_type": "UnitType",
                                   "is_bound": "IsBound?"}

        self.project_parameters_datagrid_content = ObservableCollection[object]()
        for project_parameter in ProjectParameter.read_from_revit_doc():
            self.project_parameters_datagrid_content.Add(project_parameter)
        self.datagrid.ItemsSource = self.project_parameters_datagrid_content

        self.category_datagrid_content = ObservableCollection[object]()
        for category in ProjectParameter.bound_allowed_category_generator():
            self.category_datagrid_content.Add(BoundAllowedCategory(category))
        self.category_datagrid.ItemsSource = self.category_datagrid_content

    # noinspection PyUnusedLocal
    def auto_generating_column(self, sender, e):
        # Generate only desired columns
        headername = e.Column.Header.ToString()
        if headername in self.headerdict.keys():
            e.Column.Header = self.headerdict[headername]
        else:
            e.Cancel = True

    # noinspection PyUnusedLocal
    def binding_auto_generating_column(self, sender, e):
        # Generate only desired columns
        headername = e.Column.Header.ToString()
        if headername in self.binding_headerdict.keys():
            e.Column.Header = self.binding_headerdict[headername]
        else:
            e.Cancel = True

    # noinspection PyUnusedLocal
    def auto_generated_columns(self, sender, e):
        pass

    # noinspection PyUnusedLocal
    def target_updated(self, sender, e):
        pass

    # noinspection PyUnusedLocal
    def ok_click(self, sender, e):
        with rpw.db.Transaction("Batch create shared parameters"):
            for parameter in self.data_grid_content:
                # TODO function to create parameters
                return

    # noinspection PyUnusedLocal
    def save_click(self, sender, e):
        pass

    # noinspection PyUnusedLocal
    def delete_click(self, sender, e):
        pass

    # noinspection PyUnusedLocal
    def duplicate_click(self, sender, e):
        pass

    # noinspection PyUnusedLocal
    def copy_binding_click(self, sender, e):
        pass

    # noinspection PyUnusedLocal
    def paste_binding_click(self, sender, e):
        pass

    # noinspection PyUnusedLocal
    def mouse_down(self, sender, e):
        for category in self.category_datagrid_content: # type: BoundAllowedCategory
            category.is_bound = False
        for bound_category in sender.SelectedItem.binding.Categories:
            for category in self.category_datagrid_content: # type: BoundAllowedCategory
                if bound_category.Name == category.name :
                    category.is_bound = True
        self.category_datagrid.Items.Refresh()

    # noinspection PyUnusedLocal
    def load_from_definition_file_click(self, sender, e):
        for parameter in SharedParameter.read_from_csv():
            self.data_grid_content.Add(parameter)

    # noinspection PyUnusedLocal
    def add(self, sender, e):
        self.data_grid_content.Add(SharedParameter("", "", ""))

    # noinspection PyUnusedLocal
    def remove(self, sender, e):
        for item in list(self.datagrid.SelectedItems):
            self.data_grid_content.Remove(item)

    # noinspection PyUnusedLocal
    def binding_click(self, sender, e):
        self.project_parameters_datagrid.SelectedItem


gui = Gui("WPFWindow.xaml")
gui.ShowDialog()
