import uuid
import datetime
import json
from pathlib import Path
import ifcopenshell
import ifcopenshell.api

from materialsdb.serialiser import XmlDeserialiser
from materialsdb import config, utils
from materialsdb.classes import (
    Materials,
    Material,
)

CATEGORIES = {
    "Others": {"hatch": "", "color": (255, 255, 255)},
    "Water_Proof": {"hatch": "", "color": (255, 255, 255)},
    "Vapour_Proof": {"hatch": "", "color": (0, 0, 0)},
    "Concrete": {"hatch": "", "color": (0, 255, 0)},
    "Wood_Timberproducts": {"hatch": "", "color": (91, 60, 17)},
    "Insulation": {"hatch": "", "color": (253, 108, 158)},
    "Masonry": {"hatch": "", "color": (253, 70, 38)},
    "Metal": {"hatch": "", "color": (119, 181, 254)},
    "Mortar": {"hatch": "", "color": (102, 0, 153)},
    "Plastics": {"hatch": "", "color": (96, 96, 96)},
    "Stone": {"hatch": "", "color": (0, 0, 255)},
    "Composite": {"hatch": "", "color": (112, 141, 35)},
    "Films": {"hatch": "", "color": (0, 0, 0)},
    "Render": {"hatch": "", "color": (0, 0, 0)},
    "Covering": {"hatch": "", "color": (0, 0, 0)},
    "Glas": {"hatch": "", "color": (27, 79, 8)},
    "Soil": {"hatch": "", "color": (142, 84, 52)},
}


def clean_psets(psets):
    new_dict = {}
    for pset_name, props in psets.items():
        pset_dict = {}
        for prop_name, definition in props.items():
            if definition["path"]:
                pset_dict[prop_name] = definition
        if pset_dict:
            new_dict[pset_name] = pset_dict
    return new_dict


PSETS = json.loads(Path(__file__).with_name("material_psets.json").read_text("utf-8"))
PSETS = clean_psets(PSETS)


def get_value(layer, definition, country=None):
    value = layer
    for attrib in definition["path"]:
        value = getattr(value, attrib)
        if isinstance(value, list):
            value = utils.get_by_country(value, country)
            if not value:
                return None
    return value


