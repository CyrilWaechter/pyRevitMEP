# coding: utf8

from Autodesk.Revit.DB.Plumbing import PipingSystemType
systems = FilteredElementCollector(doc).OfClass(PipingSystemType)
list_eau = []
for system in systems:
    fluidtype = doc.GetElement(system.FluidType)
    st_name = Element.Name.GetValue(system)
    ft_name = Element.Name.GetValue(fluidtype)
    if ft_name == 'Eau':
        list_eau.append(system)
    if ft_name == 'Water':
        new_type = fluidtype
    print(ft_name, st_name)

t = Transaction(doc, 'change fluid type')
t.Start()
for system in list_eau:
    system.FluidType = new_type.Id
t.Commit()