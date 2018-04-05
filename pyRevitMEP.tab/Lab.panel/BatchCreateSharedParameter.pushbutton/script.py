# coding: utf8
import rpw
# noinspection PyUnresolvedReferences
from rpw import revit
# noinspection PyUnresolvedReferences
from Autodesk.Revit.Exceptions import InvalidOperationException
from pyrevit.script import get_logger
from pyrevit.forms import WPFWindow, SelectFromList
from pyRevitMEP.parameter import SharedParameter
# noinspection PyUnresolvedReferences
from System.Collections.ObjectModel import ObservableCollection

__doc__ = "Batch create project shared parameters from file"
__title__ = "BatchCreateSharedParameters"
__author__ = "Cyril Waechter"

doc = rpw.revit.doc
uidoc = rpw.uidoc
logger = get_logger()


class Gui(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.data_grid_content = ObservableCollection[object]()
        # self.datagrid.AutoGeneratingColumn =
        self.datagrid.ItemsSource = self.data_grid_content
        self.set_image_source("plus_img", "icons8-plus-32.png")
        self.set_image_source("minus_img", "icons8-minus-32.png")
        self.set_image_source("import_img", "icons8-import-32.png")
        self.set_image_source("import_revit_img", "icons8-import-32.png")
        self.set_image_source("ok_img", "icons8-checkmark-32.png")
        self.set_image_source("save_img", "icons8-save-32.png")

    def auto_generating_column(self, sender, e):
        headername = e.Column.Header.ToString()
        headerdict = {"name": "Name",
                      "type": "Type",
                      "group": "Group",
                      "guid": "Guid",
                      "description": "Description",
                      "modifiable": "UserModifiable",
                      "visible": "Visible"}
        if headername in headerdict.keys():
            e.Column.Header = headerdict[headername]
        else:
            e.Cancel = True

    # noinspection PyUnusedLocal
    def ok_click(self, sender, e):
        """Return listed definitions"""
        self.Close()
        return self.data_grid_content

    # noinspection PyUnusedLocal
    def save_click(self, sender, e):
        """Return listed definitions"""
        for parameter in self.data_grid_content:
            return self.data_grid_content

    # noinspection PyUnusedLocal
    def load_from_file_click(self, sender, e):
        try:
            for parameter in SharedParameter.read_from_csv():
                self.data_grid_content.Add(parameter)
        except ValueError:
            return

    # noinspection PyUnusedLocal
    def load_from_definition_file_click(self, sender, e):
        available_groups = SharedParameter.get_definition_file().Groups
        groups = SelectFromList(available_groups, "Select groups", 200, 200).show_dialog()
        try:
            for parameter in SharedParameter.read_from_definition_file(definition_groups=groups):
                self.data_grid_content.Add(parameter)
        except LookupError as e:
            logger.info(e)

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

    @classmethod
    def show_dialog(cls):
        gui = Gui("WPFWindow.xaml")
        gui.ShowDialog()

        return gui.data_grid_content

if __name__ == '__main__':
    definitions = Gui.show_dialog()
    for d in definitions:
        logger.debug(d)

