# coding: utf8
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Transaction
from pyrevit.forms import WPFWindow
from pyrevit import script, forms, revit

__title__ = "RoomToSpace"
__author__ = "Cyril Waechter"
__doc__ = "Copy parameters from linked or other project rooms to current project spaces"

logger = script.get_logger()


def sample_id_by_category(doc, category):
    return FilteredElementCollector(doc).OfCategory(category).FirstElementId()


def sample_element_by_category(doc, category):
    return FilteredElementCollector(doc).OfCategory(category).FirstElement()


class Gui(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)

        # Add currently opened documents to dropdowns
        source_projects = [
            doc
            for doc in revit.docs
            if sample_element_by_category(doc, BuiltInCategory.OST_Rooms)
        ]
        target_projects = [
            doc
            for doc in revit.docs
            if sample_element_by_category(doc, BuiltInCategory.OST_MEPSpaces)
        ]
        self.source_project.DataContext = source_projects
        self.target_project.DataContext = target_projects

        self.sample_room_id = None
        self.sample_space_id = None

        self.room_parameters_set = set()
        self.space_parameters_set = set()

        if not len(source_projects) > 0:
            forms.alert(
                "Error : You need to have at least 1 link or 1 other document opened containing rooms.",
                exitscript=True,
            )
        if not len(target_projects) > 0:
            forms.alert(
                "Error : You need to have at least 1 document opened containing spaces.",
                exitscript=True,
            )
        self.space_initialise(revit.doc)
        self.target_project.SelectedItem = revit.doc

    def room_initialise(self, doc):
        logger.info("Initialise room")
        self.sample_room_id = (
            FilteredElementCollector(doc)
            .OfCategory(BuiltInCategory.OST_Rooms)
            .FirstElementId()
        )
        try:
            for parameter in doc.GetElement(self.sample_room_Id).Parameters:
                self.room_parameters_set.add(parameter.Definition.Name)
        except AttributeError:
            return
        logger.debug(
            "ROOM PARAMETER SET : {} \n ROOM ID : {}".format(
                self.room_parameters_set, self.sample_room_id
            )
        )

    def space_initialise(self, doc):
        logger.info("Initialise space")
        self.sample_space_id = (
            FilteredElementCollector(doc)
            .OfCategory(BuiltInCategory.OST_MEPSpaces)
            .FirstElementId()
        )
        try:
            for parameter in doc.GetElement(self.sample_space_Id).Parameters:
                self.space_parameters_set.add(parameter.Definition.Name)
        except AttributeError:
            return
        logger.debug(
            "SPACE PARAMETER SET : {} \n SPACE ID : {}".format(
                self.space_parameters_set, self.sample_space_id
            )
        )

    def room_to_space(self, room, space):
        if not room:
            raise ValueError("There is no room in source project")
        if not space:
            raise ValueError("There is no space in target project")
        room_attributes = self.source_parameters.Text.replace("\r", "")
        space_parameters = self.target_parameters.Text.replace("\r", "")
        logger.debug(space_parameters.Split("\n"))
        for room_field, space_param in zip(
            room_attributes.Split("\n"), space_parameters.Split("\n")
        ):
            space_param = space_param
            value = ""
            for room_attr in room_field.split("\t"):
                room_attr = room_attr
                param = room.LookupParameter(room_attr)
                if param:
                    if param.AsString():
                        value += param.AsString()
                else:
                    value += room_attr
            space_param = space.LookupParameter(space_param)
            if space_param:
                space_param.Set(value)
            else:
                logger.info(
                    "Failed to find a parameter on space with name : {}, {}".format(
                        space_param, len(space_param)
                    )
                )

    # noinspection PyUnusedLocal
    def ok_click(self, sender, e):
        room_doc = self.source_project.SelectedItem
        space_doc = self.target_project.SelectedItem
        if space_doc.IsLinked:
            forms.alert("Target cannot be a linked model")
            return
        room = room_doc.GetElement(self.sample_room_id)
        space = space_doc.GetElement(self.sample_space_id)

        # Try RoomToSpace with sample room and space to make sure it works before batch on all with all spaces
        try:
            t = Transaction(space_doc, "Test")
            t.Start()
            self.room_to_space(room, space)
        except ValueError as e:
            logger.info("{}".format(e.message))
            t.RollBack()
            return
        except TypeError as e:
            logger.info("Is target parameter empty ?")
            t.RollBack()
            return
        t.RollBack()

        # Copy from values from
        with revit.Transaction(doc=space_doc, name="RoomToSpace"):
            for space in FilteredElementCollector(
                self.target_project.SelectedItem
            ).OfCategory(BuiltInCategory.OST_MEPSpaces):
                if space.Location:
                    room = room_doc.GetRoomAtPoint(space.Location.Point)
                if room:
                    self.room_to_space(room, space)
        self.Close()

    # noinspection PyUnusedLocal
    def source_project_changed(self, sender, e):
        self.room_initialise(self.source_project.SelectedItem)

    # noinspection PyUnusedLocal
    def target_project_changed(self, sender, e):
        self.space_initialise(self.target_project.SelectedItem)

    # noinspection PyUnusedLocal
    def window_closed(self, sender, e):
        pass


gui = Gui("WPFWindow.xaml")
gui.ShowDialog()
