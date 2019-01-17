# coding: utf8

import System

from Autodesk.Revit.DB import Document, UnitUtils, UnitType, UnitSymbolType, LabelUtils, FormatOptions, DisplayUnitType

import rpw
from pyrevit import forms, script

doc = rpw.revit.doc  # type: Document

unit_format_options = doc.GetUnits().GetFormatOptions(UnitType.UT_Length)


display_unit = unit_format_options.DisplayUnits
symbol_type = unit_format_options.UnitSymbol
if symbol_type == UnitSymbolType.UST_NONE:
    try:
        symbol_type = FormatOptions.GetValidUnitSymbols(display_unit).Item[1]
    except System.ArgumentOutOfRangeException:
        display_unit = DisplayUnitType.DUT_DECIMAL_FEET
        symbol_type = FormatOptions.GetValidUnitSymbols(display_unit).Item[1]
symbol = LabelUtils.GetLabelFor(symbol_type)

def import_config_length(length):
    return str(UnitUtils.ConvertFromInternalUnits(float(length), display_unit))

def export_config_length(lenght):
    return str(UnitUtils.ConvertToInternalUnits(float(lenght), display_unit))

class CreateSectionOptions(forms.WPFWindow):
    def __init__(self):
        forms.WPFWindow.__init__(self, "CreateSectionOptions.xaml")
        self.set_image_source(self.diagram_img, "diagram.png")

        self.tblock_units.Text = "All length in {}".format(symbol)

        # get parameters from config file or use default values
        self._config = script.get_config()

        self.tbox_prefix.Text = self._config.get_option('prefix', 'Mur')
        self.tbox_depth_offset.Text = import_config_length(self._config.get_option('depth_offset', '1'))
        self.tbox_height_offset.Text = import_config_length(self._config.get_option('height_offset', '1'))
        self.tbox_width_offset.Text = import_config_length(self._config.get_option('width_offset', '1'))

    def save_options(self, sender, e):
        self._config.prefix = self.tbox_prefix.Text
        self._config.depth_offset = export_config_length(self.tbox_depth_offset.Text)
        self._config.height_offset = export_config_length(self.tbox_height_offset.Text)
        self._config.width_offset = export_config_length(self.tbox_width_offset.Text)
        script.save_config()
        self.Close()

    def reset_options(self, sender, e):
        script.reset_config()
        self.Close()
        reseted_gui = CreateSectionOptions().show_dialog()


options_gui = CreateSectionOptions().show_dialog()

