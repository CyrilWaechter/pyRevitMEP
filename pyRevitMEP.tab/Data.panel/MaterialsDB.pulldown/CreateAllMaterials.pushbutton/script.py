#! python3
import os
import json
from pathlib import Path
from System.Collections.Generic import List
from Autodesk.Revit.DB import (
    BuiltInParameter,
    Color,
    DisplayUnitType,
    FillGrid,
    FillPattern,
    FillPatternElement,
    FillPatternHostOrientation,
    FillPatternTarget,
    FilteredElementCollector,
    Material,
    MaterialAspect,
    PropertySetElement,
    SaveAsOptions,
    StructuralAsset,
    StructuralAssetClass,
    Transaction,
    ThermalAsset,
    ThermalMaterialType,
    UnitUtils,
    UnitSystem,
    UV,
)
from Autodesk.Revit import Exceptions

from materialsdb import cache, utils, config
from materialsdb.serialiser import XmlDeserialiser


COLOR_PROP_NAMES = (
    "Color",
    "SurfaceForegroundPatternColor",
    "CutForegroundPatternColor",
)
PATTERN_PROP_NAMES = ("SurfaceForegroundPatternId", "CutForegroundPatternId")
ENUM_PROPS = {
    "HostOrientation": FillPatternHostOrientation,
    "Target": FillPatternTarget,
}
FILL_PROP_NAMES = ("Angle", "Offset", "Shift")
GROUP_GRAPHICS = {
    "Others": "SIA400_Matières synthétiques",
    "Water_Proof": "SIA400_Étanchéité (vent, vapeur, eau)",
    "Vapour_Proof": "SIA400_Étanchéité (vent, vapeur, eau)",
    "Concrete": "SIA400_Béton armé et béton non armé",
    "Wood_Timberproducts": "SIA400_Bois massif",
    "Insulation": "SIA400_Matériaux absorbants ou isolants",
    "Masonry": "SIA400_Brique de terre cuite",
    "Metal": "SIA400_Acier",
    "Mortar": "SIA400_Mortier, plâtre, crépi",
    "Plastics": "SIA400_Matières synthétiques",
    "Stone": "SIA400_Pierre natuel en général",
    "Composite": "SIA400_Mastic",
    "Films": "SIA400_Matières synthétiques",
    "Render": "SIA400_Matières synthétiques",
    "Covering": "SIA400_Mortier, plâtre, crépi",
    "Glas": "SIA400_Verre",
    "Soil": "SIA400_Agglomérés à base de ciment",
    "air": "SIA400_Air",
}


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


