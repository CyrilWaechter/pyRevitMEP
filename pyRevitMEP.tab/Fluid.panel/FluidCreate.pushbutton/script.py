# coding: utf8

# noinspection PyUnresolvedReferences
from Autodesk.Revit import Exceptions
# noinspection PyUnresolvedReferences
from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons, TaskDialogResult
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import UnitUtils, DisplayUnitType
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB.Plumbing import FluidType, FluidTemperature
from pyrevit import script
from pyrevit.forms import WPFWindow
import ctypes
import os
import rpw
# noinspection PyUnresolvedReferences
from rpw import revit
# noinspection PyUnresolvedReferences

__doc__ = "Create a Fluid with all temperatures within desired range"
__title__ = "Create a fluid"
__author__ = "Cyril Waechter"

logger = script.get_logger()

ComboBox = rpw.ui.forms.flexform.ComboBox
Label = rpw.ui.forms.flexform.Label
TextBox = rpw.ui.forms.flexform.TextBox
Button = rpw.ui.forms.flexform.Button

# Load CoolProp shared library and configure PropsSI c_types units
cool_prop_dir = os.path.abspath(__commandpath__ + "/../bin/")
CP = ctypes.cdll.LoadLibrary(os.path.join(cool_prop_dir, "CoolProp_x64.dll"))
PropsSI = CP.PropsSI
PropsSI.argtypes = (ctypes.c_char_p,  # searched value. Example 'V' (Viscosity)
                    ctypes.c_char_p, ctypes.c_double,  # Fixed propriety 1. Example for temperature in K : 'T', 273.15
                    ctypes.c_char_p, ctypes.c_double,  # Fixed propriety 2. Example for pressure in Pa : 'P', 101325
                    ctypes.c_char_p)  # Fluid name
PropsSI.restype = ctypes.c_double

doc = revit.doc

fluids_dict = {}

for foldername, subfolders, files in os.walk(__commandpath__):
    for file in files:
        if str(file).endswith('.csv'):
            with open(os.path.join(foldername, file), 'r') as f:
                content = f.readlines()
            fluids_dict[file[:-4]] = content
logger.debug(fluids_dict)


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
        with rpw.db.Transaction("Create fluid type"):
            FluidType.Create(doc, fluid_name)
        fluid_type = FluidType.GetFluidType(doc, fluid_name)
    return fluid_type


def freeze_temp(fluid_name, pressure=101325):
    """
    Return freezing temperature of a given fluid at a given temperature
    :param fluid_name: fluid name including concentration if mixture
    :param pressure: defined pressure in Pa, default=101325 (1 atm)
    :return: freezing temperature in K
    """
    logger.debug(fluid_name)
    if "INCOMP::" not in fluid_name:
        return 'unknown'
    else:
        temp = 273.15 + 50
        if PropsSI("V", "T", temp, "P", pressure, fluid_name) == float('Inf'):
            return 'unknown'
        while True:
            # Check if CoolProp return a valid value. Else freeze_temp is reached.
            value = PropsSI("V", "T", temp, "P", pressure, fluid_name)
            logger.debug("{} : {}".format(type(value), value))
            if value != float('Inf'):
                temp -= 1
                continue
            else:
                temp += 1
                break
    return temp


def evaporation_temp(fluid_name, pressure=101325):
    """
    Return freezing temperature of a given fluid at a given temperature
    :param fluid_name: fluid name including concentration if mixture
    :param pressure: defined pressure in Pa, default=101325 (1 atm)
    :return: freezing temperature in K
    """
    logger.debug(fluid_name)
    if "INCOMP::" not in fluid_name:
        temp = PropsSI('T', 'P', pressure, 'Q', 0, fluid_name)
    else:
        temp = 273.15 + 50
        if PropsSI("V", "T", temp, "P", pressure, fluid_name) == float('Inf'):
            return 'unknown'
        while True:
            value = PropsSI("V", "T", temp, "P", pressure, fluid_name)
            logger.debug("{} : {}".format(type(value), value))
            if value != float('Inf'):
                temp += 1
                continue
            else:
                temp -= 1
                break
    return temp


