# coding: utf8

from rpw import revit
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory

from pyRevitMEP import excel

xl_app = excel.initialise()

# Create a workbook with designated file as template
xl_app.Workbooks.Add("C:\FichiersLocauxRevit\pyRevitMEP\pyRevitMEP.extension\pyRevitMEP.tab\Lab.panel\Excel.pushbutton\ImportExportTemplate.xlsx")

for wb in xl_app.Workbooks:
    print(wb.Name)

sion_workbook = excel.workbook_by_name(xl_app, r"180118 - 72265.01 - RBR_2.8.xlsx")

revit_spaces_dict = {}

for space in FilteredElementCollector(revit.doc).OfCategory(BuiltInCategory.OST_MEPSpaces):
    revit_spaces_dict[space.Number] = space.Id

# Retrieve main worksheet by his name, if name is changed, it will fail
main_worsheet = excel.worksheet_by_name(sion_workbook, "Feuil1")

excel_spaces_dict = {}
for row in main_worsheet.UsedRange.Rows:
    print(row.Row)
    revit_spaces_dict[main_worsheet.Cells[row.Row, 10].Value] = row.Row

print(revit_spaces_dict)
print(excel_spaces_dict)



