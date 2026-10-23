# -*- coding: utf-8 -*-
""" Renumber Mark Parameter of MEP elements."""

__title__ = 'Renumber Mark'
__author__ = 'André Rodrigues da Silva'
		
from rpw import revit, db
from rpw.ui.forms import (FlexForm, Label, ComboBox, TextBox, TextBox,Separator, Button, CheckBox)
from rpw.ui.forms import select_file
from Autodesk.Revit.DB import Transaction
from Autodesk.Revit.DB.Plumbing.PlumbingUtils import BreakCurve 
from rpw.db.xyz import XYZ
import csv

try:
	components = [ Label('Renumber Mark Parameter:'),
				   Label('Description parameter:'),
				   TextBox('textbox1', Text="AR - DESCRICAO"),
				   Label('Mark Parameter:'),
				   TextBox('textbox2', Text="Mark"),
				   Separator(),
				   Button('Process')]
	form = FlexForm('Renumber Mark Parameter', components)
	form.show()
	
	#Tubos = db.Collector(of_category='OST_PipeCurves',is_not_type=True)
	ConexoesTubo = db.Collector(of_category='OST_PipeFitting',is_not_type=True)
	AcessoriosTubo = db.Collector(of_category='OST_PipeAccessory',is_not_type=True)
	Equipamentos = db.Collector(of_category='OST_PlumbingFixtures',is_not_type=True)
	ConexoesDuto = db.Collector(of_category='OST_DuctFitting',is_not_type=True)
	AcessoriosDuto = db.Collector(of_category='OST_DuctAccessory',is_not_type=True)
	EquipamentosMecanicos = db.Collector(of_category='OST_MechanicalEquipment',is_not_type=True)

	Elementos = []

	"""
	if len(Tubos)>0:
		for i in range(0,len(Tubos)):
			Elementos.append(Tubos[i])
	"""

	if len(ConexoesTubo)>0:
		for i in range(0,len(ConexoesTubo)):
			Elementos.append(ConexoesTubo[i])
	if len(AcessoriosTubo)>0:
		for i in range(0,len(AcessoriosTubo)):
			Elementos.append(AcessoriosTubo[i])
	if len(AcessoriosTubo)>0:
		for i in range(0,len(Equipamentos)):
			Elementos.append(Equipamentos[i])
	if len(ConexoesDuto)>0:
		for i in range(0,len(ConexoesDuto)):
			Elementos.append(ConexoesDuto[i])
	if len(AcessoriosDuto)>0:
		for i in range(0,len(AcessoriosDuto)):
			Elementos.append(AcessoriosDuto[i])
	if len(EquipamentosMecanicos)>0:
		for i in range(0,len(EquipamentosMecanicos)):
			Elementos.append(EquipamentosMecanicos[i])
	
	# Typical Transaction in Revit Python Shell / pyRevit
	doc = __revit__.ActiveUIDocument.Document
	transaction = Transaction(doc, 'Delete Object')
	transaction.Start()
	
	try:
	
		DESC = []
		REF = []
		ParBase = form.values['textbox1']
		Mark = form.values['textbox2']
		for i in range(0,len(Elementos)):
			if (not Elementos[i].LookupParameter(ParBase).AsString()):
				Elementos[i].LookupParameter(Mark).Set(0)
			else:
				REF.append(Elementos[i])
				DESC.append(Elementos[i].LookupParameter(ParBase).AsString())
		
		Elementos2 = REF
		L1 = DESC
		L2 =  []
		for  i in range(0,len(L1),1):
			L2.append(i)
		
		REF = L2
		
		
		L3=[]
		for i in DESC:
			   if i not in L3:
				  L3.append(i)
		L3 = sorted(L3,  key=str.lower)

		L4 = []
		for i in range(0,len(REF),1):
			if(DESC[i] in L3):
				L4.append(str(L3.index(DESC[i])+1))	
				
		for i in range(0,len(Elementos2)):
			Elementos2[i].LookupParameter(Mark).Set(L4[i])
			
	except:
		transaction.RollBack()
	else:
		transaction.Commit()
		
except:
	pass