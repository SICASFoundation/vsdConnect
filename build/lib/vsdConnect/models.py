#!/usr/bin/python
"""
=======
INFOS
=======
* python version: 3.5
* connectVSD 0.8.1
* module: models
* @author: Michael Kistler 2016, Livia B.

========
CHANGES
========
* implemented objects as jsonmodels

"""
import json
from jsonmodels import models, fields, errors, validators
from pathlib import Path, PurePath, WindowsPath



################################################
#Custom validators
################################################

class ListValidator(object):

    """Validator for a list."""

    def __init__(self, itemlist):
        """Init.

        :param items: list of items to check against.
        :param bool exclusive: If `True`, then validated value must be strongly
            bigger than given threshold.

        """
        self.itemlist = itemlist

    def validate(self, value):
        """Validate value."""

        if value not in self.itemlist:
            raise errors.ValidationError(
                "'{value}' is not accepted, acceptable values are: ('{itemlist}').".format(
                    value=value, itemlist=self.itemlist))


    def modify_schema(self, field_schema):
        """Modify field schema."""
        field_schema['itemlist'] = self.itemlist



################################################
#Models parameters
################################################

class URLField(fields.StringField):
    pass #add url-specific fields?

#see http://python3porting.com/differences.html#long
import sys
if sys.version_info < (3,):
    fields.IntField.types = (int, long,)

##########################################
# Attributes Data
##########################################

class PaginationParameter(models.Base):
    """
    pagination parameters

    use 10000 for unlimited usage of eg dicom series (local only, not working on API)

    """

    rpp = fields.IntField(
        required=True,
        validators=ListValidator([10, 25, 50, 100, 250, 500, 10000])
        )

    page = fields.IntField(
        required=True,
        validators=validators.Min(0)
        )


################################################
#View Models
################################################

class APIVersion(models.Base):
    """
    the api version view model
    """
    major = fields.IntField()
    minor = fields.IntField()
    build = fields.IntField()
    revision = fields.IntField()
    majorRevision = fields.IntField()
    minorRevision = fields.IntField()

class HttpContent(models.Base):
    """
    header content
    """
    headers = fields.StringField()

class HttpMethod(models.Base):
    """
    http request method
    """
    method = fields.IntField()

class HttpRequestMessage(models.Base):
    """
    Http request view model
    """
    version = fields.EmbeddedField(APIVersion)
    content = fields.EmbeddedField(HttpContent)
    method = fields.EmbeddedField(HttpMethod)
    requestUri = URLField()
    headers = fields.StringField()
    proertiews = fields.EmbeddedField(dict)

class HttpResponseMessage(models.Base):
    """
    http response message view model
    """
    version = fields.EmbeddedField(APIVersion)
    content = fields.EmbeddedField(HttpContent)
    statusCode = fields.IntField()
    reasonPhrase = fields.StringField()
    headers = fields.StringField()
    requestMessage = fields.EmbeddedField(HttpRequestMessage)
    isSuccessStatusCode = fields.BoolField()

class  Token(models.Base):
    """
    API class to work with the tokens
    Supported token: JWT
    """

    tokenType = fields.StringField()
    tokenValue = fields.StringField()


class APIBase(models.Base):
    """
    Basic for all classes with selfUrl

    """

    selfUrl = fields.StringField()

    def __str__(self):
        return '{name} {url}'.format(name=self.__class__.__name__, url = self.selfUrl)



    def get_json(self):
        """
        get the object as json readable structure (dict)

        :return: json
        :rtype: json
        """
        return json.dumps(self.to_struct())

  
    def show(self):
        """
        show the object as json readable structure (dict), nicely formated

        """
        print(json.dumps(self.to_struct(), sort_keys = True, indent = 4))



    def save(self, fp = 'object.json'):
        """
        save the object as json to the given filepath

        :params Path fp: the filepath to the file
        :return: the path to the stored file
        :rtype: Path

        """

        fp = Path(fp)

        if fp.is_file():
            fp.unlink()
            fp.touch()
        else:
            fp.touch()


        with fp.open('w') as outfile:
            json.dump(self.to_struct(), outfile, indent = 4)

        return fp


class APIBaseID(APIBase):
    """
    id and selfUrl
    """
    id = fields.IntField()

    def __str__(self):
        return '{name} {url} {selfname}'.format(name=self.__class__.__name__, url = self.id, selfname = getattr(self, 'name', ""))

