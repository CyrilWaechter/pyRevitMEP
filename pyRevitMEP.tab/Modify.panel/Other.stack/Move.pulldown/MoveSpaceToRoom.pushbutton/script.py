# coding: utf8
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory
from pyrevit import script, forms, revit

__title__ = "SpaceToRoom"
__author__ = "Cyril Waechter"
__doc__ = "Move space to room location by corresponding number"


class CancelledByUserError(BaseException):
    pass


output = script.get_output()
logger = script.get_logger()

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
                output.print_html(
                    '<div style="background:orange">Space {} do not have corresponding room</div>'.format(
                        space.Number
                    )
                )
                continue
            logger.debug("{} - Id: {}".format(room.Number, room.Id))
            if not room.Location:
                output.print_html(
                    '<div style="background:orange">Room {} exist but is not placed</div>'.format(
                        room.Number
                    )
                )
                continue
            if not space.Location:
                output.print_html(
                    '<div style="background:orange">Space {} exist but is not placed</div>'.format(
                        room.Number
                    )
                )
                continue
            i += 1
            pb.update_progress(i, len(room_dict))
            if not space.Location.Point.IsAlmostEqualTo(room.Location.Point):
                space.Location.Move(room.Location.Point - space.Location.Point)
                output.print_html(
                    '<div style="background:green">Space {} has been moved</div>'.format(
                        space.Number
                    )
                )


if room_doc:
    with revit.Transaction("Move space to room location", doc) as t:
        try:
            move_space_to_room(doc, room_doc)
        except CancelledByUserError:
            t._logerror = False
