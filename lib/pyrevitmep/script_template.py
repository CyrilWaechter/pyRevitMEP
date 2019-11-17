# coding: utf8
import rpw
from pyrevit import script, forms

__title__ = "Title"
__author__ = "Cyril Waechter"
__doc__ = "Description"

doc = __revit__.ActiveUIDocument.Document  # type: Document

logger = script.get_logger()