# coding: utf8
import rpw
# noinspection PyUnresolvedReferences
from rpw import DB, UI
# noinspection PyUnresolvedReferences
from Autodesk.Revit.Exceptions import InvalidOperationException
from scriptutils import logger
from scriptutils.userinput import WPFWindow

__doc__ = "Copy legend location in active ViewSheet"
__title__ = "CopyLegendsLocations"
__author__ = "Cyril Waechter"

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


class CustomizableEvent:
    def __init__(self):
        self.function_or_method = None
        self.args = ()
        self.kwargs = {}

    def raised_method(self):
        self.function_or_method(*self.args, **self.kwargs)

    def raise_event(self, function_or_method, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.function_or_method = function_or_method
        custom_event.Raise()


customizable_event = CustomizableEvent()


# Create a subclass of IExternalEventHandler
class CustomHandler(UI.IExternalEventHandler):
    """Input : function or method. Execute input in a IExternalEventHandler"""

    # Execute method run in Revit API environment.
    # noinspection PyPep8Naming, PyUnusedLocal
    def Execute(self, application):
        try:
            customizable_event.raised_method()
        except InvalidOperationException:
            # If you don't catch this exeption Revit may crash.
            print("InvalidOperationException catched")

    # noinspection PyMethodMayBeStatic, PyPep8Naming
    def GetName(self):
        return "Execute an function or method in a IExternalHandler"


# Create an handler instance and his associated ExternalEvent
custom_handler = CustomHandler()
custom_event = UI.ExternalEvent.Create(custom_handler)


class CopyPasteGUI(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)

    def copy_click(self, sender, e):
        Legends.get_locations()

    def paste_click(self, sender, e):
        customizable_event.raise_event(Legends.set_locations)


CopyPasteGUI('CopyLegendsLocations.xaml').Show()
