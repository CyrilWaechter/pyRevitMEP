# coding: UTF-8
import uuid
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    Element,
    BuiltInParameter,
)

doc = __revit__.ActiveUIDocument.Document

from pyrevit import script, forms, revit


class SpaceNumberer:
    def __init__(self, doc):
        self.doc = doc
        self.numbers = []

    def renumber_spaces(self):
        for space in FilteredElementCollector(self.doc).OfCategory(
            BuiltInCategory.OST_MEPSpaces
        ):
            zone1 = space.LookupParameter("ZoneName").AsString()
            level_name = Element.Name.__get__(space.Level)
            zone2 = space.LookupParameter("ZoneName 2").AsString()
            if space.Occupiable:
                thermal_shell = ""
            else:
                thermal_shell = "NC"
            if zone2 in ("Communs", "Parking"):
                zone2 = 0
            last_digit = 1
            while True:
                number = "{}{}{}{}{}".format(
                    zone1, level_name, zone2, last_digit, thermal_shell
                )
                if number in self.numbers:
                    last_digit += 1
                else:
                    break
            space.Number = number
            self.numbers.append(number)


with revit.Transaction("Create uuid for spaces", doc):
    SpaceNumberer(doc).renumber_spaces()