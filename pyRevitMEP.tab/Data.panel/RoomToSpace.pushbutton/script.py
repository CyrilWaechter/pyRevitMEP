# coding: utf8
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Transaction,
    StorageType,
)
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


def is_valid_target_fields(element, fields):
    unvalid_param = []
    for field in fields:
        if len(field) > 1:
            logger.info("Space field too short: {}".format(field))
            forms.alert("Only 1 target parameter per line")
            return False
        attr_type, attr_name = field[0]
        if attr_type != "param":
            unvalid_param.append(attr_name)
            continue
        param = element.LookupParameter(attr_name)
        if param.StorageType != StorageType.String:
            unvalid_param.append(attr_name)
            continue
    if not unvalid_param:
        return True
    forms.alert(
        "Following parameter names are invalid \n{}".format("\n".join(unvalid_param))
    )
    return False


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
        sample_room = sample_element_by_category(doc, BuiltInCategory.OST_Rooms)
        for parameter in sample_room.Parameters:
            self.room_parameters_set.add(parameter.Definition.Name)
        logger.debug(
            "ROOM PARAMETER SET : {} \n ROOM ID : {}".format(
                self.room_parameters_set, sample_room
            )
        )

    def space_initialise(self, doc):
        logger.info("Initialise space")
        sample_space = sample_element_by_category(doc, BuiltInCategory.OST_MEPSpaces)
        for parameter in sample_space.Parameters:
            self.space_parameters_set.add(parameter.Definition.Name)
        logger.debug(
            "SPACE PARAMETER SET : {} \n SPACE ID : {}".format(
                self.space_parameters_set, sample_space
            )
        )

    def processed_fields(self, parameters):
        attributes = parameters.Text.replace("\r", "")
        fields = []
        for field in attributes.Split("\n"):
            attrs = []
            for attr in field.split("\t"):
                if attr in self.room_parameters_set:
                    attrs.append(("param", attr))
                    continue
                attrs.append(("sep", attr))
            fields.append(attrs)
        return fields

    def room_to_space(self, room, space, room_fields, space_fields):
        for room_field, space_field in zip(room_fields, space_fields):
            space_param = space.LookupParameter(space_field[0][1])
            value = []
            for attr_type, attr_name in room_field:
                if not attr_type == "param":
                    logger.info(attr_type, attr_name)
                    value.append(attr_name)
                    continue
                param = room.LookupParameter(attr_name)
                value.append(param.AsString())
            space_param.Set("".join(value))

    # noinspection PyUnusedLocal
    def ok_click(self, sender, e):
        room_doc = self.source_project.SelectedItem
        space_doc = self.target_project.SelectedItem
        if space_doc.IsLinked:
            forms.alert("Target cannot be a linked model")
            return
        room = sample_element_by_category(room_doc, BuiltInCategory.OST_Rooms)
        space = sample_element_by_category(space_doc, BuiltInCategory.OST_MEPSpaces)

        logger.info("Room parameter set: ", self.room_parameters_set)
        logger.info("Space parameter set: ", self.space_parameters_set)
        room_fields = self.processed_fields(self.source_parameters)
        space_fields = self.processed_fields(self.target_parameters)
        logger.info(room_fields)
        logger.info(space_fields)

        if not is_valid_target_fields(space, space_fields):
            return

        if len(room_fields) != len(space_fields):
            forms.alert("You need the same amount of source and target")
            return

        # Try RoomToSpace with sample room and space to make sure it works before batch on all with all spaces
        try:
            t = Transaction(space_doc, "Test")
            t.Start()
            self.room_to_space(room, space, room_fields, space_fields)
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
                    self.room_to_space(room, space, room_fields, space_fields)
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
