# coding: utf8

from Autodesk.Revit.DB import Document, ViewPlan

from pyrevit import forms, script
import rpw

__doc__ = """Copy view range from source views to target views.
If only 1 source view is selected same view range is applied to all views"""
__title__ = "ViewRange"
__author__ = "Cyril Waechter"

doc = rpw.revit.doc  # type:Document
logger = script.get_logger()


def copy_view_range():
    """Copy view range from source views to target views"""
    prompt_text = "Select one or multiple source views"
    with forms.WarningBar(title=prompt_text):
        source_list = forms.select_views(title=prompt_text, filterfunc=lambda x: isinstance(x, ViewPlan))

    if not source_list:
        return False

    prompt_text = "Select target views"
    with forms.WarningBar(title=prompt_text):
        target_list = forms.select_views(title=prompt_text, filterfunc=lambda x: isinstance(x, ViewPlan))

    if not target_list:
        return True

    with rpw.db.Transaction("Copy view range", doc):
        logger.info("VIEW RANGE applied from following source to target :")
        if len(source_list) == 1:
            view_range = source_list[0].GetViewRange()
            for target in target_list:  # type:ViewPlan
                target.SetViewRange(view_range)
                logger.info("{} -> {}".format(source_list[0].Name, target.Name))
        else:
            for source, target in zip(source_list, target_list):  # type:ViewPlan, ViewPlan
                target.SetViewRange(source.GetViewRange())
                logger.info("{} -> {}".format(source.Name, target.Name))
    return True


while copy_view_range():
    pass
