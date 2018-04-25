# coding: utf8
import rpw
from rpw import revit
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, StorageType, UnitUtils
from pyrevit.forms import WPFWindow
from pyrevit.script import get_logger

import os
import datetime

from pypevitmep import excel

logger = get_logger()

xl_app = excel.initialise()

# Create a workbook with designated file as template
report_template_path = os.path.join(__commandpath__, "ImportExportTemplate.xlsx")
report_workbook = xl_app.Workbooks.Add(report_template_path)
check_sheet = report_workbook.Sheets("SpaceCheck")
import_sheet = report_workbook.Sheets("Import")
export_sheet = report_workbook.Sheets("Export")
error_sheet = report_workbook.Sheets("ScriptError")


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
        self.tb_exported_parameters.Text = "SYS, " \
                                           "Ecoulement de soufflage spécifié, " \
                                           "Ecoulement d'air de retour spécifié, " \
                                           "Charge de chauffage de conception, " \
                                           "Charge de refroidissement de conception"
        self.tb_exported_column.Text = "T, CU, DH, DS, DY "

        self.check_row_count = 2
        self.import_row_count = 3
        self.export_row_count = 3
        self.error_row_count = 1
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
        service_column = self.service_column

        blank_row_count = 0

        while blank_row_count <= 10:
            if worksheet.Cells(row_count, number_column).Value2:
                blank_row_count = 0
                current_row = row_count
                row_count += 1
                yield current_row
            else:
                if not worksheet.Cells(row_count, service_column).MergeArea.Cells(1, 1).Value2:
                    blank_row_count += 1
                row_count += 1

    # noinspection PyUnusedLocal
    def test_click(self, sender, e):
        value = self.main_worksheet.Cells(7, "DY").Value2
        print(type(value))
        print(value)

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
            service_number = worksheet.Cells(row, service_column).MergeArea.Cells(1, 1).Value2

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
            self.revit_spaces_dict[space.Number] = space.Id

        logger.debug(self.revit_spaces_dict)

        # Excel space dict creation
        sheet_rows = self.sheet_loop_generator()
        for row in sheet_rows:
            current_cell_value = worksheet.Cells(row, number_column).Value2
            service_number = worksheet.Cells(row, service_column).MergeArea.Cells(1, 1).Value2
            self.excel_spaces_dict["{} {}".format(service_number, current_cell_value)] = row
        logger.debug(self.excel_spaces_dict)

        # Add Service number to Revit spaces and check if space are missing in the model
        # with rpw.db.Transaction("Add Service number to Revit spaces"):
        for number, row in self.excel_spaces_dict.items():
            service_number = worksheet.Cells(row, service_column).MergeArea.Cells(1, 1).Value2
            if not self.service_check(service_number):
                continue
            try:
                revit_space_id = self.revit_spaces_dict[number]
                # revit_space = revit.doc.GetElement(revit_space_id)
                # parameter = revit_space.LookupParameter("AAA_Service")
                # if service_number:
                #     parameter.Set(str(service_number))
            except KeyError:
                check_sheet.Cells(self.check_row_count, 1).Value2 = service_number
                check_sheet.Cells(self.check_row_count, 2).Value2 = number
                check_sheet.Cells(self.check_row_count, 3).Value2 = \
                    "Le local existe dans le tableur mais pas dans le modèle"
                self.check_row_count += 1

        # Check if some space in the model are missing in the spreadsheet
        for number, revit_id in self.revit_spaces_dict.items():
            revit_space = revit.doc.GetElement(revit_id)
            service_number = revit_space.LookupParameter("AAA_Service").AsString()
            if service_number and not self.service_check(service_number):
                continue
            try:
                self.excel_spaces_dict[service_number]
            except KeyError:
                check_sheet.Cells(self.check_row_count, 1).Value2 = service_number
                check_sheet.Cells(self.check_row_count, 2).Value2 = number
                check_sheet.Cells(self.check_row_count, 3).Value2 = \
                    "Le local existe dans le modèle mais pas dans le tableur"
                self.check_row_count += 1

    # noinspection PyUnusedLocal
    def import_click(self, sender, e):
        main_worksheet = self.main_worksheet
        service_column = self.service_column

        parameters_list = [parameter.strip() for parameter in self.tb_imported_parameters.Text.split(",")]
        columns_list = [column.strip() for column in self.tb_imported_column.Text.split(",")]

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
        self.import_row_count = 3
        for number, row in self.excel_spaces_dict.items():
            service_number = main_worksheet.Cells(row, service_column).MergeArea.Cells(1, 1).Value2

            # Check if report row is free (no number written yet)
            if import_sheet.Cells(self.import_row_count, 1).Value2:
                self.import_row_count += 1

            # Check if space is in an analysed service
            if not self.service_check(service_number):
                continue

            # Retrieve Revit space if it exist
            try:
                revit_space = revit.doc.GetElement(self.revit_spaces_dict[number])
            except KeyError:
                logger.info("L'espace {} n'a pas été trouvé dans le dictionnaire d'espaces Revit".format(number))
                continue

            # Retrieve parameter value from revit spaces
            # with unit conversion if necessary (based on Revit DisplayUnitType)
            for parameter_name, column, index in zip(parameters_list, columns_list, range(len(columns_list))):
                parameter = revit_space.LookupParameter(parameter_name)
                if parameter.StorageType == StorageType.Integer:
                    parameter_value = parameter.AsInteger()
                elif parameter.StorageType == StorageType.String:
                    parameter_value = parameter.AsString()
                elif parameter.StorageType == StorageType.Double:
                    parameter_value = UnitUtils.ConvertFromInternalUnits(parameter.AsDouble(),
                                                                         parameter.DisplayUnitType)
                    parameter_value = round(parameter_value, 1)
                if main_worksheet.Cells(row, column).Value2 == parameter_value:
                    continue
                else:
                    import_sheet.Cells(self.import_row_count, 1).Value2 = number
                    import_sheet.Cells(self.import_row_count, index*2 + 2).Value2 = main_worksheet.Cells(row,
                                                                                                         column).Value2
                    import_sheet.Cells(self.import_row_count, index*2 + 3).Value2 = parameter_value
                    main_worksheet.Cells(row, column).Value2 = parameter_value
        # Apply a TableStyle to the report
        data_range = import_sheet.Range(import_sheet.Cells(1, 1),
                                        import_sheet.Cells(self.import_row_count, len(columns_list)*2 + 2))
        excel.table_style(import_sheet, data_range)

    # noinspection PyUnusedLocal
    def export_click(self, sender, e):
        main_worksheet = self.main_worksheet
        service_column = self.service_column

        parameters_list = [parameter.strip() for parameter in self.tb_exported_parameters.Text.split(",")]
        columns_list = [column.strip() for column in self.tb_exported_column.Text.split(",")]

        # popup a message if same amount of parameter and column
        if len(parameters_list) != len(columns_list):
            rpw.ui.forms.Alert("Pas le même nombre de paramètres et colonnes indiqués."
                               "Merci de corriger puis de relancer l'opération.")
            return

        # Create report headers
        for index, parameter_name in enumerate(parameters_list):
            export_sheet.Cells(1, index * 2 + 2).Value2 = parameter_name
            export_sheet.Cells(2, index * 2 + 2).Value2 = "Avant"
            export_sheet.Cells(2, index * 2 + 3).Value2 = "Après"

        # Export values and append modified values to report
        with rpw.db.Transaction("Export excel values to Revit"):
            for number, row in self.excel_spaces_dict.items():
                service_number = main_worksheet.Cells(row, service_column).MergeArea.Cells(1, 1).Value2

                # Check if report row is free (no number written yet)
                if export_sheet.Cells(self.export_row_count, 1).Value2:
                    self.export_row_count += 1

                # Check if space is in an analysed service
                if not self.service_check(service_number):
                    continue

                # Retrieve Revit space if it exist
                try:
                    revit_space = revit.doc.GetElement(self.revit_spaces_dict[number])
                except KeyError:
                    logger.info("L'espace {} n'a pas été trouvé dans le dictionnaire d'espaces Revit".format(number))
                    continue

                # Retrieve parameter value from revit spaces
                # with unit conversion if necessary (based on Revit DisplayUnitType)
                for parameter_name, column, index in zip(parameters_list, columns_list, range(len(columns_list))):
                    parameter = revit_space.LookupParameter(parameter_name)
                    if not parameter:
                        logger.info("Parameter «{}» was not found".format(parameter_name))
                        continue
                    cell_value = main_worksheet.Cells(row, column).Value2
                    parameter_value = None
                    if parameter.StorageType == StorageType.Integer:
                        if cell_value:
                            parameter_value = parameter.AsInteger()
                            new_parameter_value = int(cell_value)
                        else:
                            new_parameter_value = 0
                    elif parameter.StorageType == StorageType.String:
                        parameter_value = parameter.AsString()
                        new_parameter_value = str(cell_value)
                    elif parameter.StorageType == StorageType.Double:
                        if cell_value:
                            parameter_value = UnitUtils.ConvertFromInternalUnits(parameter.AsDouble(),
                                                                                 parameter.DisplayUnitType)
                        else:
                            cell_value = 0
                        try:
                            new_parameter_value = UnitUtils.ConvertToInternalUnits(cell_value,
                                                                                   parameter.DisplayUnitType)
                        except TypeError:
                            error_sheet.Cells(self.error_row_count, 1).Value2 = \
                                "TypeError avec la valeur {} ligne {} colonne {}". format(cell_value, row, column)
                            self.error_row_count += 1
                            new_parameter_value = 0

                    else:
                        continue
                    if main_worksheet.Cells(row, column).Value2 == parameter_value:
                        continue
                    else:
                        export_sheet.Cells(self.export_row_count, 1).Value2 = number
                        export_sheet.Cells(self.export_row_count, index * 2 + 2).Value2 = parameter_value
                        export_sheet.Cells(self.export_row_count, index * 2 + 3).Value2 = \
                            main_worksheet.Cells(row, column).Value2
                        parameter.Set(new_parameter_value)
        # Apply a TableStyle to the report
        data_range = export_sheet.Range(export_sheet.Cells(1, 1),
                                        export_sheet.Cells(self.export_row_count, len(columns_list)*2 + 2))
        excel.table_style(export_sheet, data_range)

    # noinspection PyUnusedLocal
    def main_workbook_changed(self, sender, e):
        try:
            self.cb_main_sheet.ItemsSource = sender.SelectedItem.Sheets
        except AttributeError:
            return

    # noinspection PyUnusedLocal
    def window_closed(self, sender, e):
        folder = os.path.join(self.cb_main_workbook.SelectedItem.Path, 'reports')
        if not os.path.exists(folder):
            os.makedirs(folder)
        file_name = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S.xlsx')
        # Save report to main_sheet path under designated subfolder
        try:
            report_workbook.SaveAs(os.path.join(folder, file_name))
        except EnvironmentError:
            return

        # Release COM Object
        logger.debug("RELEASE EXCEL COM OBJECT ON WINDOW CLOSED")
        excel.release(xl_app)


gui = Gui("WPFWindow.xaml")
gui.ShowDialog()
