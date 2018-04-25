# coding: utf8
import rpw
from Autodesk.Revit.DB import Element, BuiltInCategory, Category
# from pypevitmep.category import Category

__doc__ = "A tool to select BuiltInCategories"
__title__ = "CategorySelector"
__author__ = "Cyril Waechter"

doc = rpw.revit.doc



# Category.selection_window()