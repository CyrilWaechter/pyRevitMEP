# coding: utf8
import os

from Autodesk.Revit.DB import (
    Element,
    FilteredElementCollector,
    BuiltInParameter,
    MEPSystemType,
    ElementId,
)
from pyrevit import revit
from pyrevit.script import get_logger
from pyrevit.forms import WPFWindow
from System.Collections.Generic import List

__doc__ = "Batch create MEPSystemTypes from a sheet file"
__title__ = "MEPSystemTypes"
__author__ = "Cyril Waechter"

doc = __revit__.ActiveUIDocument.Document  # type: Document

logger = get_logger()

from pyrevitmep import excel

xl_app = excel.initialise()

# Create a workbook with designated file as template
temp_template_path = os.path.join(__commandpath__, "ImportExportTemplate.xlsx")
temp_workbook = xl_app.Workbooks.Add(temp_template_path)
import_sheet = temp_workbook.Sheets("Import")
export_sheet = temp_workbook.Sheets("Export")
error_sheet = temp_workbook.Sheets("ScriptError")


class Gui(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.import_row_count = 3
        self.export_row_count = 3
        self.error_row_count = 1
        self.mep_system_type_dict = {}

    @property
    def number_column(self):
        return self.tb_space_number_column.Text

    @property
    def starting_row(self):
        return int(self.tb_space_number_starting_row.Text)

    def sheet_loop_generator(self, worksheet):
        row_count = 2
        number_column = 1

        while worksheet.Cells(row_count, number_column).Value2:
            current_row = row_count
            row_count += 1
            yield current_row

    # noinspection PyUnusedLocal
    def test_click(self, sender, e):
        value = self.main_worksheet.Cells(7, "DY").Value2
        print(type(value))
        print(value)

    # noinspection PyUnusedLocal
    def export_click(self, sender, e):
        row_count = 2
        for mep_system_type in FilteredElementCollector(doc).OfClass(MEPSystemType):
            name = Element.Name.__get__(mep_system_type)
            abv = mep_system_type.get_Parameter(
                BuiltInParameter.RBS_SYSTEM_ABBREVIATION_PARAM
            ).AsString()
            system_classification = mep_system_type.SystemClassification.ToString()
            revit_id = mep_system_type.Id

            for column, param_value in enumerate((name, abv, system_classification), 1):
                try:
                    export_sheet.Cells(row_count, column).Value2 = param_value
                except EnvironmentError:
                    logger.debug(param_value)

            self.mep_system_type_dict[name] = revit_id
            row_count += 1
        logger.debug(self.mep_system_type_dict)

    # noinspection PyUnusedLocal
    def import_click(self, sender, e):
        names = []
        abbreviations = []
        id_list = List[ElementId]()
        with revit.Transaction("BatchCreateSystemTypes"):
            for row in self.sheet_loop_generator(import_sheet):
                # Get inputs from sheet
                name = import_sheet.Cells(row, 1).Value2
                abv = import_sheet.Cells(row, 2).Value2
                base_system_type_name = import_sheet.Cells(row, 3).Value2

                # Duplicate existing type with desired new name and optional abbreviation
                new_type = doc.GetElement(
                    self.mep_system_type_dict[base_system_type_name]
                ).Duplicate(name)
                if abv:
                    abv_param = new_type.get_Parameter(
                        BuiltInParameter.RBS_SYSTEM_ABBREVIATION_PARAM
                    )
                    abv_param.Set(abv)

    # noinspection PyUnusedLocal
    def window_closed(self, sender, e):
        temp_workbook.Close(False)

        # Release COM Object
        logger.debug("RELEASE EXCEL COM OBJECT ON WINDOW CLOSED")
        excel.release(xl_app)


gui = Gui("WPFWindow.xaml")
gui.ShowDialog()
