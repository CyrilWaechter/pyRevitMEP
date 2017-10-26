# coding: utf8

import rpw
# noinspection PyUnresolvedReferences
from rpw import DB
# noinspection PyUnresolvedReferences
from Autodesk.Revit import Exceptions

__doc__ = "Batch create worksets from a text file"
__title__ = "Batch workset creation"
__author__ = "Cyril Waechter"

doc = rpw.revit.doc

if not doc.IsWorkshared:
    rpw.ui.forms.Alert("Current document is not workshared. You cannot create worksets.")
else:
    file = rpw.ui.forms.select_file(extensions='All Files (*.*)|*.*', title='Select File',
                                    multiple=False, restore_directory=True)

    with rpw.db.Transaction("Batch create worksets from file"):
        with open(file, "r") as text:
            for line in text.readlines():
                try:
                    DB.Workset.Create(doc, line.strip("\n"))
                except Exceptions.ArgumentException:
                    print("Following workset already exist or has invalid characters : {}".format(line.strip("\n")))
