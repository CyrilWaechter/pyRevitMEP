#! python3
import os
from pathlib import Path
from Autodesk.Revit.DB import (
    Material,
    Transaction,
    BuiltInParameter,
    ThermalAsset,
    StructuralAsset,
    ThermalMaterialType,
    StructuralAssetClass,
    PropertySetElement,
    UnitUtils,
    DisplayUnitType,
    UnitSystem,
    SaveAsOptions,
)
from Autodesk.Revit import Exceptions

from materialsdb import cache, utils, config
from materialsdb.serialiser import XmlDeserialiser


class CustomTransaction:
    def __init__(self, name, doc):
        self.transaction = Transaction(doc, name)

    def __enter__(self):
        self.transaction.Start()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type:
            self.transaction.RollBack()
            return
        self.transaction.Commit()


def get_valid_name(name):
    """In Revit API following characters are not allowed for material names: \:{}[]|<>?`~"""
    return (
        str(name)
        .split("\n")[0]
        .replace(":", "_")
        .replace("{", "(")
        .replace("}", ")")
        .replace("[", "(")
        .replace("]", ")")
        .replace("|", "_")
        .replace("<", "(")
        .replace(">", "]")
        .replace("?", "")
        .replace("`", "’")
        .replace("~", "")
    )


def create_materials(source, lang, country):
    for material in utils.get_materials(source, country):
        name = get_valid_name(utils.get_material_name(material, lang))
        description = str(utils.get_material_description(material, lang))
        url = str(utils.get_material_webinfo(material, lang).href)
        for layer in utils.get_material_layers(material):
            geometry = utils.get_by_country(layer.geometry, country)
            if getattr(geometry, "thick", None):
                layer_name = f"{name}_{geometry.thick}mm_id({layer.id})"
            else:
                layer_name = f"{name}_id({layer.id})"
            revit_material = doc.GetElement(Material.Create(doc, layer_name))
            # Set material properties
            revit_material.MaterialCategory = str(material.information.group)
            revit_material.get_Parameter(BuiltInParameter.ALL_MODEL_MANUFACTURER).Set(
                source.company
            )
            revit_material.get_Parameter(BuiltInParameter.ALL_MODEL_DESCRIPTION).Set(
                description
            )
            revit_material.get_Parameter(BuiltInParameter.ALL_MODEL_MODEL).Set(name)
            revit_material.get_Parameter(BuiltInParameter.ALL_MODEL_URL).Set(url)
            # revit_material.AppearanceAssetId = None
            # Set physical and thermal properties
            thermal_asset = ThermalAsset(layer_name, ThermalMaterialType.Solid)
            structural_asset = StructuralAsset(layer_name, StructuralAssetClass.Basic)
            thermal = utils.get_by_country(layer.thermal, country)
            physical = utils.get_by_country(layer.physical, country)
            density = getattr(physical, "density", 0)
            if density:
                thermal_asset.Density = (
                    structural_asset.Density
                ) = UnitUtils.ConvertToInternalUnits(
                    density,
                    DisplayUnitType.DUT_KILOGRAMS_PER_CUBIC_METER,
                )
            thermal_asset.Porosity = getattr(physical, "Porosity", 0) or 0
            specific_heat_capacity = (getattr(thermal, "therm_capa", 0) or 0) * 3600
            if specific_heat_capacity:
                thermal_asset.SpecificHeat = UnitUtils.ConvertToInternalUnits(
                    specific_heat_capacity,
                    DisplayUnitType.DUT_JOULES_PER_KILOGRAM_CELSIUS,
                )
            thermal_conductivity = getattr(thermal, "lambda_value", 0) or 0
            if thermal_conductivity:
                thermal_asset.ThermalConductivity = UnitUtils.ConvertToInternalUnits(
                    thermal_conductivity,
                    DisplayUnitType.DUT_WATTS_PER_METER_KELVIN,
                )
            thermal_property_set = PropertySetElement.Create(doc, thermal_asset)
            structural_property_set = PropertySetElement.Create(doc, structural_asset)
            thermal_property_set.get_Parameter(
                BuiltInParameter.PROPERTY_SET_DESCRIPTION
            ).Set(description)
            structural_property_set.get_Parameter(
                BuiltInParameter.PROPERTY_SET_DESCRIPTION
            ).Set(description)
            thermal_property_set.get_Parameter(
                BuiltInParameter.MATERIAL_ASSET_PARAM_SOURCE_URL
            ).Set(url)
            structural_property_set.get_Parameter(
                BuiltInParameter.MATERIAL_ASSET_PARAM_SOURCE_URL
            ).Set(url)
            thermal_property_set.get_Parameter(
                BuiltInParameter.MATERIAL_ASSET_PARAM_SOURCE
            ).Set("materialsdb.org")
            structural_property_set.get_Parameter(
                BuiltInParameter.MATERIAL_ASSET_PARAM_SOURCE
            ).Set("materialsdb.org")
            revit_material.ThermalAssetId = structural_property_set.Id
            revit_material.StructuralAssetId = thermal_property_set.Id


deserialiser = XmlDeserialiser()
lang = config.get_lang()
country = config.get_country()
output_folder = cache.get_cache_folder() / "Revit"
Path.mkdir(output_folder, parents=True, exist_ok=True)
save_as_options = SaveAsOptions()
save_as_options.OverwriteExistingFile = True
save_as_options.MaximumBackups = 1
save_as_options.Compact = True
for producer in cache.producers():
    source = deserialiser.from_xml(str(producer))
    doc = __revit__.Application.NewProjectDocument(UnitSystem.Metric)
    with CustomTransaction("Create materials", doc):
        create_materials(source, lang, country)
    output_path = (output_folder / producer.stem).with_suffix(".rvt")
    doc.SaveAs(str(output_path), save_as_options)
    doc.Close(False)
    break

os.startfile(output_folder)