class APIBaseExt(APIBaseID):
    """
    id, name, display name and selfUrl
    """
    name = fields.StringField()
    displayName = fields.StringField()


class APIBaseN3(APIBase):
    """
    for semantic triple storage
    """
    subject = fields.EmbeddedField(APIBaseExt) # will be most likely a APIBaseExt
    predicate = fields.EmbeddedField(APIBaseExt) # will be most likely a APIBaseExt
    object = fields.EmbeddedField(APIBaseExt) # will be most likely a APIBaseExt


class Preview(APIBaseID):
    imageUrl = URLField()
    thumbnailUrl = URLField()


class Pagination(models.Base):
    """
    API class for Pagination results
    """

    totalCount = fields.IntField(required=True)
    pagination = fields.EmbeddedField(PaginationParameter, required=True)
    items = fields.ListField(dict) #generic dict in order to retain all the keys
    nextPageUrl = URLField()

    def firstUrlInPage(self):
        """
        get the selfurl of the first item in the paginated list

        :return: selfUrl
        :rtype: string

        """
        firstItem = self.items[0]
        return firstItem.selfUrl

class APIBasePagination(Pagination):
    """
    class for pagination items of type APIBase
    """
    items = fields.ListField(APIBase)

################################################
#FILES
################################################

class File(APIBaseID):
    createdDate = fields.StringField()
    downloadUrl = URLField()
    originalFileName = fields.StringField()
    anonymizedFileHashCode = fields.StringField()
    size = fields.IntField()  #in Python 2 it needs the patch for long type
    fileHashCode = fields.StringField()
    objects = fields.EmbeddedField(Pagination) #ObjectPagination



