# coding: utf8

from Autodesk.Revit.DB import Document, FamilyInstance, IFamilyLoadOptions, FamilySource
from Autodesk.Revit.UI import UIDocument
from Autodesk.Revit import Exceptions

from pyrevit import script
import rpw

__doc__ = "Load or Reload selected families into chosen document"
__title__ = "Load/Reload \n families"
__author__ = "Cyril Waechter"
__context__ = "selection"

doc = __revit__.ActiveUIDocument.Document  # type: Document
uidoc = __revit__.ActiveUIDocument  # type: UIDocument

# Retrieve families in selection
families_ids = set()

for el_id in uidoc.Selection.GetElementIds():
    element = doc.GetElement(el_id)
    if not isinstance(element, FamilyInstance):
        continue
    families_ids.add(element.Symbol.Family.Id)

# Display user options
modifiable_docs = {d.Title: d for d in rpw.revit.docs if not d.IsLinked}

ComboBox = rpw.ui.forms.flexform.ComboBox
CheckBox = rpw.ui.forms.flexform.CheckBox
Label = rpw.ui.forms.flexform.Label
Button = rpw.ui.forms.flexform.Button

components = [Label("Load/Reload {} selected families into :".format(len(families_ids))),
              ComboBox("target", modifiable_docs),
              CheckBox("overwrite_family", "Overwrite existing families ?", True),
              CheckBox("overwrite_parameters", "Overwrite parameters values ?", True),
              Button("Select")]

form = rpw.ui.forms.FlexForm("Document selection and overwrite options", components)
form.ShowDialog()

try:
    target_doc = form.values["target"]  # type: Document
    overwrite_family = form.values["overwrite_family"]
    overwrite_parameters_values = form.values["overwrite_parameters"]
except KeyError:
    import sys
    sys.exit()


class CustomFamilyLoadOptions(IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues.Value = overwrite_parameters_values
        return overwrite_family

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        source.Value = FamilySource.Family
        overwriteParameterValues.Value = overwrite_parameters_values
        return overwrite_family


customfamilyloadoptions = CustomFamilyLoadOptions()

# Load/Reload families
for family_id in families_ids:
    familydoc = doc.EditFamily(doc.GetElement(family_id))
    try:
        familydoc.LoadFamily(target_doc, customfamilyloadoptions)
    except Exceptions.InvalidOperationException:
        pass
    familydoc.Close(False)
