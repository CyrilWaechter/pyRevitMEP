# coding: utf8
import os

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
                      "save_img": "icons8-save-32.png",
                      "delete_img": "icons8-trash-32.png",
                      "copy_img": "icons8-copy-32.png"}
        for k, v in image_dict.items():
            self.set_image_source(k, os.path.join(file_dir, v))

        self.headerdict = {"name": "Name",
                           "type": "Type",
                           "group": "Group",
                           "is_shared": "IsShared?",
                           "is_instance": "Instance?"}

        self.binding_headerdict = {"name": "Name",
                                   "category_type": "CategoryType",
                                   "is_bound": "IsBound?"}

        # Read existing project parameters and add it to datagrid
        self.project_parameters_datagrid_content = ObservableCollection[object]()
        for project_parameter in sorted([fp for fp in FamilyParameter.read_from_revit_doc()], key=lambda o: o.name):
            self.project_parameters_datagrid_content.Add(project_parameter)
        self.datagrid.ItemsSource = self.project_parameters_datagrid_content


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
        self.save_click(sender, e)
        self.Close()

    # noinspection PyUnusedLocal
    def save_click(self, sender, e):
        with rpw.db.Transaction("Save project parameters"):
            for projectparam in self.project_parameters_datagrid_content:  # type: ProjectParameter
                bindingmap = doc.ParameterBindings  # type: BindingMap
                try:
                    projectparam.save_to_revit_doc()
                except Exceptions.ArgumentException:
                    logger.info("Saving {} failed. At least 1 category must be selected.".format(projectparam))

    # noinspection PyUnusedLocal
    def delete_click(self, sender, e):
        with rpw.db.Transaction("Delete project parameters"):
            for projectparam in list(self.datagrid.SelectedItems):  # type: ProjectParameter
                doc.ParameterBindings.Remove(projectparam.definition)
                self.project_parameters_datagrid_content.Remove(projectparam)

    # noinspection PyUnusedLocal
    def copy_click(self, sender, e):
        self.memory_categories = CategorySet()
        for category in self.category_datagrid_content:  # type: BoundAllowedCategory
            if category.is_bound:
                self.memory_categories.Insert(category.category)

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
