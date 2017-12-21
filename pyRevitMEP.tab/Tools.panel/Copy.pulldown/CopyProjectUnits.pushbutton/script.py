# coding: utf8

import rpw
from pyrevit import script

logger = script.get_logger()
doc = rpw.revit.doc
opened_docs = rpw.revit.docs
Transaction = rpw.DB.Transaction

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
    source_doc = form.values["source"]
    target_doc = form.values["target"]

    source_units = source_doc.GetUnits()
    target_units = target_doc.GetUnits()

    source_units_list = source_units.GetModifiableUnitTypes()

    with rpw.db.Transaction(doc=target_doc, name="Copy view types"):
        for unit in source_units_list:
            format_options = source_units.GetFormatOptions(unit)
            target_units.SetFormatOptions(unit, format_options)

except KeyError:
    logger.debug('No input or incorrect inputs')
