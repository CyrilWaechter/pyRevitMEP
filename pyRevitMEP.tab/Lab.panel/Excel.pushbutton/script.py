# coding: utf8
import rpw
from rpw import revit
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory
from pyrevit.forms import WPFWindow
from pyrevit import script
import os

from pyRevitMEP import excel

xl_app = excel.initialise()

# Create a workbook with designated file as template
report_template_path = os.path.join(__commandpath__, "ImportExportTemplate.xlsx")
report_workbook = xl_app.Workbooks.Add(report_template_path)
check_sheet = report_workbook.Sheets("SpaceCheck")


# for wb in xl_app.Workbooks:
#     print(wb.Name)
#
# sion_workbook = excel.workbook_by_name(xl_app, r"180118 - 72265.01 - RBR_2.8.xlsx")

# revit_spaces_dict = {}
#
# # Retrieve main worksheet by his name, if name is changed, it will fail
# main_worsheet = excel.worksheet_by_name(sion_workbook, "Feuil1")
#
# excel_spaces_dict = {}
# for row in main_worsheet.UsedRange.Rows:
#     print(row.Row)
#     revit_spaces_dict[main_worsheet.Cells[row.Row, 10].Value] = row.Row
#
# print(revit_spaces_dict)
# print(excel_spaces_dict)



class Gui(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.cb_main_workbook.DataContext = xl_app.Workbooks
        self.cb_main_workbook.SelectedItem = xl_app.ActiveWorkBook
        self.cb_main_sheet.SelectedItem = xl_app.ActiveSheet
        self.tb_space_number_column.Text = "F"
        self.tb_space_number_starting_row.Text = "8"
        self.tb_space_service_column.Text = "C"

        self.check_row_count = 1
        self.import_row_count = 1
        self.export_row_count = 1

# noinspection PyUnusedLocal
    def space_check_click(self, sender, e):
        # Inputs
        worksheet = self.cb_main_sheet.SelectedItem
        row_count = int(self.tb_space_number_starting_row.Text)
        column = self.tb_space_number_column.Text

        # Revit space dict creation
        revit_spaces_dict = {}

        for space in FilteredElementCollector(revit.doc).OfCategory(BuiltInCategory.OST_MEPSpaces):
            revit_spaces_dict[space.Number] = space.Id

        print(revit_spaces_dict)

        # Excel space dict creation
        excel_spaces_dict = {}
        blank_row_count = 0

        while blank_row_count <= 5:
            current_cell_value = worksheet.Cells(row_count, column).Value2
            if current_cell_value:
                excel_spaces_dict[str(current_cell_value)] = row_count
                blank_row_count = 0
            else:
                blank_row_count += 1
            row_count += 1
        print(excel_spaces_dict)

        # Add Service number to Revit spaces
        service_column = self.tb_space_service_column.Text
        with rpw.db.Transaction("Add Service number to Revit spaces"):
            for number, row in excel_spaces_dict.items():
                try:
                    revit_space_id = revit_spaces_dict[number]
                    revit_space = revit.doc.GetElement(revit_space_id)
                    parameter = revit_space.LookupParameter("AAA_Service")
                    service_number = worksheet.Cells(row, service_column).MergeArea.Cells(1,1).Value2
                    if service_number:
                        parameter.Set(str(service_number))
                except KeyError:
                    check_sheet.Cells(self.check_row_count, 1).Value2 = "{} n'existe pas dans le modèle".format(number)
                    self.check_row_count += 1


    # noinspection PyUnusedLocal
    def import_click(self, sender, e):
        pass

    # noinspection PyUnusedLocal
    def export_click(self, sender, e):
        pass

    # noinspection PyUnusedLocal
    def main_workbook_changed(self, sender, e):
        try:
            self.cb_main_sheet.ItemsSource = sender.SelectedItem.Sheets
        except:
            raise

        # try:
        #     self.cb_main_sheet.SelectedItem = xl_app.ActiveSheet
        # except:
        #     raise
        return

gui = Gui("WPFWindow.xaml")
gui.ShowDialog()
