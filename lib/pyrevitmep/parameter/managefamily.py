# coding: utf8
import os
import re
import tempfile

from System.ComponentModel import ListSortDirection, SortDescription
from System.Collections.ObjectModel import ObservableCollection

from Autodesk.Revit.ApplicationServices import Application
from Autodesk.Revit.DB import Document
from Autodesk.Revit import Exceptions

import rpw
from pyrevit import script
from pyrevit import forms
import rsparam

from pyrevitmep.parameter import FamilyParameter, SharedParameter, BipGroup, PType
from pyrevitmep.parameter.manageshared import ManageSharedParameter

app = rpw.revit.app  # type: Application
doc = rpw.revit.doc  # type: Document
uidoc = rpw.uidoc
logger = script.get_logger()


class ManageFamilyParameter(forms.WPFWindow):
    def __init__(self):
        file_dir = os.path.dirname(__file__)
        xaml_source = os.path.join(file_dir, "managefamily.xaml")
        forms.WPFWindow.__init__(self, xaml_source)

        # Set icons
        image_dict = {"ok_img": "icons8-checkmark-32.png",
                      "add_img": "icons8-plus-32.png",
                      "minus_img": "icons8-minus-32.png",
                      "duplicate_img": "icons8-copy-32.png",
                      "revit_family_img": "revit_family.png",
                      "shared_parameter_img": "shared_parameter.png"
                      }
        for k, v in image_dict.items():
            self.set_image_source(getattr(self, k), os.path.join(file_dir, v))

        # Read existing project parameters and add it to datagrid
        self.family_parameters = ObservableCollection[object]()
        for family_parameter in FamilyParameter.read_from_revit_doc():
            self.family_parameters.Add(family_parameter)
        self.datagrid.ItemsSource = self.family_parameters
        self.parameter_types = sorted([PType(ptype) for ptype in PType.enum_generator()])
        self.parameter_groups = sorted([BipGroup(bip_group) for bip_group in BipGroup.enum_generator()])

        self._new_key_number = 0
        self.to_delete = set()

        self.sort_datagrid(self.datagrid)

    def setup_icon(self):
        """Setup custom icon."""
        iconpath = os.path.join(os.path.dirname(__file__), 'family_parameter.png')
        self.Icon = forms.utils.bitmap_from_file(iconpath)

    @property
    def new_key_number(self):
        self._new_key_number += 1
        return self._new_key_number

    @staticmethod
    def sort_datagrid(datagrid, column_index=0, list_sort_direction=ListSortDirection.Ascending):
        # type: (DataGrid, int, ListSortDirection) -> None
        """Method use to set actual initial sort.
        cf. https://stackoverflow.com/questions/16956251/sort-a-wpf-datagrid-programmatically"""
        column = datagrid.Columns[column_index]

        # Clear current sort descriptions
        datagrid.Items.SortDescriptions.Clear()

        # Add the new sort description
        datagrid.Items.SortDescriptions.Add(SortDescription(column.SortMemberPath, list_sort_direction))

        # Apply sort
        for col in datagrid.Columns:
            col.SortDirection = None
        column.SortDirection = list_sort_direction

        # Refresh items to display sort
        datagrid.Items.Refresh()

    # noinspection PyUnusedLocal
    def ok_click(self, sender, e):
        with rpw.db.Transaction("Modify family parameters"):
            for parameter in self.family_parameters:  # type: FamilyParameter
                try:
                    parameter.save_to_revit(doc)
                except Exceptions.ArgumentException:
                    logger.info("FAILED to save {}".format(parameter.name))
                    logger.debug(type(parameter.group.enum_member))

            for parameter in self.to_delete:
                parameter.delete_from_revit(doc)

        # Clean definition file from temporary created external definitions
        src_file = SharedParameter.get_definition_file().Filename
        if script.coreutils.check_revittxt_encoding(src_file):
            encoding = "utf_16_le"
        else:
            encoding = "utf_8"
        entries = rsparam.read_entries(src_file, encoding)
        for group in entries.groups:
            if group.name == "pyFamilyManager":
                for parameter in entries.params:
                    if parameter.group == group:
                        entries.params.remove(parameter)
                entries.groups.remove(group)
                rsparam.write_entries(entries, src_file, encoding)
        self.Close()

    # noinspection PyUnusedLocal
    def add_click(self, sender, e):
        # Iterate an index at the end if parameter name already exist
        base_name = "New"
        index = 1
        new_name = "{}{}".format(base_name, index)
        while new_name in [item.name for item in list(self.datagrid.Items)]:
            index += 1
            new_name = "{}{}".format(base_name, index)
        # Add parameter to the DataGrid
        self.family_parameters.Add(FamilyParameter(name=new_name, is_new=True))

    # noinspection PyUnusedLocal
    def minus_click(self, sender, e):
        for family_parameter in list(self.datagrid.SelectedItems):  # type: FamilyParameter
            if not family_parameter.is_new:
                self.to_delete.add(family_parameter)
            self.family_parameters.Remove(family_parameter)

    # noinspection PyUnusedLocal
    def duplicate_click(self, sender, e):
        for item in self.datagrid.SelectedItems:  # type: FamilyParameter
            # Iterate an index at the end if parameter name already exist
            try:
                base_name = re.match('(.*?)([0-9]+)$', item.name).group(1)
                index = int(re.match('(.*?)([0-9]+)$', item.name).group(2)) + 1
            except AttributeError:
                base_name = item.name
                index = 1
            new_name = "{}{}".format(base_name, index)
            while new_name in [item.name for item in list(self.datagrid.Items)]:
                index += 1
                new_name = "{}{}".format(base_name, index)

            # Add parameter to the DataGrid
            self.family_parameters.Add(
                FamilyParameter(new_name, type=item.type, group=item.group, is_instance=item.is_instance, is_new=True))

    # noinspection PyUnusedLocal
    def import_from_family_click(self, sender, e):
        family_doc = rpw.ui.forms.SelectFromList("Select source family",
                                                 {doc.Title: doc for doc in rpw.revit.docs if doc.IsFamilyDocument},
                                                 exit_on_close=False)
        if not family_doc:
            return
        for family_parameter in FamilyParameter.read_from_revit_doc(family_doc):
            if family_parameter not in self.family_parameters:
                family_parameter.is_new = True
                self.family_parameters.Add(family_parameter)

    # noinspection PyUnusedLocal
    def import_from_shared_click(self, sender, e):
        try:
            for definition in ManageSharedParameter.show_dialog():  # type: ExternalDefinition
                family_parameter = FamilyParameter.new_from_shared(definition)
                if family_parameter not in self.family_parameters:
                    self.family_parameters.Add(family_parameter)
        except TypeError:
            return

    # noinspection PyUnusedLocal
    def target_updated(self, sender, e):
        attribute = self.datagrid.CurrentColumn.SortMemberPath
        current_value = getattr(self.datagrid.CurrentItem, attribute)
        for item in self.datagrid.SelectedItems:  # type: FamilyParameter
            setattr(item, attribute, current_value)
            item.modified = True
        self.datagrid.Items.Refresh()

    @classmethod
    def show_dialog(cls):
        if not doc.IsFamilyDocument:
            forms.alert("This tool works with family documents only. Not project documents.")
            import sys
            sys.exit()
        gui = cls()
        gui.ShowDialog()
        return


if __name__ == '__main__':
    ManageFamilyParameter.show_dialog()
