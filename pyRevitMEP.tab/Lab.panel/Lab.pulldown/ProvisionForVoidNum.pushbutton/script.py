# coding: utf8
from Autodesk.Revit.DB import Document, FilteredElementCollector, BuiltInCategory, Element, Parameter

import rpw

__doc__ = "MagiCAD ProvisionForVoid numbering"
__title__ = "ProvisionForVoid Numbering"
__author__ = "Cyril Waechter"

doc = __revit__.ActiveUIDocument.Document  # type: Document

with rpw.db.Transaction("Numérotation réservations", doc):
    for element in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_GenericModel):  # type: Element
        elem_res_number = element.LookupParameter("RES_Numéro")  # type: Parameter
        try:
            print(element)
            if Element.Name.__get__(element.Symbol) == "MagiCAD_ProvisionForVoid" and not(elem_res_number.AsInteger()):
                doc_res_number = doc.ProjectInformation.LookupParameter("RES_Numéro")
                elem_res_number.Set(doc_res_number.AsInteger())
                doc_res_number.Set(doc_res_number.AsInteger() + 1)
        except AttributeError:
            continue