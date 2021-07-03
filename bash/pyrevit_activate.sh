#!/bin/bash
# This script will activate pyrevit on a machine with no admin rights

cd $APPDATA

echo "Create pyRevit.addin file"
cat << EOF > pyRevit.addin
<?xml version="1.0" encoding="utf-8" standalone="no"?>
<RevitAddIns>
    <AddIn Type = "Application">
        <Name>PyRevitLoader</Name>
        <Assembly>$APPDATA\pyrevit_git\bin\engines\IPY2710\pyRevitLoader.dll</Assembly>
        <AddInId>B39107C3-A1D7-47F4-A5A1-532DDF6EDB5D</AddInId>
        <FullClassName>PyRevitLoader.PyRevitLoaderApplication</FullClassName>
        <VendorId>eirannejad</VendorId>
    </AddIn>
</RevitAddIns>
EOF

echo "Copying pyRevit.addin into "$APPDATA"/Autodesk/Revit/Addins/"$1
mv pyRevit.addin ./Autodesk/Revit/Addins/$1