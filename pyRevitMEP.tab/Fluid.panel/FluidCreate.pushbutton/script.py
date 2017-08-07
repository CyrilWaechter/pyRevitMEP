# coding: utf8

# noinspection PyUnresolvedReferences
from Autodesk.Revit import Exceptions
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import Transaction, UnitUtils, DisplayUnitType
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB.Plumbing import FluidType, FluidTemperature
# noinspection PyUnresolvedReferences
from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons, TaskDialogResult
import ctypes
import os
import rpw

__doc__ = "Create a Fluid with all temperatures within desired range"
__title__ = "Create a fluid"
__author__ = "Cyril Waechter"

ComboBox = rpw.ui.forms.flexform.ComboBox
Label = rpw.ui.forms.flexform.Label
TextBox = rpw.ui.forms.flexform.TextBox
Button = rpw.ui.forms.flexform.Button

#Load CoolProp shared library and configure PropsSI c_types units
CP = ctypes.cdll.LoadLibrary(os.path.join(__commandpath__, "CoolProp_x64.dll"))
PropsSI = CP.PropsSI
PropsSI.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_double, ctypes.c_char_p, ctypes.c_double, ctypes.c_char_p)
PropsSI.restype = ctypes.c_double

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

fluid_list = ['1-Butene', 'Acetone', 'Air', 'Ammonia', 'Argon', 'Benzene', 'CarbonDioxide', 'CarbonMonoxide', 'CarbonylSulfide', 'cis-2-Butene', 'CycloHexane', 'Cyclopentane', 'CycloPropane', 'D4', 'D5', 'D6', 'Deuterium', 'Dichloroethane', 'DiethylEther', 'DimethylCarbonate', 'DimethylEther', 'Ethane', 'Ethanol', 'EthylBenzene', 'Ethylene', 'EthyleneOxide', 'Fluorine', 'HeavyWater', 'Helium', 'HFE143m', 'Hydrogen', 'HydrogenChloride', 'HydrogenSulfide', 'IsoButane', 'IsoButene', 'Isohexane', 'Isopentane', 'Krypton', 'm-Xylene', 'MD2M', 'MD3M', 'MD4M', 'MDM', 'Methane', 'Methanol', 'MethylLinoleate', 'MethylLinolenate', 'MethylOleate', 'MethylPalmitate', 'MethylStearate', 'MM', 'n-Butane', 'n-Decane', 'n-Dodecane', 'n-Heptane', 'n-Hexane', 'n-Nonane', 'n-Octane', 'n-Pentane', 'n-Propane', 'n-Undecane', 'Neon', 'Neopentane', 'Nitrogen', 'NitrousOxide', 'Novec649', 'o-Xylene', 'OrthoDeuterium', 'OrthoHydrogen', 'Oxygen', 'p-Xylene', 'ParaDeuterium', 'ParaHydrogen', 'Propylene', 'Propyne', 'R11', 'R113', 'R114', 'R115', 'R116', 'R12', 'R123', 'R1233zd(E)', 'R1234yf', 'R1234ze(E)', 'R1234ze(Z)', 'R124', 'R125', 'R13', 'R134a', 'R13I1', 'R14', 'R141b', 'R142b', 'R143a', 'R152A', 'R161', 'R21', 'R218', 'R22', 'R227EA', 'R23', 'R236EA', 'R236FA', 'R245ca', 'R245fa', 'R32', 'R365MFC', 'R40', 'R404A', 'R407C', 'R41', 'R410A', 'R507A', 'RC318', 'SES36', 'SulfurDioxide', 'SulfurHexafluoride', 'Toluene', 'trans-2-Butene', 'Water', 'Xenon']

form_items = [Label("Pick a fluid"),
              ComboBox("fluid", fluid_list),
              Label("Set fluid name"),
              TextBox("name"),
              Label("Set fluid starting temperature (°C)"),
              TextBox("t_start"),
              Label("Set fluid last temperature (°C)"),
              TextBox("t_end"),
              Label("Set step between each temperature)"),
              TextBox("t_step"),
              Button("Select")]

form = rpw.ui.forms.FlexForm("FluidSelection", form_items)
form.show()


#Set desired fluid, initial temperature(freezing temperature ?), desired pressure for properties call
fluid = form.values["fluid"]
fluid_name = form.values["name"]
t_init = 273.15
t_start = int(form.values["t_start"])
t_end = int(form.values["t_end"])
pressure = 101325

#Check if fluid_type exist and create it if not
fluid_type = FluidType.GetFluidType(doc, fluid_name)
if fluid_type is None:
    t = Transaction(doc, "Create fluid type")
    t.Start()
    FluidType.Create(doc, fluid_name)
    t.Commit()
    fluid_type = FluidType.GetFluidType(doc, fluid_name)

#Add new temperature with associated heat capacity and viscosity
t = Transaction(doc, "Add temperature")
t.Start()
for i in xrange(t_start, t_end+1):
    #Call CoolProp to get fluid properties and convert it to internal units if necessary
    temperature = t_init+i
    viscosity = UnitUtils.ConvertToInternalUnits(PropsSI('V', 'T', temperature, 'P', pressure, fluid),
                                                 DisplayUnitType.DUT_PASCAL_SECONDS)
    density = UnitUtils.ConvertToInternalUnits(PropsSI('D','T',temperature,'P',pressure,fluid),
                                               DisplayUnitType.DUT_KILOGRAMS_PER_CUBIC_METER)
    #Catching exceptions and trying to overwrite temperature if asked by user in the TaskDialog
    try:
        fluid_type.AddTemperature(FluidTemperature(temperature,viscosity,density))
    except Exceptions.ArgumentException:
        result = TaskDialog.Show("Error", "Temperature already exist, do you want to overwrite it ?", TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No | TaskDialogCommonButtons.Cancel, TaskDialogResult.Yes)
        if result == TaskDialogResult.Yes:
            try:
                fluid_type.RemoveTemperature(temperature)
                fluid_type.AddTemperature(FluidTemperature(temperature,viscosity,density))
            except Exceptions.ArgumentException:
                TaskDialog.Show("Overwrite error", "Temperature is currently in use and cannot be overwritten")
        elif result == TaskDialogResult.No:
            pass
        else:
            break
t.Commit()

