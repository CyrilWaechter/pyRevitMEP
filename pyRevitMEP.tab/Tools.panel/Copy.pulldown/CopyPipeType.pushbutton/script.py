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
from Autodesk.Revit.DB import FilteredElementCollector, CopyPasteOptions, ElementTransformUtils, Element,\
    ElementId, Transform, Transaction
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB.Plumbing import PipeType
# noinspection PyUnresolvedReferences
from System.Collections.Generic import List

import rpw
from scriptutils.userinput import WPFWindow
from revitutils import doc

__doc__ = "Copy pipe types from a selected opened document to active document"
__title__ = "Copy pipe type"
__author__ = "Cyril Waechter"


opened_docs = {}
for d in __revit__.Application.Documents:
    opened_docs[d.Title] = d


id_list = List[ElementId]()

def get_all_pipetype(document):
    '''
    Get all pipe type in a document
    :param document: Autodesk.Revit.DB.Document
    :return: dictionnary of pipe types
    '''
    pipe_types = {}
    for pt in FilteredElementCollector(document).OfClass(PipeType):
        pipe_types[Element.Name.GetValue(pt)] = pt
    return(pipe_types)

def copy(source_doc, elem):
    '''
    Copy elem from source_doc to active document
    :param source_doc: Autodesk.Revit.DB.Document
    :param elem: Autodesk.Revit.DB.Element
    :return: None
    '''
    copypasteoptions = CopyPasteOptions()
    id_list = List[ElementId]()
    id_list.Add(elem.Id)

    t = Transaction(doc, "Copy view types")

    t.Start()
    ElementTransformUtils.CopyElements(source_doc,id_list,doc,Transform.Identity,copypasteoptions)
    t.Commit()


class PipeTypeSelectionForm(WPFWindow):
    '''
    GUI used to select pipe type to copy
    '''

    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)

        self.source_docs.ItemsSource = opened_docs
        self.source_doc = opened_docs[self.source_docs.SelectedItem]
        self.pipe_types = get_all_pipetype(self.source_doc)

    def source_doc_selection_changed(self, sender, e):
        self.source_doc = opened_docs[sender.SelectedItem]
        self.pipe_types = get_all_pipetype(self.source_doc)
        self.source_pipe.ItemsSource = self.pipe_types.keys()

    def button_copy_click(self, sender, e):
        self.Close()
        elem = self.pipe_types[self.source_pipe.SelectedItem]
        copy(self.source_doc, elem)


PipeTypeSelectionForm('PipeTypeSelection.xaml').ShowDialog()

