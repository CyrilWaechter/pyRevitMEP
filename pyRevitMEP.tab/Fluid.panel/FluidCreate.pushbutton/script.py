# coding: utf8

# noinspection PyUnresolvedReferences
from Autodesk.Revit import Exceptions
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import Transaction, UnitUtils, DisplayUnitType
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB.Plumbing import FluidType, FluidTemperature
# noinspection PyUnresolvedReferences
from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons, TaskDialogResult
from scriptutils.userinput import WPFWindow
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

fluid_list = {'Pure':
                  ('1-Butene', 'Acetone', 'Air', 'Ammonia', 'Argon', 'Benzene', 'CarbonDioxide', 'CarbonMonoxide',
                   'CarbonylSulfide', 'cis-2-Butene', 'CycloHexane', 'Cyclopentane', 'CycloPropane', 'D4', 'D5',
                   'D6', 'Deuterium', 'Dichloroethane', 'DiethylEther', 'DimethylCarbonate', 'DimethylEther',
                   'Ethane', 'Ethanol', 'EthylBenzene', 'Ethylene', 'EthyleneOxide', 'Fluorine', 'HeavyWater',
                   'Helium', 'HFE143m', 'Hydrogen', 'HydrogenChloride', 'HydrogenSulfide', 'IsoButane',
                   'IsoButene',
                   'Isohexane', 'Isopentane', 'Krypton', 'm-Xylene', 'MD2M', 'MD3M', 'MD4M', 'MDM', 'Methane',
                   'Methanol', 'MethylLinoleate', 'MethylLinolenate', 'MethylOleate', 'MethylPalmitate',
                   'MethylStearate', 'MM', 'n-Butane', 'n-Decane', 'n-Dodecane', 'n-Heptane', 'n-Hexane',
                   'n-Nonane',
                   'n-Octane', 'n-Pentane', 'n-Propane', 'n-Undecane', 'Neon', 'Neopentane', 'Nitrogen',
                   'NitrousOxide', 'Novec649', 'o-Xylene', 'OrthoDeuterium', 'OrthoHydrogen',
                   'Oxygen', 'p-Xylene', 'ParaDeuterium', 'ParaHydrogen', 'Propylene', 'Propyne', 'R11', 'R113',
                   'R114',
                   'R115', 'R116', 'R12', 'R123', 'R1233zd(E)', 'R1234yf', 'R1234ze(E)', 'R1234ze(Z)', 'R124',
                   'R125', 'R13',
                   'R134a', 'R13I1', 'R14', 'R141b', 'R142b', 'R143a', 'R152A', 'R161', 'R21', 'R218', 'R22',
                   'R227EA', 'R23',
                   'R236EA', 'R236FA', 'R245ca', 'R245fa', 'R32', 'R365MFC', 'R40', 'R404A', 'R407C', 'R41',
                   'R410A', 'R507A',
                   'RC318', 'SES36', 'SulfurDioxide', 'SulfurHexafluoride', 'Toluene', 'trans-2-Butene', 'Water',
                   'Xenon'),
              'Incompressible : Pure':
                  ("AS10","AS20","AS30","AS40","AS55","DEB","DowJ","DowJ2","DowQ","DowQ2","HC10","HC20","HC30","HC40","HC50","HCB","HCM","HFE","HFE2","HY20","HY30","HY40","HY45","HY50","NBS","NaK","PBB","PCL","PCR","PGLT","PHE","PHR","PLR","PMR","PMS1","PMS2","PNF","PNF2","S800","SAB","T66","T72","TCO","TD12","TVP1","TVP1869","TX22","TY10","TY15","TY20","TY24","Water","XLT","XLT2","ZS10","ZS25","ZS40","ZS45","ZS55"),
              'Incompressible : Mixtures (vol)':
                  ("AEG","AKF","AL","AN","APG","GKN","PK2","PKL","ZAC","ZFC","ZLC","ZM","ZMC"),
              'Incompressible : Mixtures (%)':
                  ("FRE","IceEA","IceNA","IcePG","LiBr","MAM","MAM2","MCA","MCA2","MEA","MEA2","MEG","MEG2","MGL","MGL2","MITSW","MKA","MKA2","MKC","MKC2","MKF","MLI","MMA","MMA2","MMG","MMG2","MNA","MNA2","MPG","MPG2","VCA","VKC","VMA","VMG","VNA")
              }


