#!/bin/bash
# This script will install pyrevit on a machine with no admin rights

echo "Start updating pyRevit"
cd $APPDATA/pyRevit_git
git checkout -f

echo "Start updating pyRevitMEP"
cd extensions/pyRevitMEP.extension
git checkout -f