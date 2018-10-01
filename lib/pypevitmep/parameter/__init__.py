# coding: utf8

import os
import csv

from System import Guid, Enum

from Autodesk.Revit import Exceptions
from Autodesk.Revit.DB import ParameterType, DefinitionFile, DefinitionGroup, InstanceBinding, \
    ExternalDefinition, ExternalDefinitionCreationOptions, Definition, BuiltInParameter, Parameter, \
    ElementBinding, Category, LabelUtils, BuiltInParameterGroup, DefinitionBindingMapIterator, Document

import rpw
from rpw import revit
from pyrevit.forms import alert

# from manageshared import ManageSharedParameter


class WParameter(rpw.db.Parameter):
    def __repr__(self):
        try:
            guid = self.GUID
        except Exceptions.InvalidOperationException:
            guid = ""
        return "{} <{}> <{}>".format(self.name, self.builtin, guid)


class SharedParameter:
    """
    Class used to manage Revit shared parameters
    :param name: Displayed shared parameter name
    :param group: Group used in parameter definition file (shared parameter file)
    :param type : Parameter type like Text, PipingFlow etc…
    :param guid: Parameter globally unique identifier
    :param description: Parameter description hint
    :param user_modifiable: This property indicates whether this parameter can be modified by UI user or not.
    :param visible: If false parameter is stored without being visible.
    """
    def __init__(self, name, ptype, group="pypevitmep", guid=None,
                 description="", modifiable=True, visible=True, new=True):
        # type: (str, ParameterType or str, str, Guid or None, str, bool, bool, bool) -> None

        self.name = name
        self.description = description
        self.group = group

        true_tuple = (True, "", None, "True", "Yes", "Oui", 1)

        if modifiable in true_tuple:
            self.modifiable = True
        else:
            self.modifiable = False

        if visible in true_tuple:
            self.visible = True
        else:
            self.visible = False

        # Check if a Guid is given. If not a new one is created
        if not guid:
            self.guid = Guid.NewGuid()
        else:
            self.guid = guid
        # Check if given parameter type is valid. If not user is prompted to choose one.
        if isinstance(ptype, ParameterType):
            self.type = ptype
        else:
            try:
                self.type = getattr(ParameterType, ptype)
            except AttributeError:
                selected_type = rpw.ui.forms.SelectFromList(
                    "Select ParameterType",
                    ParameterType.GetNames(ParameterType),
                    "Parameter {} ParameterType: {} is not valid. Please select a parameter type".format(name, ptype),
                    sort=False)
                self.type = getattr(ParameterType, selected_type)

        self.initial_values = {}
        if new is True:
            self.new = new
        else:
            self.new = False
            self.initial_values_update()

        self.changed = False

    def __repr__(self):
        return "<{}> {} {}".format(self.__class__.__name__, self.name, self.guid)

    @classmethod
    def get_definition_file(cls):
        # type: () -> DefinitionFile
        try:
            return revit.app.OpenSharedParameterFile()
        except Exceptions.InternalException:
            return

    def get_definitiongroup(self, definition_file=None):
        # type: (DefinitionFile) -> DefinitionGroup
        if not definition_file:
            definition_file = self.get_definition_file()
        return definition_file.Groups[self.group]

    def get_definition(self, definition_file=None):
        try:
            return self.get_definitiongroup(definition_file).Definitions[self.name]
        except AttributeError as e:
            alert("default error message : {} \n"
                  "Unable to retrieve definition for parameter named {}".format(e.message ,self.name))

    @classmethod
    def get_definition_by_name(cls, name):
        # type: (str) -> ExternalDefinition
        for group in cls.get_definition_file().Groups:  # type: DefinitionGroup
            for definition in group.Definitions:  # type: ExternalDefinition
                if definition.Name == name:
                    return definition

    def initial_values_update(self):
        self.initial_values = {"name": self.name, "type": self.type, "group": self.group,
                               "guid": self.guid, "description": self.description, "modifiable": self.modifiable,
                               "visible": self.visible}

    @staticmethod
    def read_from_csv(csv_path=None):
        """
        Retrieve shared parameters from a csv file.
        csv file need to be formatter this way :
        <Parameter Name>, <ParameterType>, <DefinitionGroup>, (Optional)<Guid>,(Optional)<Description>,
        (Optional)<UserModifiable> True or False, (Optional)<Visible> True or False
        :param csv_path: absolute path to csv file
        """
        if not csv_path:
            csv_path = rpw.ui.forms.select_file(extensions='csv Files (*.csv*)|*.csv*', title='Select File',
                                                multiple=False, restore_directory=True)
            if not csv_path:
                raise ValueError("No file selected")
        shared_parameter_list = []

        with open(csv_path, "r") as csv_file:
            file_reader = csv.reader(csv_file)
            file_reader.next()

            for row in file_reader:
                shared_parameter_list.append(SharedParameter(*row, new=False))

        return shared_parameter_list

    @classmethod
    def read_from_definition_file(cls, definition_groups=None, definition_names=None, definition_file=None):
        # type: (list, list, DefinitionFile) -> list
        """
        Retrieve definitions from a definition file
        """
        if not definition_groups:
            definition_groups = []

        if not definition_names:
            definition_names = []

        if not definition_file:
            definition_file = cls.get_definition_file()

        shared_parameter_list = []

        for dg in definition_file.Groups:
            if definition_groups and dg.Name not in (dg.Name for dg in definition_groups):
                continue
            for definition in dg.Definitions:
                if definition_names and definition.Name not in definition_names:
                    continue
                shared_parameter_list.append(cls(definition.Name,
                                                 definition.ParameterType,
                                                 dg.Name,
                                                 definition.GUID,
                                                 definition.Description,
                                                 definition.UserModifiable,
                                                 definition.Visible,
                                                 False
                                                 )
                                             )

        return shared_parameter_list

    def write_to_definition_file(self, definition_file=None, warning=True):
        # type: (DefinitionFile, bool) -> ExternalDefinition
        """
        Create a new parameter definition in current shared parameter file
        :param definition_file: (Optional) definition file
        :param warning: (Optional) Warn user if a definition with given name already exist
        :return: External definition which have just been written
        """
        if not definition_file:
            definition_file = self.get_definition_file()

        if not self.group:
            self.group = "pypevitmep"

        definition_group = definition_file.Groups[self.group]
        if not definition_group:
            definition_group = definition_file.Groups.Create(self.group)

        if definition_group.Definitions[self.name] and warning:
            alert("A parameter definition named {} already exist".format(self.name))
            return
        else:
            external_definition_create_options = ExternalDefinitionCreationOptions(self.name,
                                                                                   self.type,
                                                                                   GUID=self.guid,
                                                                                   UserModifiable=self.modifiable,
                                                                                   Description=self.description,
                                                                                   Visible=self.visible)
            definition = definition_group.Definitions.Create(external_definition_create_options)
        self.initial_values_update()
        self.new = self.changed = False
        return

    @staticmethod
    def delete_from_definition_file(shared_parameters, definition_file=None, warning=True):
        # type: (List[SharedParameter], DefinitionFile, bool) -> None
        if definition_file is None:
            definition_file = SharedParameter.get_definition_file()
        file_path = definition_file.Filename
        tmp_file_path = "{}.tmp".format(file_path)

        with open(file_path, 'r') as file, open(tmp_file_path, 'wb') as file_tmp:
            group_dict = {}
            for line in file:
                row = line.strip("\n").strip("\x00").strip("\r").decode('utf-16').split("\t")
                if row[0] == "GROUP":
                    group_dict[row[1]] = row[2]
                    file_tmp.write(line)
                elif row[0] == "PARAM":
                    for definition in shared_parameters:
                        if row[2] == definition.name and group_dict[row[5]] == definition.group:
                            break
                    else:
                        file_tmp.write(line)
                else:
                    file_tmp.write(line)

        # Remove temp files and rename modified file to original file name
        os.remove(file_path)
        os.rename(tmp_file_path, file_path)

    @classmethod
    def create_definition_file(cls, path_and_name=None):
        """Create a new DefinitionFile to store SharedParameter definitions
        :param path_and_name: file path and name including extension (.txt file)
        :rtype: DefinitionFile
        """
        if path_and_name is None:
            path = rpw.ui.forms.select_folder()
            path_and_name = rpw.ui.forms.TextInput("name", r"{}\pyrevitmep_sharedparameters.txt".format(path), False)
        with open(path_and_name, "w"):
            pass
        rpw.revit.app.SharedParametersFilename = path_and_name
        return cls.get_definition_file()

    @classmethod
    def change_definition_file(cls):
        path = rpw.ui.forms.select_file()
        if path:
            rpw.revit.app.SharedParametersFilename = path
            return cls.get_definition_file()


