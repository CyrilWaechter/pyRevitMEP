# coding: utf8
import os
from string import digits

from System.Windows.Controls import DataGridComboBoxColumn
from System.Windows.Data import Binding
from System.ComponentModel import ListSortDirection, SortDescription
from System.Collections.ObjectModel import ObservableCollection

from Autodesk.Revit.ApplicationServices import Application
from Autodesk.Revit.DB import Document, BindingMap, ElementBinding, CategorySet
from Autodesk.Revit import Exceptions

import rpw
from pyrevit import script
from pyrevit import forms

from pypevitmep.parameter import FamilyParameter, BoundAllowedCategory, BipGroup, PType
from pypevitmep.parameter.manageshared import ManageSharedParameter

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
                      "copy_img": "icons8-copy-32.png",
                      "revit_family_img": "revit_family.png",
                      "shared_parameter_img": "shared_parameter.png"
                      }
        for k, v in image_dict.items():
            self.set_image_source(getattr(self, k), os.path.join(file_dir, v))

        self.headerdict = {"name": "Name",
                           "type": "Type",
                           "group": "Group",
                           "is_shared": "IsShared?",
                           "is_instance": "Instance?"}

        self.binding_headerdict = {"name": "Name",
                                   "category_type": "CategoryType",
                                   "is_bound": "IsBound?"}

        # Read existing project parameters and add it to datagrid
        self.family_parameters = ObservableCollection[object]()
        for project_parameter in sorted([fp for fp in FamilyParameter.read_from_revit_doc()], key=lambda o: o.name):
            self.family_parameters.Add(project_parameter)
        self.datagrid.ItemsSource = self.family_parameters

        self._new_key_number = 0
        self.to_delete = set()

    @property
    def new_key_number(self):
        self._new_key_number += 1
        return  self._new_key_number

    # noinspection PyUnusedLocal
    def auto_generating_column(self, sender, e):
        # Generate only desired columns
        headername = e.Column.Header.ToString()
        if headername in self.headerdict.keys():
            if headername == "group":
                cb = DataGridComboBoxColumn()
                cb.ItemsSource = sorted([BipGroup(fp) for fp in BipGroup.enum_generator()])
                cb.SelectedItemBinding = Binding(headername)
                cb.SelectedValuePath = "group"
                e.Column = cb
            elif headername == "type":
                cb = DataGridComboBoxColumn()
                cb.ItemsSource = sorted([PType(fp) for fp in PType.enum_generator()])
                cb.SelectedItemBinding = Binding(headername)
                cb.SelectedValuePath = "type"
                e.Column = cb
            else:
                # e.Column.IsReadOnly = True
                pass
            e.Column.Header = self.headerdict[headername]
        else:
            e.Cancel = True

    # noinspection PyUnusedLocal
    def auto_generated_columns(self, sender, e):
        # Sort column in desired way
        for column in sender.Columns:
            headerindex = {"Name": 0,
                           "Type": 1,
                           "Group": 2,
                           "Instance?": 3,
                           "IsShared?": 3}
            column.DisplayIndex = headerindex[str(column.Header)]

    @staticmethod
    def sortdatagrid(datagrid, columnindex=0, sortdirection=ListSortDirection.Ascending):
        """Sort a datagrid. Cf. https://stackoverflow.com/questions/16956251/sort-a-wpf-datagrid-programmatically"""
        column = datagrid.Columns(columnindex)
        datagrid.Items.SortDescription.Clear()
        datagrid.Items.SortDescription.Add(SortDescription(column.SortMemberPath, sortdirection))
        for col in datagrid.Columns:
            col.SortDirection = None
        column.SortDirection = sortdirection
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
        self.Close()

    # noinspection PyUnusedLocal
    def add_click(self, sender, e):
        self.family_parameters.Add(FamilyParameter("New {}".format(self.new_key_number), is_new=True))

    # noinspection PyUnusedLocal
    def minus_click(self, sender, e):
        for family_parameter in list(self.datagrid.SelectedItems):  # type: FamilyParameter
            if not family_parameter.is_new:
                self.to_delete.add(family_parameter)
            self.family_parameters.Remove(family_parameter)

    # noinspection PyUnusedLocal
    def copy_click(self, sender, e):
        for family_parameter in self.datagrid.SelectedItems:  # type: FamilyParameter
            new_name = "{}{}".format(family_parameter.name.translate(None, digits), self.new_key_number)
            new_family_parameter = FamilyParameter(new_name, is_new=True, type=family_parameter.type,
                                                   group=family_parameter.group)
            self.family_parameters.Add(new_family_parameter)

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
        e.Row.Item.modified = True

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
