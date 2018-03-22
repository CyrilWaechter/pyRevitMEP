# coding: utf8
import rpw
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import ParameterType
# noinspection PyUnresolvedReferences
from rpw import revit, DB, UI
# noinspection PyUnresolvedReferences
from System import Guid
from pyrevit.forms import WPFWindow
import csv


class SharedParameter:
    """Class used to manage Revit shared parameters
        Args:
            name (str) : Displayed shared parameter name
            group (str) : Group used in parameter definition file (shared parameter file)
            parameter_type (:obj:`Autodesk.Revit.DB.ParameterType`) : Exemple
            visible (bool)
            guid (Guid|str)
        Returns:
            None
        """
    def __init__(self, name, group, parameter_type, visible=True, guid=None):
        if not guid:
            self.guid = Guid.NewGuid()
        else:
            self.guid = guid
        self.visible = visible
        if isinstance(parameter_type, ParameterType):
            self.type = parameter_type
        else:
            try:
                self.type = getattr(ParameterType, parameter_type)
            except AttributeError:
                selected_type = rpw.ui.forms.SelectFromList("Select ParameterType",
                                                        ParameterType.GetNames(ParameterType),
                                                        "Invalid ParameterType please select a parameter type",
                                                        sort=False)
                self.type = getattr(ParameterType, selected_type)
        self.group = group
        self.name = name

    @staticmethod
    def read_from_csv(csv_path=None):
        if not csv_path:
            csv_path = rpw.ui.forms.select_file(extensions='csv Files (*.csv*)|*.csv*', title='Select File',
                                                multiple=False, restore_directory=True)

        csv_file = open(csv_path)
        file_reader = csv.reader(csv_file)

        shared_parameter_list = []

        for row in file_reader:
            row_len = len(row)
            if row_len < 3:
                print("Line {} is invalid, less than 3 column".format(file_reader.line_num))
            name, group, parameter_type = row[0:3]
            visible = True
            guid = None
            if row_len > 4:
                visible = bool(row[3])
            if row_len > 5:
                guid = Guid(row[4])

            shared_parameter_list.append(SharedParameter(name, group, parameter_type, visible, guid))
        return shared_parameter_list

    @classmethod
    def read_from_definition_file(cls, definition_groups=None, definition_names=None, definition_file=None):
        if not definition_groups:
            definition_groups = []

        if not definition_names:
            definition_names = []

        if not definition_file:
            definition_file = revit.app.OpenSharedParameterFile()
            if not definition_file:
                raise LookupError("No shared parameter file defined")

        shared_parameter_list = []

        for dg in definition_file.Groups:
            if definition_groups and dg.Name not in definition_groups:
                continue
            for dn in dg.Definitions:
                if definition_names and dn.Name not in definition_names:
                    continue
                shared_parameter_list.append(cls(dn.Name, dg.Name, dn.ParameterType, dn.Visible, dn.GUID))

        return shared_parameter_list


    def write_to_definition_file(self, definition_file=None, warning=True):
        """
        Create a new parameter definition in current shared parameter file
        :param warning: warn user if a definition with given name already exist
        :return: definition
        """
        if not definition_file:
            definition_file = revit.app.OpenSharedParameterFile()
            if not definition_file:
                raise LookupError("No shared parameter file defined")

        for dg in definition_file.Groups:
            if dg.Name == self.group:
                definition_group = dg
                break
        else:
            definition_group = definition_file.Groups.Create(self.group)

        for definition in definition_group.Definitions:
            if definition.Name == self.name:
                if warning:
                    print("A parameter definition named {} already exist")
                break
        else:
            external_definition_create_options = DB.ExternalDefinitionCreationOptions(self.name,
                                                                                      self.type,
                                                                                      GUID=self.guid,
                                                                                      Visible=self.visible)
            definition = definition_group.Definitions.Create(external_definition_create_options)

        return definition

    @staticmethod
    def create_definition_file(path_and_name):
        """Create a new DefinitionFile to store SharedParameter definitions
        Args:
            path_and_name (str): file path and name including extension (.txt file)
        Returns:
            DefinitionFile
        """
        with open(path_and_name, "w"):
            pass
        revit.app.SharedParametersFilename = path_and_name
        return revit.app.OpenSharedParameterFile()


class ProjectParameter:
    def __init__(self, definition, binding):
        self.definition = definition
        self.binding = binding
        self.category_set = None

    def __repr__(self):
        return "<{}> {}{}".format(self.__class__.__name__,
                                  self.definition.Name,
                                  [category.Name for category in self.binding.Categories])

    @classmethod
    def read_from_revit_doc(cls, doc=revit.doc):
        project_parameter_list = []
        for parameter in DB.FilteredElementCollector(doc).OfClass(DB.ParameterElement):
            definition = parameter.GetDefinition()
            binding = doc.ParameterBindings[definition]
            if binding:
                project_parameter_list.append(cls(definition, binding))
        return project_parameter_list

    @staticmethod
    def all_categories():
        category_set = revit.app.Create.NewCategorySet()
        for category in revit.doc.Settings.Categories:
            if category.AllowsBoundParameters:
                category_set.Insert(category)
        return category_set

    def create(self, category_set=None):
        if category_set is None:
            category_set = self.all_categories()


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
