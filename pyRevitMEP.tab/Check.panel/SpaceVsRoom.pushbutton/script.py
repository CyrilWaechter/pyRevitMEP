# coding: utf8
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    BuiltInParameter,
)
from pyrevit import script, forms, revit

__title__ = "SpaceVsRoom"
__author__ = "Cyril Waechter"
__doc__ = "Check if all room have his corresponding space and vice versa"

logger = script.get_logger()
output = script.get_output()

doc = revit.doc
room_doc = forms.SelectFromList.show(
    revit.docs,
    "Select project which contains rooms",
    multiselect=False,
    name_attr="Title",
)


def is_placed_str(element):
    if not element.Location:
        return "but is unplaced"
    return "despite being placed"


def print_missing(title, missing, base_dict):
    output.print_md(title)
    for number in missing:
        element = base_dict[number]
        print(
            "{} - {}: {} {}".format(
                element.Number,
                element.get_Parameter(BuiltInParameter.ROOM_NAME).AsString(),
                output.linkify(element.Id),
                is_placed_str(element),
            )
        )


def check_room_vs_space(doc, room_doc):
    room_dict = {
        room.Number: room
        for room in FilteredElementCollector(room_doc).OfCategory(
            BuiltInCategory.OST_Rooms
        )
    }
    space_dict = {
        space.Number: space
        for space in FilteredElementCollector(doc).OfCategory(
            BuiltInCategory.OST_MEPSpaces
        )
    }
    room_set = set(room_dict.keys())
    space_set = set(space_dict.keys())
    missing_room = space_set.difference(room_set)
    missing_space = room_set.difference(space_set)
    output.print_md("# Check result")
    output.print_md(
        "## {} corresponding room/space found".format(
            len(room_set.intersection(space_set))
        )
    )
    print_missing(
        "## {} following rooms have no corresponding spaces".format(len(missing_space)),
        missing_space,
        room_dict,
    )
    print_missing(
        "## {} following spaces have no corresponding rooms".format(len(missing_room)),
        missing_room,
        space_dict,
    )


if room_doc:
    check_room_vs_space(doc, room_doc)
