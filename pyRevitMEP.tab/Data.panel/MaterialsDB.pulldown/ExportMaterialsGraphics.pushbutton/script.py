#! python3
from pathlib import Path
import json
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Material,
    FillPatternHostOrientation,
    FillPatternTarget,
)

doc = __revit__.ActiveUIDocument.Document


color_prop_names = (
    "Color",
    "SurfaceForegroundPatternColor",
    "CutForegroundPatternColor",
)
pattern_prop_names = ("SurfaceForegroundPatternId", "CutForegroundPatternId")
enum_props = {
    "HostOrientation": FillPatternHostOrientation,
    "Target": FillPatternTarget,
}
bool_prop_names = ("IsSolidFill",)
fill_prop_names = ("Angle", "Offset", "Shift")
segment_prop_names = ()


def color_to_tuple(color):
    return (color.Red, color.Green, color.Blue)


def uv_to_tuple(uv):
    return (uv.U, uv.V)


def fill_grid_to_dict(fill_grid):
    data = {}
    for prop_name in fill_prop_names:
        data[prop_name] = getattr(fill_grid, prop_name)
    data["Origin"] = uv_to_tuple(getattr(fill_grid, "Origin"))
    data["Segments"] = [segment for segment in fill_grid.GetSegments()]
    return data


def pattern_to_dict(pattern_element):
    pattern = pattern_element.GetFillPattern()
    data = {}
    data["Name"] = pattern.Name
    for prop_name, enum in enum_props.items():
        prop_value = getattr(pattern, prop_name)
        value = enum.GetName(enum, prop_value)
        data[prop_name] = value
    for prop_name in bool_prop_names:
        data[prop_name] = getattr(pattern, prop_name)
    data["FillGrids"] = [
        fill_grid_to_dict(fill_grid) for fill_grid in pattern.GetFillGrids()
    ]
    return data


graph_dict = {}


for material in FilteredElementCollector(doc).OfClass(Material):
    print(material.Name)
    if not material.Name.startswith("SIA400"):
        continue
    data = {}
    for prop_name in color_prop_names:
        data[prop_name] = color_to_tuple(getattr(material, prop_name))
    for prop_name in pattern_prop_names:
        data[prop_name] = pattern_to_dict(doc.GetElement(getattr(material, prop_name)))
    graph_dict[material.Name] = data

file_path = (
    Path(__file__).parent.parent
    / r"CreateAllMaterials.pushbutton\material_graphics.json"
)

with file_path.open("w") as f:
    json.dump(graph_dict, f)
