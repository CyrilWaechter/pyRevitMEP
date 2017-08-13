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
from Autodesk.Revit.DB import FilteredElementCollector, ViewFamilyType, CopyPasteOptions, ElementTransformUtils,\
    ElementId, Transform, Transaction
# noinspection PyUnresolvedReferences
from System.Collections.Generic import List

import rpw
from scriptutils import logger

__doc__ = "Copy all view types from a selected opened project to another"
__title__ = "Copy view types"
__author__ = "Cyril Waechter"

ComboBox = rpw.ui.forms.flexform.ComboBox
Label = rpw.ui.forms.flexform.Label
Button = rpw.ui.forms.flexform.Button

def get_all_viewfamilytype_ids(document):
    id_list = List[ElementId]()
    for vft in FilteredElementCollector(document).OfClass(ViewFamilyType):
        id_list.Add(vft.Id)
    return id_list


opened_docs = {}
for d in __revit__.Application.Documents:
    opened_docs[d.Title] = d

components = [Label("Pick source document"),
              ComboBox("source", opened_docs),
              Label("Pick target document"),
              ComboBox("target", opened_docs),
              Button("Select")]

form = rpw.ui.forms.FlexForm("Pick documents", components)
form.ShowDialog()
try:
    source_doc = form.values["source"]
    target_doc = form.values["target"]
    copypasteoptions = CopyPasteOptions()

    id_list = get_all_viewfamilytype_ids(source_doc)

    t = Transaction(target_doc, "Copy view types")

    t.Start()
    ElementTransformUtils.CopyElements(source_doc,id_list,target_doc,Transform.Identity,copypasteoptions)
    t.Commit()
except KeyError:
    logger.debug('No input or incorrect inputs')


