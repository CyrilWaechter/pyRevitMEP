# -*- coding: utf-8 -*-
""" Split SELECTED Pipes by distance."""

__title__ = 'Split Selected Pipes'
__author__ = 'André Rodrigues da Silva'

from rpw import revit, db
from rpw import ui
from rpw.ui.forms import (FlexForm, Label, ComboBox, TextBox, TextBox,Separator, Button, CheckBox)

from Autodesk.Revit.DB import Transaction

from Autodesk.Revit.DB.Plumbing.PlumbingUtils import BreakCurve 
from rpw.db.xyz import XYZ

try:
	Tubos = ui.Selection()

	components = [Label('Select the distance for split pipes:'),
				   Label('Distance:'),
				   TextBox('distance', Text="3.0"),
				   Label('Parameters separated by ",":'),
				   TextBox('parameters', Text=""),
				   Separator(),
				   Button('Process')]
	form = FlexForm('Split Pipes', components)
	form.show()

	L = float(form.values['distance'])*3.28084
	P = form.values['parameters']
	P = P.split(",")
	
	TuboSelecionado = []

	#Tubos com comprimento maior que o selecionado
	TuboSecionado = []
	for i in range(0,len(Tubos)):
		if(Tubos[i].Location.Curve.Length > L):
			TuboSecionado.append(Tubos[i])

	points = []
	pointsAUX = []		
	for i in range(0,len(TuboSecionado)):
		if((TuboSecionado[i].Location.Curve.Length/L)>int(TuboSecionado[i].Location.Curve.Length/L)):
			t = int(TuboSecionado[i].Location.Curve.Length/L) + 1
		else:
			t = int(TuboSecionado[i].Location.Curve.Length/L)
		d = L *TuboSecionado[i].Location.Curve.Direction
		for n in range(0,t):
			if(n ==0):
				continue
			else:
				pointsAUX.append(TuboSecionado[i].Location.Curve.GetEndPoint(0) + n*d)
		points.append(pointsAUX)
		pointsAUX = []
		
	pipes = TuboSecionado

	# Typical Transaction in Revit Python Shell / pyRevit
	doc = __revit__.ActiveUIDocument.Document
	transaction = Transaction(doc, 'Delete Object')
	transaction.Start()
	try:
		for t in range(0,len(pipes),1):
			for i in range(0,len(points[t]),1):	
				dbPoint = points[t][i]
				pipe = pipes[t]
				newPipeId = BreakCurve(doc, pipe.Id, dbPoint)
				newPipe = doc.GetElement(newPipeId)	
				
				if(P[0]!=''):
					for z in range(0,len(P)):
						newPipe.LookupParameter(P[z]).Set(str(pipe.LookupParameter(P[z]).AsString()))
						
				newPipeConnectors = newPipe.ConnectorManager.Connectors
				connA = None
				connB = None
				for c in pipe.ConnectorManager.Connectors:
					pc = c.Origin
					nearest = [x for x in newPipeConnectors if pc.DistanceTo(x.Origin) < 0.01]
					if nearest:
						connA = c
						connB = nearest[0]
				takeoff = doc.Create.NewUnionFitting(connA, connB)	
				
				if(P[0]!=''):
					for z in range(0,len(P)):
						takeoff.LookupParameter(P[z]).Set(str(pipe.LookupParameter(P[z]).AsString()))
						
	except:
		transaction.RollBack()
	else:
		transaction.Commit()

except:
	pass