# coding: UTF-8
import uuid
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory

doc = __revit__.ActiveUIDocument.Document

from pyrevit import script, forms, revit

def create_spaces_uuids(doc):
    for space in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_MEPSpaces):
        param = space.LookupParameter("uuid")
        if not param.HasValue:
            param.Set(str(uuid.uuid4()))

create_spaces_uuids(doc)