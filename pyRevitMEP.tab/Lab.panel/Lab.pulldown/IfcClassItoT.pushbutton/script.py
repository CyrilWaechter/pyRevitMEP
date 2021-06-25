# coding=utf8
from pyrevit import revit
from pyrevitmep.parameter import SharedParameter
from Autodesk.Revit.DB import BuiltInParameterGroup, IFamilyLoadOptions, FamilySource

doc = __revit__.ActiveUIDocument.Document
class_definition = SharedParameter.get_definition_by_name("IfcExportAs[Type]")
predefinedtype_definition = SharedParameter.get_definition_by_name(
    "IfcExportType[Type]"
)

family_type_set = set()
for instance in revit.selection.get_selection():
    family_type_set.add(instance.Symbol)

class CustomFamilyLoadOptions(IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues.Value = False
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        source.Value = FamilySource.Family
        overwriteParameterValues.Value = False
        return True

customfamilyloadoptions = CustomFamilyLoadOptions()
for family_type in family_type_set:
    family = family_type.Family
    family_doc = doc.EditFamily(family)
    class_param = family_doc.FamilyManager.get_Parameter("IfcExportAs")
    predefinedtype_param = family_doc.FamilyManager.get_Parameter("IfcExportType")

    with revit.Transaction(doc=family_doc):
        if class_param:
            family_doc.FamilyManager.ReplaceParameter(
                class_param, class_definition, BuiltInParameterGroup.PG_IFC, False
            )
        if predefinedtype_param:
            family_doc.FamilyManager.ReplaceParameter(
                predefinedtype_param,
                predefinedtype_definition,
                BuiltInParameterGroup.PG_IFC,
                False,
            )
    family_doc.LoadFamily(doc, customfamilyloadoptions)
