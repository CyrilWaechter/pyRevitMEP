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
    ElementId, Transform, Transaction, Element, View
# noinspection PyUnresolvedReferences
from System.Collections.Generic import List

import rpw
from scriptutils import logger

__doc__ = "Copy all view types from a selected opened project to another"
__title__ = "CopyViewTypes"
__author__ = "Cyril Waechter"

ComboBox = rpw.ui.forms.flexform.ComboBox
Label = rpw.ui.forms.flexform.Label
Button = rpw.ui.forms.flexform.Button
CheckBox = rpw.ui.forms.flexform.CheckBox


def name(element):
    return Element.Name.__get__(element)


def get_all_viewfamilytype_ids(document):
    id_list = List[ElementId]()
    for vft in FilteredElementCollector(document).OfClass(ViewFamilyType):
        id_list.Add(vft.Id)
    return id_list


def view_type_name_template_name_dict(document):
    element_dict = {}
    for element in FilteredElementCollector(document).OfClass(ViewFamilyType):
        default_view_template = document.GetElement(element.DefaultTemplateId)
        if default_view_template is not None:
            element_dict[name(element)] = name(default_view_template)
    logger.debug("view_type_name_template_name_dict : {}".format(element_dict))
    return element_dict


def view_template_name_to_id_dict(document):
    element_dict = {}
    for view in FilteredElementCollector(document).OfClass(View):
        if view.IsTemplate:
            element_dict[name(view)] = view.Id
    logger.debug("view_template_name_to_id_dict : {}".format(element_dict))
    return element_dict


opened_docs_dict = {document.Title: document for document in rpw.revit.docs}

components = [Label("Pick source document"),
              ComboBox("source", opened_docs_dict),
              Label("Pick target document"),
              ComboBox("target", opened_docs_dict),
              Button("Select")]

form = rpw.ui.forms.FlexForm("Pick documents", components)
form.ShowDialog()
try:
    source_doc = form.values["source"]
    target_doc = form.values["target"]
except KeyError:
    logger.debug('No input or incorrect inputs')

copypasteoptions = CopyPasteOptions()

source_viewtype_id_list = get_all_viewfamilytype_ids(source_doc)

source_doc_dict = view_type_name_template_name_dict(source_doc)

with rpw.db.Transaction(doc=target_doc, name="Copy view types"):
    # Copy view type
    ElementTransformUtils.CopyElements(source_doc,
                                       source_viewtype_id_list,
                                       target_doc,
                                       Transform.Identity,
                                       copypasteoptions)

    # Assign Default Template to ViewType
    target_doc_dict = view_template_name_to_id_dict(target_doc)
    for viewtype in FilteredElementCollector(target_doc).OfClass(ViewFamilyType):
        try:
            default_template_name  = source_doc_dict[name(viewtype)]
            default_template_id = target_doc_dict[default_template_name]
            viewtype.DefaultTemplateId = default_template_id
        except KeyError:
            logger.debug("{} has no view template".format(name(viewtype)))
