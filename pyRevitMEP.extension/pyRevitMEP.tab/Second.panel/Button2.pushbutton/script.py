#Code par Cyril Waechter le 17.10.2014
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Architecture import *
from Autodesk.Revit.DB.Analysis import *
from Autodesk.Revit.UI import TaskDialog
from Autodesk.Revit.UI import UIApplication
from math import pi

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document
getselection = uidoc.Selection.GetElementIds

def quit():
   __window__.Close()
exit = quit

try:
	t = Transaction(doc, "Rotation axe x")
	t.Start()
	#Cherche l'origine de la famille sélectionnée et effectué une rotation autour de l'axe x de l'objet passant par l'origine.
	for e in getselection():
		o = doc.GetElement(e).Location.Point
		z = XYZ(o.X + 1, o.Y, o.Z)
		axis = Line.CreateBound(o, z)
		ElementTransformUtils.RotateElement(doc,e,axis,pi/2)
	t.Commit()
except:
    # print a stack trace and error messages for debugging
    import traceback
    traceback.print_exc()
    t.RollBack()
else:
    # no errors, so just close the window
    __window__.Close()
