# coding: utf8
import rpw
# noinspection PyUnresolvedReferences
from rpw import revit, DB, UI
# noinspection PyUnresolvedReferences
from Autodesk.Revit.Exceptions import InvalidOperationException
from pyRevitMEP.category import Category

__doc__ = "A tool to select BuiltInCategories"
__title__ = "CategorySelector"
__author__ = "Cyril Waechter"

Category.selection_window()