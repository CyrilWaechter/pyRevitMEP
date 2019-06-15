# coding: utf8
from pyrevitmep.parameter.managefamily import ManageFamilyParameter
from pyrevitmep.parameter.manageproject import ManageProjectParameter

__doc__ = "Manage document parameters"
__title__ = "DocumentParameters"
__author__ = "Cyril Waechter"
# __context__ = "selection"

doc = __revit__.ActiveUIDocument.Document  # type: Document

if doc.IsFamilyDocument:
    ManageFamilyParameter.show_dialog()
else:
    ManageProjectParameter.show_dialog()
