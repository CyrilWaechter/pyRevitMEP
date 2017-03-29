"""
Copyright (c) 2017 Cyril Waechter
Python scripts for Autodesk Revit

This file is part of pyRevitMEP repository at https://github.com/CyrilWaechter/pyRevitMEP

pyRevitMEP is an extension for pyRevit. It contain free set of scripts for Autodesk Revit:
you can redistribute it and/or modify it under the terms of the GNU General Public License
version 3, as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

See this link for a copy of the GNU General Public License protecting this package.
https://github.com/CyrilWaechter/pyRevitMEP/blob/master/LICENSE
"""
# noinspection PyUnresolvedReferences
from Autodesk.Revit.UI import IExternalEventHandler, ExternalEvent
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import Transaction
# noinspection PyUnresolvedReferences
from Autodesk.Revit.Exceptions import InvalidOperationException
from revitutils import selection, doc
from scriptutils.userinput import WPFWindow

__doc__ = "A simple modeless form sample"
__title__ = "Modeless Form"
__author__ = "Cyril Waechter"

uidoc = __revit__.ActiveUIDocument

def delete_elements():
    t = Transaction(doc, "ModelessDeletion")
    t.Start()
    for elid in uidoc.Selection.GetElementIds():
        print elid
        doc.Delete(elid)
    t.Commit()


class SimpleEventHandler(IExternalEventHandler):
    def __init__(self,):
        pass

    def Execute(self, uiapp):
        try:
            delete_elements()
        except InvalidOperationException:
            print "InvalidOperationException catched"

    def GetName(self):
        return "simple form event"

simple_event_handler = SimpleEventHandler()
ex_event = ExternalEvent.Create(simple_event_handler)


class ModelessForm(WPFWindow):
    """
    Simple modeless form sample
    """

    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.simple_text.Text = "Hello World"
        self.Show()

    def delete_click(self, sender, e):
        for el in selection.elements:
            print el
        ex_event.Raise()

modeless_form = ModelessForm("ModelessForm.xaml")


