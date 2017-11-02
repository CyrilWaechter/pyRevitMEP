# coding: utf8
import rpw
from rpw import DB

__doc__ = "Move selected annotation to center (set 0,0,0 coordinates)"
__title__ = "MoveTitleBlockToOrigin"
__author__ = "Cyril Waechter"
__context__ = 'Selection'

with rpw.db.Transaction("Move title block to origin"):
    for text_element in rpw.ui.Selection():
        text_element.Location.Point = DB.XYZ(0,0,0)
