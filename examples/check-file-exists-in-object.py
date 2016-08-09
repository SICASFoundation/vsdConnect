#!/usr/bin/python
"""
=======
INFOS
=======
* Example on how to check if a local file is contained in an object online. Adapt the credential, the local file an the object id
* python version: 3 
* @author: Michael Kistler 2016

========
CHANGES
========
* initial version base ond v0.8.1

"""

from vsdConnect import connect
import os
from pathlib import Path, PurePath, WindowsPath


## connect using credentials
api=connect.VSDConnecter(url='https://demo.virtualskeleton.ch/api/', username= "demo@virtualskeleton.ch", password = "demo")

## specify the local file
fp = Path('D:' + os.sep, 'hash','vsd_file_926373_20160226_120352.stl')

## which object to check
obj = api.getObject(1)

## the check
if api.checkFileInObject(obj, fp):
    print('found')

else:
    print('not found')
