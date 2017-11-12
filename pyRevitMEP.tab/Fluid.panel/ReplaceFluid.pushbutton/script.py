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
from Autodesk.Revit.DB.Plumbing import PipingSystemType, FluidTemperature
# For future implementation in rpw
# from rpw.db.plumbing import FluidType
# Until done :
import imp
import os
from pyRevitMEP.plumbing import FluidType

import rpw
from revitutils import logger
from scriptutils.forms import WPFWindow

__doc__ = "Replace a selected fluid and temperature find in all systems by an other selected fluid and temperature"
__title__ = "Replace fluid"
__author__ = "Cyril Waechter"

doc = rpw.revit.doc
ComboBox = rpw.ui.forms.flexform.ComboBox
Label = rpw.ui.forms.flexform.Label
Button = rpw.ui.forms.flexform.Button


def change_temperature(source_fluid, source_temp, target_fluid, target_temp,
                       any_source_temp=False, find_target_temp=False):
    """
    :param source_fluid: FluidType.Id to be changed
    :param source_temp: Temperature in K to be changed (float)
    :param target_fluid: Replacement FluidType.Id
    :param target_temp: Replacement temperature in K (float)
    :param any_source_temp: boolean to force match any source temperature
    :param find_target_temp: boolean combined with any_source_temp to automatically match closest temperature
    :return:
    """
    logger.debug("change_temperature inputs:\n  {0}\n   {1}\n   {2}\n   {3}\n   {4}\n END OF INPUTS"
                 .format(source_fluid, source_temp, target_fluid, target_temp, any_source_temp))
    systems = FilteredElementCollector(doc).OfClass(PipingSystemType)
    system_list = []
    for system in systems:
        if system.FluidType == source_fluid:
            logger.debug("{}=={}?".format(system.FluidTemperature, source_temp))
            if system.FluidTemperature == source_temp or any_source_temp:
                system_list.append(system)
    logger.info("{} systems will get their fluid and or temperature changed".format(len(system_list)))
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
    logger.info("COMPLETED")


class TemperatureSelection(WPFWindow):
    """
    Form used to get fluids inputs
    """

    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.fluids_dict = {FluidType(fluid_type).name:FluidType(fluid_type) for fluid_type in FluidType.collect()}
        self.cb_source_fluid_type.ItemsSource = {v['name'] for k, v in FluidType.in_use_dict().iteritems()}
        self.cb_target_fluid_type.ItemsSource = [FluidType(fluid).name for fluid in FluidType.collect()]
        self.update_source_temperatures()
        self.update_target_temperatures()

    @property
    def source_fluid(self):
        return self.fluids_dict[self.cb_source_fluid_type.SelectedItem]

    @property
    def target_fluid(self):
        return self.fluids_dict[self.cb_target_fluid_type.SelectedItem]

    def update_source_temperatures(self):
        temps = {v['temperature'] for k, v in FluidType.in_use_dict().iteritems()}
        self.cb_source_fluid_temperature.ItemsSource = sorted(list(temps))

    def update_target_temperatures(self):
        self.cb_target_fluid_temperature.ItemsSource = sorted(self.target_fluid.temperatures)

    # noinspection PyUnusedLocal
    def source_fluid_type_changed(self, sender, e):
        self.update_source_temperatures()

    # noinspection PyUnusedLocal
    def target_fluid_type_changed(self, sender, e):
        self.update_target_temperatures()

    # noinspection PyUnusedLocal
    def change_temp_click(self, sender, e):
        # Get form inputs
        source_fluid_id = self.source_fluid.Id
        target_fluid_id = self.target_fluid.Id
        source_temp = self.cb_source_fluid_temperature.SelectedItem
        target_temp = self.cb_target_fluid_temperature.SelectedItem
        # Apply temperature change
        change_temperature(source_fluid_id, source_temp, target_fluid_id, target_temp)


TemperatureSelection('TemperatureSelection.xaml').ShowDialog()
