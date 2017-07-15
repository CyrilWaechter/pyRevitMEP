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
from revitutils import doc, selection
from scriptutils.userinput import WPFWindow
import clr
clr.AddReference("PresentationFramework")
from System.Windows.Controls import TextBox

# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import Transaction, Element, BuiltInParameter
# noinspection PyUnresolvedReferences
from Autodesk.Revit import Exceptions

class ViewRename(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.DataContext = self

    def btnUpdateSource_Click(self, sender, e):
        binding = self.txtWindowTitle.GetBindingExpression(TextBox.TextProperty)
        binding.UpdateSource()

ViewRename('wpfbindingsample.xaml').ShowDialog()

__doc__ = "Copy view types"
__title__ = "Copy view type"
__author__ = "Cyril Waechter"
