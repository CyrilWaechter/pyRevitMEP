# coding: utf8
import rpw
from pyrevit.script import get_logger
from Autodesk.Revit import Exceptions
from Autodesk.Revit.DB import FilteredElementCollector, Family, FamilySymbol, Element

logger = get_logger()
doc = rpw.revit.doc

with rpw.db.Transaction("Rename families"):
    for family in FilteredElementCollector(doc).OfClass(Family):
        old_name = Element.Name.__get__(family)
        new_name = old_name.replace(" - ", "_")
        if old_name != new_name:
            print("Old : {} , New : {}".format(old_name, new_name))
            try:
                Element.Name.__set__(family, new_name)
            except Exceptions.ArgumentException:
                print("!!! ABOVE RENAMING FAILED !!!")