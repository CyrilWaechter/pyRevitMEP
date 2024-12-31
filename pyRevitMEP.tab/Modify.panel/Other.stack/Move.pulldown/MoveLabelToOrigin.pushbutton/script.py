# coding: utf8
from pyrevit import revit, DB


with revit.Transaction("Move label to origin"):
    for text_element in revit.get_selection():
        text_element.Coord = DB.XYZ()