################################################
#FOLDER
################################################
class Folder(APIBaseID):
    name = fields.StringField()
    level = fields.IntField()
    parentFolder = fields.EmbeddedField(APIBase)
    childFolders = fields.ListField(APIBase)#fields.ListField([ 'Folder'])
    folderGroupRights = fields.ListField(APIBase)
    folderUserRights = fields.ListField(APIBase)
    containedObjects = fields.ListField(APIBase)

    def get(self, apisession):
        """
        get the folder object from the API

        :param connectVSD apisession: the API session
        :return: the folder
        :rtype: Folder
        """
        res = apisession.getRequest(self.selfUrl)
        return Folder(**res)

    def get_parent(self, apisession):
        """
        return the parent Folder

        :param connectVSD apisession: the API session
        :return: the parent Folder
        :rtype: Folder
        """

        return Folder(selfUrl=self.parentFolder.selfUrl).get(apisession)

    def get_objects(self, apisession):
        """
        return the APIobject contained in the folder (convert APIBase to the correct Object)

        :param connectVSD apisession: the API session
        :return: list of APIObjects
        :rtype: list
        """
        itemlist = list()

        if self.containedObjects:

            for item in self.containedObjects:
                itemlist.append(APIObject(selfUrl=item.selfUrl).get(apisession))

            return itemlist
        else:
            print('the folder does not have any contained objects')
            return None

    def get_child_folders(self, apisession, recursive=False):
        """
        return the Folders contained in the folder (convert APIBase Folder)

        :param connectVSD apisession: the API session
        :param bool recursive: if the child folder should be recursively returned
        :return: list of Folder
        :rtype: list
        """
        folderObject = self.get(apisession)
        dirs = folderObject.childFolders
        #nondirs = folderObject.containedObjects
        if dirs is None:
            dirs = []
        #if nondirs is None:
        #    nondirs = []
        if recursive:
            yield folderObject, dirs#, nondirs

            for nextDir in dirs:
                nextDir = Folder(selfUrl=nextDir.selfUrl).get(apisession)
                for x in nextDir.get_child_folders(apisession=apisession, recursive=True):
                    yield x
        if not recursive:
            for nextDir in dirs:
                x = Folder(selfUrl=nextDir.selfUrl).get(apisession)
                yield x


    def get_content(self, apisession, recursive=False, mode='b'):
        """
        get the objects and folder contained in the given folder. can be called recursive to travel and return all objects

        :param connectVSD apisession: the API session
        :param bool recursive:  travel the folder structure recursively or not (default)
        :param str mode: what to return: only objects (f), only folders (d) or both (b) folders and objects
        :return content: dictionary with folders (APIBase) and object (APIBase)
        :rtype: dict of APIBase
        """

        objectmode = False
        foldermode = False

        if mode == 'f':
            objectmode = True

        elif mode == 'd':
            foldermode = True

        elif mode == 'b':
            objectmode = True
            foldermode = True
        else:
            print('mode {0} not supported'.format(mode))

        foldergen = self.get_child_folders(apisession)
        folders = list()
        for item in foldergen:
            folders.append(item)

        temp = dict([('folder', self), ('object', None)])


        if foldermode:
            content = list([temp])
        else:
            content = list()

        if objectmode:
            objects = self.get_objects(apisession)

            if objects is not None:
                for item in objects:
                    temp = dict([('folder', self), ('object', item)])
                    content.append(temp)

        if folders is not None:
            if recursive:
                for fold in folders:
                    content.extend(fold.get_content(apisession=apisession, mode=mode, recursive=True))

            else:
                if foldermode:
                    for fold in folders:
                        temp = dict([('folder', fold), ('object', None)])
                        content.append(temp)

        return content

    def delete(self, apisession, _root=None):
        """
        get the objects and folder contained in the given folder.

        :param connectVSD apisession: the API session
        :param Folder root: the folder to delete, has to be None by default, only set internally
        :return: status of deletion
        :rtype: bool
        """
        state = False

        ## set folder to delete
        if not _root:
            _root = self

        # Delete objects
        if self.containedObjects:
            self = self.delete_objects(apisession)

        # Delete folder if empty
        if not self.childFolders and not self.containedObjects:

            res = apisession.delRequest(self.selfUrl)

            if res == 204 or res == 200:
                state = True
            else:
                state = False

            # return state if root folder is deleted/failed
            if self.selfUrl == _root.selfUrl:
                return state
            # run delete on parent folder
            else:
                parent = self.get_partent(apisession)
                return parent.delete(apisession, _root=_root)

        else:
            folders = self.get_child_folders(apisession)
            for f in folders:
                return f.delete(apisession, _root=_root)


    def delete_objects(self, apisession):
        """
        delete the containted objects of a folder

        :param connectVSD apisession: the API session
        :return: updated folder
        :rtype: Folder
        """

        if self.containedObjects:
            self.containedObjects = list()
            res = apisession.putRequest('folders', data=self.to_struct())
            self = Folder(**res)
        return self

    def delete_content(self, apisession):

        self.delete_objects(apisession)

        if self.childFolders:
            foldergen = self.get_child_folders(apisession)
            folders = list()
            for item in foldergen:
                item.delete(apisession)

            self = self.get(apisession)

        if not self.childFolders and not self.containedObjects:
            return True
        else:
            return False

    def create(self, apisession):
        """
        creates the folder if not already exists

        :param connectVSD apisession: the API session
        :return: the folder
        :rtype: Folder
        """
        # check exists
        parent = self.get_parent(apisession)

        create = True

        if parent.childFolders:
            children = parent.get_child_folders(apisession)

            child_d = dict()
            for child in children:
                child_d[child.name]=child

            if self.name in child_d:
                print("folder exists, not created")
                create = False
                return child_d[self.name]

        if create:
            res = apisession.postRequest('folders', self.to_struct())
            print("folder:" + self.name)
            return Folder(**res)

    def create_folders(self, apisession, filepath, rootpath):
        """
        creates the folders based on the filepath if not already existing,
        starting from the rootfolder

        :param connectVSD apisession: the API session
        :param Path filepath: filepath of the file or the directory
        :param Path rootpath: rootpath of the file or the directory
        :return: the last folder in the tree
        :rtype: Folder
        """

        folders = filepath.relative_to(rootpath).parts

        if filepath.is_file():

            folders.remove(folders[-1])

        fparent = self

        if fparent:
            # iterate over file path and create the directory
            for fname in folders:
                f = Folder(
                        name=fname,
                        parentFolder=APIBase(selfUrl=fparent.selfUrl)
                    )
                fparent = f.create(apisession)
            return fparent
        else:
            print('Root folder does not exist', rootfolder)
            return None


    def put(self,apisession):
        """
        put (update) the folder 

        :param connectVSD apisession: the API session
        :return: the folder with the updated location
        :rytpe: Folder
        """
        res = apisession.putRequest('folders', self.to_struct())
        return Folder(**res)

    def move(self,target,apisession):
        """ move the folder to a new location

        :param Folder target: the target dir to move the folder
        :param connectVSD apisession: the API session
        :return: the folder with the updated location
        :rytpe: Folder
        """

        #target.childFolders = target.childFolders.append(APIBase(selfUrl=self.selfUrl))
        self.parentFolder = APIBase(selfUrl=target.selfUrl)
        res = apisession.putRequest('folders', self.to_struct())
        return Folder(**res)
        

