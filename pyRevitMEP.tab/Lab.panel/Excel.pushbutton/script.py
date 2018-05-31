# coding: utf8
import os
import datetime

from System.Collections.ObjectModel import ObservableCollection

import rpw
from rpw import revit
from Autodesk.Revit import Exceptions
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, StorageType, UnitUtils
from pyrevit.forms import WPFWindow
from pyrevit.script import get_logger

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


class Space(object):
    def __init__(self, common_name):
        # type: (str) -> None
        self.common_name = str(common_name)
        self.service = common_name.split()[0]
        try:
            self.number = common_name.split()[1]
        except IndexError:
            self.number = ""
        self.id = None
        self.row = None

    def __eq__(self, other):
        return self.number == other.number

    def __gt__(self, other):
        return self.number.split(".")[0] > other.number.split(".")[0]

    def __lt__(self, other):
        return self.number.split(".")[0] < other.number.split(".")[0]


class Gui(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)

        # Default general config
        self.cb_main_workbook.DataContext = xl_app.Workbooks
        self.cb_main_workbook.SelectedItem = xl_app.ActiveWorkBook
        self.tb_space_number_column.Text = "G"
        self.tb_space_number_starting_row.Text = "7"
        self.tb_space_service_column.Text = "C"

        # Default import config
        self.tb_imported_parameters.Text = "Surface, Nom"
        self.tb_imported_column.Text = "J, H"
        self.tb_exported_parameters.Text = "SYS, " \
                                           "Ecoulement de soufflage spécifié, " \
                                           "Ecoulement d'air de retour spécifié, " \
                                           "Charge de chauffage de conception, " \
                                           "Charge de refroidissement de conception"
        self.tb_exported_column.Text = "T, CE, CJ, CW, DC"

        self.check_row_count = 2
        self.import_row_count = 3
        self.export_row_count = 3
        self.error_row_count = 1
        self.service_set = set()
        self.revit_spaces_dict = {}
        self.excel_spaces_dict = {}
        self.spaces = list()

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

        while blank_row_count <= 10:
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
        value = self.main_worksheet.Cells(7, "DY").Value2
        print(type(value))
        print(value)

    # noinspection PyUnusedLocal
    def service_list_creation_click(self, sender, e):
        # Inputs
        worksheet = self.main_worksheet
        number_column = self.number_column

        blank_row_count = 0

        sheet_rows = self.sheet_loop_generator()
        for row in sheet_rows:
            current_cell_value = worksheet.Cells(row, number_column).Value2  # type: str
            service_number = current_cell_value.split(" ")[0]

            self.service_set.add(service_number)

        self.service_selection.ItemsSource = sorted(self.service_set)

    def service_check(self, number):
        return number in self.service_selection.SelectedItems or self.tous_services.IsChecked

    def space_check_error(self, service, number, message):
        check_sheet.Cells(self.check_row_count, 1).Value2 = service
        check_sheet.Cells(self.check_row_count, 2).Value2 = number
        check_sheet.Cells(self.check_row_count, 3).Value2 = message
        self.check_row_count += 1

    # noinspection PyUnusedLocal
    def space_check_click(self, sender, e):
        # Inputs
        worksheet = self.cb_main_sheet.SelectedItem
        number_column = self.number_column
        service_column = self.service_column

        self.spaces = list()

        sheet_rows = self.sheet_loop_generator()
        for row in sheet_rows:
            common_name = worksheet.Cells(row, number_column).Value2
            if not common_name.split():
                continue
            space = Space(common_name)
            if not self.service_check(space.service):
                continue

            # check if there is already a space with same number
            for existing_space in self.spaces:
                if space == existing_space:
                    self.space_check_error(
                        space.service,
                        space.number,
                        "Le numéro du local ligne {} est identique au numéro du local ligne {} dans le tableur".format(
                            row, existing_space.row))
                    break
            else:
                space.row = row
                self.spaces.append(space)
                logger.debug(common_name)

        for revit_space in FilteredElementCollector(revit.doc).OfCategory(BuiltInCategory.OST_MEPSpaces):

            common_name = revit_space.Number
            service_number = common_name.split()[0]

            if not self.service_check(service_number):
                continue

            id = revit_space.Id
            for space in self.spaces:  # type: Space
                if common_name == space.common_name:
                    if space.id:
                        self.space_check_error(
                            space.service,
                            space.number,
                            "Plusieurs locaux possèdent le même numéro dans le modèle")
                    else:
                        space.id = id
                        break
            else:
                # report space missing in spreadsheet
                space = Space(common_name)
                self.space_check_error(
                    space.service,
                    space.number,
                    "Le local existe dans le modèle mais pas dans le tableur")

        # report space missing in model
        for index, space in enumerate(self.spaces):
            if not space.id:
                self.space_check_error(
                    space.service,
                    space.number,
                    "Le local existe dans le tableur à la ligne {} mais pas dans le modèle".format(space.row))
            self.spaces.pop(index)

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
        for space in self.spaces:
            # Check if report row is free (no number written yet)
            if import_sheet.Cells(self.import_row_count, 1).Value2:
                self.import_row_count += 1

            # Check if space is in an analysed service
            if not self.service_check(space.service) and not self.cb_full_report.IsChecked:
                continue

            # Retrieve Revit space if it exist
            if space.id:
                revit_space = revit.doc.GetElement(space.id)
                logger.debug("IMPORT — Try to retrieve space {}".format(space.common_name))
                logger.debug(space.id, type(space.id))
                logger.debug(type(space.id))
            else:
                logger.info("L'espace {} n'a pas été trouvé".format(space.common_name))
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
                if main_worksheet.Cells(space.row, column).Value2 == parameter_value and not self.cb_full_report.IsChecked:
                    continue
                else:
                    import_sheet.Cells(self.import_row_count, 1).Value2 = space.service
                    import_sheet.Cells(self.import_row_count, index*2 + 2).Value2 = main_worksheet.Cells(space.row,
                                                                                                         column).Value2
                    import_sheet.Cells(self.import_row_count, index*2 + 3).Value2 = parameter_value
                    main_worksheet.Cells(space.row, column).Value2 = parameter_value
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
            for space in self.spaces:

                # Check if report row is free (no number written yet)
                if export_sheet.Cells(self.export_row_count, 1).Value2:
                    self.export_row_count += 1

                # Check if space is in an analysed service
                if not self.service_check(space.service):
                    continue

                # Retrieve Revit space if it exist
                if space.id:
                    revit_space = revit.doc.GetElement(space.id)
                else:
                    logger.info("L'espace {} n'a pas été trouvé".format(space.common_name))
                    continue

                # Retrieve parameter value from revit spaces
                # with unit conversion if necessary (based on Revit DisplayUnitType)
                for parameter_name, column, index in zip(parameters_list, columns_list, range(len(columns_list))):
                    parameter = revit_space.LookupParameter(parameter_name)
                    if not parameter:
                        logger.info("Parameter «{}» was not found".format(parameter_name))
                        continue
                    cell_value = main_worksheet.Cells(space.row, column).Value2
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
                                "TypeError avec la valeur {} ligne {} colonne {}". format(cell_value, space.row, column)
                            self.error_row_count += 1
                            new_parameter_value = 0

                    else:
                        continue
                    main_sheet_value = main_worksheet.Cells(space.row, column).Value2
                    if main_sheet_value == parameter_value \
                            and not self.cb_full_report.IsChecked:
                        continue
                    else:
                        export_sheet.Cells(self.export_row_count, 1).Value2 = space.service
                        export_sheet.Cells(self.export_row_count, index * 2 + 2).Value2 = parameter_value
                        if not parameter.Set(new_parameter_value):
                            main_sheet_value = "Failed to assign new value to space"
                        export_sheet.Cells(self.export_row_count, index * 2 + 3).Value2 = main_sheet_value

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

