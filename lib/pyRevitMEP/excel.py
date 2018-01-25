# coding: utf8

import clr
clr.AddReferenceByName('Microsoft.Office.Interop.Excel, Version=11.0.0.0, Culture=neutral, PublicKeyToken=71e9bce111e9429c')
from Microsoft.Office.Interop import Excel
from System.Runtime.InteropServices import Marshal


class ExcelApp:
    def __init__(self, app=None, workbook=None):
        self.app = app
        self.workbook = workbook

    def initialise(self):
        # If Excel is open, get it
        try:
            self.app = Marshal.GetActiveObject("Excel.Application")
        # Else open it
        except EnvironmentError:
            self.app = Excel.ApplicationClass()

    def get_workbook(self):
        try:
            self.workbook = self.app.ActiveWorkbook
        except AttributeError:
            self.workbook = self.app.Workbooks.Add()


