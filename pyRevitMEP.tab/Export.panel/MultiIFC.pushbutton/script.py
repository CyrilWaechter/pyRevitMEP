# coding: utf8
import sys
import os
from pathlib import Path
import clr
from Autodesk.Revit.DB import (
    IFCExportOptions,
    Document,
    ViewType,
)
import pyrevit
from pyrevit import script, forms, revit

plugin_dir = Path(pyrevit.ALLUSER_PROGRAMDATA) / r"Autodesk\ApplicationPlugins\IFC {0}.bundle\Contents\{0}".format(
    revit.HOST_APP.version
)
if plugin_dir.exists():
    sys.path.append(plugin_dir)
    clr.AddReference("IFCExporterUIOverride")
else:
    sys.path.append(Path(revit.HOST_APP.proc_path).parent / r"AddIns\IFCExporterUI")
    clr.AddReference("Autodesk.IFC.Export.UI")
from BIM.IFC.Export.UI import IFCExportConfigurationsMap

logger = script.get_logger()
output = script.get_output()

doc = revit.doc  # type: Document


def export():
    map = IFCExportConfigurationsMap()
    map.AddSavedConfigurations()
    config = forms.SelectFromList.show(
        context=map.Values,
        title="IFC Configuration",
        multiselect=False,
        name_attr="Name",
    )
    if not config:
        return
    options = IFCExportOptions()

    views = forms.select_views(multiple=True, filterfunc=lambda x: x.ViewType == ViewType.ThreeD)
    if not views:
        return

    folder = forms.pick_folder()
    if not folder:
        return

    with revit.Transaction("Multiple IFC export"):
        for view in views:
            name = view.Name
            config.UpdateOptions(options, view.Id)
            doc.Export(folder, name, options)

    os.startfile(folder)


if __name__ == "__main__":
    export()


"""
RevitPythonShell live testing:
import sys
sys.path.append(r"C:\ProgramData\Autodesk\ApplicationPlugins\IFC 2024.bundle\Contents\2024")
clr.AddReference("IFCExporterUIOverride")
from BIM.IFC.Export.UI import IFCExportConfigurationsMap, IFCExportConfiguration, IFCCommandOverrideApplication
map = IFCExportConfigurationsMap()
map.AddBuiltInConfigurations()
map.AddSavedConfigurations()
options = IFCExportOptions()
config = [c for c in map.Values][0]
"""
