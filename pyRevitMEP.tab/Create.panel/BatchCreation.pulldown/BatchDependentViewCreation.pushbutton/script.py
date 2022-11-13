# coding: utf8

from pyrevit import revit, forms, script
from pyrevit import script

__doc__ = "Batch create dependent views corresponding to existing Scope Boxes for selected views"
__title__ = "DependentViews"
__author__ = "Cyril Waechter"
__context__ = "selection"

doc = revit.doc
output = script.get_output()
logger = script.get_logger()

volumes_of_interest = forms.SelectFromList.show(
    revit.DB.FilteredElementCollector(doc).OfCategory(
        revit.DB.BuiltInCategory.OST_VolumeOfInterest
    ),
    "Select Scope Boxes for dependent views",
    multiselect=True,
    name_attr="Name",
)


def create_dependent_views(volumes_of_interest):
    for view_id in revit.uidoc.Selection.GetElementIds():
        view = doc.GetElement(view_id)
        try:
            for voi in volumes_of_interest:
                new_view_id = view.Duplicate(revit.DB.ViewDuplicateOption.AsDependent)
                new_view = doc.GetElement(new_view_id)
                parameter = new_view.get_Parameter(
                    revit.DB.BuiltInParameter.VIEWER_VOLUME_OF_INTEREST_CROP
                )
                parameter.Set(voi.Id)
        except AttributeError as e:
            print(
                "Element {} is a {} not a view".format(
                    output.linkify(view.Id), view.Category.Name
                )
            )
            logger.debug("{}".format(e.message))


if volumes_of_interest:
    with revit.Transaction("BatchCreateDependentViews"):
        create_dependent_views(volumes_of_interest)
