# coding: utf8
import rpw
from rpw import revit
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, StorageType, UnitUtils
from pyrevit.forms import WPFWindow, logger
from pyrevit import script
import os

from pyRevitMEP import excel

xl_app = excel.initialise()

# Create a workbook with designated file as template
report_template_path = os.path.join(__commandpath__, "ImportExportTemplate.xlsx")
report_workbook = xl_app.Workbooks.Add(report_template_path)
check_sheet = report_workbook.Sheets("SpaceCheck")
import_sheet = report_workbook.Sheets("Import")
export_sheet = report_workbook.Sheets("Export")

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
def excel_space_iterator():
    return

class Gui(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)

        # Default general config
        self.cb_main_workbook.DataContext = xl_app.Workbooks
        self.cb_main_workbook.SelectedItem = xl_app.ActiveWorkBook
        self.tb_space_number_column.Text = "F"
        self.tb_space_number_starting_row.Text = "8"
        self.tb_space_service_column.Text = "C"

        # Default import config
        self.tb_imported_parameters.Text = "Surface, Nom"
        self.tb_imported_column.Text = "M, K"

        self.check_row_count = 1
        self.import_row_count = 1
        self.export_row_count = 1
        self.service_set = set()
        self.revit_spaces_dict = {}
        self.excel_spaces_dict = {}

    # noinspection PyUnusedLocal
    @property
    def main_worksheet(self):
        return self.cb_main_sheet.SelectedItem

    @property
    def number_column(self):
        return self.tb_space_number_column.Text

    @property
    def service_column(self):
        return self.tb_space_service_column.Text

    @property
    def starting_row(self):
        return int(self.tb_space_number_starting_row.Text)

    def sheet_loop_generator(self):
        worksheet = self.main_worksheet
        row_count = self.starting_row
        number_column = self.number_column

        blank_row_count = 0

        while blank_row_count <= 5:
            if worksheet.Cells(row_count, number_column).Value2:
                blank_row_count = 0
                current_row = row_count
                row_count += 1
                yield current_row
            else:
                blank_row_count += 1
                row_count += 1

    # noinspection PyUnusedLocal
    def test_click(self, sender, e):
        sheet_loop = self.sheet_loop_generator()
        for row in sheet_loop:
            print(row)

    # noinspection PyUnusedLocal
    def service_list_creation_click(self, sender, e):
        # Inputs
        worksheet = self.main_worksheet
        service_column = self.service_column
        number_column = self.service_column

        blank_row_count = 0

        sheet_rows = self.sheet_loop_generator()
        for row in sheet_rows:
            space_number = worksheet.Cells(row, number_column).Value2
            service_number = worksheet.Cells(row, service_column).MergeArea.Cells(1,1).Value2

            self.service_set.add(service_number)

        self.service_selection.ItemsSource = list(self.service_set)

    def service_check(self, number):
        return number in self.service_selection.SelectedItems or self.tous_services.IsChecked

    # noinspection PyUnusedLocal
    def space_check_click(self, sender, e):
        # Inputs
        worksheet = self.cb_main_sheet.SelectedItem
        number_column = self.number_column
        service_column = self.service_column

        # Revit space dict creation
        for space in FilteredElementCollector(revit.doc).OfCategory(BuiltInCategory.OST_MEPSpaces):
            self.revit_spaces_dict[space.Number.replace(" ","")] = space.Id

        logger.debug(self.revit_spaces_dict)

        # Excel space dict creation
        sheet_rows = self.sheet_loop_generator()
        for row in sheet_rows:
            current_cell_value = worksheet.Cells(row, number_column).Value2
            self.excel_spaces_dict[str(current_cell_value).replace(" ","")] = row
        logger.debug(self.excel_spaces_dict)

        # Add Service number to Revit spaces and check if space are missing in the model
        with rpw.db.Transaction("Add Service number to Revit spaces"):
            for number, row in self.excel_spaces_dict.items():
                service_number = worksheet.Cells(row, service_column).MergeArea.Cells(1,1).Value2
                if not self.service_check(service_number):
                    continue
                try:
                    revit_space_id = self.revit_spaces_dict[number]
                    revit_space = revit.doc.GetElement(revit_space_id)
                    parameter = revit_space.LookupParameter("AAA_Service")
                    if service_number:
                        parameter.Set(str(service_number))
                except KeyError:
                    check_sheet.Cells(self.check_row_count, 1).Value2 = \
                        "Le local n°{} existe dans le tableur mais pas dans le modèle".format(number)
                    self.check_row_count += 1

        for number, id in self.revit_spaces_dict.items():
            revit_space = revit.doc.GetElement(id)
            service_number = revit_space.LookupParameter("AAA_Service").AsString()
            if service_number and not self.service_check(service_number):
                continue
            try:
                self.excel_spaces_dict[service_number]
            except KeyError:
                check_sheet.Cells(self.check_row_count, 1).Value2 = \
                    "Le local n°{} existe dans le modèle mais pas dans le tableur".format(number)
                self.check_row_count += 1

    # noinspection PyUnusedLocal
    def import_click(self, sender, e):
        main_worksheet = self.main_worksheet
        service_column = self.service_column

        parameters_list = self.tb_imported_parameters.Text.replace(" ","").split(",")
        columns_list = self.tb_imported_column.Text.replace(" ","").split(",")

        # popup a message if same amount of parameter and column
        if len(parameters_list) != len(columns_list):
            rpw.ui.forms.Alert("Pas le même nombre de paramètres et colonnes indiqués."
                               "Merci de corriger puis de relancer l'opération.")
            return

        # Create report headers
        for index, parameter_name in enumerate(parameters_list):
            import_sheet.Cells(1, index * 2 + 2).Value2 = parameter_name
            import_sheet.Cells(2, index * 2 + 2).Value2 = "Avant"
            import_sheet.Cells(2, index * 2 + 3).Value2 = "Après"

    # Import values and append modified values to report
        report_row_count = 3
        for number, row in self.excel_spaces_dict.items():
            service_number = main_worksheet.Cells(row, service_column).MergeArea.Cells(1,1).Value2

            # Check if report row is free (no number written yet)
            if import_sheet.Cells(report_row_count, 1).Value2:
                report_row_count += 1

            # Check if space is in an analysed service
            if not self.service_check(service_number):
                continue

            # Retrieve Revit space if it exist
            try:
                revit_space = revit.doc.GetElement(self.revit_spaces_dict[number])
            except KeyError:
                continue

            # Retrieve parameter value from revit spaces
            # with unit conversion if necessary (based on Revit DisplayUnitType)
            for parameter_name, column, index in zip(parameters_list ,columns_list, range(len(columns_list))):
                parameter = revit_space.LookupParameter(parameter_name)
                if parameter.StorageType == StorageType.Integer:
                    parameter_value = parameter.AsInteger()
                elif parameter.StorageType == StorageType.String:
                    parameter_value = parameter.AsString()
                elif parameter.StorageType == StorageType.Double:
                    parameter_value = UnitUtils.ConvertFromInternalUnits(parameter.AsDouble(),
                                                                         parameter.DisplayUnitType)
                if main_worksheet.Cells(row, column).Value2 == parameter_value:
                    continue
                else:
                    import_sheet.Cells(report_row_count, 1).Value2 = number
                    import_sheet.Cells(report_row_count, index*2 + 2).Value2 = main_worksheet.Cells(row, column).Value2
                    import_sheet.Cells(report_row_count, index*2 + 3).Value2 = parameter_value
                    main_worksheet.Cells(row, column).Value2 = parameter_value


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
