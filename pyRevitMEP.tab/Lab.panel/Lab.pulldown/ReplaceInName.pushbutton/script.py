# coding: utf8
import rpw
from pyrevit.script import get_logger
from Autodesk.Revit import Exceptions
from Autodesk.Revit.DB import FilteredElementCollector, Family, FamilySymbol, Element, Transaction, Document
from Autodesk.Revit.UI import UIDocument

logger = get_logger()
doc = rpw.revit.doc  # type: Document
uidoc = rpw.revit.uidoc  # type: UIDocument

def replace_in_name(elements, old=" - ", new="_"):
    with rpw.db.Transaction("Replace in Name"):
        for element in elements:
            old_name = Element.Name.__get__(element)
            new_name = old_name.replace(old, new)
            if old_name != new_name:
                print("Old : {} , New : {}".format(old_name, new_name))
                try:
                    Element.Name.__set__(element, new_name)
                except Exceptions.ArgumentException:
                    print("!!! ABOVE RENAMING FAILED !!!")


def all_families():
    return FilteredElementCollector(doc).OfClass(Family)


def selection():
    return (doc.GetElement(id) for id in uidoc.Selection.GetElementIds())


replace_in_name(selection(), "_ORG", "AAA")