class ProjectParameter:
    def __init__(self, definition, binding):
        # type: (Definition, ElementBinding) -> None
        self.definition = definition
        self.binding = binding
        self.category_set = binding.Categories
        self.bip_group =  BipGroup(definition.ParameterGroup)
        self.pt_name = LabelUtils.GetLabelFor(definition.ParameterType)
        self.ut_name = LabelUtils.GetLabelFor(definition.UnitType)
        if isinstance(binding, InstanceBinding):
            self.is_instance = True
        else:
            self.is_instance = False

    def __repr__(self):
            return "<{}> {}".format(self.__class__.__name__, self.definition.Name)

    @property
    def name(self):
        return self.definition.Name

    @property
    def parameter_type(self):
        return self.definition.ParameterType

    @property
    def unit_type(self):
        return self.definition.UnitType

    @classmethod
    def read_from_revit_doc(cls, doc=revit.doc):
        # type: (Document) -> iter
        """Generator which return all ProjectParameter in document"""
        iterator = doc.ParameterBindings.ForwardIterator()  # type: DefinitionBindingMapIterator
        for binding in iterator:  # type: ElementBinding
            definition = iterator.Key
            yield cls(definition, binding)

    def save_to_revit_doc(self, doc=revit.doc):
        """Save current project parameter to Revit doc.
        Need to be used in an open Transaction. """
        bindingmap = doc.ParameterBindings # type: BindingMap
        if bindingmap[self.definition]:
            bindingmap.ReInsert(self.definition, self.binding, self.bip_group.enum_member)
        else:
            bindingmap.Insert(self.definition, self.binding, self.bip_group.enum_member)

    @staticmethod
    def all_categories():
        category_set = revit.app.Create.NewCategorySet()
        for category in revit.doc.Settings.Categories:
            if category.AllowsBoundParameters:
                category_set.Insert(category)
        return category_set

    @staticmethod
    def bound_allowed_category_generator():
        for category in revit.doc.Settings.Categories:
            if category.AllowsBoundParameters:
                yield category


