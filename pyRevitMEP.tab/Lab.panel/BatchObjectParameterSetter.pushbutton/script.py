# coding: utf8
import rpw
# noinspection PyUnresolvedReferences
from rpw import DB, UI
# noinspection PyUnresolvedReferences
from Autodesk.Revit.Exceptions import InvalidOperationException
from scriptutils import logger
from scriptutils.userinput import WPFWindow
import re

__doc__ = "Batch parameter setter"
__title__ = "BatchParamSetter"
__author__ = "Cyril Waechter"

doc = rpw.revit.doc
uidoc = rpw.uidoc

class_dict = {
    'family': {'class': DB.FamilyInstance},
    'system': {'class': DB.MEPSystem},
    'space': {'class': DB.SpatialElement}
}

for k,v in class_dict.items():
    element = DB.FilteredElementCollector(doc).OfClass(class_dict[k]['class']).FirstElement()
    class_dict[k]['parameter_name_list'] = sorted([parameter.Definition.Name for parameter in element.Parameters])
    class_dict[k]['regex'] = re.compile(r"({})\(([\w\s]+)\)".format(k)) # class_key(parameter_name)

def set_parameter_value(pattern):
    with rpw.db.Transaction("Apply pattern to parameters"):
        for element in rpw.ui.Selection():
            applied_pattern = apply_pattern(element, pattern)
            rpw.db.Element(element).parameters['name'].value = applied_pattern

def apply_pattern(element, pattern):
    for k,v in class_dict.items():
        regex = class_dict[k]['regex']
        pattern = regex.sub(lambda m: func(getparameter(view, "BuiltInParameter." + m.group(1)),
                                           m.group(1)))


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


class Gui(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.combobox_class.ItemsSource = class_dict.keys()
        self.cursorposition = 0

    def add_click(self, sender, e):
        index = self.cursorposition
        try:
            appended_text = "{}({})".format(self.combobox_class.SelectedItem, self.combobox_parameter.SelectedItem)
            self.pattern.Text = self.pattern.Text[:index] \
                                + appended_text \
                                + self.pattern.Text[index:]
        except TypeError:
            rpw.ui.forms.Alert("Error, failed to add parameter")

    def class_changed(self, sender, e):
        try:
            self.combobox_parameter.ItemsSource = class_dict[sender.SelectedItem]['parameter_name_list']
        except KeyError:
            return

    def pattern_changed(self, sender, e):
        self.cursorposition = sender.SelectionStart

    def apply_click(self, sender, e):
        CustomizableEvent.raise_event(set_parameter_value, self.pattern.Text)

    def target_click(self, sender, e):
        self.target_text.Text = self.combobox_parameter.SelectedItem


Gui('WPFWindow.xaml').Show()
