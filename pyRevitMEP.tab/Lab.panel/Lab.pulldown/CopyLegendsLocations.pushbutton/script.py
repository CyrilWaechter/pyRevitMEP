# coding: utf8
import rpw
# noinspection PyUnresolvedReferences
from rpw import DB, UI
# noinspection PyUnresolvedReferences
from Autodesk.Revit.Exceptions import InvalidOperationException
from pyrevit.script import get_logger
from pyrevit.forms import WPFWindow
from pyrevitmep.event import CustomizableEvent

__doc__ = "Copy legend location in active ViewSheet"
__title__ = "CopyLegendsLocations"
__author__ = "Cyril Waechter"

logger = get_logger()
doc = rpw.revit.doc
uidoc = rpw.uidoc


class Legends:
    legend_dict = {}

    @classmethod
    def get_locations(cls):
        viewsheet = uidoc.ActiveView
        logger.debug(viewsheet)

        if not isinstance(viewsheet, DB.ViewSheet):
            rpw.ui.forms.Alert("Please launch this command in a ViewSheet")
        else:
            for viewport_id in viewsheet.GetAllViewports():
                viewport = doc.GetElement(viewport_id)
                view = doc.GetElement(viewport.ViewId)
                if view.ViewType == DB.ViewType.Legend:
                    cls.legend_dict[viewport.ViewId] = viewport.GetBoxCenter()
            logger.debug(cls.legend_dict)

    @classmethod
    def set_locations(cls):
        viewsheet = uidoc.ActiveView
        if not isinstance(viewsheet, DB.ViewSheet):
            rpw.ui.forms.Alert("Please launch this command in a ViewSheet")
        else:
            with rpw.db.Transaction("Paste copied legends locations"):
                for viewport_id in viewsheet.GetAllViewports():
                    viewport = doc.GetElement(viewport_id)
                    view = doc.GetElement(viewport.ViewId)
                    if view.ViewType == DB.ViewType.Legend:
                        logger.debug(viewport.GetBoxCenter())
                        new_location = cls.legend_dict[viewport.ViewId]
                        logger.debug(new_location)
                        if new_location:
                            viewport.SetBoxCenter(new_location)


customizable_event = CustomizableEvent()


class CopyPasteGUI(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)

    def copy_click(self, sender, e):
        Legends.get_locations()

    def paste_click(self, sender, e):
        customizable_event.raise_event(Legends.set_locations)


CopyPasteGUI('CopyLegendsLocations.xaml').Show()
