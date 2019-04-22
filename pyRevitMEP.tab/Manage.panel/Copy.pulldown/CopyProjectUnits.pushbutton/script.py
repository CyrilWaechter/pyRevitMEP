# coding: utf8
from Autodesk.Revit.DB import Document

import rpw
from pyrevit import script

__doc__ = """Copy project units from another document. 
Display a form to select source and target document."""
__title__ = "Project Units"
__author__ = "Cyril Waechter"

logger = script.get_logger()
doc = rpw.revit.doc  # type: Document

opened_docs = {d.Title:d for d in rpw.revit.docs}
modifiable_docs = {d.Title:d for d in rpw.revit.docs if not d.IsLinked}

ComboBox = rpw.ui.forms.flexform.ComboBox
Label = rpw.ui.forms.flexform.Label
Button = rpw.ui.forms.flexform.Button

components = [Label("Pick source document"),
              ComboBox("source", opened_docs),
              Label("Pick target document"),
              ComboBox("target", modifiable_docs),
              Button("Select")]

form = rpw.ui.forms.FlexForm("Documents selection", components)
form.ShowDialog()

try:
    source_doc = form.values["source"]  # type: Document
    target_doc = form.values["target"]  # type: Document

    with rpw.db.Transaction(doc=target_doc, name="Copy project units"):
        target_doc.SetUnits(source_doc.GetUnits())

except KeyError:
    logger.debug('No input or incorrect inputs')
