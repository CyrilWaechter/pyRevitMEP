# coding: utf8
import rpw
# noinspection PyUnresolvedReferences
from rpw import revit, DB, UI
# noinspection PyUnresolvedReferences
from Autodesk.Revit.Exceptions import InvalidOperationException
from scriptutils import logger
from scriptutils.userinput import WPFWindow
from pyRevitMEP.parameter import SharedParameter, ProjectParameter
# noinspection PyUnresolvedReferences
from System.Collections.ObjectModel import ObservableCollection

__doc__ = "Batch create project shared parameters from file"
__title__ = "BatchCreateSharedParameters"
__author__ = "Cyril Waechter"

doc = rpw.revit.doc
uidoc = rpw.uidoc

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
        self.set_image_source("import_img", "icons8-import-32.png")
        self.set_image_source("ok_img", "icons8-checkmark-32.png")

        self.project_parameters_datagrid_content = ObservableCollection[object]()
        for project_parameter in ProjectParameter.read_from_revit_doc():
            self.project_parameters_datagrid_content.Add(project_parameter)
        self.project_parameters_datagrid.ItemsSource = self.project_parameters_datagrid_content

    # noinspection PyUnusedLocal
    def ok_click(self, sender, e):
        with rpw.db.Transaction("Batch create shared parameters"):
            for parameter in self.data_grid_content:
                # TODO function to create parameters
                return

    # noinspection PyUnusedLocal
    def load_from_file_click(self, sender, e):
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
