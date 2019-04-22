# coding: utf8

import csv

from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter, Parameter, UnitUtils, \
    DisplayUnitType
from Autodesk.Revit.DB.Mechanical import Space

import rpw
from pyrevit import script

doc = rpw.revit.doc
logger = script.get_logger()

path = r""

with open(path, 'rb') as csvfile:
    file_reader = csv.reader(csvfile, delimiter='\t')

    # Skip first 2 lines
    file_reader.next()
    file_reader.next()

    with rpw.db.Transaction('Import heating/cooling', doc):
        for row in file_reader:
            number = '{}.{}'.format(row[0][0], row[0][1:3])
            for space in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_MEPSpaces):  # type: Space
                if space.Number == number:
                    hl_param = space.get_Parameter(BuiltInParameter.ROOM_DESIGN_HEATING_LOAD_PARAM)  # type: Parameter
                    hl_param.Set(UnitUtils.ConvertToInternalUnits(float(row[9]), DisplayUnitType.DUT_WATTS))
                    cl_param = space.get_Parameter(BuiltInParameter.ROOM_DESIGN_COOLING_LOAD_PARAM)  # type: Parameter
                    cl_param.Set(UnitUtils.ConvertToInternalUnits(float(row[12]), DisplayUnitType.DUT_WATTS))
                    break
            else:
                logger.info('Following space not found : {}'.format(number))
