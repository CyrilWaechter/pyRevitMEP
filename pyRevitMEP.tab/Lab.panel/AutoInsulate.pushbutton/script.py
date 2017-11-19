# coding: utf8
import rpw
from rpw import DB, revit
from rpw import logger

__doc__ = "Auto"
__title__ = "Auto Insulate"
__author__ = "Cyril Waechter"
__context__ = "Selection"


# TODO
def apply_size_rule(size,  rule):
    pass


def set_system_rule(mep_system):
    mep_system
    return # rule


def get_element_mep_systems(element):
    mep_system = []
    if isinstance(element, DB.MEPCurve):
        mep_system.append(element.MEPsystem)
    elif isinstance(element, DB.FamilyInstance):
        for connector in element.MEPModel.ConnectorManager.Connectors:
            if connector.MEPSystem:
                mep_system.append(element.MEPModel.ConnectorManager.Connectors)
    else:
        logger.info("No system found in element {}".format(element))
    return mep_system


def get_nominal_diameter(element):
    if isinstance(element, DB.MEPCurve):
        return element.get_Parameter(DB.BuiltInParameter.RBS_PIPE_DIAMETER_PARAM).AsDouble()
    if isinstance(element, DB.FamilyInstance):
        return 2 * max(connector.Radius for connector in element.MEPModel.ConnectorManager.Connectors)


class ConnectorsBreadthFirstSearch:
    def __init__(self, element):
        self.element = element
        self.nominal_diameter = 2 * max(connector.Radius for connector in element.MEPModel.ConnectorManager.Connectors)
        self.queue = [element]
        self.visited = []

    def outside_diameter_search(self):
        if self.queue:
            current_element = self.queue.pop(0)
            print current_element
            if isinstance(current_element, DB.Plumbing.Pipe):
                return current_element.get_Parameter(DB.BuiltInParameter.RBS_PIPE_OUTER_DIAMETER).AsDouble()
            else:
                self.visited.append(current_element)
                for connector in current_element.MEPModel.ConnectorManager.Connectors:
                    for ref in connector.AllRefs:
                        if isinstance(ref.Owner, (DB.FamilyInstance, DB.Plumbing.Pipe)):
                            if ref.Owner not in self.visited and ref.Radius * 2 >= self.nominal_diameter:
                                self.queue.append(ref.Owner)
                return self.outside_diameter_search()
        else:
            return self.nominal_diameter


def get_outer_diameter(element):
    if isinstance(element, DB.Plumbing.Pipe):
        return element.get_Parameter(DB.BuiltInParameter.RBS_PIPE_OUTER_DIAMETER).AsDouble()
    if isinstance(element, DB.FamilyInstance):
        for connector in element.MEPModel.ConnectorManager.Connectors:
            for sub_con in connector.AllRefs:
                logger.debug(sub_con.Owner)
                get_outer_diameter(sub_con.Owner)


def get_inner_diameter(element):
    if isinstance(element, DB.MEPCurve):
        element.get_Parameter(DB.BuiltInParameter.RBS_PIPE_INNER_DIAM_PARAM)
    if isinstance(element, DB.FamilyInstance):
        max(connector.Radius for connector in element.MEPModel.ConnectorManager.Connectors)

# InsulationLiningBase.GetInsulationIds

# for element in rpw.ui.Selection():
#     element
#     # TODO Determine system rule
#     mep_systems = get_element_mep_systems(element)
#     if mep_systems:
#         rule = set_system_rule(mep_systems[0])
#     # TODO Apply size rule
#     apply_size_rule(size, rule)

# TODO GUI to set and save configuration
