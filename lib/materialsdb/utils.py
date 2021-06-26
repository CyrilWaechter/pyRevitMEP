import datetime
from typing import Generator
from materialsdb.classes import (
    TDateTime,
    TLocalizedString,
    Mimetype,
    Webinfo,
    ISO639_1,
    Materials,
    Material,
    Layer,
)


def date_from_xml(days: float) -> datetime.datetime:
    """Convert days since 30.12.1899 which is materialsdb xml convention to datetime"""
    return datetime.datetime(1899, 12, 30) + datetime.timedelta(days=days)


def date_to_xml(date: datetime.datetime) -> float:
    """Convert datetime to days since 30.12.1899 which is materialsdb xml convention
    >>> datetime.timedelta(days=1).total_seconds()
    86400.0"""
    return (
        date - datetime.datetime(1899, 12, 30, tzinfo=datetime.timezone.utc)
    ).total_seconds() / 86400


def new_tdatetime():
    return TDateTime(date_to_xml(datetime.datetime.now(datetime.timezone.utc)))


def get_materials(
    materials: Materials, country: str, include_outdated=False
) -> Generator[Material, None, None]:
    for material in materials.material:
        if include_outdated:
            yield material
            continue
        material_countries = getattr(
            getattr(material.information, "countries", ()), "country", ()
        )
        if not material_countries:
            yield material
            continue
        for material_country in material_countries:
            if not material_country == country:
                break
        else:
            continue
        current_datetime = date_to_xml(datetime.datetime.now(tz=datetime.timezone.utc))
        selling_from = material_country.sellingfrom
        selling_until = getattr(material_country, "sellinguntil", None) or 10 ** 66
        if selling_from < current_datetime and selling_until > current_datetime:
            yield material


def get_material_name(material: Material, lang: str) -> TLocalizedString:
    name = TLocalizedString("")
    for name in material.information.names.name:
        if name.lang == lang or not name.lang:
            return name
    return name


def get_material_description(material: Material, lang: str) -> TLocalizedString:
    description = TLocalizedString("")
    explanations = getattr(material.information, "explanations", None)
    for description in getattr(explanations, "explanation", ()):
        if description.lang == lang:
            return description
    return description


def get_material_webinfo(material: Material, lang: str) -> Webinfo:
    webinfo = Webinfo(Mimetype(""), "", "", lang=ISO639_1(lang))
    webinfos = getattr(material.information, "webinfos", None)
    for webinfo in getattr(webinfos, "webinfo", ()):
        if webinfo.lang == lang:
            return webinfo
    return webinfo


def get_material_layers(material: Material) -> Generator[Layer, None, None]:
    for layer in getattr(getattr(material, "layers", ()), "layer", ()):
        yield layer


def get_by_country(values, country):
    for value in values:
        if value.country == country:
            return value
    for value in values:
        if value.country is None:
            return value
