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
from Autodesk.Revit.UI import IExternalEventHandler, IExternalApplication, Result, ExternalEvent, IExternalCommand
from Autodesk.Revit.DB import Transaction
from Autodesk.Revit.Exceptions import InvalidOperationException
from revitutils import selection, uidoc, doc
from scriptutils.userinput import WPFWindow

__doc__ = "A simple modeless form"
__title__ = "Modeless Form"
__author__ = "Cyril Waechter"

def delete_elements():
    t = Transaction(doc, "ModelessDeletion")
    t.Start()
    for elid in selection.element_ids:
        print elid
        doc.Delete(elid)
    t.Commit()

class SimpleEventHandler(IExternalEventHandler):
    def __init__(self,):
        pass

    def Execute(self, uiapp):
        try:
            t = Transaction(doc, "ModelessDeletion")
            t.Start()
            for elid in selection.element_ids:
                print elid
                doc.Delete(elid)
            t.Commit()
        except InvalidOperationException:
            raise

    def GetName(self):
        return "simple form event"


class ModelessForm(WPFWindow):
    """
    Simple modeless form sample
    """

    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.simple_text.Text = "Hello World"
        self.Show()

    def delete_click(self, sender, e):
        SimpleEventHandler.Execute(simple_event_handler, uidoc)

simple_event_handler = SimpleEventHandler()
exEvent = ExternalEvent.Create(simple_event_handler)

# exEvent.Raise()

modeless_form = ModelessForm("ModelessForm.xaml")