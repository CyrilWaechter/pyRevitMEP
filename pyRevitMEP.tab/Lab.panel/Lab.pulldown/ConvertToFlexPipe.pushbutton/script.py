import rpw
from pyrevit.script import get_logger

logger = get_logger()
selection = rpw.ui.Selection()

# TODO check in only one loop
number_of_unused_connectors = sum([element.ConnectorManager.UnusedConnectors.Size for element in selection])
logger.debug(number_of_unused_connectors)
if number_of_unused_connectors > 2:
    rpw.ui.forms.Alert('Please select only one loop')

for element in selection:
    element.ConnectorManager.UnusedConnectors