class MaterialCreator:
    def __init__(self, lang, country):
        self.lang = lang
        self.country = country
        self.doc = None
        self.source = None
        self.name = None
        self.description = None
        self.url = None
        self.layer_name = None
        file_path = Path(__file__).parent / "material_graphics.json"
        with file_path.open("r", encoding="utf-8") as f:
            self.graphics_dict = json.load(f)
        self.patterns_dict = {}
        self.base_fill_pattern = None

    def create_patterns(self):
        doc = self.doc
        self.base_fill_pattern = self.get_base_pattern()
        for group, graphic_name in GROUP_GRAPHICS.items():
            data = self.graphics_dict[graphic_name]
            for prop_name in PATTERN_PROP_NAMES:
                pattern = self.get_pattern(data[prop_name])
                self.patterns_dict[pattern.Name] = pattern.Id

    def get_pattern(self, data):
        doc = self.doc
        if data["IsSolidFill"]:
            for pattern in FilteredElementCollector(doc).OfClass(FillPatternElement):
                if pattern.GetFillPattern().IsSolidFill:
                    return pattern
        pattern_name = data["Name"]
        target = FillPatternTarget.Parse(FillPatternTarget, data["Target"])
        pattern = FillPatternElement.GetFillPatternElementByName(
            doc, target, pattern_name
        )
        return pattern if pattern else self.create_pattern(data)

    def get_base_pattern(self):
        for pattern_element in FilteredElementCollector(self.doc).OfClass(
            FillPatternElement
        ):
            fill_pattern = pattern_element.GetFillPattern()
            if not fill_pattern.IsSolidFill:
                return fill_pattern

    def create_pattern(self, data):
        fill_pattern = FillPattern(self.base_fill_pattern)
        fill_pattern.Name = data["Name"]
        for prop_name, enum in ENUM_PROPS.items():
            setattr(fill_pattern, prop_name, enum.Parse(enum, data[prop_name]))
        fill_grids = List[FillGrid]()
        for grid_data in data["FillGrids"]:
            fill_grids.Add(self.fill_grid_from_dict(grid_data))
        fill_pattern.SetFillGrids(fill_grids)
        return FillPatternElement.Create(self.doc, fill_pattern)

    def fill_grid_from_dict(self, data):
        fill_grid = FillGrid()
        for prop_name in FILL_PROP_NAMES:
            setattr(fill_grid, prop_name, data[prop_name])
        setattr(fill_grid, "Origin", UV(*data["Origin"]))
        setattr(fill_grid, "Segments", data["Segments"])
        return fill_grid

    def create_materials(self, doc, source):
        self.doc = doc
        self.source = source
        self.create_patterns()
        lang = self.lang
        country = self.country
        for material in utils.get_materials(source, country):
            self.material = material
            self.name = get_valid_name(utils.get_material_name(material, lang))
            self.description = str(utils.get_material_description(material, lang))
            self.url = str(utils.get_material_webinfo(material, lang).href)
            self.create_layers(material)

    def create_layers(self, material):
        doc = self.doc
        country = self.country
        for layer in utils.get_material_layers(material):
            geometry = utils.get_by_country(layer.geometry, country)
            if getattr(geometry, "thick", None):
                layer_name = f"{self.name}_{geometry.thick}mm_id({layer.id})"
            else:
                layer_name = f"{self.name}_id({layer.id})"
            revit_material = doc.GetElement(Material.Create(doc, layer_name))
            self.layer_name = layer_name
            self.set_material_identity(revit_material)
            self.create_assets(revit_material, layer)
            self.assign_graphics(revit_material, material.information.group)

    def set_material_identity(self, revit_material):
        revit_material.MaterialCategory = str(self.material.information.group)
        revit_material.get_Parameter(BuiltInParameter.ALL_MODEL_MANUFACTURER).Set(
            self.source.company
        )
        revit_material.get_Parameter(BuiltInParameter.ALL_MODEL_DESCRIPTION).Set(
            self.description
        )
        revit_material.get_Parameter(BuiltInParameter.ALL_MODEL_MODEL).Set(self.name)
        revit_material.get_Parameter(BuiltInParameter.ALL_MODEL_URL).Set(self.url)

    def create_assets(self, revit_material, layer):
        doc = self.doc
        layer_name = self.layer_name
        country = self.country
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
        # Create thermal and structural property sets
        thermal_property_set = PropertySetElement.Create(doc, thermal_asset)
        structural_property_set = PropertySetElement.Create(doc, structural_asset)
        thermal_property_set.get_Parameter(
            BuiltInParameter.PROPERTY_SET_DESCRIPTION
        ).Set(self.description)
        structural_property_set.get_Parameter(
            BuiltInParameter.PROPERTY_SET_DESCRIPTION
        ).Set(self.description)
        thermal_property_set.get_Parameter(
            BuiltInParameter.MATERIAL_ASSET_PARAM_SOURCE_URL
        ).Set(self.url)
        structural_property_set.get_Parameter(
            BuiltInParameter.MATERIAL_ASSET_PARAM_SOURCE_URL
        ).Set(self.url)
        thermal_property_set.get_Parameter(
            BuiltInParameter.MATERIAL_ASSET_PARAM_SOURCE
        ).Set("materialsdb.org")
        structural_property_set.get_Parameter(
            BuiltInParameter.MATERIAL_ASSET_PARAM_SOURCE
        ).Set("materialsdb.org")
        # Assign thermal and structural property sets to material
        revit_material.SetMaterialAspectByPropertySet(
            MaterialAspect.Thermal, thermal_property_set.Id
        )
        revit_material.SetMaterialAspectByPropertySet(
            MaterialAspect.Structural, structural_property_set.Id
        )

    def assign_graphics(self, revit_material, group):
        doc = self.doc
        graphic_name = GROUP_GRAPHICS[group]
        data = self.graphics_dict[graphic_name]
        for prop_name in COLOR_PROP_NAMES:
            setattr(revit_material, prop_name, Color(*data[prop_name]))
        for prop_name in PATTERN_PROP_NAMES:
            pattern_id = self.patterns_dict[data[prop_name]["Name"]]
            setattr(revit_material, prop_name, pattern_id)


def main():
    deserialiser = XmlDeserialiser()
    lang = config.get_lang()
    country = config.get_country()
    output_folder = cache.get_cache_folder() / "Revit"
    Path.mkdir(output_folder, parents=True, exist_ok=True)
    save_as_options = SaveAsOptions()
    save_as_options.OverwriteExistingFile = True
    save_as_options.MaximumBackups = 1
    save_as_options.Compact = True
    material_creator = MaterialCreator(lang, country)
    for producer in cache.producers():
        print(f"Creating {producer.stem}")
        source = deserialiser.from_xml(str(producer))
        doc = __revit__.Application.NewProjectDocument(UnitSystem.Metric)
        with CustomTransaction("Create materials", doc):
            material_creator.create_materials(doc, source)
        output_path = (output_folder / producer.stem).with_suffix(".rvt")
        doc.SaveAs(str(output_path), save_as_options)
        doc.Close(False)
        break

    os.startfile(output_folder)


if __name__ == "__main__":
    main()
