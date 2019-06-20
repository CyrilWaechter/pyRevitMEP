# coding: utf8

import rpw
from rpw import revit, DB
from Autodesk.Revit.DB.Plumbing import PipingSystemType
from pyrevit.forms import WPFWindow
from pyrevitmep.workset import Workset
# noinspection PyUnresolvedReferences
from System.Collections.ObjectModel import ObservableCollection

__doc__ = "Batch create worksets from a text file or on the fly by creating a list"
__title__ = "ManageSystems"
__author__ = "Cyril Waechter"


class ManageSystems(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        #
        self.data_grid_content = ObservableCollection[PipingSystemType](DB.FilteredElementCollector(revit.doc)
                                                              .OfClass(PipingSystemType))
        self.datagrid.ItemsSource = self.data_grid_content

        # Set icons
        image_dict = {
            "plus_img": "icons8-plus-32.png",
            "minus_img": "icons8-minus-32.png",
            "import_img": "icons8-import-32.png",
            "ok_img": "icons8-checkmark-32.png"
        }

        for k, v in image_dict.items():
            self.set_image_source(getattr(self, k), v)

    # Set empty external system list source
        self.data_grid_imported_content = ObservableCollection[PipingSystemType]()
        self.datagrid_imported.ItemsSource = self.data_grid_imported_content

    # noinspection PyUnusedLocal
    def ok_click(self, sender, e):
        with rpw.db.Transaction("Batch workset creation"):
            for workset in self.data_grid_content:
                workset.create()

    # noinspection PyUnusedLocal
    def load_from_file_click(self, sender, e):
        for workset in Workset.read_from_txt():
            self.data_grid_content.Add(workset)

    # noinspection PyUnusedLocal
    def add(self, sender, e):
        self.data_grid_content.Add(Workset(""))

    # noinspection PyUnusedLocal
    def remove(self, sender, e):
        for item in list(self.datagrid.SelectedItems):
            self.data_grid_content.Remove(item)


gui = ManageSystems("ManageSystems.xaml")
gui.ShowDialog()
