#!/bin/bash
# This script will install pyrevit on a machine with no admin rights

echo "Start installing pyRevit + pyRevitMEP"
cd $APPDATA
echo "Start cloning pyRevit into "$APPDATA
git clone https://github.com/eirannejad/pyRevit.git pyRevit_git --depth=1

echo "Start cloning pyRevitMEP into "$AppData"/pyRevit/extensions/pyRevitMEP.extension"
git clone https://github.com/CyrilWaechter/pyRevitMEP.git pyRevit_git/extensions/pyRevitMEP.extension --depth=1

echo "Process completed. Do not forget to activate pyRevit for your Revit version."
