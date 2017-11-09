# coding: utf8
import rpw
from rpw import revit, DB, UI


def create_shared_parameter_definition(revit_app, name, group_name, parameter_type, visible=True):
    # Open shared parameter file
    definition_file = revit_app.OpenSharedParameterFile()
    if not definition_file:
        raise LookupError("No shared parameter file")

    for dg in definition_file.Groups:
        if dg.Name == group_name:
            definition_group = dg
            break
    else:
        definition_group = definition_file.Groups.Create(group_name)

    for definition in definition_group.Definitions:
        if definition.Name == name:
            break
    else:
        external_definition_create_options = DB.ExternalDefinitionCreationOptions(name, parameter_type)
        definition = definition_group.Definitions.Create(external_definition_create_options)

    return definition


def create_project_parameter(revit_app, definition, category_set, built_in_parameter_group, instance):
    if instance:
        binding = revit_app.Create.NewInstanceBinding(category_set)
    else:
        binding = revit.app.Create.NewTypeBinding(category_set)
    parameter_bindings = revit.doc.ParameterBindings
    parameter_bindings.Insert(definition, binding, built_in_parameter_group)
