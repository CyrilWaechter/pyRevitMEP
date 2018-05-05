# coding: utf8

from Autodesk.Revit.DB import Document, Element, Parameter, ElementId

import rpw
from rpw import revit
from pyrevit.forms import WPFWindow
from pyrevit.script import get_logger

import os
import datetime

from pypevitmep import excel

logger = get_logger()
doc = revit.doc # type: Document

xl_app = excel.initialise()

# Create a workbook with designated file as template
res_path = os.path.join(__commandpath__, r"A03_Correction des reservations.xlsx")
res_workbook = xl_app.Workbooks("A03_Correction des reservations.xlsx")
res_sheet = res_workbook.Sheets("Feuil1")

row = 2
with rpw.db.Transaction("Set BY_GROUP_ID, BY_ELEMENT_ID"):
    while res_sheet.Cells(row, 1):
        try:
            el_id = ElementId(int(res_sheet.Cells(row, 1).Value2))
            element = doc.GetElement(el_id)  # type: Element
            if element is None:
                logger.info("ID {} do not exist".format(el_id))
                row += 1
                continue
        except TypeError:
            logger.info("{} END ?".format(row))
            break

        try:
            by_group_id = element.LookupParameter("BY_GROUP_ID")  # type: Parameter
            by_element_id = element.LookupParameter("BY_ELEMENT_ID")

            by_group_id.Set(str(res_sheet.Cells(row, 2).Value2))
            by_element_id.Set(str(res_sheet.Cells(row, 3).Value2))
            logger.info("{} OK".format(el_id))
        except AttributeError:
            logger.info("{} FAIL".format(el_id))

        row += 1

excel.release(xl_app)
