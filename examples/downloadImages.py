#!/usr/bin/python

from vsdConnect import connect
import sys
import argparse

parser = argparse.ArgumentParser(description='Download original image files from SMIR to a specific folder.')
parser.add_argument('--targetFolder', dest='targetFolder', default="./",
                   help='folder to store images in')
parser.add_argument('--sourceProject', dest='targetProject', required=0,
                   help='Project/Folder Name of VSD (sub folder of SSMProjects)')
parser.add_argument('--sourceFolderID', dest='sourceFolderID', required=0,
                   help='VSD ID of fodler to download')
parser.add_argument('--sourceFolderName', dest='sourceFolderName', required=0,
                   help='Folder name of folder to download, must be unique, can contain parentfolders, does not need to be complete')



args=parser.parse_args()

if (args.targetProject=="" and args.sourceFolderID=="" and args.sourceFolderName==""):
    print "Arguments incomplete, need either ID or name of VSD folder"
    sys.exit()

con=connect.VSDConnecter("username","password")
#con=connect.VSDConnecter()



print "Arguments:",args
if args.sourceFolderID==None:
    #get information of all folders and search for the correct one
    print "Retrieving folder list from SMIR.."
    folderList=con.getFolderList()
    folderHash=con.readFolders(folderList)
    OriginalFolder=None
    if (args.targetProject != ""):
        targetProject=args.targetProject

        
        print "Retrieving target folder IDs from folder list."
        searchstring="SSMPipeline/"+args.targetProject+"/01_Original"
        for key,folder in folderHash.iteritems():
            if searchstring in folder.fullName:
                OriginalFolder=folder
    else:
        for key,folder in folderHash.iteritems():
            if args.sourceFolderName in folder.fullName:
                OriginalFolder=folder
    if OriginalFolder==None:
        print "Error retrieving folder, exiting"
        sys.exit()
    print "Retrieving file list from folder with ID", OriginalFolder.ID
    fileIDList=OriginalFolder.containedObjects.keys()
else:
    fileList=con.getFileListInFolder(args.sourceFolderID)
    fileIDList=con.getFileIDs(fileList)


for ID in fileIDList:
    print ID
    filename=con.generateBaseFilenameFromOntology(ID)
    filename=args.targetFolder+"/"+filename
    con.downloadFile(ID,filename)

