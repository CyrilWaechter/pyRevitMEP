# coding: utf8
import rpw
# noinspection PyUnresolvedReferences
from rpw import revit, DB, UI
from scriptutils.forms import WPFWindow
# noinspection PyUnresolvedReferences
from System.Collections.ObjectModel import ObservableCollection
import os


class Category:
    def __init__(self, built_in_name):
        self.built_in_name = built_in_name
        self.category = DB.Category.GetCategory(revit.doc, built_in_name)

    @staticmethod
    def selection_window():
        gui = Gui(os.path.join(os.path.dirname(__file__),"category/WPFWindow.xaml"))
        gui.ShowDialog()


class Gui(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.categories = ObservableCollection[object]()
        for category in revit.doc.Settings.Categories:
            if category.AllowsBoundParameters:
                self.categories.Add(category)
        self.datagrid.ItemsSource = self.categories

