# coding: utf8
import rpw
# noinspection PyUnresolvedReferences
from rpw import revit, DB, UI
# noinspection PyUnresolvedReferences
from Autodesk.Revit.Exceptions import InvalidOperationException
from scriptutils import logger
from scriptutils.userinput import WPFWindow
import csv
from pyRevitMEP.parameter import SharedParameter
# noinspection PyUnresolvedReferences
from System.Collections.Generic import List

__doc__ = "Batch create project shared parameters from file"
__title__ = "BatchCreateSharedParameters"
__author__ = "Cyril Waechter"

doc = rpw.revit.doc
uidoc = rpw.uidoc

# text_box = TextBox("parameters_text",text_text, Height=400, Width=400)
# components = [text_box]
#
# form = rpw.ui.forms.FlexForm("Parameters to create check", components)
# form.ShowDialog()
#
# parameters_text = text_box.Text.split("\n")
#
# for parameter in parameters_text:
#     print parameter
#
# with rpw.db.Transaction("Batch create shared parameters from file"):
#      for parameter_name in parameters_text:
#         SharedParameter(revit.app, parameter_name, "MCR", DB.ParameterType.Text)


class Gui(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.datagrid.ItemsSource = SharedParameter.read_from_csv()


gui = Gui("WPFWindow.xaml")
gui.ShowDialog()
