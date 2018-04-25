"""
Copyright (c) 2017 Cyril Waechter
Python scripts for Autodesk Revit

This file is part of pypevitmep repository at https://github.com/CyrilWaechter/pypevitmep

pypevitmep is an extension for pyRevit. It contain free set of scripts for Autodesk Revit:
you can redistribute it and/or modify it under the terms of the GNU General Public License
version 3, as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

See this link for a copy of the GNU General Public License protecting this package.
https://github.com/CyrilWaechter/pypevitmep/blob/master/LICENSE
"""

__doc__ = "simple external event which just delete selection"
__title__ = "ExEvent Delete"
__author__ = "Cyril Waechter"

# noinspection PyUnresolvedReferences
from Autodesk.Revit.UI import IExternalEventHandler, IExternalApplication, Result, ExternalEvent, IExternalCommand
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import Transaction
# noinspection PyUnresolvedReferences
from Autodesk.Revit.Exceptions import InvalidOperationException
import rpw
doc = rpw.revit.doc
uidoc = rpw.revit.uidoc

class ExternalEventMy(IExternalEventHandler):
    def Execute(self, uiapp):
        try:
            with rpw.db.Transaction("MyEvent"):
                for elid in uidoc.Selection.GetElementIds():
                    doc.Delete(elid)
        except InvalidOperationException:
            print "exception catched"

    def GetName(self):
        return "my event"

handler_event = ExternalEventMy()
exEvent = ExternalEvent.Create(handler_event)

exEvent.Raise()

ExternalEventMy.Execute(handler_event, uidoc)