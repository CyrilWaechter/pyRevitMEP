# coding: UTF-8
import uuid
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Element,
    UV,
    BuiltInParameter,
    StorageType,
)
from Autodesk.Revit import Exceptions

from pyrevit import script, forms, revit

output = script.get_output()
logger = script.get_logger()


def get_src_doc(name):
    for doc in revit.HOST_APP.docs:
        if doc.Title == name:
            return doc


class SpaceSync:
    def __init__(self, src_name):
        output.log_info("Initialise")
        self.tgt_doc = (
            __revit__.ActiveUIDocument.Document
        )  # type: Autodesk.Revit.Document
        self.src_doc = get_src_doc(src_name)
        if self.src_doc:
            output.log_info("Document «{}» found".format(src_name))
        else:
            output.log_error("Document «{}» not found".format(src_name))
        self.src_levels = {
            level.Id: Element.Name.__get__(level)
            for level in FilteredElementCollector(self.tgt_doc).OfCategory(
                BuiltInCategory.OST_Levels
            )
        }
        self.tgt_levels = {
            Element.Name.__get__(level): level
            for level in FilteredElementCollector(self.tgt_doc).OfCategory(
                BuiltInCategory.OST_Levels
            )
        }
        self.src_spaces = self.init_space_dict(self.src_doc)
        self.tgt_spaces = self.init_space_dict(self.tgt_doc)

    def init_space_dict(self, doc):
        return {
            space.LookupParameter("uuid").AsString(): space
            for space in FilteredElementCollector(doc).OfCategory(
                BuiltInCategory.OST_MEPSpaces
            )
        }

    def remove_unused_space(self):
        doc = self.tgt_doc
        to_delete = [
            space
            for space in FilteredElementCollector(doc).OfCategory(
                BuiltInCategory.OST_MEPSpaces
            )
            if not space.LookupParameter("uuid").HasValue
        ]
        for space in to_delete:
            doc.Delete(space.Id)
        logger.debug(self.src_spaces.keys())
        logger.debug(self.tgt_spaces.keys())
        extra_spaces = set(self.tgt_spaces.keys()).difference(
            set(self.src_spaces.keys())
        )
        logger.debug(extra_spaces)
        if extra_spaces:
            output.log_info("Remove {} unused spaces".format(len(extra_spaces)))
        for space_uuid in extra_spaces or ():
            doc.Delete(self.tgt_spaces[space_uuid].Id)
            self.tgt_spaces.pop(space_uuid)

    def get_tgt_space(self, space_uuid, src_space):
        try:
            return self.tgt_spaces[space_uuid]
        except KeyError:
            level = self.tgt_levels[src_space.Level.Name]
            uv = UV(src_space.Location.Point.X, src_space.Location.Point.Y)
            return self.tgt_doc.Create.NewSpace(level, uv)

    def sync_data(self, src_space, tgt_space):
        output.log_info("Sync spaces datas")
        synced_attr = ["UpperLimit", "Number", "ConditionType"]
        synced_bip = [
            BuiltInParameter.ROOM_NAME,
            BuiltInParameter.ROOM_UPPER_OFFSET,
            BuiltInParameter.ROOM_LOWER_OFFSET,
            BuiltInParameter.SPACE_IS_OCCUPIABLE,
        ]
        synced_param = [
            "ZoneDescription",
            "ZoneDescription 2",
            "ZoneName",
            "ZoneName 2",
            "uuid",
        ]
        for attr_name in synced_attr:
            if attr_name == "Name":
                value = Element.Name.__get__(src_space)
                Element.Name.__set__(tgt_space, value)
            else:
                value = getattr(src_space, attr_name)
                if attr_name == "UpperLimit":
                    level_name = Element.Name.__get__(value)
                    value = self.tgt_levels[level_name]
                setattr(tgt_space, attr_name, value)
        for bip in synced_bip:
            param = src_space.get_Parameter(bip)
            if param.StorageType == StorageType.Double:
                value = param.AsDouble()
            elif param.StorageType == StorageType.Integer:
                value = param.AsInteger()
            elif param.StorageType == StorageType.String:
                value = param.AsString()
            elif param.StorageType == StorageType.ElementId:
                value = param.ElementId()
            else:
                output.log_warning(
                    "Unknown storage type for {}".format(param.Definition.Name)
                )
            try:
                tgt_space.get_Parameter(bip).Set(value)
            except TypeError:
                output.log_error(
                    "Fail to set value {} to parameter {}".format(
                        value, param.Definition.Name
                    )
                )
        for param_name in synced_param:
            value = src_space.LookupParameter(param_name).AsString()
            try:
                tgt_space.LookupParameter(param_name).Set(value)
            except TypeError:
                output.log_error(
                    "Fail to set value {} to parameter {}".format(
                        value, param.Definition.Name
                    )
                )

    def sync_location(self, src_space, tgt_space):
        output.log_info("Sync spaces location")
        translation = src_space.Location.Point - tgt_space.Location.Point
        if not translation.IsZeroLength():
            tgt_space.Location.Move(translation)

    def process(self):
        with revit.Transaction(
            "Sync spaces",
            self.tgt_doc,
        ):
            self.remove_unused_space()
            for space_uuid, src_space in self.src_spaces.items():
                tgt_space = self.get_tgt_space(space_uuid, src_space)
                self.sync_location(src_space, tgt_space)
                self.sync_data(src_space, tgt_space)


SpaceSync("0014_Vernier112D_CVS_ModèleCVS_R21").process()
