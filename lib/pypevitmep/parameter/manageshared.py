# coding: utf8

import os
import locale
from functools import cmp_to_key

from Autodesk.Revit import Exceptions
from Autodesk.Revit.DB import DefinitionFile

from pyrevit.script import get_logger
from pyrevit.forms import WPFWindow, SelectFromList, alert

from pypevitmep.parameter import SharedParameter

from System.Collections.ObjectModel import ObservableCollection

logger = get_logger()


class ManageSharedParameter(WPFWindow):
    def __init__(self):
        file_dir = os.path.dirname(__file__)
        xaml_source = os.path.join(file_dir, "manageshared.xaml")
        WPFWindow.__init__(self, xaml_source)
        self.data_grid_content = ObservableCollection[object]()
        self.datagrid.ItemsSource = self.data_grid_content

        image_dict = {"plus_img": "icons8-plus-32.png",
                      "minus_img": "icons8-minus-32.png",
                      "import_csv_img": "icons8-csv-32.png",
                      "import_revit_img": "icons8-import-32.png",
                      "ok_img": "icons8-checkmark-32.png",
                      "save_img": "icons8-save-32.png",
                      "delete_img": "icons8-trash-32.png",
                      "new_file_img": "icons8-file-32.png",
                      "open_file_img": "icons8-open-32.png",
                      "duplicate_img": "icons8-copy-32.png"}
        for k, v in image_dict.items():
            self.set_image_source(getattr(self, k), os.path.join(file_dir, v))

        self.headerdict = {"name": "Name",
                           "type": "Type",
                           "group": "Group",
                           "guid": "Guid",
                           "description": "Description",
                           "modifiable": "UserModifiable",
                           "visible": "Visible"}
        self.tbk_file_name.DataContext = self.definition_file

        self.bool_return_parameters = False

    @property
    def definition_file(self):
        return SharedParameter.get_definition_file()

    @definition_file.setter
    def definition_file(self, value):
        self.tbk_file_name.DataContext = value
        self._definition_file = value

    @staticmethod
    def invalid_definition_file():
        alert("Invalid definition file. Operation canceled.")

    # noinspection PyUnusedLocal
    def auto_generating_column(self, sender, e):
        # Generate only desired columns
        headername = e.Column.Header.ToString()
        if headername in self.headerdict.keys():
            e.Column.Header = self.headerdict[headername]
        else:
            e.Cancel = True

    # noinspection PyUnusedLocal
    def auto_generated_columns(self, sender, e):
        # Sort column in desired way
        for column in self.datagrid.Columns:
            headerindex = {"Name": 0,
                           "Type": 1,
                           "Group": 2,
                           "Guid": 3,
                           "Description": 4,
                           "UserModifiable": 5,
                           "Visible": 6}
            column.DisplayIndex = headerindex[column.Header.ToString()]

    # noinspection PyUnusedLocal
    def ok_click(self, sender, e):
        """Return listed definitions"""
        self.save_click(sender, e)
        self.bool_return_parameters = True
        self.Close()

    # noinspection PyUnusedLocal
    def save_click(self, sender, e):
        """Save ExternalDefinitions to DefinitionFile"""
        definition_file = self.definition_file
        if not definition_file:
            self.invalid_definition_file()
            return
        tocreate = []
        todelete = []
        for parameter in self.data_grid_content:  # type: SharedParameter
            if parameter.new:
                try:
                    parameter.write_to_definition_file(definition_file)
                except Exceptions.InvalidOperationException:
                    logger.info("Failed to write {}".format(parameter.name))
            elif parameter.new is False and parameter.changed is True:
                todelete.append(SharedParameter(**parameter.initial_values))
                tocreate.append(parameter)
        SharedParameter.delete_from_definition_file(todelete, definition_file)
        for parameter in tocreate:
            parameter.write_to_definition_file(definition_file)

    # noinspection PyUnusedLocal
    def delete_click(self, sender, e):
        """Delete definitions from definition file"""
        definition_file = self.definition_file
        if not definition_file:
            self.invalid_definition_file()
            return
        confirmed = alert(
            "Are you sur you want to delete followinge parameters : \n{}".format(
                "\n".join([item.name for item in self.datagrid.SelectedItems])),
            "Delete parameters ?",
            yes=True, no=True
        )
        if not confirmed:
            return
        for item in list(self.datagrid.SelectedItems):
            SharedParameter.delete_from_definition_file(self.datagrid.SelectedItems, definition_file)
            self.data_grid_content.Remove(item)

    # noinspection PyUnusedLocal
    def load_from_csv_click(self, sender, e):
        try:
            for parameter in SharedParameter.read_from_csv():
                self.data_grid_content.Add(parameter)
        except ValueError:
            return

    # noinspection PyUnusedLocal
    def load_from_definition_file_click(self, sender, e):
        definition_file = self.definition_file
        if not definition_file:
            self.invalid_definition_file()
            return

        available_groups = sorted([group.Name for group in definition_file.Groups], key=cmp_to_key(locale.strcoll))
        selected_groups = SelectFromList.show(available_groups, "Select groups", 400, 300)
        logger.debug("{} result = {}".format(SelectFromList.__name__, selected_groups))
        if selected_groups is None:
            return
        else:
            groups = [definition_file.Groups[group] for group in selected_groups]
        try:
            for parameter in SharedParameter.read_from_definition_file(definition_groups=groups):
                self.data_grid_content.Add(parameter)
        except LookupError as e:
            logger.info(e)

    # noinspection PyUnusedLocal
    def add(self, sender, e):
        self.data_grid_content.Add(SharedParameter("", ""))

    # noinspection PyUnusedLocal
    def remove(self, sender, e):
        for item in list(self.datagrid.SelectedItems):
            self.data_grid_content.Remove(item)

    # noinspection PyUnusedLocal
    def duplicate(self, sender, e):
        for item in list(self.datagrid.SelectedItems):  # type: SharedParameter
            args = ("{}1".format(item.name), item.type, item.group, None,
                    item.description, item.modifiable, item.visible, True)
            self.data_grid_content.Add(SharedParameter(*args))

    # noinspection PyUnusedLocal
    def target_updated(self, sender, e):
        e.Row.Item.changed = True

    # noinspection PyUnusedLocal
    def new_definition_file_click(self, sender, e):
        self.definition_file = SharedParameter.create_definition_file()
        for parameter in self.data_grid_content:  # type: SharedParameter
            parameter.new = True

    # noinspection PyUnusedLocal
    def open_definition_file_click(self, sender, e):
        definition_file = SharedParameter.change_definition_file()
        if definition_file:
            self.definition_file = definition_file
            for parameter in self.data_grid_content:  # type: SharedParameter
                parameter.new = True

    @classmethod
    def show_dialog(cls):
        gui = cls()
        gui.ShowDialog()
        if gui.bool_return_parameters:
            return [shared_parameter.get_definition(gui.definition_file) for shared_parameter in gui.data_grid_content]

if __name__ == '__main__':
    definitions = ManageSharedParameter.show_dialog()
