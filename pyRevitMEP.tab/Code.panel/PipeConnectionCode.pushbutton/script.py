# -*- coding: utf-8 -*-
""" Insert code in ALL elements."""

__title__ = 'Pipe \n Connection'
__author__ = 'André Rodrigues da Silva'

import clr
clr.AddReference("PresentationFramework")
from System.Windows import Window

file = ''
class ButtonClass(Window):
    @staticmethod
    def Importarbase(sender, e):
		global file
		file = select_file('csv separated by semicolon (*.csv)|*.csv')
		return(file)


def RevitCodes(dim):
    if(dim == '15'):
        return ('0.049212598425196846')
    if(dim == '16'):
        return ('0.052493438320209973')
    if(dim == '20'):
        return ('0.065616797900262466')
    if(dim == '22'):
        return ('0.072178477690288706')
    if(dim == '25'):
        return ('0.082020997375328086')
    if(dim == '28'):
        return ('0.091863517060367453')
    if(dim == '32'):
        return ('0.10498687664041995')
    if(dim == '35'):
        return ('0.11482939632545931')
    if(dim == '40'):
        return ('0.13123359580052493')
    if(dim == '42'):
        return ('0.13779527559055119')
    if(dim == '50'):
        return ('0.16404199475065617')
    if(dim == '54'):
        return ('0.17716535433070865')
    if(dim == '60'):
        return ('0.19685039370078738')
    if(dim == '63'):
        return ('0.20669291338582677')
    if(dim == '73'):
        return ('0.23950131233595801')
    if(dim == '75'):
        return ('0.24606299212598426')
    if(dim == '85'):
        return ('0.27887139107611547')
    if(dim == '89'):
        return ('0.29199475065616798')
    if(dim == '90'):
        return ('0.29527559055118108')
    if(dim == '100'):
        return ('0.32808398950131235')
    if(dim == '110'):
        return ('0.36089238845144356')
    if(dim == '114'):
        return ('0.37401574803149606')
    if(dim == '150'):
        return ('0.49212598425196852')
    if(dim == '200'):
        return ('0.65616797900262469')
    if(dim == '12.70'):
        return ('0.041666666666666664')
    if(dim == '19.05'):
        return ('0.0625')
    if(dim == '19.10'):
        return ('0.062664041994750661')
    if(dim == '25.40'):
        return ('0.083333333333333329')
    if(dim == '31.75'):
        return ('0.10433070866141732')
    if(dim == '38.10'):
        return ('0.125')
    if(dim == '50.80'):
        return ('0.16666666666666666')
    if(dim == '50.80'):
        return ('0.16666666666666666')
    if(dim == '63.50'):
        return ('0.20833333333333334')
    if(dim == '76.20'):
        return ('0.25')
    if(dim == '101.60'):
        return ('0.33333333333333331')
    if(dim == '45°'):
        return ('0.7853981633974475')
    if(dim == '90°'):
        return ('1.570796326794895')
    if(dim == '45º'):
        return ('0.7853981633974475')
    if(dim == '90º'):
        return ('1.570796326794895')
            
    else:
        return(dim)

		
from rpw import revit, db
from rpw.ui.forms import (FlexForm, Label, ComboBox, TextBox, TextBox,Separator, Button, CheckBox)
from rpw.ui.forms import select_file
from Autodesk.Revit.DB import Transaction
from Autodesk.Revit.DB.Plumbing.PlumbingUtils import BreakCurve 
from rpw.db.xyz import XYZ
import csv

