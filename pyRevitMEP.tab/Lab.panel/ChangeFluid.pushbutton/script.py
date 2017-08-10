# coding: utf8
"""
Copyright (c) 2017 Cyril Waechter
Python scripts for Autodesk Revit

This file is part of pyRevitMEP repository at https://github.com/CyrilWaechter/pyRevitMEP

pyRevitMEP is an extension for pyRevit. It contain free set of scripts for Autodesk Revit:
you can redistribute it and/or modify it under the terms of the GNU General Public License
version 3, as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

See this link for a copy of the GNU General Public License protecting this package.
https://github.com/CyrilWaechter/pyRevitMEP/blob/master/LICENSE
"""
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import FilteredElementCollector, Element, Transaction
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB.Plumbing import PipingSystemType, FluidType, FluidTemperature
from revitutils import doc
from scriptutils.forms import WPFWindow
import rpw

ComboBox = rpw.ui.forms.flexform.ComboBox
Label = rpw.ui.forms.flexform.Label
Button = rpw.ui.forms.flexform.Button

class RevitFluids(object):
    def __init__(self, document=doc):
        self.doc = document
        self.fluids = FilteredElementCollector(self.doc).OfClass(FluidType)

    @property
    def names(self):
        names_list = []
        for fluid in self.fluids:
            names_list.append(Element.Name.GetValue(fluid))
        return names_list

    @property
    def fluid_dict(self):
        d = {}
        for fluid in self.fluids:
            d[Element.Name.GetValue(fluid)]=RevitFluidType(fluid)
        return d


class RevitFluidType(object):
    def __init__(self, revit_fluid):
        self.revit_fluid = revit_fluid

    @property
    def name(self):
        """
        :return: fluid type name
        """
        return Element.Name.GetValue(self.revit_fluid)

    @property
    def revit_temperatures(self):
        """
        :return: temperatures of fluid
        """
        return list(self.revit_fluid.GetFluidTemperatureSetIterator())

    @property
    def temperatures_dict(self):
        d = {}
        for temp in self.revit_fluid.GetFluidTemperatureSetIterator():
            d[temp.Temperature]=temp
        return d

    @property
    def viscosity_dict(self):
        d = {}
        for temp in self.revit_fluid.GetFluidTemperatureSetIterator():
            d[temp.Viscosity]=temp
        return d

    @property
    def density_dict(self):
        d = {}
        for temp in self.revit_fluid.GetFluidTemperatureSetIterator():
            d[temp.Density]=temp
        return d

revit_fluids = RevitFluids()


def change_temperature(source_fluid, source_temp, target_fluid, target_temp, any_source_temp=False, find_target_temp=False):

    systems = FilteredElementCollector(doc).OfClass(PipingSystemType)
    system_list = []
    for system in systems:
        if doc.GetElement(system.FluidType) == source_fluid:
            if doc.GetElement(system.FluidTemperature) == source_temp or any_source_temp:
                system_list.append(system)
    t = Transaction(doc, 'change systems fluid')
    t.Start()
    for system in system_list:
        system.FluidType = target_fluid
        if find_target_temp:
            temp = doc.GetElement(system.FluidTemperature).Temperature
            revit_temp = target_fluid.GetTemperature(temp)
            if revit_temp is not None:
                system.FluidTemperature = revit_temp
            else:
                system.FluidTemperature = target_temp
        else:
            system.FluidTemperature = target_temp
    t.Commit()


class TemperatureSelection(WPFWindow):
    """
    Form used to get fluids inputs
    """

    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.cb_source_fluid_type.ItemsSource = revit_fluids.names
        self.cb_target_fluid_type.ItemsSource = revit_fluids.names
        source_fluid = revit_fluids.fluid_dict[self.cb_source_fluid_type.SelectedItem]
        target_fluid = revit_fluids.fluid_dict[self.cb_target_fluid_type.SelectedItem]
        self.cb_source_fluid_temperature.ItemsSource = sorted(source_fluid.temperatures_dict.keys())
        self.cb_target_fluid_temperature.ItemsSource = sorted(target_fluid.temperatures_dict.keys())


    # noinspection PyUnusedLocal
    def source_fluid_type_changed(self, sender, e):
        source_fluid = revit_fluids.fluid_dict[sender.SelectedItem]
        self.cb_source_fluid_temperature.ItemsSource = sorted(source_fluid.temperatures_dict.keys())

    def target_fluid_type_changed(self, sender, e):
        target_fluid = revit_fluids.fluid_dict[sender.SelectedItem]
        self.cb_target_fluid_temperature.ItemsSource = sorted(target_fluid.temperatures_dict.keys())

    # noinspection PyUnusedLocal
    def change_temp_click(self, sender, e):
        # Get form inputs
        source_fluid = revit_fluids.fluid_dict[self.cb_source_fluid_type.SelectedItem]
        target_fluid = revit_fluids.fluid_dict[self.cb_target_fluid_type.SelectedItem]
        source_temp = source_fluid.temperatures_dict[self.cb_source_fluid_temperature.SelectedItem]
        target_temp = target_fluid.temperatures_dict[self.cb_source_fluid_temperature.SelectedItem]
        change_temperature(source_fluid, source_temp, target_fluid, target_temp)

TemperatureSelection('TemperatureSelection.xaml').ShowDialog()


