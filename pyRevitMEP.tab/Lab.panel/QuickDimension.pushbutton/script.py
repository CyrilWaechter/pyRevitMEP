# coding: utf8
import rpw
from rpw import DB, revit

__doc__ = "Quick dimension selected pipes"
__title__ = "QuickDimensionPipe"
__author__ = "Cyril Waechter"
__context__ = 'Selection'

selection = [revit.doc.GetElement(id) for id in __revit__.ActiveUIDocument.Selection.GetElementIds()]
reference_array = DB.ReferenceArray()
for element in selection:
    if isinstance(element, DB.Plumbing.Pipe):
        reference_array.Append(DB.Reference(element))

pt1 = DB.XYZ(5,10,0)
pt2 = DB.XYZ(10,10,0)
line = DB.Line.CreateBound(pt1,pt2)

with rpw.db.Transaction("QuickDimensionPipe"):
    dim = revit.doc.Create.NewDimension(revit.doc.ActiveView, line, reference_array)
