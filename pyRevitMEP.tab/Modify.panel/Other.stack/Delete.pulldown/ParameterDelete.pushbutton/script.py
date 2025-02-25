from Autodesk.Revit.DB import FilteredElementCollector, ParameterElement

from pyrevit import revit, forms

doc = revit.doc
params = FilteredElementCollector(doc).OfClass(ParameterElement)

selected_params = forms.SelectFromList.show(
    params,
    "Select parameters to delete",
    multiselect=True,
    name_attr="Name",
)


if selected_params:
    with revit.Transaction("Delete ParameterElement"):
        for param in selected_params:
            doc.Delete(param.Id)
