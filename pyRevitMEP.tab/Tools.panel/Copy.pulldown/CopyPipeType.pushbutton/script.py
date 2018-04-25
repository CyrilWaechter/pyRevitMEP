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
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import FilteredElementCollector, CopyPasteOptions, ElementTransformUtils, Element,\
    ElementId, Transform, Transaction
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB.Plumbing import PipeType
# noinspection PyUnresolvedReferences
from System.Collections.Generic import List

import rpw
from rpw import doc
from pyrevit.forms import WPFWindow

__doc__ = "Copy pipe types from a selected opened document to active document"
__title__ = "CopyPipeType"
__author__ = "Cyril Waechter"


opened_docs = {d.Title:d for d in rpw.revit.docs}


def copy(source_doc, elem):
    """
    Copy elem from source_doc to active document
    :param source_doc: Autodesk.Revit.DB.Document
    :param elem: Autodesk.Revit.DB.Element
    :return: None
    """
    copypasteoptions = CopyPasteOptions()
    id_list = List[ElementId]()
    id_list.Add(elem.Id)

    with rpw.db.Transaction("Copy pipe type", doc):
        ElementTransformUtils.CopyElements(source_doc, id_list, doc, Transform.Identity, copypasteoptions)


class PipeTypeSelectionForm(WPFWindow):
    """
    GUI used to select pipe type to copy
    """

    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.source_docs.DataContext = rpw.revit.docs

    # noinspection PyUnusedLocal
    def source_doc_selection_changed(self, sender, e):
        try:
            self.source_doc = sender.SelectedItem
            self.source_pipe.DataContext = FilteredElementCollector(self.source_doc).OfClass(PipeType)
        except:
            pass

    # noinspection PyUnusedLocal
    def button_copy_click(self, sender, e):
        self.Close()
        elem = self.source_pipe.SelectedItem
        copy(self.source_doc, elem)


PipeTypeSelectionForm('PipeTypeSelection.xaml').ShowDialog()
