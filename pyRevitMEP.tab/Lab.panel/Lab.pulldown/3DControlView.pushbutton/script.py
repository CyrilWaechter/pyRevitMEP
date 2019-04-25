# coding: utf8
from System.Collections.Generic import List

from Autodesk.Revit.DB import Document, FilterStringRule, ParameterValueProvider, FilteredElementCollector, \
    BuiltInParameter, FilterStringBeginsWith, FilterRule, ParameterFilterElement, BuiltInCategory, Category, \
    ElementId, FilterInverseRule, View3D, ViewDuplicateOption, FilterStringContains
from Autodesk.Revit.DB.Mechanical import Duct
from Autodesk.Revit.DB.Plumbing import Pipe

import rpw

doc = __revit__.ActiveUIDocument.Document  # type: Document


# valueProvider
def parameter_value_provider(base_class, built_in_parameter):
    # type: (type, str) -> ParameterValueProvider
    element = FilteredElementCollector(doc).OfClass(base_class).FirstElement()
    system_type_parameter_id = element.get_Parameter(built_in_parameter).Id
    return ParameterValueProvider(system_type_parameter_id)


# Base view
def get_base_view(name):
    # type: (str) -> View3D
    for view in FilteredElementCollector(doc).OfClass(View3D):
        if view.Name == name:
            return view


def create_views(value_provider, built_in_category_list, prefix, num_range, num_format):
    # type: (ParameterValueProvider, iter, str, iter, str) -> None
    # evaluator
    # rule_evaluator = FilterStringBeginsWith()
    rule_evaluator = FilterStringContains()

    # caseSensitive
    case_sensitive = True

    # categories
    cat_ids = List[ElementId]()
    for cat in built_in_category_list:
        cat_id = Category.GetCategory(doc, eval("BuiltInCategory.{}".format(cat))).Id
        cat_ids.Add(cat_id)

    base_view = get_base_view("3DControlBaseView")

    with rpw.db.Transaction("Create 3D Control Views"):
        for n in num_range:
            # ruleString
            filter_string = "{prefix}{number:{num_format}}".format(prefix=prefix, number=n, num_format=num_format)

            # rules
            filter_string_rule = FilterStringRule(value_provider, rule_evaluator, filter_string, case_sensitive)
            inverse_filter_rule = FilterInverseRule(filter_string_rule)
            rules = List[FilterRule]()
            rules.Add(inverse_filter_rule)

            # Create Filter
            filter_element = ParameterFilterElement.Create(doc, "SAUF_{}".format(filter_string), cat_ids, rules)

            # Add filter to view
            view = doc.GetElement(base_view.Duplicate(ViewDuplicateOption.Duplicate))
            view.Name = filter_string
            view.AddFilter(filter_element.Id)
            view.SetFilterVisibility(filter_element.Id, False)


def create_piping_views(prefix, num_range):
    # type: (str, iter) -> None
    value_provider = parameter_value_provider(Pipe, BuiltInParameter.RBS_PIPING_SYSTEM_TYPE_PARAM)
    bic_list = "OST_PipeCurves", "OST_PipeFitting", "OST_PipeAccessory", "OST_PipeInsulations"
    num_format = ""
    create_views(value_provider, bic_list, prefix, num_range, num_format)


def create_ventilation_views(prefix, num_range):
    # type: (str, iter) -> None
    value_provider = parameter_value_provider(Duct, BuiltInParameter.RBS_DUCT_SYSTEM_TYPE_PARAM)
    bic_list = "OST_DuctCurves", "OST_DuctFitting", "OST_DuctAccessory", "OST_DuctTerminal", "OST_DuctInsulations"
    num_format = ":02d"
    create_views(value_provider, bic_list, prefix, num_range, num_format)


# create_piping_views("HYD_SPE_247.", range(1, 4))
# create_ventilation_views("VEN_244.", range(1, 67))
create_piping_views("353.", range(1, 7))
