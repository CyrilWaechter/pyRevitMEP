# coding: utf8

from Autodesk.Revit.DB import Document, FamilyInstance, IFamilyLoadOptions, FamilySource
from Autodesk.Revit.UI import UIDocument

from pyrevit import script

logger = script.get_logger()

import rpw

doc = __revit__.ActiveUIDocument.Document  # type: Document
uidoc = __revit__.ActiveUIDocument  # type: UIDocument

modifiable_docs = {d.Title:d for d in rpw.revit.docs if not d.IsLinked}

ComboBox = rpw.ui.forms.flexform.ComboBox
CheckBox = rpw.ui.forms.flexform.CheckBox
Label = rpw.ui.forms.flexform.Label
Button = rpw.ui.forms.flexform.Button

components = [Label("Pick target document"),
              ComboBox("target", modifiable_docs),
              CheckBox("overwrite", "Overwrite parameters values ?", True),
              Button("Select")]

form = rpw.ui.forms.FlexForm("Documents selection", components)
form.ShowDialog()

target_doc = form.values["target"]  # type: Document
overwrite = form.values["overwrite"]

class CustomFamilyLoadOptions(IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues=overwrite):
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source=FamilySource.Family, overwriteParameterValues=overwrite):
        return True

customfamilyloadoptions = CustomFamilyLoadOptions()

for el_id in uidoc.Selection.GetElementIds():
    element = doc.GetElement(el_id)
    if not isinstance(element, FamilyInstance):
        continue
    familydoc = doc.EditFamily(element.Symbol.Family)
    familydoc.LoadFamily(target_doc, customfamilyloadoptions)
    familydoc.Close()

# logger.debug(familydocs)
#
# with rpw.db.Transaction("Reload families"):
#     for familydoc in familydocs:
#         familydoc.LoadFamily(target_doc)
#         familydoc.Close()