def create_fluid_type(fluid_name):
    """
    Check if fluid_type exist and create it if not
    :type fluid_name: str
    :param fluid_name: fluid name as string
    :return: FluidType with given name
    :rtype: Autodesk.Revit.DB.Plumbing.FluidType
    """
    fluid_type = FluidType.GetFluidType(doc, fluid_name)
    if fluid_type is None:
        t = Transaction(doc, "Create fluid type")
        t.Start()
        FluidType.Create(doc, fluid_name)
        t.Commit()
        fluid_type = FluidType.GetFluidType(doc, fluid_name)
    return fluid_type


def freeze_temp(fluid_name, pressure=101325):
    """
    Return freezing temperature of a given fluid at a given temperature
    :param fluid_name: fluid name including concentration if mixture
    :param pressure: defined pressure in Pa, default=101325 (1 atm)
    :return: freezing temperature in K
    """
    return PropsSI('T_FREEZE','T',275.15,'P',pressure, fluid_name)



def add_temperatures(t_start, t_end, fluid_type, coolprop_fluid, pressure, t_init=273.15):
    """
    Add new temperature with associated heat capacity and viscosity
    :return: None
    """
    t = Transaction(doc, "Add temperatures")
    t.Start()
    for i in xrange(t_start, t_end+1):
        #Call CoolProp to get fluid properties and convert it to internal units if necessary
        temperature = t_init+i
        viscosity = UnitUtils.ConvertToInternalUnits(PropsSI('V', 'T', temperature, 'P', pressure, coolprop_fluid),
                                                     DisplayUnitType.DUT_PASCAL_SECONDS)
        density = UnitUtils.ConvertToInternalUnits(PropsSI('D','T', temperature,'P', pressure, coolprop_fluid),
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

class FluidSelection(WPFWindow):
    """
    Form used to get fluids inputs
    """

    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.set_image_source("freeze_img", "icons8-Snowflake-32.png")
        self.set_image_source("evaporate_img", "icons8-Air-32.png")
        self.cb_fluid_category.ItemsSource = fluid_list.keys()
        self.cb_fluid_name.ItemsSource = fluid_list[self.cb_fluid_category.SelectedItem]

    # noinspection PyUnusedLocal
    def fluid_category_changed(self, sender, e):
        self.cb_fluid_name.ItemsSource = fluid_list[self.cb_fluid_category.SelectedItem]

    # noinspection PyUnusedLocal
    def add_temperature_click(self, sender, e):
        # Get form inputs
        t_start = float(self.t_start.Text)
        t_end = float(self.t_end.Text)
        t_step = float(self.t_step.Text)
        coolprop_fluid = self.cb_fluid_name.SelectedItem
        fluid_concentration = float(self.txt_concentration.Text)
        pressure = float(self.txt_pressure.Text)

        # Create or get Revit FluidType
        revit_fluid_name = self.revit_fluid_name.Text
        fluid_type = create_fluid_type(revit_fluid_name)

        # If it is an incompressible fluid. CoolProp need a special format.
        if 'incompressible' in coolprop_fluid.lower():
            coolprop_fluid = 'INCOMP::{0}[{1}]'.format(coolprop_fluid, fluid_concentration)

        # Finally add temperatures to Revit Project
        add_temperatures(t_start, t_end, fluid_type, coolprop_fluid, pressure)

FluidSelection('FluidSelection.xaml').ShowDialog()


