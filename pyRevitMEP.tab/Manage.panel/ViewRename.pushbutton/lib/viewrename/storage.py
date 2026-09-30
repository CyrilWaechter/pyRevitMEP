"""Pattern storage: ExtensibleStorage on Project Information, legacy parameter, pyRevit config.

Revit/pyRevit imports stay inside functions so the module imports locally without Revit.
"""

from . import CLASS_NAMES, codec

SCHEMA_GUID = "62444aa5-69f7-4aa6-9b0e-238dd1309f83"
SCHEMA_NAME = "pyRevitMEP_ViewRename"  # dots are rejected by Revit for schema names
FIELD_NAME = "Patterns"
LEGACY_PARAM_NAME = "pyRevitMEP_viewrename_patterns"


def _get_schema(doc, create=False):
    from Autodesk.Revit.DB.ExtensibleStorage import AccessLevel, Schema, SchemaBuilder
    from System import Guid

    schema = Schema.Lookup(Guid(SCHEMA_GUID))
    if schema is None and create:
        builder = SchemaBuilder(Guid(SCHEMA_GUID))
        builder.SetSchemaName(SCHEMA_NAME)
        builder.SetReadAccessLevel(AccessLevel.Public)
        builder.SetWriteAccessLevel(AccessLevel.Public)
        builder.AddSimpleField(FIELD_NAME, str)
        schema = builder.Finish()
    return schema


def _read_entity(doc):
    schema = _get_schema(doc)
    if schema is None:
        return ""
    entity = doc.ProjectInformation.GetEntity(schema)
    if not entity.IsValid():
        return ""
    return entity.Get[str](FIELD_NAME)


def _write_entity(doc, text):
    from Autodesk.Revit.DB.ExtensibleStorage import Entity

    schema = _get_schema(doc, create=True)
    entity = Entity(schema)
    entity.Set[str](FIELD_NAME, text)
    doc.ProjectInformation.SetEntity(entity)


def read_legacy_parameter(doc):
    parameter = doc.ProjectInformation.LookupParameter(LEGACY_PARAM_NAME)
    if not parameter:
        return {}
    return codec.decode_patterns(parameter.AsString())


def read_from_config():
    from pyrevit import script

    config = script.get_config()
    patterns = {}
    for name in CLASS_NAMES:
        value = codec.normalize_config_value(getattr(config, name, ""))
        if value:
            patterns[name] = value
    return patterns


def write_to_config(patterns):
    from pyrevit import script

    config = script.get_config()
    for name in CLASS_NAMES:
        setattr(config, name, patterns.get(name, ""))
    script.save_config()


def read_patterns(doc):
    """Read patterns with precedence: ExtensibleStorage, legacy parameter, config."""
    patterns = codec.decode_patterns(_read_entity(doc))
    if patterns:
        return patterns
    patterns = read_legacy_parameter(doc)
    if patterns:
        return patterns
    return read_from_config()


def write_to_model(doc, patterns):
    """Write patterns into the model (own transaction, on the given document)."""
    from pyrevit import revit

    text = codec.encode_patterns(patterns)
    with revit.Transaction("ViewRename: save patterns", doc):
        _write_entity(doc, text)
