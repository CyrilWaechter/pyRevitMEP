import pathlib
import sys

LIB = pathlib.Path(__file__).resolve().parents[2] / "pyRevitMEP.tab" / "Manage.panel" / "ViewRename.pushbutton" / "lib"
sys.path.insert(0, str(LIB))
