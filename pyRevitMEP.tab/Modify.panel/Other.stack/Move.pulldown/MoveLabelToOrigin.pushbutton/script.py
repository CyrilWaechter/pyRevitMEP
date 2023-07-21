# coding: utf8
from pyrevit import revit, DB

__doc__ = "Designed for annotation families. It moves selected annotation to center (set 0,0,0 coordinates)"
__title__ = "Label/Text"
__author__ = "Cyril Waechter"
__context__ = "Selection"

with revit.Transaction("Move label to origin"):
    for text_element in revit.get_selection():
        text_element.Coord = DB.XYZ()
