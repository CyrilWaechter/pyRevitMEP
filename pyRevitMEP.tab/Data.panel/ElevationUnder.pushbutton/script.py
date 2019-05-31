# coding: utf8
from System.Collections.Generic import List

from Autodesk.Revit.DB import ReferenceIntersector, View3D, Document, ElementMulticategoryFilter, BuiltInCategory, \
    MEPCurve, FamilyInstance, XYZ, FindReferenceTarget, ElementId
from Autodesk.Revit.UI import UIDocument

from pyrevit.script import get_logger
from pyrevit.forms import select_views, WPFWindow
import rpw

from pyrevitmep.event import CustomizableEvent

__doc__ = """Compute distance of selected elements (origin or middle of the curve) to closest floor/roof above.
Result is stored in designated parameter"""
__title__ = "ElevationUnder"
__author__ = "Cyril Waechter"

doc = rpw.revit.doc # type: Document
uidoc = rpw.revit.uidoc # type: UIDocument
logger = get_logger()


def get_view3d(doc=doc, uidoc=uidoc):
    # type: (Document ,UIDocument) -> View3D
    if isinstance(uidoc.ActiveView, View3D):
        return uidoc.ActiveView
    return select_views("Select target 3D View", multiple=False, filterfunc=lambda x: isinstance(x, View3D))


def get_element_origin(element):
    # type: (MEPCurve or FamilyInstance) -> XYZ
    try:
        # If it is a MEPCurve alike. Return its middle point.
        return (element.Location.Curve.GetEndPoint(0) + element.Location.Curve.GetEndPoint(1))/2
    except AttributeError:
        # If it is a FamiliyIntance alike. Return its origin.
        return element.Location.Point


def get_type_name(element):
    try:
        return doc.GetElement(element.GetTypeId()).Family.Name
    except AttributeError:
        return element.Category.Name


def compute_elevation(view3d, parameter_name):
    # type: (View3D, str) -> float
    """Compute distance from the object to closest floor or roof above"""
    category_list = List[BuiltInCategory]()
    category_list.Add(BuiltInCategory.OST_Roofs)
    category_list.Add(BuiltInCategory.OST_Floors)
    category_filter = ElementMulticategoryFilter(category_list)

    reference_intersector = ReferenceIntersector(category_filter, FindReferenceTarget.Element,
                                                 view3d, FindReferencesInRevitLinks=True)

    with rpw.db.Transaction("ComputeElevation", doc=doc):
        for id in uidoc.Selection.GetElementIds():  # type: ElementId
            element = doc.GetElement(id)
            origin = get_element_origin(element)
            direction = XYZ.BasisZ
            try:
                reference = reference_intersector.FindNearest(origin, direction).GetReference()
            except AttributeError:
                logger.info("Failed to find a roof or a floor above Element {} {}, id {}".format(
                    get_type_name(element),
                    element.Name,
                    element.Id)
                )
                continue
            distance = -reference.GlobalPoint.DistanceTo(origin)
            element.LookupParameter(parameter_name).Set(distance)


customizable_event = CustomizableEvent()


class Gui(WPFWindow):
    def __init__(self, xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)
        self.view3d = get_view3d()
        self.tbk_view3d.Text = self.view3d.Name
        self.tbx_parameter_name.Text = "py_Elevation"

    def compute_selected_click(self, sender, e):
        # compute_elevation(self.view3d, self.tbx_parameter_name.Text)
        customizable_event.raise_event(compute_elevation, self.view3d, self.tbx_parameter_name.Text)

    def select_view3d_click(self, sender, e):
        self.view3d = get_view3d()
        self.tbk_view3d.Text = self.view3d.Name


gui = Gui("WPFWindow.xaml")
gui.Show()
# gui.ShowDialog()

# view3d = get_view3d()
# compute_elevation(view3d)
