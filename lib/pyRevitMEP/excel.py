# coding: utf8

import clr
clr.AddReferenceByName('Microsoft.Office.Interop.Excel, Version=11.0.0.0, Culture=neutral, PublicKeyToken=71e9bce111e9429c')
from Microsoft.Office.Interop import Excel
from System.Runtime.InteropServices import Marshal


class ExcelApp:
    def __init__(self, app=None, workbook=None):
        self.app = app
        self.workbook = workbook


def initialise():
    # If Excel is open, get it
    try:
        return Marshal.GetActiveObject("Excel.Application")
    # Else open it
    except EnvironmentError:
        return Excel.ApplicationClass()


def workbook_by_name(app, name):
    for workbook in app.Workbooks:
        if workbook.Name == name:
            return workbook


def none():
    try:
        workbook = app.ActiveWorkbook
    except AttributeError:
        workbook = app.Workbooks.Add()


def worksheet_by_name(workbook, name):
    for worksheet in workbook.Sheets:
        if worksheet.Name == name:
            return worksheet
