# coding: UTF-8
"""This module serialise/deserialise materials from different schema/format.

© All rights reserved.
ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE, Switzerland, Laboratory CNPA, 2019-2020

See the LICENSE.md file for more details.

Author : Cyril Waechter
"""
import re
from pathlib import Path
import typing
from typing import Protocol, Tuple, Dict, Type, Optional, Any, Union

from lxml import objectify, etree

from materialsdb import classes


def get_xml_schema() -> str:
    return str(Path(__file__).parent / "schema/materialsdb103.xsd")


def get_element_name(element: objectify.ObjectifiedElement) -> str:
    m = re.search("{.*}(.*)", element.tag)
    return m.group(1) if m else element.tag


def create_element_maker():
    nsmap = {
        None: "http://www.materialsdb.org",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "SchemaLocation": "http://www.materialsdb.org/schemas/materialsdb103.xsd",
    }
    return objectify.ElementMaker(
        namespace="http://www.materialsdb.org", nsmap=nsmap, annotate=False
    )


def get_valid_root(tree: objectify.ObjectifiedElement) -> str:
    root = tree.getroot()
    for attr in ("sig", "publickey"):
        if not hasattr(root, attr):
            oem = create_element_maker()
            print(
                f"{Path(root.base).name}: Element '{attr}' is missing from '{root.tag}'"
            )
            root.append(oem(attr, "Missing '{attr}'", {"ver": 0}))
    return root


class XmlDeserialiser:
    def __init__(self):
        self.schema = etree.XMLSchema(file=get_xml_schema())
        self.parser = objectify.makeparser(schema=self.schema)

    def from_xml(self, xml_path: str, assert_schema: bool = False) -> classes.Materials:
        if assert_schema:
            tree = objectify.parse(xml_path, self.parser)
        else:
            tree = objectify.parse(xml_path)
        return self.from_element(get_valid_root(tree))

    def from_element(self, element=None, base_class=None):
        element_name = get_element_name(element)
        element_class = base_class or getattr(classes, self.cls_name(element_name))
        kwargs: Dict[str, Any] = {}
        if element_class.xs_type != "element":
            kwargs["object"] = element.text or ""
        type_hints = typing.get_type_hints(element_class)
        for attrib in getattr(element_class, "xml_attributes", ()):
            value = element.get(attrib)
            if value is None:
                continue
            base_class = self.strip_optional(type_hints[attrib])

            kwargs[attrib] = base_class(value)
        for child_name in getattr(element_class, "xml_elements", ()):
            type_hint = type_hints[child_name]
            base_class = self.strip_optional(type_hint)
            if typing.get_origin(base_class) is list:
                value = []
                inner_type = typing.get_args(base_class)[0]
                for child in getattr(element, child_name, ()):
                    try:
                        value.append(self.from_element(child, inner_type))
                    except TypeError as err:
                        print(
                            f"{Path(child.base).name}: Element '{child_name}' line {child.sourceline} seems invalid:\n\t{err}"
                        )
                kwargs[child_name] = value
            else:
                child = getattr(element, child_name, None)
                if child is not None:
                    kwargs[child_name] = self.from_element(child, base_class)

        return element_class(**kwargs)

    def strip_optional(self, type_hint):
        if self.is_optional(type_hint):
            return typing.get_args(type_hint)[0]
        return type_hint

    def is_optional(self, type_hint):
        return typing.get_origin(type_hint) is typing.Union and typing.get_args(
            type_hint
        )[1] is type(None)

    def cls_name(self, name: str) -> str:
        return name if name[0].isupper() else name.title()


class XmlSerialiser:
    def __init__(self):
        self.schema = etree.XMLSchema(file=get_xml_schema())
        self.parser = objectify.makeparser(schema=self.schema)
        self.oem = create_element_maker()

    def to_xml(self, source: classes.Materials, xml_path: str) -> None:
        xml_root = self.serialise(source)
        objectify.deannotate(xml_root, xsi_nil=True)
        xml_str = etree.tostring(
            xml_root,
            encoding="UTF-8",
            xml_declaration=True,
            pretty_print=True,
            standalone=False,
        )
        with open(xml_path, "wb") as file:
            file.write(xml_str)

    def serialise(self, element, name: str = None):
        # Process base element with attribute and text value
        kwargs = {}
        for attrib in getattr(element, "xml_attributes", ()):
            value = getattr(element, attrib)
            if value is None:
                continue
            kwargs[attrib] = str(value)
        text = element if element.xs_type != "element" else None
        name = name or element.xml_name
        xml_element = self.oem(name, text, **kwargs)
        # Process child elements and their childs recursively
        for child_name in getattr(element, "xml_elements", ()):
            childs = getattr(element, child_name, None)
            if childs is None:
                continue
            if not isinstance(childs, list):
                childs = (childs,)
            for child in childs:
                xml_element.append(self.serialise(child, child_name))

        return xml_element


def main():
    xml_path = "example_v103.xml"
    deserialiser = XmlDeserialiser()
    sources = []
    sources.append(deserialiser.from_xml(xml_path))
    serialiser = XmlSerialiser()
    serialiser.to_xml(sources[0], xml_path="test.xml")


if __name__ == "__main__":
    main()
