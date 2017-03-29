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

__doc__ = "simple external event which just delete selection"
__title__ = "ExEvent Delete"
__author__ = "Cyril Waechter"

from Autodesk.Revit.UI import IExternalEventHandler, IExternalApplication, Result, ExternalEvent, IExternalCommand
from Autodesk.Revit.DB import Transaction
from Autodesk.Revit.Exceptions import InvalidOperationException
from revitutils import selection, uidoc, doc

class ExternalEventMy(IExternalEventHandler):
    def Execute(self, uiapp):
        try:
            tx = Transaction(doc)
            tx.Start("MyEvent")
            for elid in selection.element_ids:
                doc.Delete(elid)
            tx.Commit()
        except InvalidOperationException:
            print "exception catched"

    def GetName(self):
        return "my event"

handler_event = ExternalEventMy()
exEvent = ExternalEvent.Create(handler_event)

exEvent.Raise()

ExternalEventMy.Execute(handler_event, uidoc)