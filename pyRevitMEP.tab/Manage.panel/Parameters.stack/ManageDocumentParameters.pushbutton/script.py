# coding: utf8
from pyrevitmep.parameter.managefamily import ManageFamilyParameter
from pyrevitmep.parameter.manageproject import ManageProjectParameter

doc = __revit__.ActiveUIDocument.Document  # type: Document

if doc.IsFamilyDocument:
    ManageFamilyParameter.show_dialog()
else:
    ManageProjectParameter.show_dialog()
