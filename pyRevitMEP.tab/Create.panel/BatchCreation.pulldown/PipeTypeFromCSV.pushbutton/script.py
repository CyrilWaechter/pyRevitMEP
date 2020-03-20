# coding: utf8

import csv

from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    BuiltInParameter,
    Parameter,
    UnitUtils,
    DisplayUnitType,
    Document,
    MEPSize,
    Material,
)
from Autodesk.Revit.DB.Plumbing import PipeSegment, PipeScheduleType

import rpw
from pyrevit import script, forms, revit

doc = __revit__.ActiveUIDocument.Document  # type: Document
logger = script.get_logger()


def read_csv(csv_path):
    size_set = List[MEPSize]()
    with open(csv_path, "rb") as csvfile:
        reader = csv.reader(csvfile, delimiter="\t")
        headers = next(reader)
        for row in reader:
            nominal_diameter = convert_to_internal(row[1])
            inner_diameter = convert_to_internal(row[2])
            outer_diameter = convert_to_internal(row[3])
            used_in_size_lists = True
            used_in_sizing = True
            mep_size = MEPSize(
                nominal_diameter,
                inner_diameter,
                outer_diameter,
                used_in_size_lists,
                used_in_sizing,
            )
            size_set.Add(mep_size)
    return size_set


def convert_to_internal(value, unit="mm"):
    return UnitUtils.ConvertToInternalUnits(
        float(value), DisplayUnitType.DUT_MILLIMETERS
    )


csv_path = forms.pick_file(file_ext="csv")

if csv_path:
    with revit.Transaction("Create PipeType from csv"):
        name = forms.ask_for_string(
            default="ScheduleName",
            prompt="Enter a schedule name eg. SDR6 or EN10217-1 serie 2",
            title="PipeTypeCreation",
        )
        schedule_id = PipeScheduleType.Create(doc, name).Id

        size_set = read_csv(csv_path)

        materials = [
            (material.Name, material.Id)
            for material in FilteredElementCollector(doc).OfClass(Material)
        ]
        material = forms.SelectFromList.show(
            materials,
            multiselect=False,
            button_name="Select material",
            title="PipeTypeCreation",
        )
        if material:
            material_id = material[1]
        else:
            name = forms.ask_for_string(
                default="MaterialName",
                prompt="Enter a new material name eg. PP-R or Steel",
                title="PipeTypeCreation",
            )
            material_id = Material.Create()
        PipeSegment.Create(doc, material_id, schedule_id, size_set)

