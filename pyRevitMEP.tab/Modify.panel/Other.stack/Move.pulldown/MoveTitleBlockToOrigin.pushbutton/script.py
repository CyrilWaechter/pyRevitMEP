# coding: utf8
from pyrevit import revit, DB

__doc__ = "Move selected annotation to center (set 0,0,0 coordinates)"
__title__ = "TitleBlock"
__author__ = "Cyril Waechter"
__context__ = "Selection"

with revit.Transaction("Move title block to origin"):
    for text_element in revit.get_selection():
        text_element.Location.Point = DB.XYZ(0, 0, 0)