class FamilyParameter:
    def __init__(self, name, **kwargs):
        # type: (str) -> None

        # Default values
        self.name = name  # type: str
        self.is_instance = False  # type: bool
        self.is_shared = False  # type: bool
        self.definition = None  # type: ExternalDefinition
        self.modified = False  # type: bool
        self.is_new = False  # type: bool

        # Given values if provided
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

        if not self.definition:
            self.type = PType(ParameterType.Length)
            self.group = BipGroup(BuiltInParameterGroup.PG_TEXT)
            self.initial_values = dict()
        else:
            self.type = PType(self.definition.ParameterType)
            self.group = BipGroup(self.definition.ParameterGroup)
            self.initial_values_update()

    def initial_values_update(self):
        self.initial_values = {"name": self.name, "type": self.type, "group": self.group,
                               "is_instance":self.is_instance, "is_shared":self.is_shared}

    @classmethod
    def read_from_revit_doc(cls, doc=revit.doc):
        """Generator which return all FamilyParameter in document"""
        # type: (Document) -> iter
        iterator = doc.FamilyManager.Parameters.ForwardIterator()  # type: DefinitionBindingMapIterator
        for parameter in iterator:
            if parameter.Definition.BuiltInParameter == BuiltInParameter.INVALID:
                yield cls(parameter.Definition.Name,
                          is_instance=parameter.IsInstance,
                          is_shared=parameter.IsShared,
                          definition=parameter.Definition)

    @classmethod
    def new_from_shared(cls, definition):
        # type: (ExternalDefinition) -> FamilyParameter
        return cls(definition.Name, is_shared=True, definition=definition, is_new=True)

    def save_to_revit(self, doc=revit.doc):
        # type: (Document) -> Autodesk.Revit.DB.FamilyParameter
        """Save current family parameter to Revit doc.
        Need to be used in an open Transaction. """
        if self.is_new and self.is_shared:
            return doc.FamilyManager.AddParameter(self.definition, self.group.enum_member, self.is_instance)
        elif self.is_new:
            return doc.FamilyManager.AddParameter(
                self.name, self.group.enum_member, self.type.enum_member, self.is_instance)
        elif self.modified:
            fp = doc.FamilyManager.get_Parameter(self.initial_values["name"])

            # Get the string or ExternalDefinition necessary
            if self.is_shared:
                # In case only Instance/Type has been switched
                for key in ("type", "group", "is_shared"):
                    if getattr(self, key) != self.initial_values[key]:
                        break
                else:
                    if self.is_instance:
                        return doc.FamilyManager.MakeInstance(fp)
                    else:
                        return doc.FamilyManager.MakeType(fp)
                var_attr = SharedParameter.get_definition_by_name(self.name)
            else:
                var_attr = self.name

            if self.type == self.initial_values["type"]:
                return doc.FamilyManager.ReplaceParameter(fp, var_attr, self.group.enum_member, self.is_instance)
            else:
                doc.FamilyManager.RemoveParameter(fp)
                if self.is_shared:
                    return doc.FamilyManager.AddParameter(var_attr, self.group.enum_member, self.is_instance)
                else:
                    return doc.FamilyManager.AddParameter(
                        self.name, self.group.enum_member, self.type.enum_member, self.is_instance)

    def delete_from_revit(self, doc):
        # type: (Document) -> None
        """Delete current family parameter from current Revit doc.
        Need to be used in an open Transaction. """
        doc.FamilyManager.RemoveParameter(doc.FamilyManager.get_Parameter(self.name))


