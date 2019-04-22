# coding: utf8

import rpw

__doc__ = "Add reference level to a defined parameter"
__title__ = "Change Level"
__author__ = "Cyril Waechter"

doc = rpw.revit.doc
uidoc = rpw.revit.uidoc


def get_reference_level(element):
    try:
        return element.ReferenceLevel
    except AttributeError:
        return doc.GetElement(element.LevelId)


with rpw.db.Transaction("Add reference level to parameter", doc):
    for id in uidoc.Selection.GetElementIds():
        element = doc.GetElement(id)
        parameter = element.LookupParameter("")
        parameter.Set(get_reference_level(element).Name)