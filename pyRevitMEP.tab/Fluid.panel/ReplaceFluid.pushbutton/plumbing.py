# coding: utf8
"""
Plumbing Wrapper
"""
from rpw.db import Element
from rpw import revit, DB


class FluidType(Element):
    """
    Allow you to treat fluids as dictionnary
    >>> # TODO: make an example
    """
    def __repr__(self, data=None):
        """ Adds data to Base __repr__ to add Parameter List Name """
        if not data:
            data = {}
        data['name'] = self.name
        return super(FluidType, self).__repr__(data=data)

    @staticmethod
    def all(doc=revit.doc):
        return [FluidType(fluid) for fluid in DB.FilteredElementCollector(doc).OfClass(DB.Plumbing.FluidType)]

    @staticmethod
    def in_use_dict(doc=revit.doc):
        result = {}
        for system in DB.FilteredElementCollector(doc).OfClass(DB.Plumbing.PipingSystemType):
            rpw_system = Element(system)
            rpw_fluid_type = Element.from_id(system.FluidType)
            result[rpw_system.name]={'name':rpw_fluid_type.name, 'temperature':rpw_system.FluidTemperature}
        return result

    @property
    def fluid_temperatures(self):
        """
        :return: temperatures of fluid
        """
        return list(self.GetFluidTemperatureSetIterator())

    @property
    def temperatures(self):
        return sorted([temp.Temperature for temp in self.fluid_temperatures])