class FolderPagination(Pagination):
    """
    API class for Pagination results containing folders
    """

    items = fields.ListField(Folder)



################################################
#FOLDER RIGHTS
################################################

class FolderRight(APIBaseID):
    """
    represents a folder right
    """
    name = fields.StringField()
    rightValue = fields.IntField()


class FolderRightPagination(Pagination):
    """
    API class for pagination result containing folder rights
    """
    items = fields.ListField(FolderRight)

class FolderRightSet(APIBaseID):
    """
    folder rights set
    """
    name = fields.StringField()
    folderRights = fields.ListField(APIBase)


class FolderRightSetPagination(Pagination):
    """
    API class for pagination result containing folder rights
    """
    items = fields.ListField(FolderRightSet)

class FolderGroupRight(APIBaseID):
    """
    relations between folder, group and right (permission)
    """
    relatedFolder = fields.EmbeddedField(APIBase)
    relatedGroup = fields.EmbeddedField(APIBase)
    relatedRights= fields.ListField(APIBase)


class FolderUserRight(APIBaseID):
    """
    relations between folder, user and right (permission)
    """
    relatedFolder = fields.EmbeddedField(APIBase)
    relatedUser = fields.EmbeddedField(APIBase)
    relatedRights= fields.ListField(APIBase)

class FolderGroupRightPagination(Pagination):
    """
    API class for pagination result containing folder group rights
    """
    items = fields.ListField(FolderGroupRight)

class FolderUserRightPagination(Pagination):
    """
    API class for pagination result containing folder userrights
    """
    items = fields.ListField(FolderUserRight)






################################################
#GROUP
################################################

class Group(APIBaseID):
    """
    class for groups
    """
    name = fields.StringField()
    chief = fields.EmbeddedField(APIBase)

class GroupPagination(Pagination):
    """
    class for pagination results containing groups
    """

    items = fields.ListField(Group)





################################################
#LICENSES
################################################

class License(APIBase):
    """
    class for licenses
    """
    name = fields.StringField()
    description = fields.StringField()

class LicensePagination(Pagination):
    """
    class for pagination results containing groups
    """

    items = fields.ListField(License)




################################################
#MODALITY
################################################

class Modality(APIBaseID):
    description = fields.StringField()
    name = fields.StringField()

class ModalityPagination(Pagination):
    """
    class for pagination results containing modalities
    """

    items = fields.ListField(Modality)



################################################
#OBJECTS LINKS
################################################
class ObjectLinks(APIBaseID):
    """
    a link betwen two objects
    """
    object1 = fields.EmbeddedField(APIBase)
    object2 = fields.EmbeddedField(APIBase)
    description = fields.StringField()

    def post(self, apisession):
        """
        create the link for 2 objects
        :param connectVSD apisession: the connection to the API
        """
        apisession.postRequest('object-links', data=self.to_struct())

################################################
#OBJECTS ONTOLOGY & ONTOLOGY
################################################
class ObjectOntology(APIBaseID):
    """
    A relation between an object and an ontology item
    """
    position = fields.IntField()
    type = fields.IntField()
    object = fields.EmbeddedField(APIBase)
    ontologyItem = fields.EmbeddedField(APIBase)



class OntologyItem(APIBaseID):
    """
    An ontology item
    """

    term = fields.StringField()
    type = fields.IntField()

class OntologyItemPagination(Pagination):
    """
    class for pagination results containing ontology items
    """

    items = fields.ListField(OntologyItem)

class OntologyOptions(models.Base):
    """
    additional information for the ontologies resource.
    """
    types = fields.ListField(dict)

################################################
#OBJECTS RIGHTS
################################################
class ObjectRight(APIBase):
    """
    Represents an object right.
    """
    name = fields.StringField()
    rightValue = fields.IntField()

class ObjectRightPagination(Pagination):
    """
    class for pagination results containing object rights
    """
    items = fields.ListField(ObjectRight)


class ObjectRightSet(APIBaseID):
    """
    object rights set
    """
    name = fields.StringField()
    objectRights = fields.ListField(APIBase)


