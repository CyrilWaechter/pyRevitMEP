# -*- coding: utf-8 -*-
""" Clear Mark Parameter of MEP elements."""

__title__ = 'Clear Mark'
__author__ = 'André Rodrigues da Silva'
		
from rpw import revit, db
from rpw.ui.forms import (FlexForm, Label, ComboBox, TextBox, TextBox,Separator, Button, CheckBox)
from rpw.ui.forms import select_file
from Autodesk.Revit.DB import Transaction
from Autodesk.Revit.DB.Plumbing.PlumbingUtils import BreakCurve 
from rpw.db.xyz import XYZ
import csv

try:
	components = [ Label('Clear Mark Parameter:'),
				   Label('Mark Parameter:'),
				   TextBox('textbox1', Text="Mark"),
				   Separator(),
				   Button('Process')]
	form = FlexForm('Clear Mark Parameter', components)
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
		Mark = form.values['textbox1']
		for i in range(0,len(Elementos)):
			Elementos[i].LookupParameter(Mark).Set('')
			
	except:
		transaction.RollBack()
	else:
		transaction.Commit()
		
except:
	pass