class BoundAllowedCategory:
    def __init__(self, category):
        # type: (Category) -> None
        self.category = category
        self.is_bound = False

    @property
    def name(self):
        return self.category.Name

    @property
    def category_type(self):
        return self.category.CategoryType


class RevitEnum:
    def __init__(self, enum_member):
        # type: (Enum) -> None
        """Enum wrapper"""
        self.enum_member = enum_member

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        try:
            return self.enum_member == other.enum_member
        except AttributeError:
            return False

    def __gt__(self, other):
        return self.name > other.name

    def __lt__(self, other):
        return self.name < other.name

    @property
    def name(self):
        try:
            return "{}{}({})".format(LabelUtils.GetLabelFor(self.enum_member), 4*" ", self.enum_member)
        except Exceptions.InvalidOperationException:
            return "Invalid"

    @staticmethod
    def enum_generator():
        for enum_member in Enum.GetValues(Enum):
            yield enum_member  # type: Enum

    @classmethod
    def enum_name_generator(cls):
        for enum_member in cls.enum_generator():
            yield LabelUtils.GetLabelFor(enum_member)

    @classmethod
    def enum_member_by_name(cls, name):
        # type: (str) -> Enum
        for enum_member in cls.enum_generator():
            if LabelUtils.GetLabelFor(enum_member) == name:
                return enum_member


class BipGroup(RevitEnum):
    @staticmethod
    def enum_generator():
        for bip_group in BuiltInParameterGroup.GetValues(BuiltInParameterGroup):
            yield bip_group  # type: ParameterType


class PType(RevitEnum):
    @staticmethod
    def enum_generator():
        for paramater_type in ParameterType.GetValues(ParameterType):
            yield paramater_type  # type: ParameterType