class ObjectRightSetPagination(Pagination):
    """
    API class for pagination result containing object rights
    """
    items = fields.ListField(ObjectRightSet)

class ObjectGroupRight(APIBaseID):
    """
    relations between object, group and right (permission)
    """
    relatedObject = fields.EmbeddedField(APIBase)
    relatedGroup = fields.EmbeddedField(APIBase)
    relatedRights= fields.ListField(APIBase)


class ObjectUserRight(APIBaseID):
    """
    relations between object, user and right (permission)
    """
    relatedObject = fields.EmbeddedField(APIBase)
    relatedUser = fields.EmbeddedField(APIBase)
    relatedRights= fields.ListField(APIBase)

class ObjectGroupRightPagination(Pagination):
    """
    API class for pagination result containing object group rights
    """
    items = fields.ListField(ObjectGroupRight)

class ObjectUserRightPagination(Pagination):
    """
    API class for pagination result containing object userrights
    """
    items = fields.ListField(ObjectUserRight)



################################################
#OBJECTS
################################################

class ObjectType(APIBase):
    """
    for semantic triple storage
    """
    name = fields.StringField()
    displayName = fields.StringField()
    displayNameShort = fields.StringField()


class APIObject(APIBaseID):
    """
    base object class
    """
    createdDate = fields.StringField()
    name = fields.StringField()
    description  = fields.StringField()
    ontologyCount = fields.IntField()
    type = fields.EmbeddedField(ObjectType)
    downloadUrl = URLField()
    license = fields.EmbeddedField(APIBase)
    files = fields.EmbeddedField(APIBasePagination)
    linkedObjects = fields.EmbeddedField(Pagination)
    linkedObjectRelations = fields.EmbeddedField(Pagination)
    ontologyItems = fields.EmbeddedField(Pagination)
    ontologyItemRelations = fields.EmbeddedField(Pagination)
    objectPreviews = fields.ListField(Preview)
    objectGroupRights = fields.ListField(APIBase)
    objectUserRights = fields.ListField(APIBase)

    ## not part of API: holds the explicit information for objectGroupRights,
    ## and objectUserRights
    userRights = fields.ListField(ObjectUserRight)
    groupRights = fields.ListField(ObjectGroupRight)


    @classmethod
    def _create(self, response=None, **kwargs):
        """
        Constructor that performs downcasting according to the type.
        The input can either be a dictionary or a sequence of field
        :param response: dictionary (typically json response)
        :param kwargs: named arguments (used if response is none). Typically used in iterateAllPaginated
        :return: instance of object
        """

        if response is None:
            response = kwargs
        objType = self._get_object_type(response)

        return objType(**response)

    @classmethod
    def _get_object_type(cls, response):
        """
        create an APIObject depending on the type

        :param json response: object data
        :return: object
        :rtype: APIObject
        """

        obj = APIObject(**response)
        otype = obj.type.name + 'Object'
        if not globals()[otype]:
            print("Unknown type %s" % otype)
            return cls

        return globals()[otype] #eval() works, but security issues


    def get(self, apisession):
        """
        get the object from the API and convert to correct object_type object
        :param connectVSD apisession: the connection to the API
        """
        return self._create(apisession._get(self.selfUrl))

        #self = apisession.createObject(apisession._get(self.selfUrl))

    def update(self, apisession):
        """update an objects information

        :param connectVSD apisession: the connection to the API
        :return: the updated object
        :rtype: APIObject
        """

        res = apisession.putRequest(self.selfUrl, data=self.to_struct())

        if res:
            self = APIObject(**res).get(apisession)
            #self = apisession.createObject(res)
        else:
            print('failed to update the object')

    def publish(self, apisession):
        """
        publish the object

        :param connectVSD apisession: the connection to the API
        """
        return apisession._put(self.selfUrl + '/publish')

    def copy_to_folder(self, apisession, folder):
        """
        copy object to a folder

        :param Folder folder: the target folder object
        """
        objSelfUrl = APIBase(**self.to_struct())

        if not objSelfUrl in folder.containedObjects:
            folder.containedObjects.append(objSelfUrl)
            return apisession.putRequest('folders', data=folder.to_struct())

    def remove(self, apisession, folder):
        """
        remove the object from the target folder

        :param Folder folder: the target folder object
        :param connectVSD apisession: the connection to the API
        """
        pass

    def delete(self, apisession):
        """
        delete unpublished object
        :param connectVSD apisession: the connection to the API
        """

        return apisession._delete(self.selfUrl)

    def  add_object_rights(self, apisession):
        """
        the permission defined in userRights or groupRights are pushed to the Database
        :param connectVSD apisession: the connection to the API
        """

        if len(self.userRights) > 0:
            for item in self.userRights:
                res = apisession.postRequest(
                    'object-user-rights',
                    data=item.to_struct()
                )
        if len(self.groupRights) > 0:
            for item in self.groupRights:
                res = apisession.postRequest(
                    'object-group-rights',
                    data=item.to_struct()
                )

    def add_ontology_item(self, apisession):
        """ add ontology terms to an object

        :param connectVSD apisession: the connection to the API
        """
        i = -1
        for item in self.ontologyItems.items:
            i = i + 1
            ana = ObjectOntology(
                type=OntologyItem(**item).type,
                position=i,
                ontologyItem=APIBase(selfUrl=OntologyItem(**item).selfUrl),
                object=APIBase(selfUrl=self.selfUrl)
            )

            apisession.postRequest(
                'object-ontologies/{0}'.format(
                    OntologyItem(**item).type
                ),
                data=ana.to_struct())

    def remove_links(self, apisession):
        """ TODO remove all link to related objects

        :param connectVSD apisession: the connection to the API
        """

        if self.linkedObjectRelations:
            #for link in self.iteratePageItems(self.linkedObjectRelations, ObjectLink):
            #    self.delRequest(link.selfUrl)
            pass
        else:
            print('nothing to delete, no links available')

