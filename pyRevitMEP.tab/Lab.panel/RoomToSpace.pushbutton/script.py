# coding: utf8
import rpw
from rpw import revit
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, StorageType, UnitUtils
from pyrevit.forms import WPFWindow
from pyrevit import script

logger = script.get_logger()


def sample_id_by_category(doc, category):
    return FilteredElementCollector(doc).OfCategory(category).FirstElementId()

class Gui(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)

        # Add currently opened documents to dropdowns
        self.source_project.DataContext = revit.docs
        self.target_project.DataContext = revit.docs

        self.room_parameters_set = set()
        self.space_parameters_set = set()

        self.source_project.SelectedIndex = None
        self.target_project.SelectedIndex = None

    # noinspection PyUnusedLocal
    def source_project_changed(self, sender, e):
        doc = self.source_project.SelectedItem
        self.sample_room_id = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).FirstElementId()
        try:
            for parameter in doc.GetElement(self.sample_room_Id).Parameters:
                self.room_parameters_set.add(parameter.Definition.Name)
        except AttributeError:
            return
        logger.debug(self.room_parameters_set)

    # noinspection PyUnusedLocal
    def target_project_changed(self, sender, e):
        pass

    def service_check(self, number):
        return number in self.service_selection.SelectedItems or self.tous_services.IsChecked

    # noinspection PyUnusedLocal
    def window_closed(self, sender, e):
        pass

gui = Gui("WPFWindow.xaml")
gui.ShowDialog()