try:
	components = [ Label('Codes in all pipe connections:'),
				   Label('Code parameter:'),
				   TextBox('textbox1', Text="AR - CODIGO"),
				   Label('Description parameter:'),
				   TextBox('textbox2', Text="AR - DESCRICAO"),
				   Button('Search base', on_click=ButtonClass.Importarbase),
				   Separator(),
				   Button('Process')]
	form = FlexForm('Insert code in all pipe connections', components)
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
	if len(Equipamentos)>0:
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

	with open(file,'r') as csv_file:
		lines = csv_file.readlines()

	line = lines[0].split(";")
	codigo_construtora = form.values['textbox1']
	descricao_construtora = form.values['textbox2']
	a = 0
	b = 0

	for i in range(0,len(line)):
		if(line[i] == codigo_construtora):
			a = i
		#if(line[i] == descricao_construtora):
			#b = i
			

	FamilyName = []
	Parameter1 = []
	Parameter2 = []
	Parameter3 = []
	Parameter4 = []
	Angle = []
	Indice = []
	ProductDescription = []
	TypeName = []
	CODIGO = []
	DESCRICAO = []

	for line in lines:
		data = line.split(';')
		FamilyName.append(data[0])
		Parameter1.append(data[1])
		Parameter2.append(data[2])
		Parameter3.append(data[3])
		Parameter4.append(data[4])
		Angle.append(data[5])
		Indice.append(data[6])
		ProductDescription.append(data[7])
		TypeName.append(data[8])
		CODIGO.append(data[a])
		DESCRICAO.append(data[a+1])

	# Typical Transaction in Revit Python Shell / pyRevit
	doc = __revit__.ActiveUIDocument.Document
	transaction = Transaction(doc, 'Delete Object')
	transaction.Start()

	try:
		for i in range(0,len(Elementos)):
			for t in range(0,len(FamilyName)):		
				if(Parameter1[t]!='' and Parameter2[t]!='' and Parameter3[t]=='' and Parameter4[t]=='' and Angle[t]=='' and ProductDescription[t] =='' and Indice[t]=='' and TypeName[t]==''):
					info1 = list(Parameter1[t].split('='))
					info2 = list(Parameter2[t].split('='))
					if(Elementos[i].Symbol.FamilyName == FamilyName[t] and Elementos[i].LookupParameter(info1[0]).AsDouble() == float(RevitCodes(info1[1])) and Elementos[i].LookupParameter(info2[0]).AsDouble() == float(RevitCodes(info2[1])) ):
						Elementos[i].LookupParameter(codigo_construtora).Set(CODIGO[t])
						Elementos[i].LookupParameter(descricao_construtora).Set(DESCRICAO[t])
				
				if(Parameter1[t]!='' and Parameter2[t]!='' and Parameter3[t]!='' and Parameter4[t]=='' and Angle[t]=='' and ProductDescription[t] =='' and Indice[t]=='' and TypeName[t]==''):
					info1 = list(Parameter1[t].split('='))
					info2 = list(Parameter2[t].split('='))
					info3 = list(Parameter3[t].split('='))
					if(Elementos[i].Symbol.FamilyName == FamilyName[t] and Elementos[i].LookupParameter(info1[0]).AsDouble() == float(RevitCodes(info1[1])) and Elementos[i].LookupParameter(info2[0]).AsDouble() == float(RevitCodes(info2[1])) and Elementos[i].LookupParameter(info3[0]).AsDouble() == float(RevitCodes(info3[1])) ):
						Elementos[i].LookupParameter(codigo_construtora).Set(CODIGO[t])
						Elementos[i].LookupParameter(descricao_construtora).Set(DESCRICAO[t])
				
				if(Parameter1[t]!='' and Parameter2[t]!='' and Parameter3[t]!='' and Parameter4[t]=='' and Angle[t]!='' and ProductDescription[t] =='' and Indice[t]=='' and TypeName[t]==''):
					info1 = list(Parameter1[t].split('='))
					info2 = list(Parameter2[t].split('='))
					info3 = list(Parameter3[t].split('='))
					angle = list(Angle[t].split('='))
					if(Elementos[i].Symbol.FamilyName == FamilyName[t] and Elementos[i].LookupParameter(info1[0]).AsDouble() == float(RevitCodes(info1[1])) and Elementos[i].LookupParameter(info2[0]).AsDouble() == float(RevitCodes(info2[1])) and Elementos[i].LookupParameter(info3[0]).AsDouble() == float(RevitCodes(info3[1])) and Elementos[i].LookupParameter(angle[0]).AsDouble() == float(RevitCodes(angle[1])) ):
						Elementos[i].LookupParameter(codigo_construtora).Set(CODIGO[t])
						Elementos[i].LookupParameter(descricao_construtora).Set(DESCRICAO[t])
						
				if(Parameter1[t]!='' and Parameter2[t]!='' and Parameter3[t]=='' and Parameter4[t]=='' and Angle[t]!='' and ProductDescription[t] ==''and Indice[t]=='' and TypeName[t]==''):
					info1 = list(Parameter1[t].split('='))
					info2 = list(Parameter2[t].split('='))
					angle = list(Angle[t].split('='))
					if(Elementos[i].Symbol.FamilyName == FamilyName[t] and Elementos[i].LookupParameter(info1[0]).AsDouble() == float(RevitCodes(info1[1])) and Elementos[i].LookupParameter(info2[0]).AsDouble() == float(RevitCodes(info2[1])) and Elementos[i].LookupParameter(angle[0]).AsDouble() == float(RevitCodes(angle[1])) ):
						Elementos[i].LookupParameter(codigo_construtora).Set(CODIGO[t])
						Elementos[i].LookupParameter(descricao_construtora).Set(DESCRICAO[t])
						
				if(Parameter1[t]!='' and Parameter2[t]=='' and Parameter3[t]=='' and Parameter4[t]=='' and Angle[t]!='' and ProductDescription[t] =='' and Indice[t]=='' and TypeName[t]==''):
					info1 = list(Parameter1[t].split('='))
					angle = list(Angle[t].split('='))
					if(Elementos[i].Symbol.FamilyName == FamilyName[t] and Elementos[i].LookupParameter(info1[0]).AsDouble() == float(RevitCodes(info1[1])) and Elementos[i].LookupParameter(angle[0]).AsDouble() == float(RevitCodes(angle[1])) ):
						Elementos[i].LookupParameter(codigo_construtora).Set(CODIGO[t])
						Elementos[i].LookupParameter(descricao_construtora).Set(DESCRICAO[t])				
		
				if(Parameter1[t]!='' and Parameter2[t]=='' and Parameter3[t]=='' and Parameter4[t]=='' and Angle[t]=='' and ProductDescription[t] =='' and Indice[t]=='' and TypeName[t]==''):
					info1 = list(Parameter1[t].split('='))
					if(Elementos[i].Symbol.FamilyName == FamilyName[t] and Elementos[i].LookupParameter(info1[0]).AsDouble() == float(RevitCodes(info1[1]))):
						Elementos[i].LookupParameter(codigo_construtora).Set(CODIGO[t])
						Elementos[i].LookupParameter(descricao_construtora).Set(DESCRICAO[t])
							
				if(Parameter1[t]=='' and Parameter2[t]!='' and Parameter3[t]=='' and Parameter4[t]=='' and Angle[t]=='' and ProductDescription[t] =='' and Indice[t]=='' and TypeName[t]==''):
					info1 = list(Parameter1[t].split('='))
					if(Elementos[i].Symbol.FamilyName == FamilyName[t] and Elementos[i].LookupParameter(info1[0]).AsDouble() == float(RevitCodes(info1[1]))):
						Elementos[i].LookupParameter(codigo_construtora).Set(CODIGO[t])
						Elementos[i].LookupParameter(descricao_construtora).Set(DESCRICAO[t])
						

				if(Parameter1[t]!='' and Parameter2[t]=='' and Parameter3[t]=='' and Parameter4[t]=='' and Angle[t]!='' and ProductDescription[t] =='' and Indice[t]=='' and TypeName[t]==''):
					info1 = list(Parameter1[t].split('='))
					angle = list(Angle[t].split('='))
					if(Elementos[i].Symbol.FamilyName == FamilyName[t] and Elementos[i].LookupParameter(info1[0]).AsDouble() == float(RevitCodes(info1[1])) and Elementos[i].LookupParameter(angle[0]).AsDouble() == float(RevitCodes(angle[1])) ):
						Elementos[i].LookupParameter(codigo_construtora).Set(CODIGO[t])
						Elementos[i].LookupParameter(descricao_construtora).Set(DESCRICAO[t])
						
				if(Parameter1[t]!='' and Parameter2[t]!='' and Parameter3[t]!='' and Parameter4[t]!='' and Angle[t]!='' and ProductDescription[t] =='' and Indice[t]=='' and TypeName[t]==''):
					info1 = list(Parameter1[t].split('='))
					angle = list(Angle[t].split('='))
					if(Elementos[i].Symbol.FamilyName == FamilyName[t] and Elementos[i].LookupParameter(info1[0]).AsDouble() == float(RevitCodes(info1[1])) and Elementos[i].LookupParameter(info2[0]).AsDouble() == float(RevitCodes(info2[1])) and Elementos[i].LookupParameter(info3[0]).AsDouble() == float(RevitCodes(info3[1])) and Elementos[i].LookupParameter(info4[0]).AsDouble() == float(RevitCodes(info4[1])) and Elementos[i].LookupParameter(angle[0]).AsDouble() == float(RevitCodes(angle[1])) ):
						Elementos[i].LookupParameter(codigo_construtora).Set(CODIGO[t])
						Elementos[i].LookupParameter(descricao_construtora).Set(DESCRICAO[t])
						
				if(Parameter1[t]!='' and Parameter2[t]!='' and Parameter3[t]!='' and Parameter4[t]!='' and Angle[t]=='' and ProductDescription[t] =='' and Indice[t]=='' and TypeName[t]==''):
					info1 = list(Parameter1[t].split('='))
					angle = list(Angle[t].split('='))
					if(Elementos[i].Symbol.FamilyName == FamilyName[t] and Elementos[i].LookupParameter(info1[0]).AsDouble() == float(RevitCodes(info1[1])) and Elementos[i].LookupParameter(info2[0]).AsDouble() == float(RevitCodes(info2[1])) and Elementos[i].LookupParameter(info3[0]).AsDouble() == float(RevitCodes(info3[1])) and Elementos[i].LookupParameter(info4[0]).AsDouble() == float(RevitCodes(info4[1])) ):
						Elementos[i].LookupParameter(codigo_construtora).Set(CODIGO[t])
						Elementos[i].LookupParameter(descricao_construtora).Set(DESCRICAO[t])
				
				if(Parameter1[t]=='' and Parameter2[t]=='' and Parameter3[t]=='' and Parameter4[t]=='' and Angle[t]=='' and ProductDescription[t] =='' and Indice[t]=='' and TypeName[t]==''):
					if(Elementos[i].Symbol.FamilyName == FamilyName[t]):
						Elementos[i].LookupParameter(codigo_construtora).Set(CODIGO[t])
						Elementos[i].LookupParameter(descricao_construtora).Set(DESCRICAO[t])
						
				if(Parameter1[t]=='' and Parameter2[t]=='' and Parameter3[t]=='' and Parameter4[t]=='' and Angle[t]=='' and ProductDescription[t] !='' and Indice[t]=='' and TypeName[t]==''):
					info1 = list(ProductDescription[t].split('='))
					if(Elementos[i].Symbol.FamilyName == FamilyName[t] and Elementos[i].LookupParameter(info1[0]).AsString() == str(info1[1])):
						Elementos[i].LookupParameter(codigo_construtora).Set(CODIGO[t])
						Elementos[i].LookupParameter(descricao_construtora).Set(DESCRICAO[t])
						
				if(Parameter1[t]=='' and Parameter2[t]=='' and Parameter3[t]=='' and Parameter4[t]=='' and Angle[t]=='' and ProductDescription[t] =='' and Indice[t]!='' and TypeName[t]==''):
					info1 = list(Indice[t].split('='))
					if(Elementos[i].Symbol.FamilyName == FamilyName[t] and Elementos[i].LookupParameter(info1[0]).AsInteger() == int(info1[1])):
						Elementos[i].LookupParameter(codigo_construtora).Set(CODIGO[t])
						Elementos[i].LookupParameter(descricao_construtora).Set(DESCRICAO[t])
						
				
				if(Parameter1[t]=='' and Parameter2[t]=='' and Parameter3[t]=='' and Parameter4[t]=='' and Angle[t]=='' and ProductDescription[t] =='' and Indice[t]=='' and TypeName[t]!=''):
					#info1 = list(TypeName[t].split('='))
					info1 = TypeName[t]
					if(Elementos[i].Symbol.FamilyName == FamilyName[t] and Elementos[i].Name == str(info1)):
						Elementos[i].LookupParameter(codigo_construtora).Set(CODIGO[t])
						Elementos[i].LookupParameter(descricao_construtora).Set(DESCRICAO[t])
					
				

											
	except:
		transaction.RollBack()
	else:
		transaction.Commit()
		
except:
	pass