def add_temperatures(t_start, t_end, fluid_type, coolprop_fluid, pressure, t_init=273.15):
    """
    Add new temperature with associated heat capacity and viscosity
    :return: None
    """
    with rpw.db.Transaction("Add temperatures"):
        for i in xrange(t_start, t_end + 1):
            # Call CoolProp to get fluid properties and convert it to internal units if necessary
            temperature = t_init + i
            viscosity = UnitUtils.ConvertToInternalUnits(
                PropsSI('V', 'T', temperature, 'P', pressure, coolprop_fluid), DisplayUnitType.DUT_PASCAL_SECONDS)
            density = UnitUtils.ConvertToInternalUnits(PropsSI('D', 'T', temperature, 'P', pressure, coolprop_fluid),
                                                          DisplayUnitType.DUT_KILOGRAMS_PER_CUBIC_METER)
            logger.debug('ν={}, ρ={}'.format(viscosity, density))
            # Catching exceptions and trying to overwrite temperature if asked by user in the TaskDialog
            try:
                fluid_type.AddTemperature(FluidTemperature(temperature, viscosity, density))
            except Exceptions.ArgumentException:
                result = TaskDialog.Show("Error", "Temperature already exist, do you want to overwrite it ?",
                                         TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No |
                                         TaskDialogCommonButtons.Cancel,
                                         TaskDialogResult.Yes)
                if result == TaskDialogResult.Yes:
                    try:
                        fluid_type.RemoveTemperature(temperature)
                        fluid_type.AddTemperature(FluidTemperature(temperature, viscosity, density))
                    except Exceptions.ArgumentException:
                        TaskDialog.Show("Overwrite error", "Temperature is currently in use and cannot be overwritten")
                elif result == TaskDialogResult.No:
                    pass
                else:
                    break

class FluidSelection(WPFWindow):
    """
    Form used to get fluids inputs
    """

    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.set_image_source(self.freeze_img, "icons8-Snowflake-32.png")
        self.set_image_source(self.evaporate_img, "icons8-Air-32.png")
        self.cb_fluid_category.ItemsSource = fluids_dict.keys()
        self.cb_fluid_name.ItemsSource = fluids_dict[self.cb_fluid_category.SelectedItem]

    # noinspection PyUnusedLocal
    def fluid_category_changed(self, sender, e):
        self.cb_fluid_name.ItemsSource = fluids_dict[self.cb_fluid_category.SelectedItem]

    # noinspection PyUnusedLocal
    def fluid_property_changed(self, sender, e):
        pressure = float(self.txt_pressure.Text)
        fluid_concentration = float(self.txt_concentration.Text)
        coolprop_fluid = str(self.cb_fluid_name.SelectedItem).split(',')[0]
        if coolprop_fluid is not None:
            if 'incompressible' in self.cb_fluid_category.SelectedItem.lower():
                coolprop_fluid = 'INCOMP::{0}[{1}]'.format(coolprop_fluid, fluid_concentration)
            self.freeze_temp_text.Text = str(freeze_temp(coolprop_fluid, pressure))
            self.evaporate_temp_text.Text = str(evaporation_temp(coolprop_fluid, pressure))

    # noinspection PyUnusedLocal
    def add_temperature_click(self, sender, e):
        # Get form inputs
        t_start = float(self.t_start.Text)
        t_end = float(self.t_end.Text)
        t_step = float(self.t_step.Text)
        coolprop_fluid = str(self.cb_fluid_name.SelectedItem).split(',')[0]
        fluid_concentration = float(self.txt_concentration.Text)
        pressure = float(self.txt_pressure.Text)

        # Create or get Revit FluidType
        revit_fluid_name = self.revit_fluid_name.Text
        fluid_type = create_fluid_type(revit_fluid_name)

        # If it is an incompressible fluid. CoolProp need a special format.
        if 'incompressible' in self.cb_fluid_category.SelectedItem.lower():
            coolprop_fluid = 'INCOMP::{0}[{1}]'.format(coolprop_fluid, fluid_concentration)

        # Finally add temperatures to Revit Project
        add_temperatures(t_start, t_end, fluid_type, coolprop_fluid, pressure)

    def hyperlink(self, sender, e):
        script.open_url(str(sender.NavigateUri))


FluidSelection('FluidSelection.xaml').ShowDialog()