class ObjectPagination(Pagination):
    """
    API class for Pagination results containing objects
    """
    items = fields.ListField(APIObject)

################################################
#specification for Object types
################################################


class RawImageData(models.Base):
    """
    raw image attributes
    """
    sliceThickness = fields.FloatField()
    kilovoltPeak = fields.FloatField()
    spaceBetweenSlices = fields.FloatField()
    modality = fields.EmbeddedField(Modality)
    MRSScore = fields.StringField()
    timeToMRS = fields.StringField()
    TICIScaleGrade = fields.StringField()
    timeSinceStroke = fields.StringField()
    timeToTreatment = fields.StringField()
    lysisType = fields.StringField()

class RawImageObject(APIObject):
    """
    API class for raw image view model
    """
    rawImage = fields.EmbeddedField(RawImageData)

class SegmentationImageData(models.Base):
    """
    segmentation specific attributes

    """
    methodDescription = fields.StringField()
    segmentationMethod = fields.EmbeddedField(APIBase)
    #{u'displayName': u'Manual', u'id': 3, u'selfUrl': u'https://www.virtualskeleton.ch/api/segmentation_methods/3', u'name': u'Manual'})

class SegmentationImageObject(APIObject):
    """
    API class for segmenation image view model
    """
    segmentationImage = fields.EmbeddedField(SegmentationImageData)

class StatisticalModelObject(APIObject):
    """
    API class for Statistical model view model - empty
    """
    pass


class SurfaceModelData(APIObject):
    """
    attributes of surface model
    """
    vectorCount = fields.IntField()
    minX = fields.FloatField()
    minY = fields.FloatField()
    minZ = fields.FloatField()
    maxX = fields.FloatField()
    maxY = fields.FloatField()
    maxZ = fields.FloatField()

class SurfaceModelObject(APIObject):
    """
    API class for surface model view model
    """
    surfaceModel = fields.EmbeddedField(SurfaceModelData)


class SubjectData(APIObject):
    """
    attributes for subject data
    """
    subjectKey = fields.StringField()


class SubjectObject(APIObject):
    """
    API class for Subject view model

    """
    subject = fields.EmbeddedField(SubjectData)


class ClinicalStudyDataObject(APIObject):
    """
    API class for clinical trial data view model
    """
    subject = fields.EmbeddedField(SubjectData)
    clinicalStudyDefinition = fields.EmbeddedField(APIBase)

class ClinicalStudyDefinitionData(models.Base):
    """
    attributes for clinical study definition
    """
    studyOID = fields.StringField()
    studyName = fields.StringField()
    studyDescription = fields.StringField()
    protocolName = fields.StringField()
    metaDataVersionOID = fields.StringField()
    metaDataVersionName = fields.StringField()

class ClinicalStudyDefinitionObject(APIObject):
    """
    API class for clinical trail definition view model
    """
    clinicalStudyDefinition = fields.EmbeddedField(ClinicalStudyDefinitionData)


