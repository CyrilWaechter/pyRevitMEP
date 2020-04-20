# coding: utf8

import os
import locale
import re
import inspect

from Autodesk.Revit import Exceptions
from Autodesk.Revit.DB import ParameterType

from pyrevit.script import get_logger
from pyrevit.forms import WPFWindow, SelectFromList, alert, utils

import rsparam

from pyrevitmep.parameter import SharedParameter

from System.Collections.ObjectModel import ObservableCollection
from System.Windows.Controls import DataGrid
from System.ComponentModel import ListSortDirection, SortDescription

logger = get_logger()


class ManageSharedParameter(WPFWindow):
    parameter_types = ParameterType.GetValues(ParameterType)

    def __init__(self):
        file_dir = os.path.dirname(__file__)
        xaml_source = os.path.join(file_dir, "manageshared.xaml")
        WPFWindow.__init__(self, xaml_source)
        self.data_grid_content = ObservableCollection[object]()
        self.datagrid.ItemsSource = self.data_grid_content

        image_dict = {
            "plus_img": "icons8-plus-32.png",
            "minus_img": "icons8-minus-32.png",
            "import_csv_img": "icons8-csv-32.png",
            "import_revit_img": "icons8-import-32.png",
            "ok_img": "icons8-checkmark-32.png",
            "save_img": "icons8-save-32.png",
            "delete_img": "icons8-trash-32.png",
            "new_file_img": "icons8-file-32.png",
            "open_file_img": "icons8-open-32.png",
            "duplicate_img": "icons8-copy-32.png",
        }
        for k, v in image_dict.items():
            self.set_image_source(getattr(self, k), os.path.join(file_dir, v))

        self.tbk_file_name.DataContext = self.definition_file

        self.bool_return_parameters = False

        self.sort_datagrid(self.datagrid, 1)

    def setup_icon(self):
        """Setup custom icon."""
        iconpath = os.path.join(os.path.dirname(__file__), "shared_parameter.png")
        self.Icon = utils.bitmap_from_file(iconpath)

    @property
    def definition_file(self):
        return SharedParameter.get_definition_file()

    @definition_file.setter
    def definition_file(self, value):
        self.tbk_file_name.DataContext = value
        self._definition_file = value

    @property
    def definition_file_path(self):
        return self.tbk_file_name.Text

    @staticmethod
    def invalid_definition_file():
        alert("Invalid definition file. Operation canceled.")

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
                    logger.info(
                        "[{}] Failed to write {}".format(
                            inspect.stack()[1][3], parameter.name
                        )
                    )
            elif parameter.new is False and parameter.changed is True:
                logger.debug(parameter.initial_values)
                todelete.append(SharedParameter(**parameter.initial_values))
                tocreate.append(parameter)
        SharedParameter.delete_from_definition_file(todelete, self.definition_file_path)
        for parameter in tocreate:
            parameter.write_to_definition_file()  # do not specify definition file to force reopening it after deletions
        self.datagrid.Items.Refresh()

    # noinspection PyUnusedLocal
    def delete_click(self, sender, e):
        """Delete definitions from definition file"""
        definition_file = self.definition_file
        if not definition_file:
            self.invalid_definition_file()
            return
        confirmed = alert(
            "Are you sur you want to delete followinge parameters : \n{}".format(
                "\n".join([item.name for item in self.datagrid.SelectedItems])
            ),
            "Delete parameters ?",
            yes=True,
            no=True,
        )
        if not confirmed:
            return
        for item in list(self.datagrid.SelectedItems):
            SharedParameter.delete_from_definition_file(
                self.datagrid.SelectedItems, definition_file
            )
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
        try:
            groups = rsparam.get_paramgroups(
                self.definition_file_path, encoding="utf-16"
            )
            available_groups = sorted(groups, key=lambda x: locale.strxfrm(x.name))
        except IOError:
            self.invalid_definition_file()
            return
        # available_groups = sorted(definition_file.Groups, key=lambda x: locale.strxfrm(x.Name))
        selected_groups = SelectFromList.show(
            available_groups,
            "Select groups",
            400,
            300,
            name_attr="name",
            multiselect=True,
        )
        logger.debug("{} result = {}".format(SelectFromList.__name__, selected_groups))

        if selected_groups is None:
            return

        try:
            for parameter in rsparam.get_params(
                self.definition_file_path, encoding="utf-16"
            ):
                if parameter.group in selected_groups:
                    self.data_grid_content.Add(SharedParameter.from_rsparam(parameter))
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
        """Duplicate selected shared parameters"""
        for item in list(self.datagrid.SelectedItems):  # type: SharedParameter
            # Iterate an index at the end if parameter name already exist
            try:
                base_name = re.match("(.*?)([0-9]+)$", item.name).group(1)
                index = int(re.match("(.*?)([0-9]+)$", item.name).group(2)) + 1
            except AttributeError:
                base_name = item.name
                index = 1
            new_name = "{}{}".format(base_name, index)
            while new_name in [item.name for item in list(self.datagrid.Items)]:
                index += 1
                new_name = "{}{}".format(base_name, index)
            # Add parameter to the DataGrid
            args = (
                new_name,
                item.type,
                item.group,
                None,
                item.description,
                item.modifiable,
                item.visible,
                True,
            )
            self.data_grid_content.Add(SharedParameter(*args))

    # noinspection PyUnusedLocal
    def target_updated(self, sender, e):
        attribute = self.datagrid.CurrentColumn.SortMemberPath
        current_value = getattr(self.datagrid.CurrentItem, attribute)
        for item in self.datagrid.SelectedItems:
            setattr(item, attribute, current_value)
            item.changed = True
        self.datagrid.Items.Refresh()

    @staticmethod
    def sort_datagrid(
        datagrid, column_index=0, list_sort_direction=ListSortDirection.Ascending
    ):
        # type: (DataGrid, int, ListSortDirection) -> None
        """Method use to set actual initial sort.
        cf. https://stackoverflow.com/questions/16956251/sort-a-wpf-datagrid-programmatically"""
        column = datagrid.Columns[column_index]

        # Clear current sort descriptions
        datagrid.Items.SortDescriptions.Clear()

        # Add the new sort description
        datagrid.Items.SortDescriptions.Add(
            SortDescription(column.SortMemberPath, list_sort_direction)
        )

        # Apply sort
        for col in datagrid.Columns:
            col.SortDirection = None
        column.SortDirection = list_sort_direction

        # Refresh items to display sort
        datagrid.Items.Refresh()

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
        # type: () -> List[Definition]
        gui = cls()
        gui.ShowDialog()
        if gui.bool_return_parameters:
            return [
                shared_parameter.get_definition(gui.definition_file)
                for shared_parameter in gui.data_grid_content
            ]


if __name__ == "__main__":
    definitions = ManageSharedParameter.show_dialog()
