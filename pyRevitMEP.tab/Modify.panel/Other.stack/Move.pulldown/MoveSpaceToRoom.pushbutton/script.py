# coding: utf8
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory
from pyrevit import script, forms, revit

__title__ = "SpaceToRoom"
__author__ = "Cyril Waechter"
__doc__ = "Move space to room location by corresponding number"


class CancelledByUserError(BaseException):
    pass


logger = script.get_logger()
output = script.get_output()

doc = revit.doc
room_doc = forms.SelectFromList.show(
    revit.docs,
    "Select project which contains rooms",
    multiselect=False,
    name_attr="Title",
)


def move_space_to_room(doc, room_doc):
    room_dict = {
        room.Number: room
        for room in FilteredElementCollector(room_doc).OfCategory(
            BuiltInCategory.OST_Rooms
        )
    }
    i = 0
    with forms.ProgressBar(title="Moving space", cancellable=True) as pb:
        for space in FilteredElementCollector(doc).OfCategory(
            BuiltInCategory.OST_MEPSpaces
        ):
            if pb.cancelled:
                raise CancelledByUserError
            room = room_dict.get(space.Number)
            if not room:
                continue
            if not room.Location:
                output.log_warning(
                    "Room {} exist but is not placed".format(room.Number)
                )
                continue
            i += 1
            pb.update_progress(i, len(room_dict))
            space.Location.Move(room.Location.Point - space.Location.Point)


if room_doc:
    with revit.Transaction("Move space to room location", doc) as t:
        try:
            move_space_to_room(doc, room_doc)
        except CancelledByUserError:
            t._logerror = False