class GenomicPlatformObject(APIObject):
    """
    API class for  genomic platform view model - empty
    """
    pass

class GenomicSeriesObject(APIObject):
    """
    API class for genomic series view model - empty
    """
    pass

class GenomicSampleObject(APIObject):
    """
    API class for genomic sample view model - empty
    """
    pass

class StudyObject(APIObject):
    """
    API class for study
    """
    pass

class PlainObject(APIObject):
    """
    API class for plain (undefined object) model view model
    """
    pass

class PlainSubjectObject(APIObject):
    """
    API class for plain subject (undefined subject object) model view model
    """
    pass

class ObjectOptions(models.Base):
    """
    class for additional information of the API objects
    """

    genomicPlatform = fields.EmbeddedField(GenomicPlatformObject)
    genomicSample = fields.EmbeddedField(GenomicSampleObject)
    genomicSeries = fields.EmbeddedField(GenomicSeriesObject)
    rawImage = fields.EmbeddedField(RawImageObject)
    segmentationImage = fields.EmbeddedField(SegmentationImageObject)
    statisticalModel = fields.EmbeddedField(StatisticalModelObject)
    clinicalStudyData = fields.EmbeddedField(ClinicalStudyDataObject)
    clinicalStudyDefinition = fields.EmbeddedField(ClinicalStudyDefinitionObject)
    study = fields.EmbeddedField(StudyObject)
    subject = fields.EmbeddedField(StudyObject)
    surfaceModel = fields.EmbeddedField(SurfaceModelObject)


################################################
#SEGMENTATION METHOD
################################################


class SegmentationMethod(APIBaseID):
    """
    segmentation methods view model
    """
    name = fields.StringField()
    displayName = fields.StringField()



################################################
#SEARCH
################################################
class DynamicSearchLogicalOperator(models.Base):
    """
    logical operator view model
    """
    name = fields.StringField()
    displayName = fields.StringField()
    position = fields.IntField()

class DynamicSearchComparisonOperator(models.Base):
    """
    docstring
    """

    name = fields.StringField()
    displayName = fields.StringField()
    position = fields.IntField()
    typeaheadUrl = fields.StringField()

class DynamicSearchSourceField(models.Base):
    """
    fiels view model for dynamic search
    """
    name = fields.StringField()
    displayName = fields.StringField()
    position = fields.IntField()
    comparisonOperators = fields.ListField(DynamicSearchComparisonOperator)

class DynamicSearchSourceType(models.Base):
    """
    source type view model for search
    """
    name = fields.StringField()
    displayName = fields.StringField()
    position = fields.IntField()
    sourceFields = fields.ListField(DynamicSearchSourceField)

class DynamicSearchOptions(models.Base):
    """ for DynamicSearchOptions"""

    logicalOperators = fields.ListField(DynamicSearchLogicalOperator)
    sourceTypes = fields.ListField(DynamicSearchSourceType)

class DynamicSearchInputItem(models.Base):
    """ docstring"""
    data = fields.EmbeddedField(APIObject)
    displayName = fields.StringField()
    isTypeahead = fields.BoolField()

class DynamicSearchCondition(models.Base):
    """docstring """
    sourceField = fields.EmbeddedField(DynamicSearchSourceField)
    comparisonOperator = fields.EmbeddedField(DynamicSearchComparisonOperator)
    inputItem = fields.EmbeddedField(DynamicSearchInputItem)

class DynamicSearchGroup(models.Base):
    """docstring"""

    sourceType = fields.EmbeddedField(DynamicSearchSourceType)
    logicalOperator = fields.EmbeddedField(DynamicSearchLogicalOperator)
    conditions = fields.ListField(DynamicSearchCondition)
    groups = fields.ListField(dict) # DynamicSearchGroup -> recursive...

################################################
#UPLOAD
################################################
class UploadResponse(models.Base):
    """
    a response consisting of a combination between a file and an object after the upload
    """
    file = fields.EmbeddedField(APIBase)
    relatedObject = fields.EmbeddedField(APIBase)




################################################
#USERS
################################################
class User(APIBaseID):
    """
    Users of the repository
    """
    username = fields.StringField()



###############################
# API url dictionary
############################
resourceTypes = {
    'files': File,
    'folders': Folder,
    'objects': APIObject,
    'object-links' : ObjectLinks
}