class ProjectLibrary:
    def __init__(self, schema: str = "IFC4"):
        self.file = ifcopenshell.file(schema=schema)
        self.application = self.create_application()
        self.project_library = None
        self.lang = config.get_lang()
        self.country = config.get_country()
        self.owner_history = None

    def create_application(self):
        file = self.file

        # https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/link/ifcaddress.htm
        address = file.createIfcAddress(
            Purpose="OFFICE",
            Description="Anton Philipslaan 199\n5616TW Eindhoven\nThe Netherlands",
        )

        # https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/link/ifcorganization.htm
        organisation = file.createIfcOrganization(
            Name="AECGeeks",
            Description="""Software development and consultancy for the
            Architecture Engineering and Construction industry""",
            Addresses=[address],
        )

        # https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/link/ifcapplication.htm
        return file.createIfcApplication(
            ApplicationDeveloper=organisation,
            Version=ifcopenshell.version,
            ApplicationFullName="IfcOpenShell",
            ApplicationIdentifier="ifcopenshell",
        )

    def create_project_library(self, source: Materials, role: str = "MANUFACTURER"):
        file = self.file

        # https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/link/ifcroleenum.htm
        role = file.createIfcActorRole(role)

        # https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/link/ifcperson.htm
        person = file.createIfcPerson(
            Identification=str(uuid.uuid4()),
            FamilyName="Unknown",
            GivenName="Unknown",
            Roles=[role],
        )

        # https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/link/ifcorganization.htm
        organisation = file.createIfcOrganization(
            Identification=source.companyid, Name=source.company, Roles=[role]
        )

        # https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/link/ifcpersonandorganization.htm
        person_and_organisation = file.createIfcPersonAndOrganization(
            person, organisation, Roles=[role]
        )

        # https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/link/ifcownerhistory.htm
        owner_history = file.createIfcOwnerHistory(
            OwningUser=person_and_organisation,
            OwningApplication=self.application,
            CreationDate=int(utils.date_from_xml(source.crd).timestamp()),
        )
        self.owner_history = owner_history

        # https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/link/ifcprojectlibrary.htm
        file.createIfcProjectLibrary(
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=owner_history,
            Name=source.company,
            Description=f"Material library converted from materialsdb xml for company {source.company}",
            ObjectType="MaterialLibrary",
            LongName=f"{source.company} version {source.ver}",
        )

    def create_materials(self, source: Materials):
        file = self.file
        context = file.createIfcRepresentationContext()
        for material in utils.get_materials(source, self.country):
            name = utils.get_material_name(material, self.lang)
            description = utils.get_material_description(material, self.lang)
            webinfo = utils.get_material_webinfo(material, self.lang)
            category = material.information.group
            labels = material.information.labels
            color = material.information.color
            brushstyle = material.information.BrushStyle
            surface_style = self.get_surface_style(color, category)
            styled_item = file.createIfcStyledItem(Styles=[surface_style])
            # TODO: hatch_item = file.createIfcFillAreaStyleHatching()
            representation = file.createIfcStyledRepresentation(
                ContextOfItems=context,
                RepresentationIdentifier="Body",
                Items=[styled_item],
            )
            for layer in getattr(getattr(material, "layers", ()), "layer", ()):
                ifc_material = file.createIfcMaterial(name, description, category)
                for pset_name, props in PSETS.items():
                    properties = list()
                    for prop_name, definition in props.items():
                        primary_measure_type = definition["primary_measure_type"]
                        if not primary_measure_type:
                            continue
                        value = get_value(layer, definition, self.country)
                        if value:
                            unit_factor = definition.get("unit_factor", None) or 1
                            properties.append(
                                file.create_entity(
                                    "IfcPropertySingleValue",
                                    Name=prop_name,
                                    NominalValue=file.create_entity(
                                        primary_measure_type, value * unit_factor
                                    ),
                                )
                            )
                    if not properties:
                        continue
                    pset = file.create_entity(
                        "IfcMaterialProperties",
                        Name=pset_name,
                        Properties=properties,
                        Material=ifc_material,
                    )
                geometry = utils.get_by_country(layer.geometry, self.country)
                if getattr(geometry, "thick", None):
                    element_name = f"{name} | {geometry.thick}mm"
                    ifc_layer = file.create_entity(
                        "IfcMaterialLayer",
                        Material=ifc_material,
                        LayerThickness=geometry.thick / 1000,
                        Name=element_name,
                    )
                    assigned_material = file.create_entity(
                        "IfcMaterialLayerSet",
                        MaterialLayers=[ifc_layer],
                        LayerSetName=element_name,
                    )
                else:
                    element_name = name
                    assigned_material = ifc_material
                if material.information.wall:
                    wall = file.create_entity(
                        "IfcWallType",
                        GlobalId=ifcopenshell.guid.new(),
                        Name=element_name,
                    )
                    ifcopenshell.api.run(
                        "material.assign_material",
                        file,
                        product=wall,
                        material=assigned_material,
                    )
                if material.information.roof:
                    roof = file.create_entity(
                        "IfcRoofType",
                        GlobalId=ifcopenshell.guid.new(),
                        Name=element_name,
                    )
                    ifcopenshell.api.run(
                        "material.assign_material",
                        file,
                        product=roof,
                        material=assigned_material,
                    )
                if material.information.floor:
                    slab = file.create_entity(
                        "IfcRoofType",
                        GlobalId=ifcopenshell.guid.new(),
                        Name=element_name,
                    )
                    ifcopenshell.api.run(
                        "material.assign_material",
                        file,
                        product=slab,
                        material=assigned_material,
                    )
                if material.information.door:
                    door = file.create_entity(
                        "IfcDoorType",
                        GlobalId=ifcopenshell.guid.new(),
                        Name=element_name,
                    )
                    ifcopenshell.api.run(
                        "material.assign_material",
                        file,
                        product=door,
                        material=assigned_material,
                    )

    def get_surface_style(self, color, category):
        file = self.file
        if color:
            name = f"color {color}"
            style = file.createIfcSurfaceStyleShading(
                SurfaceColour=self.color_xml_to_ifc(color)
            )
        else:
            if not category:
                category = "Others"
            name = f"category {category}"
            for style in file.by_type("IfcSurfaceStyle"):
                if style.Name == name:
                    return style
            style = file.createIfcSurfaceStyleShading(
                SurfaceColour=self.file.createIfcColourRgb(
                    None, *CATEGORIES[category]["color"]
                ),
            )
        for surface_style in file.by_type("IfcSurfaceStyle"):
            if surface_style.Name == name:
                return surface_style
        return file.createIfcSurfaceStyle(Name=name, Side="BOTH", Styles=[style])

    def color_xml_to_ifc(self, color: int):
        """Color definition in xml is obscur. We assume that it is a decimal color.
        See: https://stackoverflow.com/a/2262152/4098083"""
        return self.file.createIfcColourRgb(
            Blue=color & 255, Green=(color >> 8) & 255, Red=(color >> 16) & 255
        )


def create_project_library_from_xml(xml_path):
    library = ProjectLibrary()
    deserialiser = XmlDeserialiser()
    source = deserialiser.from_xml(str(xml_path))
    library.create_project_library(source)
    library.create_materials(source)
    return library.file


def main():
    file = create_project_library_from_xml("example_v103.xml")
    file.write("example_v103.xml")


if __name__ == "__main__":
    main()
