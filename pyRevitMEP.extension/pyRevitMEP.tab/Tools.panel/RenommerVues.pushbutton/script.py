from Autodesk.Revit.UI import TaskDialog
from Autodesk.Revit.UI import UIApplication
def alert(msg):
   TaskDialog.Show('RevitPythonShell', msg)

def quit():
   __window__.Close()
exit = quit

try:
	t = Transaction(doc, "Renomme la vue")
	t.Start()
	for e in getselection(): #Cherche l'Id des éléments sélectionnés
		view = doc.GetElement(e) #Cherche l'élément correspondant à l'Id
		
		vft = doc.GetElement(view.GetTypeId()) #Get ViewFamilyType Id
		vft_name = Element.Name.GetValue(vft) #Get ViewFamilyType Name
		
		#S'il existe une zone de définition, récupère son nom
		try:
			vzv = view.get_Parameter(BuiltInParameter.VIEWER_VOLUME_OF_INTEREST_CROP)
			vzv_name = "" if vzv.AsValueString() == 'None' else "_" + vzv.AsValueString()
		except:
			vzv_name = ""
			
		vgl = "" if view.GenLevel == None else view.GenLevel.Name #S'il y a un niveau associé, récupère son nom
		
		view_name = "{c}_{a}{b}".format(a=vgl, b=vzv_name, c=vft_name,) #Nomme la vue avec nom du niveau associé + nom du type de la vue
		i = 0
		while True:
			try:
				view.Name = view_name
			except Exceptions.ArgumentException:
				i += 1
				view_name = view_name + str(i)
			except:
				break
			else:
				break
	t.Commit()
except:
    # print a stack trace and error messages for debugging
    import traceback
    traceback.print_exc()
    t.RollBack()
else:
    # no errors, so just close the window
    __window__.Close()
