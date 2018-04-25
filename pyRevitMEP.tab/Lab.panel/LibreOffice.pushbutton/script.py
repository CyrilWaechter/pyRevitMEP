# coding: utf8
import sys
import clr
import os
sys.path.append(r"C:\Program Files\LibreOffice\sdk\cli")
clr.AddReference("cli_basetypes")
clr.AddReference("cli_cppuhelper")
clr.AddReference("cli_oootypes")
clr.AddReference("cli_ure")
clr.AddReference("cli_uretypes")

# from unoidl.com.sun.star.lang import *
# from unoidl.com.sun.star.uno import *
# from unoidl.com.sun.star.bridge import *
# from unoidl.com.sun.star.frame import *
#
# from unoidl.com.sun.star.lang import XMultiServiceFactory
from unoidl.com.sun.star.uno import XComponentContext
# from unoidl.com.sun.star.registry import ImplementationRegistration
# from unoidl.com.sun.star.bridge import UnoUrlResolver
#
# __fullframeengine__ = True
#

# You need to add LibreOffice to environment variable "PATH".
# Else it throw an `System.Runtime.InteropServices.SEHException`
lo_path = r"C:\Program Files\LibreOffice\program"
if lo_path not in os.environ["PATH"]:
    os.environ["PATH"] = "{}{};".format(os.environ["PATH"],lo_path)


print(os.environ["PATH"])
from uno.util import Bootstrap
# This method is supposed to return an XComponentContext but i git an object instead.
xcontext = Bootstrap.bootstrap()
print(type(xcontext)) # -> object
# This is how we are supposed to get ServiceManager but it throws a NotImplemented error
xservicemanager = xcontext.getServiceManager()
