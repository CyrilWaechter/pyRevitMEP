# coding: utf8
import rpw
from rpw import DB

__doc__ = "Designed for annotation families. It moves selected annotation to center (set 0,0,0 coordinates)"
__title__ = "Label/Text"
__author__ = "Cyril Waechter"
__context__ = 'Selection'

with rpw.db.Transaction():
    for text_element in rpw.ui.Selection():
        text_element.Coord = DB.XYZ()
