# pyRevitMEP
PyRevitMEP - MEP Extensions for PyRevit

[![GitHub license](https://img.shields.io/badge/License-GPL3-brightgreen.svg)](https://github.com/Nahouhak/pyRevitMEP/blob/master/LICENSE)

## Installation
### Automatic
* [Install pyRevit](https://github.com/eirannejad/pyRevit/)
* Use pyRevit Package Manager (pyRevit > Extensions > Enable pyRevitMEP)
### Manual (no admin rights required)
#### Command lines (Cmder)
* Download [cmder](https://cmder.net/) unzip it anywhere you like
* Clone [pyRevit](https://github.com/eirannejad/pyRevit/) repository using git (skip this step if pyRevit is already installed)
    * Destination folder : replace %APPDATA%\pyRevit_git with another destination folder if you like
    * --depth=1 allow to only clone last version without full git history
```cmd
git clone https://github.com/eirannejad/pyRevit.git %APPDATA%\pyRevit_git --depth=1
```
* Clone [pyRevit MEP](https://github.com/CyrilWaechter/pyRevitMEP) repository pyrevit extensions folder using git
    * Destination folder : replace %APPDATA%\pyRevit_git\extensions with pyRevit path from step 1 if custom
    * extensions folder is in pyRevit gitignore so it will not affect pyRevit
```cmd
git clone https://github.com/CyrilWaechter/pyRevitMEP.git %APPDATA%\pyRevit_git\extensions\pyRevitMEP.extension --depth=1
```
* Create a text file containing following text and save it as pyRevit.addin :
    * Replace `#APPDATA\pyrevit_git` with your pyrevit path if custom
```xml
<?xml version="1.0" encoding="utf-8" standalone="no"?>
<RevitAddIns>
    <AddIn Type = "Application">
        <Name>PyRevitLoader</Name>
        <Assembly>$APPDATA\pyrevit_git\bin\engines\279\pyRevitLoader.dll</Assembly>
        <AddInId>B39107C3-A1D7-47F4-A5A1-532DDF6EDB5D</AddInId>
        <FullClassName>PyRevitLoader.PyRevitLoaderApplication</FullClassName>
        <VendorId>eirannejad</VendorId>
    </AddIn>
</RevitAddIns>
```
* Copy the addin file to your `%APPDATA%\Revit\Addins\2019` (Replace 2019 with your Revit version)
#### Bash script (Cmder)
* Download [latest bash scripts](https://github.com/CyrilWaechter/pyRevitMEP/releases/latest/download/bash.zip) and unzip it anywhere
* Launch Cmder in bash scripts folder and and execute the scripts
    * Replace 2019 with your Revit version
```bash
bash pyrevit_install.sh
bash pyrevit_activate.sh 2019
```

## Update
### Automatic
* Use pyRevit update function
### Manual
#### Command  line (Cmder)
* Execute a git pull in your pyRevit and pyRevitMEP.extension folders
    * -f will force update any modification will be overwritten
```git
git checkout -f
```
#### Bash script (Cmder)

* Launch Cmder in bash scripts folder and and execute the script
    * Replace 2019 with your Revit version
```bash
bash pyrevit_update.sh
```

## [Contribute](https://github.com/CyrilWaechter/pyRevitMEP/blob/master/CONTRIBUTING.md)

## [Report bugs](https://github.com/CyrilWaechter/pyRevitMEP/issues)

## Documentation
* [pyRevitMEP on pythoncvc.net](http://pythoncvc.net/?page_id=123)
* [playlist on youtube channel](https://www.youtube.com/channel/UCIsRFoaVQNSl_RlGAZE2mVg/playlists)

## Credits
* [Ehsan Iran-Nejad](https://github.com/eirannejad) for developing pyRevit
* people which contribute in pyRevit and tools used in pyRevit
* [Icons8](https://icons8.com/) and its contributors for the sweet free icons
* [Inkscape](https://inkscape.org) the great vector drawing software under GPL license which allows me to create missing icons with ease
* Everyone else  [listed on the PyRevit Repo](https://github.com/eirannejad/pyRevit/blob/master/README.md#credits)
