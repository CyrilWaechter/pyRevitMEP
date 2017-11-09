# coding: utf8
import rpw
# noinspection PyUnresolvedReferences
from rpw import DB, UI
# noinspection PyUnresolvedReferences
from Autodesk.Revit.Exceptions import InvalidOperationException
from scriptutils import logger
from scriptutils.userinput import WPFWindow
import re

__doc__ = "Batch create project shared parameters from file"
__title__ = "BatchCreateSharedParameters"
__author__ = "Cyril Waechter"

doc = rpw.revit.doc
uidoc = rpw.uidoc
TextBox = rpw.ui.forms.TextBox

file = rpw.ui.forms.select_file(extensions='All Files (*.*)|*.*', title='Select File',
                                multiple=False, restore_directory=True)
with open(file, "r") as text:
    text_text = text.read()

text_box = TextBox("parameters_text",text_text, Height=400, Width=400)
components = [text_box]

form = rpw.ui.forms.FlexForm("Parameters to create check", components)
form.ShowDialog()

parameters_text = text_box.Text.split("\n")

for parameter in parameters_text:
    print parameter

# with rpw.db.Transaction("Batch create worksets from file"):
#     pass
