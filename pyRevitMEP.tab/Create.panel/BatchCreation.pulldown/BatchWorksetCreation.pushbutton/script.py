# coding: utf8

import rpw
from rpw import revit
from pyrevit.forms import WPFWindow
from pypevitmep.workset import Workset
# noinspection PyUnresolvedReferences
from System.Collections.ObjectModel import ObservableCollection

__doc__ = "Batch create worksets from a text file or on the fly by creating a list"
__title__ = "Worksets"
__author__ = "Cyril Waechter"


class Gui(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.data_grid_content = ObservableCollection[object]()
        self.datagrid.ItemsSource = self.data_grid_content

        image_dict = {
            "plus_img": "icons8-plus-32.png",
            "minus_img": "icons8-minus-32.png",
            "import_img": "icons8-import-32.png",
            "ok_img": "icons8-checkmark-32.png"
        }

        for k, v in image_dict.items():
            self.set_image_source(getattr(self, k), v)

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


if not revit.doc.IsWorkshared:
    rpw.ui.forms.Alert("Current document is not workshared. You cannot create worksets.")
else:
    gui = Gui("WPFWindow.xaml")
    gui.ShowDialog()
