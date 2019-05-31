# coding: utf8

import rpw
# noinspection PyUnresolvedReferences
from rpw import revit, DB
from pyrevit.forms import WPFWindow
from pyrevit import script
from pyrevitmep.workset import Workset
# noinspection PyUnresolvedReferences
from System.Collections.ObjectModel import ObservableCollection

__doc__ = "Batch create dependent views corresponding to existing Scope Boxes for selected views"
__title__ = "DependentViews"
__author__ = "Cyril Waechter"
__context__ = "selection"

doc = rpw.revit.doc
logger = script.get_logger()

class Gui(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        volume_of_interest = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_VolumeOfInterest)
        self.data_grid_content = ObservableCollection[object](volume_of_interest)
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
        for view_id in rpw.uidoc.Selection.GetElementIds():
            view = doc.GetElement(view_id)
            try:
                with rpw.db.Transaction("BatchCreateDependentViews"):
                    for volume_of_interest in self.data_grid_content:
                        new_view_id = view.Duplicate(DB.ViewDuplicateOption.AsDependent)
                        new_view = doc.GetElement(new_view_id)
                        parameter = new_view.get_Parameter(DB.BuiltInParameter.VIEWER_VOLUME_OF_INTEREST_CROP)
                        parameter.Set(volume_of_interest.Id)
            except AttributeError as e:
                print("{} doesn't seem to be a view".format(view))
                logger.debug("{}".format(e.message))


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


gui = Gui("WPFWindow.xaml")
gui.ShowDialog()
