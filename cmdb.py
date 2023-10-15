#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
#############################################################################
#
# This is the high level implementation of the BMC Atrium C-API in Python.
# (C) 2006-2012 by Ergorion
#
# Currently supported Version: Atrium API V1.0 (AROS), V1.1 (CMDB)-V7.6
# (using CMDB prefix!)
#
#############################################################################
# known issues: none
#
#
#############################################################################

import logging

from ctypes import c_uint, c_int, c_char_p, byref, Structure, POINTER

from pyars import cars, ccmdb
from pyars.ars import ARS, my_byref 

if ccmdb.cmdbversion == 'arosapi63':
    class AROSAttributeStruct(Structure):
        _fields_ = [("attributeName", ccmdb.ARNameType),
                     ("attributeId",  ccmdb.ARNameType),
                     ("dataType",  c_uint),
                     ("attributeType", c_uint),
                     ("baseClassNameId",  ccmdb.AROSClassNameId),
                     ("arFieldId",  ccmdb.ARInternalId),
                     ("entryMode", c_uint),
                     ("attributeLimit", ccmdb.AROSAttributeLimit),
                     ("defaultValue", ccmdb.ARValueStruct),
                     ("characList", ccmdb.ARPropList),
                     ("customCharacList", ccmdb.ARPropList)]
    
    class CMDBAttributeStruct(AROSAttributeStruct):
        pass
    
    class AROSAttributeList(Structure):
        _fields_ = [("numItems", c_uint),
                     ("attributeList", POINTER(AROSAttributeStruct))]
    
    class CMDBAttributeList (AROSAttributeList):
        pass
    
    class AROSClassStruct(Structure):
        _fields_ = [("classNameId", ccmdb.AROSClassNameId),
                     ("classId", ccmdb.ARNameType),
                     ("classTypeInfo", ccmdb.AROSClassTypeInfo),
                     ("superclassNameId", ccmdb.AROSClassNameId),
                     ("indexList", ccmdb.AROSIndexList),
                     ("characList", ccmdb.ARPropList),
                     ("customCharacList", ccmdb.ARPropList)]
    
    class AROSClassList(Structure):
        _fields_ = [("numItems", c_uint),
                     ("classList", POINTER(AROSClassStruct))]
    
    class AROS10(ARS):
        '''pythonic wrapper Class for Atrium C API, Version 1.0

Create an instance of CMDB and call its methods...
All methods have prefix "AROS".'''
        def __init__(self, server='', user='', password='', language='', 
                   authString = '',
                   tcpport = 0,
                   rpcnumber = 0):
            '''Class constructor'''
            self.__version__ = "1.0.0"
            self.arversion = ''
            self.errnr = 0
            self.context = ccmdb.ARControlStruct()
            self.arsl = ccmdb.ARStatusList()
            self.logger = logging.getLogger()
            hdlr = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
            hdlr.setFormatter(formatter)
            self.logger.addHandler(hdlr) 
            self.logger.setLevel(logging.DEBUG)
            # we need both api's loaded and stored in seperate variables, as 
            # we need access to the standard API functions in addition to the
            # CMDB functions!
            self.arapi = cars.arapi
            self.cmdbapi = ccmdb.cmdbapi # set in ccmdb
            self.arversion = cars.version
            self.cmdbversion = ccmdb.cmdbversion # set in ccmdb
            if server != '':
                self.Login(server, user, password)
    
        def Login (self,
                   server,
                   username,
                   password,
                   language='', 
                   authString = '',
                   tcpport = 0,
                   rpcnumber = 0):
            '''A small convenience function that takes care of systeminitialization.
Input: server (can be: hostname:server)
       username,
       password,
       (optional) language (default='')
       (optional) authString (default='')
       (optional) tcpport (default=0)
       (optional) rpcnumber (default=0)
Output: errnr'''
            self.errnr = self.AROSInitialization()
            if self.errnr > 1:
                self.logger.error('Login: error during Initialization of the Class Manager')
                pass
    
            # first use the normal login procedure
            ARS.Login(self, server, username, password,language, authString, 
                      tcpport, rpcnumber)
            if self.errnr > 1:
                self.logger.error('Login failed!') 
                return self.errnr
            
            if server.find(':') > -1:
                server,tcpport = server.split(':')
                tcpport = int(tcpport)
            
            self.logger.debug('calling AROSSetServerPort with %d' % (tcpport))
            ret = self.AROSSetServerPort(tcpport, rpcnumber)
            if ret > 1:
                self.logger.error('AROSSetServerPort failed!') 
                pass            
            return self.errnr

        def Logoff (self):
            '''Logoff ends the session with the Atrium server.
    
Input: 
Output: errnr'''
            self.logger.debug('enter Logoff...')
            if self.context:
                self.errnr = self.cmdbapi.AROSTermination(byref(self.context),
                                                          byref(self.arsl))
            if self.errnr > 1:
                self.logger.error( "Logoff: failed")
            return self.errnr
        
        def AROSBeginBulkEntryTransaction(self):
            '''AROSBeginBulkEntryTransaction starts a transaction.

It indicates that subsequent API calls are part of the bulk transaction. Any API
calls that arrive after this function call are placed in a queue. Metadata
function calls are not part of the bulk transaction.
Input: 
Output: errnr'''
            self.logger.debug('enter AROSBeginBulkEntryTransaction: ')
            self.errnr = self.cmdbapi.AROSBeginBulkEntryTransaction(byref(self.context),
                                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('enter AROSBeginBulkEntryTransaction failed!')
            return self.errnr
    
        def AROSCreateAttribute(self,classNameId, 
                                attributeName,
                                attributeId,
                                dataType,
                                arFieldId = 0,
                                entryMode = ccmdb.AROS_ATTR_ENTRYMODE_OPTIONAL,
                                attributeLimit = None,
                                defaultValue = None, 
                                characList = None,
                                customCharacList = None):
            '''AROSCreateAttribute creates a new attribute with the indicated name for the specified class.

AROSClassNameId               classNameId,         /* IN: name of owning class */
ARNameType                    attributeName,       /* IN: name of the attribute */
ARNameType                    attributeId,         /* IN: Id of the attribute */
unsigned int                  dataType,            /* IN: data type */
ARInternalId                  arFieldId,           /* IN: field Id of attribute */
unsigned int                  entryMode,           /* IN: entry mode */
AROSAttributeLimit            attributeLimit,      /* IN: attribute limit */
ARValueStruct                 defaultValue,        /* IN: default value */
ARPropList                    characList,          /* IN: characteristics list */
ARPropList                    customCharacList,    /* IN: custom characteristics list */
Output: errnr'''
            self.logger.debug('enter AROSCreateAttribute...')
            self.errnr = self.cmdbapi.AROSCreateAttribute(byref(self.context),
                                                        my_byref(classNameId),
                                                        attributeName,
                                                        attributeId,
                                                        dataType,
                                                        my_byref(arFieldId),
                                                        entryMode,
                                                        my_byref(attributeLimit),
                                                        my_byref(defaultValue),
                                                        my_byref(characList),
                                                        my_byref(customCharacList),
                                                        byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('AROSCreateAttribute failed for %s:%s:%s' % (classNameId.namespaceName,
                                  classNameId.className,
                                  attributeName))
            return self.errnr
    
        def AROSCreateClass (self, classNameId, 
                             classId, 
                             classTypeInfo = ccmdb.AROS_CLASS_TYPE_REGULAR, 
                             superclassNameId = None, 
                             indexList = None, 
                             characList = None, 
                             customCharacList = None):
            '''AROSCreateClass creates a class with core attributes in the Object form. 

The name of the form
contains the prefix <namespace>:<classname>. The metadata is stored in the
OBJSTR:Class form and the attribute information is stored in the
OBJSTR:AttributeDefinition form.
AROSClassNameId               classNameId,         /* IN: name of the class */
ARNameType                    classId,             /* IN: class Id */
AROSClassTypeInfo             classTypeInfo,       /* IN: default = ccmdb.AROS_CLASS_TYPE_REGULAR */
AROSClassNameId               superclassNameId,    /* IN: default = None */
AROSIndexList                 indexList,           /* IN; default = None */
ARPropList                    characList,          /* IN: default = None */
ARPropList                    customCharacList,    /* IN: default = None */
Output: errnr'''
            self.logger.debug('enter AROSCreateClass...')
            self.errnr = self.cmdbapi.AROSCreateClass(byref(self.context),
                                                    my_byref(classNameId),
                                                    classId,
                                                    my_byref(classTypeInfo),
                                                    my_byref(superclassNameId),
                                                    my_byref(indexList),
                                                    my_byref(characList),
                                                    my_byref(customCharacList),
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('AROSCreateClass failed for %s:%s' % (classNameId.namespaceName,
                                                                         classNameId.className))
            return self.errnr
    
        def AROSCreateGuid(self):
            '''AROSCreateGuid creates a class or relationship instance in the Object form.

Input: 
Output: guid'''
            self.logger.debug('enter AROSCreateGuid...')
            guid = ccmdb.ARGuid()
            self.errnr = self.cmdbapi.AROSCreateGuid(byref(self.context),
                                                     guid,
                                                     byref(self.arsl))
            if self.errnr < 2:
                return guid
            else:
                self.logger.error('AROSCreateGuid failed!')
                return None
        
        def AROSCreateInstance(self, classNameId, 
                               attributeValueList):
            '''AROSCreateInstance creates a class or relationship instance.

AROSClassNameId               classNameId,         /* IN: class name */
AROSAttributeValueList        attributeValueList,  /* IN: list of attributeId/value pairs for instance */
Output: ARNameType                    instanceId,          /* OUT: instance Id */
    or None in case of failure'''
            self.logger.debug('enter AROSCreateInstance...')
            instanceId = ccmdb.ARNameType()
            self.errnr = self.cmdbapi.AROSCreateInstance(byref(self.context),
                                                         my_byref(classNameId),
                                                         my_byref(attributeValueList),
                                                         instanceId,
                                                         byref(self.arsl))
            if self.errnr < 2:
                return instanceId
            else:
                self.logger.error('AROSCreateInstance failed!')
                return None

        def AROSCreateMultipleAttribute(self, classNameId, 
                                        attributeNameList, 
                                        attributeIdList, 
                                        dataTypeList,
                                        arFieldIdList,
                                        entryModeList, 
                                        attributeLimitList, 
                                        defaultValueList, 
                                        characListList,
                                        customCharacListList):
            '''AROSCreateMultipleAttribute creates multiple new attributes.

Input: classNameId
       attributeNameList
       attributeIdList
       dataTypeList
       arFieldIdList
       entryModeList
       attributeLimitList
       defaultValueList
       characListList
       customCharacListList
Output: errnr'''
            self.logger.debug('enter AROSCreateMultipleAttribute...')
            self.errnr = self.cmdbapi.AROSCreateMultipleAttribute (byref(self.context),
                                                   my_byref(classNameId),
                                                   my_byref(attributeNameList),
                                                   my_byref(attributeIdList),
                                                   my_byref(dataTypeList),
                                                   my_byref(arFieldIdList),
                                                   my_byref(entryModeList),
                                                   my_byref(attributeLimitList),
                                                   my_byref(defaultValueList),
                                                   my_byref(characListList),
                                                   my_byref(customCharacListList),
                                                   byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('AROSCreateClass failed for %s:%s' % (
                                                    classNameId.namespaceName,
                                                    classNameId.className))
            return self.errnr
        
        def AROSDeleteAttribute(self, classNameId, 
                                attributeName, 
                                deleteOption = ccmdb.AR_ATTRIBUTE_CLEAN_DELETE):
            '''AROSDeleteAttribute deletes the attribute with the indicated ID. 

Depending on the value you
specify for the deleteOption parameter, the attribute is deleted immediately
and is not returned to users who request information about attributes.
Input: classNameId, 
       attributeName, 
       (optional) deleteOption (default  = ccmdb.AR_ATTRIBUTE_CLEAN_DELETE)
Output: errnr'''
            self.logger.debug('enter AROSDeleteAttribute...')
            self.errnr = self.cmdbapi.AROSDeleteAttribute(byref(self.context),
                                                    my_byref(classNameId),
                                                    attributeName,
                                                    deleteOption,
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('AROSDeleteAttribute failed for %s:%s' % (classNameId.namespaceName,
                                                                         classNameId.className))
            return self.errnr
        
        def AROSDeleteClass(self, classNameId, deleteOption = ccmdb.AROS_DELETE_CLASS_OPTION_NONE):
            '''AROSDeleteClass deletes the attribute with the indicated ID. 

Depending on the value you
specify for the deleteOption parameter, the attribute is deleted immediately
and is not returned to users who request information about attributes.
Input: classNameId,
       (optional) deleteOption (default  = ccmdb.AROS_DELETE_CLASS_OPTION_NONE)
Output: errnr'''
            self.logger.debug('enter AROSDeleteClass...')
            self.errnr = self.cmdbapi.AROSDeleteClass(byref(self.context),
                                                    my_byref(classNameId),
                                                    deleteOption,
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('AROSDeleteClass failed for %s:%s' % (
                                                    classNameId.namespaceName,
                                                    classNameId.className))
            return self.errnr
    
        def AROSDeleteInstance(self, classNameId,  
                               instanceId, 
                               deleteOption = ccmdb.AROS_DERIVED_DELOPTION_NONE):
            '''AROSDeleteInstance deletes the instance of the class.

AROSClassNameId               classNameId,         /* IN: class name */
ARNameType                    instanceId,          /* IN: instance Id */
unsigned int                  deleteOption,        /* IN: delete options */
Output: errnr'''
            self.logger.debug('enter AROSDeleteInstance...')
            self.errnr = self.cmdbapi.AROSDeleteInstance(byref(self.context),
                                                    my_byref(classNameId),
                                                    instanceId,
                                                    deleteOption,
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('AROSDeleteInstance failed for %s:%s' % (classNameId.namespaceName,
                                                                         classNameId.className))
            return self.errnr        
    
        def AROSEndBulkEntryTransaction(self,
                                        actionType = ccmdb.AR_BULK_ENTRY_ACTION_SEND):
            '''AROSEndBulkEntryTransaction: This function commits the bulk transaction.

For an action type of SEND, the API call will be executed as part of the
transaction. For an action type of CANCEL, the transaction will be canceled.
Input: (optional) actionType (default = ccmdb.AR_BULK_ENTRY_ACTION_SEND)
Output: bulkEntryReturnList (ARBulkEntryReturnList) or None in case of failure'''
            self.logger.debug('enter AROSEndBulkEntryTransaction...')
            bulkEntryReturnList = ccmdb.ARBulkEntryReturnList()
            self.errnr = self.cmdbapi.AROSEndBulkEntryTransaction(byref(self.context),
                                                      actionType,
                                                      byref(bulkEntryReturnList),
                                                      byref(self.arsl))
            if self.errnr < 2:
                return bulkEntryReturnList
            else:
                self.logger.error('enter AROSEndBulkEntryTransaction failed!')
                return None
    
        def AROSExport(self, exportItemList, exportFormat, directoryPath):
            '''AROSExport exports the indicated structure definitions.

Input: exportItemList, 
        exportFormat, 
        directoryPath
Output: errnr'''
            self.logger.debug('enter AROSExport...')
            self.errnr = self.cmdbapi.AROSExport(byref(self.context),
                                               my_byref(exportItemList),
                                               exportFormat,
                                               directoryPath,
                                               byref(self.arsl))
            if self.errnr >1:
                self.logger.error('AROSExport failed!')
            return self.errnr        
    
        def AROSGetAttribute(self, classNameId, 
                             attributeName):
            '''AROSGetAttribute retrieves a single attribute.

Input: classNameId, 
       attributeName    
Output: AROSAttributeStruct (attributeId, 
        dataType, 
        attributeType,
        baseClassNameId, 
        arFieldId, 
        entryMode, 
        attributeLimit, 
        defaultValue,
        characList, 
        customCharacList) or None in case of failure'''
            self.logger.debug('enter AROSGetAttribute...')
            attributeId = ccmdb.ARNameType()
            dataType = c_uint()
            attributeType = c_uint()
            baseClassNameId = ccmdb.AROSClassNameId()
            arFieldId = ccmdb.ARInternalId()
            entryMode = c_uint()
            attributeLimit = ccmdb.AROSAttributeLimit()
            defaultValue = ccmdb.ARValueStruct()
            characList = ccmdb.ARPropList()
            customCharacList = ccmdb.ARPropList()        
            self.errnr = self.cmdbapi.AROSGetAttribute(byref(self.context),
                                                       byref(classNameId),
                                                       attributeName,
                                                       attributeId,
                                                       byref(dataType),
                                                       byref(attributeType),
                                                       byref(baseClassNameId),
                                                       byref(arFieldId),
                                                       byref(entryMode),
                                                       byref(attributeLimit),
                                                       byref(defaultValue),
                                                       byref(characList),
                                                       byref(customCharacList),
                                                       byref(self.arsl))
            if self.errnr < 2:
                return AROSAttributeStruct(attributeName, 
                                           attributeId.value, 
                                           dataType, 
                                           attributeType,
                                           baseClassNameId, 
                                           arFieldId, 
                                           entryMode, 
                                           attributeLimit, 
                                           defaultValue,
                                           characList, 
                                           customCharacList)
            else:
                self.logger.error('AROSGetAttribute failed for %s:%s/%s' % (
                                                classNameId.namespaceName,
                                                classNameId.className,
                                                attributeName))
                return None
    
        def AROSGetClass(self, classNameId):
            '''AROSGetClass retrieves the class information from the OBJSTR:Class form.

Input: classNameId (AROSClassNameID)
Output: AROSClassStruct (classId (ARNameType)
        classTypeInfo (AROSClassTypeInfo)
        superclassNameId (AROSClassNameId)
        indexList (AROSIndexList)
        characList (ARPropList)
        customCharacList (ARPropList)) or None in case of failure'''
            self.logger.debug('enter AROSGetClass...')
            classId = ccmdb.ARNameType()
            classTypeInfo = ccmdb.AROSClassTypeInfo()
            superclassNameId = ccmdb.AROSClassNameId()
            indexList = ccmdb.AROSIndexList()
            characList = ccmdb.ARPropList()
            customCharacList = ccmdb.ARPropList()
            self.errnr = self.cmdbapi.AROSGetClass(byref(self.context),
                                                 my_byref(classNameId),
                                                 classId,
                                                 my_byref(classTypeInfo),
                                                 my_byref(superclassNameId),
                                                 my_byref(indexList),
                                                 my_byref(characList),
                                                 my_byref(customCharacList),
                                                 byref(self.arsl))
            if self.errnr < 2:
                return AROSClassStruct(classNameId, 
                                        classId.value, 
                                        classTypeInfo, 
                                        superclassNameId, 
                                        indexList,
                                        characList, 
                                        customCharacList)
            else:
                self.logger.error('AROSGetClass failed for %s:%s' % (classNameId.namespaceName,
                                  classNameId.className))
                return None
            
        def AROSGetInstance(self, classNameId, 
                            instanceId, 
                            attributeGetList):
            '''AROSGetInstance retrieves information about the instance.
            
Input: classNameId, 
       instanceId, 
       attributeGetList    
Output: attributeValueList or None in case of failure'''
            self.logger.debug('enter AROSGetInstance...')
            attributeValueList = ccmdb.AROSAttributeValueList()
            self.errnr = self.cmdbapi.AROSGetInstance(byref(self.context),
                                                        classNameId,
                                                        instanceId,
                                                        my_byref(attributeGetList),
                                                        byref(attributeValueList),
                                                        byref(self.arsl))
            if self.errnr < 2:
                return attributeValueList
            else:
                self.logger.error('AROSGetInstance failed for %s:%s' % (
                                                    classNameId.namespaceName,
                                                    classNameId.className))
                return None
    
        def AROSGetInstanceBLOB(self, classNameId, instanceId, attributeName, loc):
            '''AROSGetInstanceBLOB retrieves the attachment, or binary large object (BLOB).

It retrieves whatever is stored for the attachment field. The BLOB is placed in a file.
Input: classNameId, 
       instanceId, 
       attributeName
Output: loc or None in case of failure'''
            self.logger.debug('enter AROSGetInstanceBLOB...')
            loc = ccmdb.ARLocStruct()
            self.errnr = self.cmdbapi.AROSGetInstanceBLOB(byref(self.context),
                                                     byref(classNameId),
                                                     instanceId,
                                                     attributeName,
                                                     byref(loc),
                                                     byref(self.arsl))
            if self.errnr < 2:
                return loc
            else:
                self.logger.error('AROSGetInstanceBLOB failed for %s:%s' % (
                                                    classNameId.namespaceName,
                                                    classNameId.className))
                return None
        
        def AROSGetListClass(self,
                             namespaceName = ccmdb.BMC_namespace,
                             classNameIdRelation = None,
                             superclassName = None,
                             characQueryList = None,
                             getHiddenClasses = False):
            '''AROSGetListClass retrieves information about classes that are 
related to this class or derived from this class.
Input: (optional) namespaceName (ARNameType, default = ccmdb.BMC_namespace),
       (optional) classNameIdRelation (AROSClassNameId, default = None),
       (optional) superclassName (AROSClassNameId, default = None),
       (optional) characQueryList (ARPropList, default = None),
       (optional) getHiddenClasses (ARBoolean, default = False)
Output: classNameIdList or None in case of failure'''
            self.logger.debug('enter AROSGetListClass...')
            classNameIdList = ccmdb.AROSClassNameIdList()
            self.errnr = self.cmdbapi.AROSGetListClass(byref(self.context),
                                                     namespaceName,
                                                     my_byref(classNameIdRelation),
                                                     my_byref(superclassName),
                                                     my_byref(characQueryList),
                                                     getHiddenClasses,
                                                     byref(classNameIdList),
                                                     byref(self.arsl))
            if self.errnr < 1:
                return classNameIdList
            else:
                self.logger.error('AROSGetListClass failed for %s' % namespaceName)
                return None
    
        def AROSGetListInstance(self, classNameId,
                                qualifier = None,
                                attributeGetList = None,
                                sortList = None,
                                firstRetrieve = ccmdb.AROS_START_WITH_FIRST_INSTANCE,
                                maxRetrieve = ccmdb.AROS_NO_MAX_LIST_RETRIEVE):
            '''Retrieves a list of instances. You can limit the list to entries that match
particular conditions by specifying the qualifier parameter.
Input: classNameId,
       (optional) qualifier (AROSQualifierStruct, default = None),
       (optional) attributeGetList (ARNameList, default = None),
       (optional) sortList (AROSSortList, default = None),
       (optional) firstRetrieve (c_uint, default = ccmdb.AROS_START_WITH_FIRST_INSTANCE),
       (optional) maxRetrieve (c_uint, default = ccmdb.AROS_NO_MAX_LIST_RETRIEVE) 
Output: (instanceIdList, 
        attrValueListList, 
        numMatches) or None in case of failure'''
            self.logger.debug('enter AROSGetListInstance...')
            if qualifier is None:
                qualifier = ccmdb.AROSQualifierStruct()
            instanceIdList = ccmdb.ARNameList()
            attrValueListList = ccmdb.AROSAttributeValueListList()
            numMatches = c_uint()
            self.errnr = self.cmdbapi.AROSGetListInstance(byref(self.context),
                                                        my_byref(classNameId),
                                                        byref(qualifier),
                                                        my_byref(attributeGetList),
                                                        my_byref(sortList),
                                                        firstRetrieve,
                                                        maxRetrieve,
                                                        byref(instanceIdList),
                                                        byref(attrValueListList),
                                                        byref(numMatches),
                                                        byref(self.arsl))
            if self.errnr < 2:
                return (instanceIdList, attrValueListList, numMatches)
            else:
                self.logger.error('AROSGetListInstance failed for %s:%s' % (classNameId.namespaceName,
                                                                         classNameId.className))
                return None
    
        def AROSGetMultipleAttribute(self, classNameId, 
                                     getHiddenAttrs = ccmdb.ARBoolean('\1'), 
                                     getDerivedAttrs = ccmdb.ARBoolean('\1'),
                                     nameList = None,
                                     attrCharacQueryList = None):
            '''AROSGetMultipleAttribute retrieves multiple attributes.
            
Input: classNameId, 
       (optional) getHiddenAttrs (ARBoolean, default = ccmdb.ARBoolean('\1')), 
       (optional) getDerivedAttrs (ARBoolean, default = ccmdb.ARBoolean('\1')),
       (optional) nameList (ARNameList, default = None),
       (optional) attrCharacQueryList (ARPropList, default = None)  
Output: AROSAttributeList or None in case of failure'''
            self.logger.debug('enter AROSGetMultipleAttribute...')
            existList = ccmdb.ARBooleanList()
            attributeNameList = ccmdb.ARNameList()
            attributeIdList = ccmdb.ARNameList()
            dataTypeList = ccmdb.ARUnsignedIntList()
            attributeTypeList = ccmdb.ARUnsignedIntList()
            baseClassNameIdList = ccmdb.AROSClassNameIdList()
            arFieldIdList = ccmdb.ARInternalIdList()
            entryModeList = ccmdb.ARUnsignedIntList()
            attributeLimitList = ccmdb.AROSAttributeLimitList()
            defaultValueList = ccmdb.ARValueList()
            characListList = ccmdb.ARPropListList()
            customCharacListList = ccmdb.ARPropListList()
            self.errnr = self.cmdbapi.AROSGetMultipleAttribute(byref(self.context),
                                                               my_byref(classNameId),
                                                               getHiddenAttrs,
                                                               getDerivedAttrs,
                                                               my_byref(nameList),
                                                               my_byref(attrCharacQueryList),
                                                               byref(existList),
                                                               byref(attributeNameList),
                                                               byref(attributeIdList),
                                                               byref(dataTypeList),
                                                               byref(attributeTypeList),
                                                               byref(baseClassNameIdList),
                                                               byref(arFieldIdList),
                                                               byref(entryModeList),
                                                               byref(attributeLimitList),
                                                               byref(defaultValueList),
                                                               byref(characListList),
                                                               byref(customCharacListList),
                                                               byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('AROSGetMultipleAttribute: failed for %s:%s' % (
                                  classNameId.namespaceName,
                                  classNameId.className))
                return None
            else:
                tempArray = (AROSAttributeStruct * existList.numItems)()
                for i in range(existList.numItems):
                    if existList.booleanList[i]:
                        tempArray[i].attributeName = attributeNameList.nameList[i].value
                        if attributeIdList: tempArray[i].attributeId = attributeIdList.nameList[i].value
                        if dataTypeList: tempArray[i].dataType = dataTypeList.intList[i]
                        if attributeTypeList: tempArray[i].attributeType = attributeTypeList.intList[i]
                        if baseClassNameIdList: tempArray[i].baseClassNameId = baseClassNameIdList.classNameIdList[i]
                        if arFieldIdList: tempArray[i].arFieldId = arFieldIdList.internalIdList[i]
                        if entryModeList: tempArray[i].entryMode = entryModeList.intList[i]
                        if attributeLimitList: tempArray[i].attributeLimit = attributeLimitList.limitList[i]
                        if defaultValueList: tempArray[i].defaultValue = defaultValueList.valueList[i]
                        if characListList: tempArray[i].characList = characListList.propsList[i]
                        if customCharacListList: tempArray[i].customCharacList = customCharacListList.propsList[i]
                return AROSAttributeList (existList.numItems, tempArray)
    
        def AROSGetMultipleInstances(self, classNameId, 
                                     instanceIds, 
                                     attributeGetList):
            '''AROSGetMultipleInstances retrieves multiple instances.

Input: classNameId (AROSClassNameId) 
       instanceIds (ARNameList)
       attributeGetList (ARNameList)
Output: (existList, attrValueListList) or None in case of failure'''
            self.logger.debug('enter AROSGetMultipleInstances...')
            existList = ccmdb.ARBooleanList()
            attrValueListList = ccmdb.AROSAttributeValueListList()
            self.errnr = self.cmdbapi.AROSGetMultipleInstances(byref(self.context),
                                                       my_byref(classNameId),
                                                       my_byref(instanceIds),
                                                       my_byref(attributeGetList),
                                                       byref(existList), 
                                                       byref(attrValueListList),
                                                       byref(self.arsl))
            if self.errnr < 2:
                return (existList, attrValueListList)
            else:
                self.logger.error('AROSGetMultipleInstances failed for %s:%s' % (
                                                 classNameId.namespaceName,
                                                 classNameId.className))
                return None           
    
        def AROSGetServerPort(self):
            '''AROSGetServerPort retrieves the port information.
Input:
Output: (tcpPort, rpcPort) or None in case of failure'''
            self.logger.debug('enter AROSGetServerPort...')
            tcpPort = c_int()
            rpcPort = c_int()
            self.errnr = self.cmdbapi.AROSGetServerPort(byref(self.context),
                                                    byref(tcpPort),
                                                    byref(rpcPort),
                                                    byref(self.arsl)                                                   )
            if self.errnr < 2:
                return (tcpPort, rpcPort)
            else:
                self.logger.error('AROSGetServerPort failed')
                return None    
    
        def AROSGraphQuery(self,
                           startClassNameId,
                           startExtensionId,
                           startInstanceId, 
                           numLevels = -1,
                           direction = ccmdb.AROS_RELATIONSHIP_DIRECTION_OUT,
                           noMatchProceed = 1, 
                           onMatchProceed = 1, 
                           queryGraph = None):
            '''AROSGraphQuery is used to search or query related instances.

AROSClassNameId      startClassNameId,/* IN: class name id of the starting node */
ARNameType           startExtensionId,/* IN: extension id of the starting node */
ARNameType           startInstanceId, /* IN: instance Id of the starting node */
int                  numLevels,        /* IN: number of levels to go, -1 means all */
int                  direction,        /* IN: 1 for impact(node on the right), 0 for cause(node on the */
                                       /*     left) */
ARBoolean            noMatchProceed,   /* IN: boolean indicating whether to proceed if instance doesn't*/
                                       /*     match specified qualification */
ARBoolean            onMatchProceed,   /* IN: boolean indicating whether to proceed on matching of */
                                       /*     specified instance */
AROSGraphList        queryGraph,      /* IN: input graph to query on */
Output:
AROSGetObjectList    objects,         /* OUT: list of objects returned via graph walking */
AROSGetRelationList  relations,       /* OUT: list of relationships that connects the returned objects */
    or None in case of failure'''
            self.logger.debug('enter AROSGraphQuery...')
            objects = ccmdb.AROSGetObjectList()
            relations = ccmdb.AROSGetRelationList()
            self.errnr = self.cmdbapi.AROSGraphQuery(byref(self.context),
                                                      byref(startClassNameId),
                                                      startExtensionId,
                                                      startInstanceId,
                                                      numLevels,
                                                      direction,
                                                      noMatchProceed,
                                                      onMatchProceed,
                                                      my_byref(queryGraph),
                                                      byref(objects),
                                                      byref(relations),
                                                      byref(self.arsl))
            if self.errnr < 2:
                return (objects, relations)
            else:
                self.logger.error('AROSGraphQuery failed for %s' % startClassNameId.className)
                return None
    
        def AROSImport(self, importItemList, directoryPath):
            '''AROSImport imports the indicated structure definitions.

Use this function to copy structure definitions from one server to another.
Input: importItemList
       directoryPath
Output: errnr'''
            self.logger.debug('enter AROSImport...')
            self.errnr = self.cmdbapi.AROSImport(byref(self.context),
                                               my_byref(importItemList),
                                               directoryPath,
                                               byref(self.arsl))
            if self.errnr >1:
                self.logger.error('AROSImport failed!')
            return self.errnr   
            
        def AROSInitialization (self):
            '''AROSInitialization Initializes the Class Manager C API session. 

This function must be called before any Class Manager C API calls are made.
Input:
Output: errnr'''
            self.logger.debug('enter AROSInitialization...')
            self.errnr =  self.cmdbapi.AROSInitialization(byref(self.context),
                                                        byref(self.arsl))
            if self.errnr > 1:
                self.logger.error( "AROSInitialization: failed")
            return self.errnr
    
        def AROSSetAttribute(self, classNameId,
                             attributeName,
                             newAttributeName,
                             entryMode, 
                             attributeLimit,
                             defaultValue,
                             characList,
                             customCharacList):
            '''AROSSetAttribute sets an attribute with the indicated name for the specified class.

AROSClassNameId               classNameId,         /* IN: name of owning class */
ARNameType                    attributeName,       /* IN: name of the attribute */
ARNameType                    newAttributeName,    /* IN: new name of the attribute */
unsigned int                  entryMode,           /* IN: entry mode */
AROSAttributeLimit            attributeLimit,      /* IN: attribute limit */
ARValueStruct                 defaultValue,        /* IN: default value */
ARPropList                    characList,          /* IN: characteristics list */
ARPropList                    customCharacList,    /* IN: custom characteristics list */
Output: errnr'''
            self.logger.debug('enter AROSSetAttribute...')
            self.errnr = self.cmdbapi.AROSSetAttribute(byref(self.context),
                                                    my_byref(classNameId),
                                                    attributeName,
                                                    newAttributeName,
                                                    my_byref(entryMode),
                                                    my_byref(attributeLimit),
                                                    my_byref(defaultValue),
                                                    my_byref(characList),
                                                    my_byref(customCharacList),
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('AROSSetAttribute failed for %s:%s:%s' % (classNameId.namespaceName,
                                  classNameId.className,
                                  attributeName))
            return self.errnr
    
        def AROSSetClass(self, classNameId, 
                             newClassNameId, 
                             classTypeInfo, 
                             indexList, 
                             characList, 
                             customCharacList):
            '''AROSSetClass sets the class properties in the OBJSTR:Class form. 

For the supplied
properties to modify, ARSetEntry() will be called on the OBJSTR:Class form
to modify the appropriate class entry. After you create a class, you cannot
modify the following properties: classId, classType (regular, relationship),
and persistence provider.
AROSClassNameId               classNameId,         /* IN: name of the class */
AROSClassNameId               newClassNameId,      /* IN: new name of the class */
AROSClassTypeInfo             classTypeInfo,       /* IN: info on the class type */
AROSIndexList                 indexList,           /* IN; list of indexes defined for the class */
ARPropList                    characList,          /* IN: class characteristics */
ARPropList                    customCharacList,    /* IN: custom class characteristics */
Output: errnr'''
            self.logger.debug('enter AROSSetClass...')
            self.errnr = self.cmdbapi.AROSSetClass(byref(self.context),
                                                    my_byref(classNameId),
                                                    my_byref(newClassNameId),
                                                    my_byref(classTypeInfo),
                                                    my_byref(indexList),
                                                    my_byref(characList),
                                                    my_byref(customCharacList),
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('AROSSetClass failed for %s:%s' % (classNameId.namespaceName,
                                                                     classNameId.className))
            return self.errnr
    
        def AROSSetInstance(self,classNameId, 
                            instanceId,
                            attributeValueList):
            '''AROSSetInstance sets a class or relationship instance in the Object form.

AROSClassNameId              *classNameId,         /* IN: class name */
ARNameType                    instanceId,          /* IN: instance Id */
AROSAttributeValueList       *attributeValueList,  /* IN: list of attributeId/value pairs for instance */
Output: errnr'''
            self.logger.debug('enter AROSSetInstance...')
            self.errnr = self.cmdbapi.AROSSetInstance(byref(self.context),
                                                      my_byref(classNameId),
                                                      instanceId,
                                                      my_byref(attributeValueList),
                                                      byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('AROSSetInstance failed for %s:%s' % (classNameId.namespaceName,
                                                                        classNameId.className))
            return self.errnr
        
        def AROSSetMultipleAttribute(self, classNameId,
                                     attributeNameList,
                                     newAttributeNameList,
                                     entryModeList,
                                     attributeLimitList,
                                     defaultValueList, 
                                     characListList,
                                     customCharacListList):
            '''AROSSetMultipleAttribute sets multiple attributes with the indicated name.

AROSClassNameId               classNameId,         /* IN: name of owning class */
ARNameList                    attributeNameList,   /* IN: name of the attribute */
ARNameList                    newAttributeNameList,/* IN: new name of the attribute */
ARUnsignedIntList             entryModeList,       /* IN: entry mode */
AROSAttributeLimitList        attributeLimitList,  /* IN: attribute limit */
ARValueList                   defaultValueList,    /* IN: default value */
ARPropListList                characListList,      /* IN: characteristics list */
ARPropListList                customCharacListList,/* IN: custom characteristics list */
Output: errnr'''
            self.logger.debug('enter AROSSetMultipleAttribute...')
            self.errnr = self.cmdbapi.AROSSetMultipleAttribute(byref(self.context),
                                               my_byref(classNameId),
                                               my_byref(attributeNameList),
                                               my_byref(newAttributeNameList),
                                               my_byref(entryModeList),
                                               my_byref(entryModeList),
                                               my_byref(attributeLimitList),
                                               my_byref(defaultValueList),
                                               my_byref(characListList),
                                               my_byref(customCharacListList),
                                               byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('AROSSetMultipleAttribute failed for %s:%s' % (
                                                 classNameId.namespaceName,
                                                 classNameId.className))
            return self.errnr
    
        def AROSSetServerPort(self, tcpPort = 0, 
                            rpcPort = 0):
            '''AROSSetServerPort sets the specified server port.

Input: tcpPort (default: 0)
       rpcPort (default: 0)
Output: errnr'''
            self.logger.debug('enter AROSSetServerPort...')
            # convert parameters to ctypes transparently
            ctcpPort = c_int(tcpPort)
            crpcPort = c_int(rpcPort)
            self.errnr = self.cmdbapi.AROSSetServerPort(byref(self.context),
                                                    my_byref(ctcpPort),
                                                    my_byref(crpcPort),
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('AROSSetServerPort: failed')
            return self.errnr
    
        def AROSSynchMetaData(self, pendingId):
            '''AROSSynchMetaData creates objects (forms and workflow) using metadata definitions.

Input: pendingId
Output: classNameIdList or None in case of failure'''
            self.logger.debug('enter AROSSynchMetaData...')
            classNameIdList = ccmdb.AROSClassNameIdList()
            self.errnr = self.cmdbapi.AROSSynchMetaData(byref(self.context),
                                                      pendingId,
                                                      byref(classNameIdList),
                                                      byref(self.arsl))
            if self.errnr < 2:
                return classNameIdList
            else:
                self.logger.error('AROSSynchMetaData failed for %s' % pendingId)
                return None    
    
        def AROSSystemInit(self):
            '''AROSSystemInit performs server- and network-specific 
initialization operations for internal use by BMC.

Input:
Output: propList or None in case of failure'''
            self.logger.debug('enter AROSSystemInit...')
            propList = ccmdb.ARPropList()
            self.errnr = self.cmdbapi.AROSSystemInit(byref(propList),
                                                     byref(self.arsl))
            if self.errnr < 2:
                return propList
            else:
                self.logger.error('enter AROSSystemInit failed!')
                return None 
    
        def AROSTermination (self):
            '''AROSTermination performs environment-specific cleanup routines.
            
It disconnects from the
specified session. All API programs that interact with the C API session
should call this function upon completing work in a given session.
Input:
Output: errnr'''
            self.logger.debug('enter AROSTermination...')
            # this function is used during the load phase of cmdb/cmdb api
            # to identify which version of the DLL is used: the one with cmdb prefixes
            # or with the cmdb prefixes
            # during loading, we don't have a context yet, therefore we need to use
            # my_byref...
            self.errnr = self.cmdbapi.AROSTermination(my_byref(self.context),
                                                      byref(self.arsl))
            self.context = None
            return self.errnr
        
        def AROSUpgrade(self):
            '''AROSUpgrade: no documentation available
Input:
Output: errnr'''
            self.logger.debug('enter AROSUpgrade...')
            self.errnr = self.cmdbapi.AROSUpgrade(byref(self.context),
                                                  byref(self.arsl))
            if self.errnr >1:
                self.logger.error('enter AROSUpgrade failed!')
            return self.errnr 

    class CMDB10(AROS10):
        '''
        pythonic wrapper Class for Atrium C API, Version 1.0 and 1.1 up to, 
but excluding patch 002
    
Create an instance of CMDB and call its methods; this CMDB10 class is a convenience layer
so that I can call all AROS functions under their CMDB names.
        '''
    
        def CMDBBeginBulkEntryTransaction(self):
            self.logger.debug('enter CMDBBeginBulkEntryTransaction: ')
            return self.AROSBeginBulkEntryTransaction()
    
        def CMDBCreateAttribute(self,classNameId, 
                                attributeName,
                                attributeId,
                                dataType,
                                arFieldId,
                                entryMode,
                                attributeLimit,
                                defaultValue, 
                                characList,
                                customCharacList):
            self.logger.debug('enter CMDBCreateAttribute...')
            return self.AROSCreateAttribute(classNameId, 
                                attributeName,
                                attributeId,
                                dataType,
                                arFieldId,
                                entryMode,
                                attributeLimit,
                                defaultValue, 
                                characList,
                                customCharacList)
    
        def CMDBCreateClass (self, classNameId, 
                             classId, 
                             classTypeInfo, 
                             superclassNameId, 
                             indexList, 
                             characList, 
                             customCharacList):
            self.logger.debug('enter CMDBCreateClass...')
            return self.AROSCreateClass (classNameId, 
                             classId, 
                             classTypeInfo, 
                             superclassNameId, 
                             indexList, 
                             characList, 
                             customCharacList)
    
        def CMDBCreateGuid(self, guid):
            self.logger.debug('enter CMDBCreateGuid...')
            return self.AROSCreateGuid(guid)
        
        def CMDBCreateInstance(self, classNameId, attributeValueList):
            self.logger.debug('enter CMDBCreateInstance...')
            return self.AROSCreateInstance(classNameId, attributeValueList)
    
        def CMDBCreateMultipleAttribute(self, classNameId, 
                                        attributeNameList, 
                                        attributeIdList, 
                                        dataTypeList,
                                        arFieldIdList,
                                        entryModeList, 
                                        attributeLimitList, 
                                        defaultValueList, 
                                        characListList,
                                        customCharacListList):
            self.logger.debug('enter CMDBCreateMultipleAttribute...')
            return self.AROSCreateMultipleAttribute(classNameId, 
                                        attributeNameList, 
                                        attributeIdList, 
                                        dataTypeList,
                                        arFieldIdList,
                                        entryModeList, 
                                        attributeLimitList, 
                                        defaultValueList, 
                                        characListList,
                                        customCharacListList)
    
        def CMDBDeleteAttribute(self, classNameId, attributeName, deleteOption):
            self.logger.debug('enter CMDBDeleteAttribute...')
            return self.AROSDeleteAttribute(classNameId, attributeName, deleteOption)
        
        def CMDBDeleteClass(self, classNameId,  deleteOption):
            self.logger.debug('enter CMDBDeleteClass...')
            return self.AROSDeleteClass(classNameId,  deleteOption)
    
        def CMDBDeleteInstance(self,classNameId,  instanceId, deleteOption):
            self.logger.debug('enter CMDBDeleteInstance...')
            return self.AROSDeleteInstance(classNameId,  instanceId, deleteOption)
    
        def CMDBEndBulkEntryTransaction(self,
                                        actionType):
            self.logger.debug('enter CMDBEndBulkEntryTransaction...')
            return self.AROSEndBulkEntryTransaction(actionType)
    
        def CMDBExport(self, exportItemList, exportFormat, directoryPath):
            self.logger.debug('enter CMDBExport...')
            return self.AROSExport(exportItemList, exportFormat, directoryPath)
    
        def CMDBImport(self, importItemList, directoryPath):
            self.logger.debug('enter CMDBImport...')
            return self.AROSImport(importItemList, directoryPath)
            
        def CMDBGetAttribute(self, classNameId, attributeName):
            self.logger.debug('enter CMDBGetAttribute...')
            return self.AROSGetAttribute(classNameId, attributeName)
    
        def CMDBGetClass(self, classNameId):
            self.logger.debug('enter CMDBGetClass...')
            return self.AROSGetClass(classNameId)
            
        def CMDBGetInstanceBLOB(self, classNameId, instanceId, attributeName, loc):
            self.logger.debug('enter CMDBGetInstanceBLOB...')
            return self.AROSGetInstanceBLOB(classNameId, instanceId, attributeName, loc)
        
        def CMDBGetInstance(self, classNameId, 
                            instanceId, 
                            attributeGetList):
            self.logger.debug('enter CMDBGetInstance...')
            return self.AROSGetInstance(classNameId, 
                                        instanceId, 
                                        attributeGetList)
    
        def CMDBGetListClass(self, namespaceName = ccmdb.BMC_namespace,
                             classNameIdRelation = None,
                             superclassName = None,
                             characQueryList = None,
                             getHiddenClasses = False):
            '''CMDBGetListClass retrieves information about classes that are 
related to this class or derived from this class.

Input: (optional) namespaceName (ARNameType, default = ccmdb.BMC_namespace),
       (optional) classNameIdRelation (CMDBClassNameId, default = None),
       (optional) superclassName (CMDBClassNameId, default = None),
       (optional) characQueryList (ARPropList, default = None),
       (optional) getHiddenClasses (ARBoolean, default = False)
Output: classNameIdList (AROSClassNameIdList) or None in case of failure'''            
            self.logger.debug('enter CMDBGetListClass...')
            return self.AROSGetListClass(namespaceName,
                                         classNameIdRelation,
                                         superclassName,
                                         characQueryList,
                                         getHiddenClasses)
    
        def CMDBGetListInstance(self, classNameId,
                                qualifier = None,
                                attributeGetList = None,
                                sortList = None,
                                firstRetrieve = ccmdb.AROS_START_WITH_FIRST_INSTANCE,
                                maxRetrieve = ccmdb.AROS_NO_MAX_LIST_RETRIEVE):
            self.logger.debug('enter CMDBGetListInstance...')
            return self.AROSGetListInstance(classNameId,
                                            qualifier,
                                            attributeGetList,
                                            sortList,
                                            firstRetrieve,
                                            maxRetrieve)
    
        def CMDBGetMultipleAttribute(self, classNameId, 
                                     getHiddenAttrs = ccmdb.ARBoolean(True), 
                                     getDerivedAttrs = ccmdb.ARBoolean(True),
                                     nameList = None,
                                     attrCharacQueryList = None):
            self.logger.debug('enter CMDBGetMultipleAttribute...')
            return self.AROSGetMultipleAttribute(classNameId, 
                                     getHiddenAttrs,
                                     getDerivedAttrs,
                                     nameList,
                                     attrCharacQueryList)
    
        def CMDBGetMultipleInstances(self, classNameId, 
                                     instanceIds, 
                                     attributeGetList):
            self.logger.debug('enter CMDBGetMultipleInstances...')
            return self.AROSGetMultipleInstances(classNameId, 
                                                 instanceIds, 
                                                 attributeGetList)
    
        def CMDBGetServerPort(self):
            self.logger.debug('enter CMDBGetServerPort...')
            return self.AROSGetServerPort()
    
        def CMDBGraphQuery(self,
                           startClassNameId,
                           startExtensionId,
                           startInstanceId, 
                           numLevels = -1,
                           direction = ccmdb.AROS_RELATIONSHIP_DIRECTION_OUT,
                           noMatchProceed = 1, 
                           onMatchProceed = 1, 
                           queryGraph = None):
            self.logger.debug('enter CMDBGraphQuery...')
            return self.AROSGraphQuery(startClassNameId,
                                       startExtensionId,
                                       startInstanceId, 
                                       numLevels,
                                       direction,
                                       noMatchProceed,
                                       onMatchProceed,
                                       queryGraph)
    
        def CMDBInitialization (self):
            self.logger.debug('enter CMDBInitialization...')
            return self.AROSInitialization()
    
        def CMDBSetAttribute(self, classNameId,
                             attributeName,
                             newAttributeName,
                             entryMode, 
                             attributeLimit,
                             defaultValue,
                             characList,
                             customCharacList):
            self.logger.debug('enter CMDBSetAttribute...')
            return self.AROSSetAttribute(classNameId,
                             attributeName,
                             newAttributeName,
                             entryMode, 
                             attributeLimit,
                             defaultValue,
                             characList,
                             customCharacList)
    
        def CMDBSetClass(self, classNameId, 
                             newClassNameId, 
                             classTypeInfo, 
                             indexList, 
                             characList, 
                             customCharacList):
            self.logger.debug('enter CMDBSetClass...')
            return self.AROSSetClass(classNameId, 
                             newClassNameId, 
                             classTypeInfo, 
                             indexList, 
                             characList, 
                             customCharacList)
    
        def CMDBSetInstance(self,classNameId, 
                            instanceId,
                            attributeValueList):
            self.logger.debug('enter CMDBSetInstance...')
            return self.AROSSetInstance(classNameId, 
                            instanceId,
                            attributeValueList)
    
        def CMDBSetMultipleAttribute(self, classNameId,
                                     attributeNameList,
                                     newAttributeNameList,
                                     entryModeList,
                                     attributeLimitList,
                                     defaultValueList, 
                                     characListList,
                                     customCharacListList):
            self.logger.debug('enter CMDBSetMultipleAttribute...')
            return self.AROSSetMultipleAttribute(classNameId,
                                     attributeNameList,
                                     newAttributeNameList,
                                     entryModeList,
                                     attributeLimitList,
                                     defaultValueList, 
                                     characListList,
                                     customCharacListList)
    
        def CMDBSetServerPort(self, tcpPort = 0, 
                              rpcPort = 0):
            self.logger.debug('enter CMDBSetServerPort...')
            return self.AROSSetServerPort(tcpPort, rpcPort)
    
        def CMDBSynchMetaData(self, pendingId):
            self.logger.debug('enter CMDBSynchMetaData...')
            return self.AROSSynchMetaData(pendingId)
    
        def CMDBSystemInit(self):
            self.logger.debug('enter CMDBSystemInit...')
            return self.AROSSystemInit()
    
        def CMDBTermination (self):
            self.logger.debug('enter CMDBTermination...')
            return self.AROSTermination()
        
        def CMDBUpgrade(self):
            self.logger.debug('enter CMDBUpgrade...')
            return self.AROSUpgrade()

    class AROS(AROS10):
        pass
    class CMDB(CMDB10):
        pass
    
if ccmdb.cmdbversion in ['cmdbapi63', 'cmdbapi20', 'cmdbapi21', 'cmdbapi75', 
                         'cmdbapi76']:
    class CMDBAttributeStruct(Structure):
        _fields_ = [("attributeName", ccmdb.ARNameType),
                     ("attributeId",  ccmdb.ARNameType),
                     ("dataType",  c_uint),
                     ("attributeType", c_uint),
                     ("baseClassNameId",  ccmdb.CMDBClassNameId),
                     ("arFieldId",  ccmdb.ARInternalId),
                     ("entryMode", c_uint),
                     ("attributeLimit", ccmdb.CMDBAttributeLimit),
                     ("defaultValue", ccmdb.ARValueStruct),
                     ("characList", ccmdb.ARPropList),
                     ("customCharacList", ccmdb.ARPropList)]
    
    class CMDBAttributeList(Structure):
        _fields_ = [("numItems", c_uint),
                     ("attributeList", POINTER(CMDBAttributeStruct))]

    class CMDB11(ARS):
        '''pythonic wrapper Class for Atrium C API, Version 1.1. starting with patch 002
CMDB API, using the true CMDB... function calls.'''
        def __init__(self, server='', user='', password='', language='', 
                   authString = '',
                   tcpport = 0,
                   rpcnumber = 0):
            '''Class constructor'''
            self.__version__ = "1.4.6"
            self.arversion = ""
            self.errstr = ''
            self.errnr = 0
            self.context = ccmdb.ARControlStruct()
            self.arsl = ccmdb.ARStatusList()
            self.logger = logging.getLogger() # 'pyars'
            hdlr = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
            hdlr.setFormatter(formatter)
            self.logger.addHandler(hdlr) 
            self.logger.setLevel(logging.INFO)
            # we need both api's loaded and stored in seperate variables, as 
            # we need access to the standard API functions in addition to the
            # CMDB functions!
            self.arapi = cars.arapi
            self.cmdbapi = ccmdb.cmdbapi # set in ccmdb
            self.arversion = cars.version
            self.cmdbversion = ccmdb.cmdbversion # set in ccmdb
            if server != '':
                self.Login(server, user, password)
    
        def Login (self,
                   server,
                   username,
                   password,
                   language='', 
                   authString = '',
                   tcpport = 0,
                   rpcnumber = 0):
            '''Login logs the user in on the specified server.
Input: server,
       username,
       password,
       language='', 
       authString = '',
       tcpport = 0,
       rpcnumber = 0
Output: errnr'''
    
            self.errnr = self.CMDBInitialization()
            if self.errnr > 1:
                self.logger.error('Login: error during Initialization of the Class Manager')
                pass
    
            # first use the normal login procedure
            ARS.Login(self, server, username, password,language, authString, 
                      tcpport, rpcnumber)
            if self.errnr > 1:
                self.logger.error('Login failed!') 
                return self.errnr
            
            if server.find(':') > -1:
                server,tcpport = server.split(':')
                tcpport = int(tcpport)
            
            self.logger.debug('calling CMDBSetServerPort with %d' % (tcpport))
            ret = self.CMDBSetServerPort(tcpport, rpcnumber)
            if ret > 1:
                self.logger.error('CMDBSetServerPort failed!') 
                pass            
            return self.errnr

        def Logoff (self):
            '''Logoff ends the session with the CMDB server.

Input: 
Output: errnr
'''
            self.logger.debug('enter Logoff...')
            if self.context:
                self.errnr = self.cmdbapi.CMDBTermination(byref(self.context),
                                                      byref(self.arsl))
            if self.errnr > 1:
                self.logger.error( "Logoff: failed")
            return self.errnr
    
        def CMDBBeginBulkEntryTransaction(self):
            '''CMDBBeginBulkEntryTransaction indicates that subsequent API 
calls are part of the bulk transaction. 

Any API calls that arrive after this function call are placed in a queue. Metadata
function calls are not part of the bulk transaction.
Input: 
Output: errnr'''
            self.logger.debug('enter CMDBBeginBulkEntryTransaction: ')
            self.errnr = self.cmdbapi.CMDBBeginBulkEntryTransaction(byref(self.context),
                                                                  byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('enter CMDBBeginBulkEntryTransaction failed!')
            return self.errnr
    
        def CMDBCreateAttribute(self, classNameId, 
                                attributeName,
                                attributeId,
                                dataType,
                                arFieldId = 0,
                                entryMode = ccmdb.CMDB_ATTR_ENTRYMODE_OPTIONAL,
                                attributeLimit = None,
                                defaultValue = None, 
                                characList = None,
                                customCharacList = None):
            '''CMDBCreateAttribute creates a new attribute with the indicated 
name for the specified class::

Input:  (CMDBClassNameId) classNameId, 
        (ARNameType) attributeName,
        (ARNameType) attributeId,
        (c_uint) dataType (should be one of CMDB_ATTR_DATA_TYPE_*),
        (ARInternalId) arFieldId (optional, default = 0),
        (c_uint) entryMode (optional, default = ccmdb.CMDB_ATTR_ENTRYMODE_OPTIONAL),
        (CMDBAttributeLimit) attributeLimit (optional, default = None),
        (ARValueStruct) defaultValue (optional, default = None), 
        (ARPropList) characList (optional, default = None),
        (ARPropList) customCharacList (optional, default = None)
Output: errnr
'''
            self.logger.debug('enter CMDBCreateAttribute...')
            self.errnr = self.cmdbapi.CMDBCreateAttribute(byref(self.context),
                                                        my_byref(classNameId),
                                                        attributeName,
                                                        attributeId,
                                                        dataType,
                                                        my_byref(arFieldId),
                                                        entryMode,
                                                        my_byref(attributeLimit),
                                                        my_byref(defaultValue),
                                                        my_byref(characList),
                                                        my_byref(customCharacList),
                                                        byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBCreateAttribute failed for %s:%s:%s' % (
                                   classNameId.namespaceName,
                                   classNameId.className,
                                   attributeName))
            return self.errnr
    
        def CMDBCreateClass (self, classNameId, 
                             classId, 
                             classTypeInfo = ccmdb.CMDB_CLASS_TYPE_REGULAR, 
                             superclassNameId = None, 
                             indexList = None, 
                             characList = None, 
                             customCharacList = None):
            '''CMDBCreateClass creates a class with core attributes in the 
Object form. 

The name of the form contains the prefix <namespace>:<classname>. The metadata 
is stored in the OBJSTR:Class form and the attribute information is stored in the
OBJSTR:AttributeDefinition form.
Input: (CMDBClassNameId) classNameId
       (ARNameType) classId (unique identifier for the class)
       (CMDBClassTypeInfo) classTypeInfo (optional, default = ccmdb.CMDB_CLASS_TYPE_REGULAR), 
       (CMDBClassNameId) superclassNameId (optional, default = None), 
       (CMDBIndexList) indexList (optional, default = None), 
       (ARPropList) characList (optional, default = None), 
       (ARPropList) customCharacList (optional, default = None)
Output: errnr'''
            self.logger.debug('enter CMDBCreateClass...')
            self.errnr = self.cmdbapi.CMDBCreateClass(byref(self.context),
                                                    my_byref(classNameId),
                                                    classId,
                                                    my_byref(classTypeInfo),
                                                    my_byref(superclassNameId),
                                                    my_byref(indexList),
                                                    my_byref(characList),
                                                    my_byref(customCharacList),
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBCreateClass failed for %s:%s' % (
                                                    classNameId.namespaceName,
                                                    classNameId.className))
            return self.errnr
    
        def CMDBCreateGuid(self):
            '''CMDBCreateGuid creates a GUID.
            
Input: 
Output: guid or None in case of failure'''
            self.logger.debug('enter CMDBCreateGuid...')
            guid = ccmdb.ARGuid()
            self.errnr = self.cmdbapi.CMDBCreateGuid(guid,
                                                     byref(self.arsl))
            if self.errnr < 2:
                return guid
            else:
                self.logger.error('CMDBCreateGuid failed!')
                return None
        
        def CMDBCreateInstance(self, classNameId, 
                               attributeValueList):
            '''CMDBCreateInstance creates a class or relationship instance in 
the Object form.

Input: classNameId
       attributeValueList
Output: instanceId (ARNameType) or None in case of failure'''
            self.logger.debug('enter CMDBCreateInstance...')
            instanceId = ccmdb.ARNameType()
            self.errnr = self.cmdbapi.CMDBCreateInstance(byref(self.context),
                                                         my_byref(classNameId),
                                                         my_byref(attributeValueList),
                                                         instanceId,
                                                         byref(self.arsl))
            if self.errnr < 2:
                return instanceId
            else:
                self.logger.error('CMDBCreateInstance failed for %s:%s' % (
                                                   classNameId.namespaceName,
                                                   classNameId.className))
                return None
                                                         
    
        def CMDBCreateMultipleAttribute(self, classNameId, 
                                        attributeNameList, 
                                        attributeIdList, 
                                        dataTypeList,
                                        arFieldIdList,
                                        entryModeList, 
                                        attributeLimitList, 
                                        defaultValueList, 
                                        characListList,
                                        customCharacListList):
            '''CMDBCreateMultipleAttribute creates multiple new attributes 
with the indicated name for the specified class.

CMDBClassNameId               classNameId,         /* IN: name of owning class */
ARNameList                    attributeNameList,   /* IN: name of the attribute */
ARNameList                    attributeIdList,     /* IN: Id of the attribute */
ARUnsignedIntList             dataTypeList,        /* IN: data type */
ARInternalIdList              arFieldIdList,       /* IN: AR field Id of attribute */
ARUnsignedIntList             entryModeList,       /* IN: entry mode */
CMDBAttributeLimitList        attributeLimitList,  /* IN: attribute limit */
ARValueList                   defaultValueList,    /* IN: default value */
ARPropListList                characListList,      /* IN: characteristics list */
ARPropListList                customCharacListList,/* IN: custom characteristics list */
Output: errnr'''
            self.logger.debug('enter CMDBCreateMultipleAttribute...')
            self.errnr = self.cmdbapi.CMDBCreateMultipleAttribute (byref(self.context),
                                               my_byref(classNameId),
                                               my_byref(attributeNameList),
                                               my_byref(attributeIdList),
                                               my_byref(dataTypeList),
                                               my_byref(arFieldIdList),
                                               my_byref(entryModeList),
                                               my_byref(attributeLimitList),
                                               my_byref(defaultValueList),
                                               my_byref(characListList),
                                               my_byref(customCharacListList),
                                               byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBCreateMultipleAttribute failed for %s:%s' % (
                                                    classNameId.namespaceName,
                                                    classNameId.className))
            return self.errnr
        
        def CMDBDeleteAttribute(self, classNameId, 
                                attributeName, 
                                deleteOption = ccmdb.AR_ATTRIBUTE_CLEAN_DELETE):
            '''CMDBDeleteAttribute deletes the attribute with the indicated ID. 

Depending on the value you specify for the deleteOption parameter, the 
attribute is deleted immediately and is not returned to users who request 
information about attributes.
Input: classNameId, 
       attributeName, 
       (optional) deleteOption (default  = ccmdb.AR_ATTRIBUTE_CLEAN_DELETE)
Output: errnr'''
            self.logger.debug('enter CMDBDeleteAttribute...')
            self.errnr = self.cmdbapi.CMDBDeleteAttribute(byref(self.context),
                                                    my_byref(classNameId),
                                                    attributeName,
                                                    deleteOption,
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBDeleteAttribute failed for %s:%s' % (
                                                    classNameId.namespaceName,
                                                    classNameId.className))
            return self.errnr
        
        def CMDBDeleteClass(self, classNameId, 
                            deleteOption = ccmdb.CMDB_DELETE_CLASS_OPTION_NONE):
            '''CMDBDeleteClass deletes the class.

It deletes the class with the indicated ID. Depending on the value you
specify for the deleteOption parameter, the class is deleted immediately
and is not returned to users who request information about classes.
Input: classNameId,
       (optional) deleteOption (default  = ccmdb.CMDB_DELETE_CLASS_OPTION_NONE)
Output: errnr'''
            self.logger.debug('enter CMDBDeleteClass...')
            self.errnr = self.cmdbapi.CMDBDeleteClass(byref(self.context),
                                                    my_byref(classNameId),
                                                    deleteOption,
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBDeleteClass failed for %s:%s' % (
                                                    classNameId.namespaceName,
                                                    classNameId.className))
            return self.errnr
    
        def CMDBDeleteInstance(self, classNameId,  
                               instanceId, 
                               deleteOption = ccmdb.CMDB_DERIVED_DELOPTION_NONE):
            '''CMDBDeleteInstance deletes the instance of the class.

Input: classNameId, 
       instanceId, 
       (optional) deleteOption (default = ccmdb.CMDB_DERIVED_DELOPTION_NONE)
Output: errnr'''
            self.logger.debug('enter CMDBDeleteInstance...')
            self.errnr = self.cmdbapi.CMDBDeleteInstance(byref(self.context),
                                                    my_byref(classNameId),
                                                    instanceId,
                                                    deleteOption,
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBDeleteInstance failed for %s:%s' % (
                                                   classNameId.namespaceName,
                                                   classNameId.className))
            return self.errnr        
    
        def CMDBEndBulkEntryTransaction(self,
                                        actionType = ccmdb.AR_BULK_ENTRY_ACTION_SEND):
            '''CMDBEndBulkEntryTransaction commits the bulk 
transaction, depending on the action type.

For an action type of SEND, the API call will be executed as part of the
transaction. For an action type of CANCEL, the transaction will be canceled.
Input: (optional) actionType (default = ccmdb.AR_BULK_ENTRY_ACTION_SEND)
Output: bulkEntryReturnList or None in case of failure'''
            self.logger.debug('enter CMDBEndBulkEntryTransaction...')
            bulkEntryReturnList = ccmdb.ARBulkEntryReturnList()
            self.errnr = self.cmdbapi.CMDBEndBulkEntryTransaction(byref(self.context),
                                                      actionType,
                                                      byref(bulkEntryReturnList),
                                                      byref(self.arsl))
            if self.errnr < 2:
                return bulkEntryReturnList
            else:
                self.logger.error('enter CMDBEndBulkEntryTransaction failed!')
                return None
    
        def CMDBExport(self, exportItemList, 
                       exportFormat, 
                       directoryPath):
            '''CMDBExport exports the indicated structure definitions from the specified server.

Input: exportItemList, 
        exportFormat, 
        directoryPath
Output: errnr'''
            self.logger.debug('enter CMDBExport...')
            self.errnr = self.cmdbapi.CMDBExport(byref(self.context),
                                               my_byref(exportItemList),
                                               exportFormat,
                                               directoryPath,
                                               byref(self.arsl))
            if self.errnr >1:
                self.logger.error('CMDBExport failed!')
            return self.errnr        
    
        def CMDBGetAttribute(self, classNameId, 
                             attributeName):
            '''CMDBGetAttribute retrieves a single attribute.
            
Input: classNameId, 
       attributeName    
Output: CMDBAttributeStruct (containing: attributeId, 
        dataType, 
        attributeType,
        baseClassNameId, 
        arFieldId, 
        entryMode, 
        attributeLimit, 
        defaultValue,
        characList, 
        customCharacList) or None in case of failure'''
            self.logger.debug('enter CMDBGetAttribute...')
            attributeId = ccmdb.ARNameType()
            dataType = c_uint()
            attributeType = c_uint()
            baseClassNameId = ccmdb.CMDBClassNameId()
            arFieldId = ccmdb.ARInternalId()
            entryMode = c_uint()
            attributeLimit = ccmdb.CMDBAttributeLimit()
            defaultValue = ccmdb.ARValueStruct()
            characList = ccmdb.ARPropList()
            customCharacList = ccmdb.ARPropList()        
            self.errnr = self.cmdbapi.CMDBGetAttribute(byref(self.context),
                                                       byref(classNameId),
                                                       attributeName,
                                                       attributeId,
                                                       byref(dataType),
                                                       byref(attributeType),
                                                       byref(baseClassNameId),
                                                       byref(arFieldId),
                                                       byref(entryMode),
                                                       byref(attributeLimit),
                                                       byref(defaultValue),
                                                       byref(characList),
                                                       byref(customCharacList),
                                                       byref(self.arsl))
            if self.errnr < 2:
                return CMDBAttributeStruct(attributeName, 
                                           attributeId.value, 
                                           dataType, 
                                           attributeType,
                                           baseClassNameId, 
                                           arFieldId, 
                                           entryMode, 
                                           attributeLimit, 
                                           defaultValue,
                                           characList, 
                                           customCharacList)
            else:
                self.logger.error('CMDBGetAttribute failed for %s:%s:%s' % (
                                    classNameId.namespaceName,
                                    classNameId.className,
                                    attributeName))
                return None
    
        def CMDBGetClass(self, classNameId, 
                         classId, 
                         classTypeInfo = None,
                         superclassNameId = None,
                         indexList = None,
                         characList = None,
                         customCharacList = None):
            '''CMDBGetClass retrieves the class information from the OBJSTR:Class form.
            
Input: (CMDBClassNameId)classNameId
       (ARNameType)classId 
       (CMDBClassTypeInfo)classTypeInfo (optional, default = None)
       (CMDBClassNameId)superclassNameId (optional, default = None)
       (CMDBIndexList)indexList (optional, default = None)
       (ARPropList)characList (optional, default = None)
       (ARPropList)customCharacList (optional, default = None)
Output: errnr'''
            self.logger.debug('enter CMDBGetClass...')
            self.errnr = self.cmdbapi.CMDBGetClass(byref(self.context),
                                                 my_byref(classNameId),
                                                 classId,
                                                 my_byref(classTypeInfo),
                                                 my_byref(superclassNameId),
                                                 my_byref(indexList),
                                                 my_byref(characList),
                                                 my_byref(customCharacList),
                                                 byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBGetClass failed for %s:%s' % (
                                                 classNameId.namespaceName,
                                                 classNameId.className))
            return self.errnr
            
        def CMDBGetInstance(self, classNameId, 
                            instanceId, 
                            attributeGetList = None):
            '''CMDBGetInstance retrieves information about the instance.
            
Input: (CMDBClassNameId) classNameId, 
       (ARNameType) instanceId, 
       (ARNameList) attributeGetList    
Output: CMDBAttributeValueList or None in case of failure'''
            self.logger.debug('enter CMDBGetInstance...')
            attributeValueList = ccmdb.CMDBAttributeValueList()
            self.errnr = self.cmdbapi.CMDBGetInstance(byref(self.context),
                                                      byref(classNameId),
                                                      instanceId,
                                                      my_byref(attributeGetList),
                                                      byref(attributeValueList),
                                                      byref(self.arsl))
            if self.errnr < 2:
                return attributeValueList
            else:
                self.logger.error('CMDBGetInstance failed for %s:%s' % (
                                                    classNameId.namespaceName,
                                                    classNameId.className))
                return None
    
        def CMDBGetInstanceBLOB(self, classNameId,
                                instanceId, 
                                attributeName, 
                                loc):
            '''CMDBGetInstanceBLOB retrieves the attachment.

It retrieves attachments, or binary large object (BLOB), stored for the
attachment field. The BLOB is placed in a file.
Input: (CMDBClassNameId) classNameId, 
       (ARNameType) instanceId, 
       attributeName
Output: loc (ARLocStruct) or None in case of failure'''
            self.logger.debug('enter CMDBGetInstanceBLOB...')
            loc = ccmdb.ARLocStruct()
            self.errnr = self.cmdbapi.CMDBGetInstanceBLOB(byref(self.context),
                                                     byref(classNameId),
                                                     instanceId,
                                                     attributeName,
                                                     byref(loc),
                                                     byref(self.arsl))
            if self.errnr < 2:
                return loc
            else:
                self.logger.error('CMDBGetInstanceBLOB failed for %s:%s' % (
                                                    classNameId.namespaceName,
                                                    classNameId.className))
                return None
        
        def CMDBGetListClass(self, namespaceName = ccmdb.BMC_namespace,
                             classNameIdRelation = None,
                             superclassName = None,
                             characQueryList = None,
                             getHiddenClasses = True):
            '''CMDBGetListClass retrieves information about classes that are 
related to this class or derived from this class.

Input: (optional) namespaceName (ARNameType, default = ccmdb.BMC_namespace),
       (optional) classNameIdRelation (CMDBClassNameId, default = None),
       (optional) superclassName (CMDBClassNameId, default = None),
       (optional) characQueryList (ARPropList, default = None),
       (optional) getHiddenClasses (ARBoolean, default = False)
Output: classNameIdList (CMDBClassNameIdList) or None in case of failure'''
            self.logger.debug('enter CMDBGetListClass...')
            classNameIdList = ccmdb.CMDBClassNameIdList()
            self.errnr = self.cmdbapi.CMDBGetListClass(byref(self.context),
                                                     namespaceName,
                                                     my_byref(classNameIdRelation),
                                                     my_byref(superclassName),
                                                     my_byref(characQueryList),
                                                     getHiddenClasses,
                                                     byref(classNameIdList),
                                                     byref(self.arsl))
            if self.errnr < 1:
                return classNameIdList
            else:
                self.logger.error('CMDBGetListClass failed for %s' % namespaceName)
                return None
    
        def CMDBGetListInstance(self, classNameId,
                                qualifier = None,
                                attributeGetList = None,
                                sortList = None,
                                firstRetrieve = ccmdb.CMDB_START_WITH_FIRST_INSTANCE,
                                maxRetrieve = ccmdb.CMDB_NO_MAX_LIST_RETRIEVE):
            '''CMDBGetListInstance retrieves a list of instances. You can limit 
the list to entries that match particular conditions by specifying the qualifier 
parameter.

Input: (CMDBClassNameId) classNameId,
       (CMDBQualifierStruct) qualifier (optional, default = None),
       (ARNameList) attributeGetList (optional, default = None),
       (CMDBSortList) sortList (optional, default = None),
       (c_uint) firstRetrieve (optional, default = ccmdb.CMDB_START_WITH_FIRST_INSTANCE),
       (c_uint) maxRetrieve (optional, default = ccmdb.CMDB_NO_MAX_LIST_RETRIEVE) 
Output: (instanceIdList [ARNameList], 
         attrValueListList [CMDBAttributeValueListList], 
         numMatches [int]) or None in case of failure'''
            self.logger.debug('enter CMDBGetListInstance...')
            if qualifier is None:
                qualifier = ccmdb.CMDBQualifierStruct()
            instanceIdList = ccmdb.ARNameList()
            attrValueListList = ccmdb.CMDBAttributeValueListList()
            numMatches = c_uint()
            self.errnr = self.cmdbapi.CMDBGetListInstance(byref(self.context),
                                                        my_byref(classNameId),
                                                        byref(qualifier),
                                                        my_byref(attributeGetList),
                                                        my_byref(sortList),
                                                        firstRetrieve,
                                                        maxRetrieve,
                                                        byref(instanceIdList),
                                                        byref(attrValueListList),
                                                        byref(numMatches),
                                                        byref(self.arsl))
            if self.errnr < 2:
                return (instanceIdList, attrValueListList, numMatches.value)
            else:
                self.logger.error('CMDBGetListInstance failed for %s:%s' % (
                                                    classNameId.namespaceName,
                                                    classNameId.className))
                return None
    
        def CMDBGetMultipleAttribute(self, classNameId, 
                                     getHiddenAttrs = ccmdb.ARBoolean(True), 
                                     getDerivedAttrs = ccmdb.ARBoolean(True),
                                     nameList = None,
                                     attrCharacQueryList = None):
            '''CMDBGetMultipleAttribute retrieves multiple attributes.

Input: (CMDBClassNameId) classNameId 
       (optional) getHiddenAttrs (ARBoolean, default = ccmdb.ARBoolean('\1')), 
       (optional) getDerivedAttrs (ARBoolean, default = ccmdb.ARBoolean('\1')),
       (optional) nameList (ARNameList, default = None),
       (optional) attrCharacQueryList (ARPropList, default = None)  
Output: CMDBAttributeList or None in case of failure'''
            self.logger.debug('enter CMDBGetMultipleAttribute...')
            existList = ccmdb.ARBooleanList()
            attributeNameList = ccmdb.ARNameList()
            attributeIdList = ccmdb.ARNameList()
            dataTypeList = ccmdb.ARUnsignedIntList()
            attributeTypeList = ccmdb.ARUnsignedIntList()
            baseClassNameIdList = ccmdb.CMDBClassNameIdList()
            arFieldIdList = ccmdb.ARInternalIdList()
            entryModeList = ccmdb.ARUnsignedIntList()
            attributeLimitList = ccmdb.CMDBAttributeLimitList()
            defaultValueList = ccmdb.ARValueList()
            characListList = ccmdb.ARPropListList()
            customCharacListList = ccmdb.ARPropListList()
            self.errnr = self.cmdbapi.CMDBGetMultipleAttribute(byref(self.context),
                                                   my_byref(classNameId),
                                                   getHiddenAttrs,
                                                   getDerivedAttrs,
                                                   my_byref(nameList),
                                                   my_byref(attrCharacQueryList),
                                                   byref(existList),
                                                   byref(attributeNameList),
                                                   byref(attributeIdList),
                                                   byref(dataTypeList),
                                                   byref(attributeTypeList),
                                                   byref(baseClassNameIdList),
                                                   byref(arFieldIdList),
                                                   byref(entryModeList),
                                                   byref(attributeLimitList),
                                                   byref(defaultValueList),
                                                   byref(characListList),
                                                   byref(customCharacListList),
                                                   byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBGetMultipleAttribute: failed for %s:%s' % (
                                                      classNameId.namespaceName,
                                                      classNameId.className))
                return None
            else:
                tempArray = (CMDBAttributeStruct * existList.numItems)()
                for i in range(existList.numItems):
                    if existList.booleanList[i]:
                        tempArray[i].attributeName = attributeNameList.nameList[i].value
                        if attributeIdList: tempArray[i].attributeId = attributeIdList.nameList[i].value
                        if dataTypeList: tempArray[i].dataType = dataTypeList.intList[i]
                        if attributeTypeList: tempArray[i].attributeType = attributeTypeList.intList[i]
                        if baseClassNameIdList: tempArray[i].baseClassNameId = baseClassNameIdList.classNameIdList[i]
                        if arFieldIdList: tempArray[i].arFieldId = arFieldIdList.internalIdList[i]
                        if entryModeList: tempArray[i].entryMode = entryModeList.intList[i]
                        if attributeLimitList: tempArray[i].attributeLimit = attributeLimitList.limitList[i]
                        if defaultValueList: tempArray[i].defaultValue = defaultValueList.valueList[i]
                        if characListList: tempArray[i].characList = characListList.propsList[i]
                        if customCharacListList: tempArray[i].customCharacList = customCharacListList.propsList[i]
                return CMDBAttributeList (existList.numItems, tempArray)
    
        def CMDBGetMultipleInstances(self, classNameId, 
                                     instanceIds = None, 
                                     attributeGetList = None):
            '''CMDBGetMultipleInstances retrieves multiple instances.
            
Input: classNameId (CMDBClassNameId) 
       (optional) instanceIds (ARNameList, default = None -- but don't expect results then)
       (optional) attributeGetList (ARNameList, default = None, all attributes)
Output: (existList, attrValueListList) or None in case of failure'''
            self.logger.debug('enter CMDBGetMultipleInstances...')
            existList = ccmdb.ARBooleanList()
            attrValueListList = ccmdb.CMDBAttributeValueListList()
            self.errnr = self.cmdbapi.CMDBGetMultipleInstances(byref(self.context),
                                                       my_byref(classNameId),
                                                       my_byref(instanceIds),
                                                       my_byref(attributeGetList),
                                                       byref(existList), 
                                                       byref(attrValueListList),
                                                       byref(self.arsl))
            if self.errnr < 2:
                return (existList, attrValueListList)
            else:
                self.logger.error('CMDBGetMultipleInstances failed for %s:%s' % (
                                                 classNameId.namespaceName,
                                                 classNameId.className))
                return None           
    
        def CMDBGetServerPort(self):
            '''CMDBGetServerPort retrieves information about the server port.

Input:
Output: (tcpPort, rpcPort) or None in case of failure'''
            self.logger.debug('enter CMDBGetServerPort...')
            tcpPort = c_int()
            rpcPort = c_int()
            self.errnr = self.cmdbapi.CMDBGetServerPort(byref(self.context),
                                                    byref(tcpPort),
                                                    byref(rpcPort),
                                                    byref(self.arsl)                                                   )
            if self.errnr < 2:
                return (tcpPort.value, rpcPort.value)
            else:
                self.logger.error('CMDBGetServerPort failed')
                return None    
    
        def CMDBGraphQuery(self,
                           startClassNameId,
                           startExtensionId,
                           startInstanceId, 
                           numLevels = -1,
                           direction = ccmdb.CMDB_RELATIONSHIP_DIRECTION_OUT,
                           noMatchProceed = 1, 
                           onMatchProceed = 1, 
                           queryGraph = None):
            '''CMDBGraphQuery searches related instances.

Input: startClassNameId,
       startExtensionId,
       startInstanceId, 
       (optional) numLevels = -1,
       (optional) direction = ccmdb.CMDB_RELATIONSHIP_DIRECTION_OUT,
       (optional) noMatchProceed = 1, 
       (optional) onMatchProceed = 1, 
       (optional) queryGraph = None
Output: (CMDBGetObjectList, CMDBGetRelationList) or None in case of failure'''
            self.logger.debug('enter CMDBGraphQuery...')
            objects = ccmdb.CMDBGetObjectList()
            relations = ccmdb.CMDBGetRelationList()
            self.errnr = self.cmdbapi.CMDBGraphQuery(byref(self.context),
                                                      byref(startClassNameId),
                                                      startExtensionId,
                                                      startInstanceId,
                                                      numLevels,
                                                      direction,
                                                      noMatchProceed,
                                                      onMatchProceed,
                                                      my_byref(queryGraph),
                                                      byref(objects),
                                                      byref(relations),
                                                      byref(self.arsl))
            if self.errnr < 2:
                return (objects, relations)
            else:
                self.logger.error('CMDBGraphQuery failed for %s:%s' % (
                                               startClassNameId.namespaceName,
                                               startClassNameId.className))
                return None
    
        def CMDBImport(self, importItemList, directoryPath):
            '''CMDBImport imports the indicated structure definitions to the specified server. Use this
function to copy structure definitions from one server to another.

Input: importItemList
       directoryPath
Output: errnr'''
            self.logger.debug('enter CMDBImport...')
            self.errnr = self.cmdbapi.CMDBImport(byref(self.context),
                                               my_byref(importItemList),
                                               directoryPath,
                                               byref(self.arsl))
            if self.errnr >1:
                self.logger.error('CMDBImport failed!')
            return self.errnr   
            
        def CMDBInitialization (self):
            '''CMDBInitialization initializes the C API session. 

This function must be called before any C API calls are made.
Input:
Output: errnr'''

            self.logger.debug('enter CMDBInitialization...')
            self.errnr =  self.cmdbapi.CMDBInitialization(byref(self.context),
                                                          byref(self.arsl))
            if self.errnr > 1:
                self.logger.error( "CMDBInitialization: failed")
            return self.errnr
    
        def CMDBSetAttribute(self, classNameId,
                             attributeName,
                             newAttributeName,
                             entryMode, 
                             attributeLimit,
                             defaultValue,
                             characList,
                             customCharacList):
            '''CMDBSetAttribute sets an attribute with the specified name for 
the specified class.

Input: classNameId,
     attributeName,
     newAttributeName,
     entryMode, 
     attributeLimit,
     defaultValue,
     characList,
     customCharacList
Output: errnr'''
            self.logger.debug('enter CMDBSetAttribute...')
            self.errnr = self.cmdbapi.CMDBSetAttribute(byref(self.context),
                                                    my_byref(classNameId),
                                                    attributeName,
                                                    newAttributeName,
                                                    my_byref(entryMode),
                                                    my_byref(attributeLimit),
                                                    my_byref(defaultValue),
                                                    my_byref(characList),
                                                    my_byref(customCharacList),
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBSetAttribute failed for %s:%s/%s' % (
                                                classNameId.namespaceName,
                                                classNameId.className,
                                                attributeName))
            return self.errnr
    
        def CMDBSetClass(self, classNameId, 
                             newClassNameId, 
                             classTypeInfo, 
                             indexList, 
                             characList, 
                             customCharacList):
            '''CMDBSetClass sets the class properties in the OBJSTR:Class form. 

After you create a class,
you cannot modify the following properties: classId, classType (regular,
relationship), and persistence provider.
CMDBClassNameId               classNameId,         /* IN: name of the class */
CMDBClassNameId               newClassNameId,      /* IN: new name of the class */
CMDBClassTypeInfo             classTypeInfo,       /* IN: info on the class type */
CMDBIndexList                 indexList,           /* IN; list of indexes defined for the class */
ARPropList                    characList,          /* IN: class characteristics */
ARPropList                    customCharacList,    /* IN: custom class characteristics */
Output: errnr'''
            self.logger.debug('enter CMDBSetClass...')
            self.errnr = self.cmdbapi.CMDBSetClass(byref(self.context),
                                                    my_byref(classNameId),
                                                    my_byref(newClassNameId),
                                                    my_byref(classTypeInfo),
                                                    my_byref(indexList),
                                                    my_byref(characList),
                                                    my_byref(customCharacList),
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBSetClass failed for %s:%s' % (
                                                     classNameId.namespaceName,
                                                     classNameId.className))
            return self.errnr
    
        def CMDBSetInstance(self, classNameId, 
                            instanceId,
                            attributeValueList):
            '''CMDBSetInstance Sets a CI or relationship instance in the OBJSTR:Class.

CMDBClassNameId               classNameId,         /* IN: class name */
ARNameType                    instanceId,          /* IN: instance Id */
CMDBAttributeValueList        attributeValueList,  /* IN: list of attributeId/value pairs for instance */
Output: errnr'''
            self.logger.debug('enter CMDBSetInstance...')
            self.errnr = self.cmdbapi.CMDBSetInstance(byref(self.context),
                                                      my_byref(classNameId),
                                                      instanceId,
                                                      my_byref(attributeValueList),
                                                      byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBSetInstance failed for %s:%s' % (classNameId.namespaceName,
                                                                        classNameId.className))
            return self.errnr
        
        def CMDBSetMultipleAttribute(self, classNameId,
                                     attributeNameList,
                                     newAttributeNameList,
                                     entryModeList,
                                     attributeLimitList,
                                     defaultValueList, 
                                     characListList,
                                     customCharacListList):
            '''CMDBSetMultipleAttribute sets multiple attributes with the 
specified names for the specified class.

CMDBClassNameId               classNameId,         /* IN: name of owning class */
ARNameList                    attributeNameList,   /* IN: name of the attribute */
ARNameList                    newAttributeNameList,/* IN: new name of the attribute */
ARUnsignedIntList             entryModeList,       /* IN: entry mode */
CMDBAttributeLimitList        attributeLimitList,  /* IN: attribute limit */
ARValueList                   defaultValueList,    /* IN: default value */
ARPropListList                characListList,      /* IN: characteristics list */
ARPropListList                customCharacListList,/* IN: custom characteristics list */
Output: errnr'''
            self.logger.debug('enter CMDBSetMultipleAttribute...')
            self.errnr = self.cmdbapi.CMDBSetMultipleAttribute(byref(self.context),
                                               my_byref(classNameId),
                                               my_byref(attributeNameList),
                                               my_byref(newAttributeNameList),
                                               my_byref(entryModeList),
                                               my_byref(entryModeList),
                                               my_byref(attributeLimitList),
                                               my_byref(defaultValueList),
                                               my_byref(characListList),
                                               my_byref(customCharacListList),
                                               byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBSetMultipleAttribute failed for %s:%s' % (
                                                     classNameId.namespaceName,
                                                     classNameId.className))
            return self.errnr
    
        def CMDBSetServerPort(self, tcpPort = 0, 
                            rpcPort = 0):
            '''CMDBSetServerPort sets the specified server port.

Input: (optional) tcpPort (default: 0)
       (optional) rpcPort (default: 0)
Output: errnr'''
            self.logger.debug('enter CMDBSetServerPort...')
            # convert parameters to ctypes transparently
            ctcpPort = c_int(tcpPort)
            crpcPort = c_int(rpcPort)
            self.errnr = self.cmdbapi.CMDBSetServerPort(byref(self.context),
                                                    my_byref(ctcpPort),
                                                    my_byref(crpcPort),
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBSetServerPort: failed')
            return self.errnr
    
        def CMDBSynchMetaData(self, pendingId):
            '''CMDBSynchMetaData syncs a specific pending change entry.

Input: pendingId
Output: CMDBClassNameIdList or None in case of failure'''
            self.logger.debug('enter CMDBSynchMetaData...')
            classNameIdList = ccmdb.CMDBClassNameIdList()
            self.errnr = self.cmdbapi.CMDBSynchMetaData(byref(self.context),
                                                      pendingId,
                                                      byref(classNameIdList),
                                                      byref(self.arsl))
            if self.errnr < 2:
                return classNameIdList
            else:
                self.logger.error('CMDBSynchMetaData failed for %s' % pendingId)
                return None    
    
        def CMDBSystemInit(self):
            '''CMDBSystemInit performs server- and network-specific 
initialization operations for internal use by BMC.

Input:
Output: propList or None in case of failure'''
            self.logger.debug('enter CMDBSystemInit...')
            propList = ccmdb.ARPropList()
            self.errnr = self.cmdbapi.CMDBSystemInit(byref(propList),
                                                     byref(self.arsl))
            if self.errnr < 2:
                return propList 
            else:
                self.logger.error('enter CMDBSystemInit failed!')
                return None
    
        def CMDBTermination (self):
            '''CMDBTermination performs environment-specific cleanup routines.
            
It disconnects from the
specified session. All API programs that interact with the C API session
should call this function upon completing work in a given session.
Input:
Output: errnr'''
            self.logger.debug('enter CMDBTermination...')
            # this function is used during the load phase of cmdb/cmdb api
            # to identify which version of the DLL is used: the one with cmdb prefixes
            # or with the cmdb prefixes
            # during loading, we don't have a context yet, therefore we need to use
            # my_byref...
            self.errnr = self.cmdbapi.CMDBTermination(my_byref(self.context),
                                                      byref(self.arsl))
            self.context = None
            return self.errnr
        
        def CMDBUpgrade(self):
            '''CMDBUpgrade - no documentation available

Input:
Output: errnr'''
            self.logger.debug('enter CMDBUpgrade...')
            self.errnr = self.cmdbapi.CMDBUpgrade(byref(self.context),
                                                  byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('enter CMDBUpgrade failed!')
            return self.errnr 

    class CMDB(CMDB11):
        pass

if ccmdb.cmdbversion in ['cmdbapi20', 'cmdbapi21', 'cmdbapi75', 'cmdbapi76']:
             
    class CMDB20(CMDB11):
        '''pythonic wrapper Class for Atrium C API, Version 2.0'''
        
        def CMDBActivateFederatedInContext(self, classNameId,
                                           datasetId,
                                           instanceId,
                                           federatedInstanceId,
                                           activateOption):
            '''CMDBActivateFederatedInContext expands the FederatedInterface instance
for a specific CI and federated interface. 

Depending on a flag you specific when you call this function, your
federated instance might either be expanded or expanded and launched.
CMDBClassNameId            classNameId, /* IN: class name of the instance in context */
ARNameType                 datasetId,   /* IN: dataset Id */
ARNameType                 instanceId,  /* IN: instance id of the instance context */
ARNameType                 federatedInstanceId,/* IN: instance Id of the federation data to be launched */
unsigned int               activateOption,/* IN: CMDB_FEDERATION_ACTIVATION_XXX */
Output:
CMDBFederatedActivateInfo  federatedInfo,/* OUT: only filled in if "expandOnly" flag is true */
or None in case of failure'''
            self.logger.debug('enter CMDBActivateFederatedInContext...')
            federatedInfo = ccmdb.CMDBFederatedActivateInfo()
            self.errnr = self.cmdbapi.CMDBActivateFederatedInContext(byref(self.context),
                                                    my_byref(classNameId),
                                                    datasetId,
                                                    instanceId,
                                                    federatedInstanceId,
                                                    activateOption,
                                                    byref(federatedInfo),
                                                    byref(self.arsl))
            if self.errnr < 2:
                return federatedInfo
            else:
                self.logger.error('CMDBFederatedActivateInfo failed for %s:%s' % (
                                                 classNameId.namespaceName,
                                                 classNameId.className))
                return None
        
        def CMDBCreateClass (self, classNameId, 
                             classId, 
                             classTypeInfo = ccmdb.CMDB_CLASS_TYPE_REGULAR, 
                             superclassNameId = None, 
                             auditInfo = None,
                             indexList = None, 
                             characList = None, 
                             customCharacList = None):
            '''CMDBCreateClass creates a class with core attributes in the Object form. 

The name of the form contains the prefix <namespace>:<classname>. The metadata 
is stored in the OBJSTR:Class form and the attribute information is stored in 
the OBJSTR:AttributeDefinition form.
CMDBClassNameId               classNameId,         /* IN: name of the class */
ARNameType                    classId,             /* IN: class Id */
CMDBClassTypeInfo             classTypeInfo,       /* IN: info on the class type */
CMDBClassNameId               superclassNameId,    /* IN: name of superclass */
CMDBIndexList                 indexList,           /* IN; list of indexes defined for the class */
CMDBAuditInfoStruct           auditInfo,           /* IN; audit info for the class */
ARPropList                    characList,          /* IN: class characteristics */
ARPropList                    customCharacList,    /* IN: custom class characteristics */
Output: errnr'''
            self.logger.debug('enter CMDBCreateClass...')
            self.errnr = self.cmdbapi.CMDBCreateClass(byref(self.context),
                                                    my_byref(classNameId),
                                                    classId,
                                                    my_byref(classTypeInfo),
                                                    my_byref(superclassNameId),
                                                    my_byref(indexList),
                                                    my_byref(auditInfo),
                                                    my_byref(characList),
                                                    my_byref(customCharacList),
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBCreateClass failed for %s:%s' % (
                                                 classNameId.namespaceName,
                                                 classNameId.className))
            return self.errnr

        def CMDBCreateInstance(self, classNameId,
                               datasetId,
                               attributeValueList):
            '''CMDBCreateInstance creates a class or relationship instance in the Object form.

CMDBClassNameId               classNameId,         /* IN: name of the class */
ARNameType                    datasetId,           /* IN: dataset Id */
CMDBAttributeValueList        attributeValueList,  /* IN: list of attributeId/value pairs for instance */
Output: instanceId (ARNameType) or None in case of failure'''
            self.logger.debug('enter CMDBCreateInstance...')
            instanceId = ccmdb.ARNameType()
            self.errnr = self.cmdbapi.CMDBCreateInstance(byref(self.context),
                                                         my_byref(classNameId),
                                                         datasetId,
                                                         my_byref(attributeValueList),
                                                         instanceId,
                                                         byref(self.arsl))
            if self.errnr < 2:
                return instanceId
            else:
                self.logger.error('CMDBCreateInstance failed for %s:%s' % (
                                                 classNameId.namespaceName,
                                                 classNameId.className))
                return None

        def CMDBDeleteInstance(self, classNameId,
                               datasetId,
                               instanceId, 
                               deleteOption = ccmdb.CMDB_DERIVED_DELOPTION_NONE):
            '''CMDBDeleteInstance deletes the instance of the class.

CMDBClassNameId               classNameId,         /* IN: name of the class */
ARNameType                    datasetId,           /* IN: dataset Id */
ARNameType                    instanceId,          /* IN: instance Id */
unsigned int                  deleteOption,        /* default = ccmdb.CMDB_DERIVED_DELOPTION_NONE) */
Output: errnr'''
            self.logger.debug('enter CMDBDeleteInstance...')
            self.errnr = self.cmdbapi.CMDBDeleteInstance(byref(self.context),
                                                    my_byref(classNameId),
                                                    datasetId,
                                                    instanceId,
                                                    deleteOption,
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBDeleteInstance failed for %s:%s' % (
                                                 classNameId.namespaceName,
                                                 classNameId.className))
            return self.errnr        

        def  CMDBExpandParametersForCI(self, paramString,
                                       attValueList):
            '''CMDBExpandParametersForCI accepts an unexpanded string.
            
This string contains parameters and substitutes
values from the attribute value list provided in the CMDBAttributeValueList
structure.
Input: paramString,        /* IN: string containing parameters */
       attValueList,       /* IN: attribute value list */
Output: expandedStr or None in case of failure'''
            
            self.logger.debug('enter CMDBExpandParametersForCI...')
            expandedStr = c_char_p()
            self.errnr = self.cmdbapi.CMDBExpandParametersForCI(byref(self.context),
                                                    paramString,
                                                    my_byref(attValueList),
                                                    expandedStr,
                                                    byref(self.arsl))
            if self.errnr < 2:
                return expandedStr
            else:
                self.logger.error('CMDBExpandParametersForCI failed')
                return None

        def CMDBGetClass(self, classNameId,
                         classId, 
                         classTypeInfo = None,
                         superclassNameId = None,
                         indexList = None,
                         auditInfo = None,
                         characList = None,
                         customCharacList = None):
            '''CMDBGetClass retrieves the class information from the OBJSTR:Class form.

Input: classNameId (CMDBClassNameID)
       (ARNameType) classId
       (CMDBClassTypeInfo)classTypeInfo (optional,d efault = None)
       (CMDBClassNameId)superclassNameId (optional,d efault = None)
       (CMDBIndexList)indexList (optional,d efault = None)
       (CMDBAuditInfoStruct)auditInfo (optional,d efault = None)
       (ARPropList) characList (optional,d efault = None)
       (ARPropList) customCharacList (optional,d efault = None)
Output: errnr'''
            self.logger.debug('enter CMDBGetClass...')
            self.errnr = self.cmdbapi.CMDBGetClass(byref(self.context),
                                                 my_byref(classNameId),
                                                 byref(classId),
                                                 my_byref(classTypeInfo),
                                                 my_byref(superclassNameId),
                                                 my_byref(indexList),
                                                 my_byref(auditInfo),
                                                 my_byref(characList),
                                                 my_byref(customCharacList),
                                                 byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBGetClass failed for %s:%s' % (
                                                 classNameId.namespaceName,
                                                 classNameId.className))
            return self.errnr

        def CMDBGetCMDBUIComponents(self,inputInfo,
                                    datasetId,
                                    instanceId):
            '''CMDBGetCMDBUIComponents retrieves a list of various UI components 
for a specified class.

Input: inputInfo,          /* IN: input args to qualify the component to retrieve */
        datasetId,           /* IN: dataset Id */
        instanceId,          /* IN: given the CI, load appropriate UI components */
Output: CMDBUIComponentResultList or None in case of failure'''
            self.logger.debug('enter CMDBGetCMDBUIComponents...')
            outputInfo = cars.CMDBUIComponentResultList()
            self.errnr = self.cmdbapi.CMDBGetCMDBUIComponents(byref(self.context),
                                                   my_byref(inputInfo),
                                                   datasetId,
                                                   instanceId,
                                                   byref(outputInfo),
                                                   byref(self.arsl))
            if self.errnr < 2:
                return outputInfo
            else:
                self.logger.error('CMDBGetCMDBUIComponents failed')
                return None

        def CMDBGetCopyAuditData(self, classNameId,
                                 datasetId,
                                 instanceId,
                                 auditTimestamp = None,
                                 qualifier = None,
                                 attributeGetList = None,
                                 sortList = None,
                                 firstRetrieve = cars.AR_START_WITH_FIRST_ENTRY,
                                 maxRetrieve = cars.AR_NO_MAX_LIST_RETRIEVE):
            '''CMDBGetCopyAuditData retrieves a copy of the specified CI.

It retrieves a copy of the specified CI instance if the attribute data for the
instance is modified. The audit option must be set for the attribute's
characteristic to get the audit data.
Input: classNameId,         /* IN: class name */
       datasetId,           /* IN: dataset Id */
       instanceId,          /* IN: instance id  */
       auditTimestamp,      /* IN: modified after this timestamp  */
       qualifier,           /* IN: qualifier to get the subset of list */
       attributeGetList,    /* IN: attribute namelist of which to retrieve values */
       sortList,            /* IN: sort order for returned data */
       firstRetrieve,       /* IN: first entry retrieved for query chunk.*/
       maxRetrieve,         /* IN: max entries to retrieve for query       */
Output: (CMDBAuditValueListList, numMatches) or None in case of failure'''
            self.logger.debug('enter CMDBGetCopyAuditData...')
            auditValueListList = ccmdb.CMDBAuditValueListList()
            numMatches = c_uint()
            self.errnr = self.cmdbapi.CMDBGetCMDBUIComponents(byref(self.context),
                                                              my_byref(classNameId),
                                                              datasetId,
                                                              instanceId,
                                                              auditTimestamp,
                                                              my_byref(qualifier),
                                                              my_byref(attributeGetList),
                                                              my_byref(sortList),
                                                              firstRetrieve,
                                                              maxRetrieve,
                                                              byref(auditValueListList),
                                                              byref(numMatches),
                                                              byref(self.arsl))
            if self.errnr < 2:
                return (auditValueListList, numMatches)
            else:
                self.logger.error('CMDBGetCMDBUIComponents failed for %s:%s' % (
                                                 classNameId.namespaceName,
                                                 classNameId.className))
                return None                

        def CMDBGetInstance(self, classNameId, 
                            datasetId = ccmdb.BMC_dataset,
                            getMask = ccmdb.CMDB_GET_MASK_NONE,
                            instanceId = '', 
                            attributeGetList = None):
            '''CMDBGetInstance retrieves information about the instance.

Input: (CMDBClassNameId) classNameId
       (ARNameType) datasetId (optional, default: ccmdb.BMC_dataset)
       (c_uint) getMask (optional, default: ccmdb.CMDB_GET_MASK_NONE)
       (ARNameType) instanceId 
       (ARNameList) attributeGetList (optional, default = None) 
Output: attributeValueList (CMDBAttributeValueList) or None in case of failure'''
            self.logger.debug('enter CMDBGetInstance...')
            attributeValueList = ccmdb.CMDBAttributeValueList()
            self.errnr = self.cmdbapi.CMDBGetInstance(byref(self.context),
                                                        byref(classNameId),
                                                        datasetId,
                                                        getMask,
                                                        instanceId,
                                                        my_byref(attributeGetList),
                                                        byref(attributeValueList),
                                                        byref(self.arsl))
            if self.errnr < 2:
                return attributeValueList
            else:
                self.logger.error('CMDBGetInstance failed for %s:%s' % (
                                                 classNameId.namespaceName,
                                                 classNameId.className))
                return None

        def CMDBGetInstanceBLOB(self, classNameId,
                                datasetId,
                                getMask,
                                instanceId, 
                                attributeName, 
                                loc):
            '''CMDBGetInstanceBLOB retrieves the attachment.

It retrieves attachments, or binary large object (BLOB), stored for the
attachment field. The BLOB is placed in a file.
Input: (CMDBClassNameId) classNameId, 
       (ARNameType) datasetId
       (c_uint) getMask
       (ARNameType) instanceId, 
       (ARNameType) attributeName
Output: loc (ARLocStruct) or None in case of failure'''
            self.logger.debug('enter CMDBGetInstanceBLOB...')
            loc = ccmdb.ARLocStruct()
            self.errnr = self.cmdbapi.CMDBGetInstanceBLOB(byref(self.context),
                                                     byref(classNameId),
                                                     datasetId,
                                                     getMask,
                                                     instanceId,
                                                     attributeName,
                                                     byref(loc),
                                                     byref(self.arsl))
            if self.errnr < 2:
                return loc
            else:
                self.logger.error('CMDBGetInstanceBLOB failed for %s:%s' % (
                                                    classNameId.namespaceName,
                                                    classNameId.className))
                return None
        
        def CMDBGetListInstance(self, classNameId,
                                datasetId = ccmdb.BMC_dataset,
                                getMask = ccmdb.CMDB_GET_MASK_NONE,
                                qualifier = None,
                                attributeGetList = None,
                                sortList = None,
                                firstRetrieve = ccmdb.CMDB_START_WITH_FIRST_INSTANCE,
                                maxRetrieve = ccmdb.CMDB_NO_MAX_LIST_RETRIEVE):
            '''CMDBGetListInstance retrieves a list of instances. 

You can limit the list to entries that match particular conditions by 
specifying the qualifier parameter.
Input: classNameId,
       (ARNameType) datasetId (optional, default: ccmdb.BMC_dataset),
       (c_uint) getMask (optional, default CMDB_GET_MASK_NONE, based on the datasetId being passed, 
instances are retrieved from either the overlay or the original dataset.
       (CMDBQualifierStruct) qualifier (optional, default = None),
       (ARNameList) attributeGetList (optional, default = None),
       (CMDBSortList) sortList (optional, default = None),
       (c_uint) firstRetrieve (optional, default = ccmdb.CMDB_START_WITH_FIRST_INSTANCE),
       (c_uint) maxRetrieve (optional, default = ccmdb.CMDB_NO_MAX_LIST_RETRIEVE) 
Output: (instanceIdList, attrValueListList, numMatches) or None in case of failure'''
            self.logger.debug('enter CMDBGetListInstance...')
            if qualifier is None:
                qualifier = ccmdb.CMDBQualifierStruct()
            instanceIdList = ccmdb.ARNameList()
            attrValueListList = ccmdb.CMDBAttributeValueListList()
            numMatches = c_uint()
            self.errnr = self.cmdbapi.CMDBGetListInstance(byref(self.context),
                                                        my_byref(classNameId),
                                                        datasetId,
                                                        getMask,
                                                        byref(qualifier),
                                                        my_byref(attributeGetList),
                                                        my_byref(sortList),
                                                        firstRetrieve,
                                                        maxRetrieve,
                                                        byref(instanceIdList),
                                                        byref(attrValueListList),
                                                        byref(numMatches),
                                                        byref(self.arsl))
            if self.errnr < 2:
                return (instanceIdList, attrValueListList, numMatches.value)
            else:
                self.logger.error('CMDBGetListInstance failed for %s:%s' % (
                                                 classNameId.namespaceName,
                                                 classNameId.className))
                return None

        def CMDBGetLogAuditData(self, classNameId,
                                datasetId = ccmdb.BMC_dataset,
                                instanceId = ''):
            '''CMDBGetLogAuditData retrieves the audit log for the specified CI instance. 

For you to retrieve the audit log, the AuditLog option must be set at the class-level.
Input: classNameId,         /* IN: class name */
       datasetId,           /* IN: dataset Id */
       instanceId,          /* IN: instance id  */
Output: auditLog or None in case of failure'''
            self.logger.debug('enter CMDBGetLogAuditData...')
            auditLog = cars.ARTextString()
            self.errnr = self.cmdbapi.CMDBGetLogAuditData(byref(self.context),
                                                          my_byref(classNameId),
                                                          datasetId,
                                                          instanceId,
                                                          byref(auditLog),
                                                          byref(self.arsl))
            if self.errnr < 2:
                return auditLog
            else:
                self.logger.error('CMDBGetLogAuditData failed for %s:%s' % (
                                                 classNameId.namespaceName,
                                                 classNameId.className))
                return None                

        def CMDBGetMultipleInstances(self, classNameId,
                                     datasetId,
                                     getMask = ccmdb.CMDB_GET_MASK_NONE,
                                     instanceIds = None,
                                     attributeGetList = None):
            '''CMDBGetMultipleInstances retrieves multiple instances of the 
specified class in a dataset.
Input: (CMDBClassNameId) classNameId
       (ARNameType) datasetId
       (c_uint) getMask (optional, default = ccmdb.CMDB_GET_MASK_NONE)
       (ARNameList) instanceIds
       (ARNameList) attributeGetList
Output: (ARBooleanList, CMDBAttributeValueListList) or None in case of failure'''
            self.logger.debug('enter CMDBGetMultipleInstances...')
            existList = ccmdb.ARBooleanList()
            attributeValueListList = ccmdb.CMDBAttributeValueListList()
            self.errnr = self.cmdbapi.CMDBGetMultipleInstances(byref(self.context),
                                                               my_byref(classNameId),
                                                               datasetId,
                                                               getMask,
                                                               my_byref(instanceIds),
                                                               my_byref(attributeGetList),
                                                               byref(existList),
                                                               byref(attributeValueListList),
                                                               byref(self.arsl))
            if self.errnr < 2:
                return (existList, attributeValueListList)
            else:
                self.logger.error('CMDBGetMultipleInstances failed')
                return None

        def CMDBGetRelatedFederatedInContext(self, classNameId,
                                             instanceId,
                                             attributeGetList = None):
            '''CMDBGetRelatedFederatedInContext returns related 
FederatedInterface instances for a specific CI (context).

Input: classNameId,         /* IN: class name */
       instanceId,          /* IN: ID of the instance in context */
       attributeGetList,    /* IN; list of names of attributes to retrieve */
Output: (instanceIdList, attrValueListList) or None in case of failure'''
            self.logger.debug('enter CMDBGetRelatedFederatedInContext...')
            instanceIdList = cars.ARNameList()
            attrValueListList = ccmdb.CMDBAttributeValueListList()
            self.errnr = self.cmdbapi.CMDBGetRelatedFederatedInContext(byref(self.context),
                                                      my_byref(classNameId),
                                                      instanceId,
                                                      my_byref(attributeGetList),
                                                      byref(instanceIdList),
                                                      byref(attrValueListList),
                                                      byref(self.arsl))
            if self.errnr < 2:
                return (instanceIdList, attrValueListList)
            else:
                self.logger.error('CMDBGetRelatedFederatedInContext failed for %s:%s' % (
                                                 classNameId.namespaceName,
                                                 classNameId.className))
                return None

        def CMDBGetVersions(self, appIdList = None):
            '''CMDBGetVersions retrieves the version information for any CMDB 
component that is installed.

Input: (optional) appIdList [ARNameList],   /* IN: list of app Ids, NULL OK */
Output: (existList, versionInfoList) or None in case of failure'''
            self.logger.debug('enter CMDBGetVersions...')
            existList = cars.ARBooleanList()
            versionInfoList = ccmdb.CMDBVersionInfoList()
            self.errnr = self.cmdbapi.CMDBGetVersions(byref(self.context),
                                                      my_byref(appIdList),
                                                      byref(existList),
                                                      byref(versionInfoList),
                                                      byref(self.arsl))
            if self.errnr < 2:
                return (existList, versionInfoList)
            else:
                self.logger.error('CMDBGetVersions failed')
                return None

        def CMDBGraphQuery(self, startClassNameId,
                           datasetId,
                           getMask,
                           startExtensionId,
                           startInstanceId, 
                           numLevels = -1,
                           direction = ccmdb.CMDB_RELATIONSHIP_DIRECTION_OUT,
                           noMatchProceed = 1, 
                           onMatchProceed = 1, 
                           queryGraph = None):
            '''CMDBGraphQuery searches related instances.

Input: (CMDBClassNameId) startClassNameId
       (ARNameType) datasetId
       (c_uint) getMask
       (ARNameType) startExtensionId
       (ARNameType) startInstanceId
       (c_int) numLevels (optional, default = -1)
       (c_int) direction (optional, default = ccmdb.CMDB_RELATIONSHIP_DIRECTION_OUT,
       (ARBoolean) noMatchProceed (optional, default = 1, 
       (ARBoolean) onMatchProceed (optional, default = 1, 
       (CMDBGraphList) queryGraph (optional, default = None
Output: (CMDBGetObjectList, CMDBGetRelationList) or None in case of failure'''
            self.logger.debug('enter CMDBGraphQuery...')
            objects = ccmdb.CMDBGetObjectList()
            relations = ccmdb.CMDBGetRelationList()
            self.errnr = self.cmdbapi.CMDBGraphQuery(byref(self.context),
                                                      byref(startClassNameId),
                                                      datasetId,
                                                      getMask,
                                                      startExtensionId,
                                                      startInstanceId,
                                                      numLevels,
                                                      direction,
                                                      noMatchProceed,
                                                      onMatchProceed,
                                                      my_byref(queryGraph),
                                                      byref(objects),
                                                      byref(relations),
                                                      byref(self.arsl))
            if self.errnr < 2:
                return (objects, relations)
            else:
                self.logger.error('CMDBGraphQuery failed for %s:%s' % (
                                                 startClassNameId.namespaceName,
                                                 startClassNameId.className))
                return None
            
        def CMDBRECancelJobRun(self, jobRunId):
            '''CMDBRECancelJobRun Cancels a specific, currently running 
Reconciliation Engine job. 

Depending on the system resources, Reconciliation Engine might cancel a job with a
certain delay.
ARNameType                    jobRunId,            /* IN: Id of job to cancel */
Output: errnr'''

            self.logger.debug('enter CMDBRECancelJobRun...')
#            jobRunInfo = ccmdb.CMDBREJobRunInfoStruct()
#            jobRunLog = c_char_p()
            self.errnr = self.cmdbapi.CMDBRECancelJobRun(byref(self.context),
                                                                jobRunId,
                                                                byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBRECancelJobRun failed for %s' % jobRunId)
            return self.errnr

        
        def CMDBREGetJobRun(self, jobRunId):
            '''Gets information about the currently running reconciliation job

ARNameType                    jobRunId,            /* IN: Id of job run */
Output:
CMDBREJobRunInfoStruct         jobRunInfo,         /* OUT: job run info */
char                           jobRunLog,           /* OUT: job run log */
 or None in case of failure'''
            self.logger.debug('enter CMDBREGetJobRun...')
            jobRunInfo = ccmdb.CMDBREJobRunInfoStruct()
            jobRunLog = c_char_p()
            self.errnr = self.cmdbapi.CMDBREGetJobRun(byref(self.context),
                                                                jobRunId,
                                                                byref(jobRunInfo),
                                                                byref(jobRunLog),
                                                                byref(self.arsl))
            if self.errnr < 2:
                return (jobRunInfo, jobRunLog)
            else:
                self.logger.error('CMDBREGetJobRun failed for %s' % jobRunId)
                return None
        
        def CMDBREGetListJobRun(self, jobQualifier):
            '''CMDBREGetListJobRun get a list of running Reconciliation Engine jobs. 

The job list will be retrieved based on the qualification passed to the function.
CMDBQualifierStruct           jobQualifier,        /* IN: job qualifier run */
Output: tuple (
CMDBREJobRunInfoList          jobRunInfoList,      /* OUT: job run info */
unsigned int                  numMatches)          /* OUT; number of matches for qualifier; */
or (None, errnr) in case of failure'''
            self.logger.debug('enter CMDBREGetListJobRun...')
            jobRunInfoList = ccmdb.CMDBREJobRunInfoList()
            numMatches = c_uint()
            self.errnr = self.cmdbapi.CMDBREGetListJobRun(byref(self.context),
                                                            my_byref(jobQualifier),
                                                            byref(jobRunInfoList),
                                                            byref(numMatches),
                                                            byref(self.arsl))
            if self.errnr < 2:
                return (jobRunInfoList, numMatches)
            else:
                self.logger.error('CMDBREGetListJobRun failed')
                return (None, self.errnr)
        
        def CMDBREStartJobRun(self, jobName, 
                              classQualList, 
                              datasetList):
            '''CMDBREStartJobRun starts an existing Reconciliation Engine job.

Before starting a job, make sure
the job is defined and exists in an Active state. If no job for the specified job
name exists, or the job is not Active, the CMDBStartJobRun function returns
an error. Only one instance of the same job can be executed at a given time.
ARNameType                    jobName,             /* IN: name of job to run */
CMDBClassQualList             *classQualList,       /* IN: list of class qualifications */
CMDBREDatasetList             *datasetList,
ARNameType                    jobRunId,            /* OUT: Id of job run */'''
            self.logger.debug('enter CMDBREStartJobRun...')
            jobRunId = ccmdb.ARNameType()
            self.errnr = self.cmdbapi.CMDBREStartJobRun(byref(self.context),
                                                                jobName,
                                                                my_byref(classQualList),
                                                                my_byref(datasetList),
                                                                byref(jobRunId),
                                                                byref(self.arsl))
            if self.errnr < 2:
                return jobRunId
            else:
                self.logger.error('CMDBREStartJobRun failed')
                return None
        
        def CMDBRunQualificationForCI(self, qualifier,
                                      attValueList):
            '''CMDBRunQualificationForCI performs validation.

Validation happens on a list of attributes for a specified CI. The
CMDBRunQualificationForCI function takes qualification parameters in
both structured and encoded modes.
Input: qualifier,          /* IN: qualifier to be matched against */
        attValueList,       /* IN: attribute value list */
Output: ARBoolean or None in case of failure'''
            self.logger.debug('enter CMDBRunQualificationForCI...')
            qualStatus = cars.ARBoolean()
            self.errnr = self.cmdbapi.CMDBRunQualificationForCI(byref(self.context),
                                                                my_byref(qualifier),
                                                                my_byref(attValueList),
                                                                byref(qualStatus),
                                                                byref(self.arsl))
            if self.errnr < 2:
                return qualStatus
            else:
                self.logger.error('CMDBRunQualificationForCI failed')
                return None

        def CMDBSetClass(self, classNameId, 
                         newClassNameId, 
                         classTypeInfo, 
                         indexList,
                         auditInfo,
                         characList, 
                         customCharacList):
            '''CMDBSetClass sets the class properties in the OBJSTR:Class form. 

After you create a class,
you cannot modify the following properties: classId, classType (regular,
relationship), and persistence provider.
Input: classNameId, 
         newClassNameId, 
         classTypeInfo, 
         indexList,
         auditInfo,
         characList, 
         customCharacList
Output: errnr'''
            self.logger.debug('enter CMDBSetClass...')
            self.errnr = self.cmdbapi.CMDBSetClass(byref(self.context),
                                                    my_byref(classNameId),
                                                    my_byref(newClassNameId),
                                                    my_byref(classTypeInfo),
                                                    my_byref(indexList),
                                                    my_byref(auditInfo),
                                                    my_byref(characList),
                                                    my_byref(customCharacList),
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBSetClass failed for %s:%s' % (
                                                     classNameId.namespaceName,
                                                     classNameId.className))
            return self.errnr

        def CMDBSetInstance(self, classNameId, 
                            datasetId,
                            instanceId,
                            attributeValueList):
            '''CMDBSetInstance Sets a CI or relationship instance in the OBJSTR:Class.

Input: classNameId, (CMDBClassNameId)
        datasetId, (ARNameType)
        instanceId, (ARNameType)
        attributeValueList (CMDBAttributeValueList)
Output: errnr'''
            self.logger.debug('enter CMDBSetInstance...')
            self.errnr = self.cmdbapi.CMDBSetInstance(byref(self.context),
                                                      my_byref(classNameId),
                                                      datasetId,
                                                      instanceId,
                                                      my_byref(attributeValueList),
                                                      byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBSetInstance failed for %s:%s' % (
                                                    classNameId.namespaceName,
                                                    classNameId.className))
            return self.errnr

    class CMDB(CMDB20):
        pass

if ccmdb.cmdbversion in ['cmdbapi21', 'cmdbapi75', 'cmdbapi76']:
    class CMDB21(CMDB20):
        '''pythonic wrapper Class for Atrium C API, Version 2.1'''
        def  CMDBExpandParametersForCI(self, datasetId,
                                       paramString,
                                       attValueList):
            '''CMDBExpandParametersForCI accepts an unexpanded string.
            
This string contains parameters and substitutes
values from the attribute value list provided in the CMDBAttributeValueList
structure.
Input: datasetId,           /* IN: dataset Id */
       paramString,        /* IN: string containing parameters */
       attValueList,       /* IN: attribute value list */
Output: expandedStr or None in case of failure'''
            
            self.logger.debug('enter CMDBExpandParametersForCI...')
            expandedStr = c_char_p()
            self.errnr = self.cmdbapi.CMDBExpandParametersForCI(byref(self.context),
                                                    datasetId,
                                                    paramString,
                                                    my_byref(attValueList),
                                                    expandedStr,
                                                    byref(self.arsl))
            if self.errnr < 2:
                return expandedStr
            else:
                self.logger.error('CMDBExpandParametersForCI failed')
                return None

        def CMDBExportData(self, classNameId,
                           datasetId,
                           qualifier,
                           attributeGetList = None,
                           sortList = None,
                           firstRetrieve = ccmdb.CMDB_START_WITH_FIRST_INSTANCE,
                           maxRetrieve = ccmdb.CMDB_NO_MAX_LIST_RETRIEVE):
            '''CMDBExportData
Input: CMDBClassNameId     *classNameId,            /* IN: class name id */
       ARNameType           datasetId,              /* IN: dataset Id */
       CMDBQualifierStruct *qualifier,              /* IN: export qualifier */
       ARNameList          *attributeGetList,       /* IN: list of names of attributes to retrieve */
       CMDBSortList        *sortList,               /* IN: sort order for exported data */
       unsigned int         firstRetrieve,          /* IN: first instance retrieved,*/
                                                   /*     CMDB_START_WITH_FIRST_INSTANCE means */
                                                   /*     retrieve the first instance from class */
       unsigned int         maxRetrieve,            /* IN: max instances to retrieve for query       */
                                                   /*     CMDB_NO_MAX_LIST_RETRIEVE means unlimited */
Output: exportBuf,              /* OUT: XML export data */'''
            self.logger.debug('enter CMDBExportData...')
            exportBuf = c_char_p()
            self.errnr = self.cmdbapi.CMDBExportData(byref(self.context),
                                                     my_byref(classNameId),
                                                     datasetId,
                                                     my_byref(qualifier),
                                                     my_byref(attributeGetList),
                                                     my_byref(sortList),
                                                     firstRetrieve,
                                                     maxRetrieve,
                                                     byref(exportBuf),
                                                     byref(self.arsl))
            if self.errnr < 2:
                return exportBuf
            else:
                self.logger.error('CMDBExportDef failed')
                return None

        def CMDBExportDef(self, exportItemList):
            '''CMDBExportDef
Input: CMDBXMLExportItemList exportItemList,       /* IN: items to export */
Output: exportBuf or None in case of failure'''
            self.logger.debug('enter CMDBExportDef...')
            exportBuf = c_char_p()
            self.errnr = self.cmdbapi.CMDBExportDef(byref(self.context),
                                                    my_byref(exportItemList),
                                                    byref(exportBuf),
                                                    byref(self.arsl))
            if self.errnr < 2:
                return exportBuf
            else:
                self.logger.error('CMDBExportDef failed')
                return None

        def CMDBGetRelatedFederatedInContext(self, classNameId,
                                             datasetId,
                                             instanceId,
                                             attributeGetList = None):
            '''CMDBGetRelatedFederatedInContext returns related 
FederatedInterface instances for a specific CI (context).

Input: classNameId,         /* IN: class name */
       datasetId,           /* IN: dataset Id */
       instanceId,          /* IN: ID of the instance in context */
       attributeGetList,    /* IN; list of names of attributes to retrieve */
Output: (instanceIdList, attrValueListList) or None in case of failure'''
            self.logger.debug('enter CMDBGetRelatedFederatedInContext...')
            instanceIdList = cars.ARNameList()
            attrValueListList = ccmdb.CMDBAttributeValueListList()
            self.errnr = self.cmdbapi.CMDBGetRelatedFederatedInContext(byref(self.context),
                                                      my_byref(classNameId),
                                                      datasetId,
                                                      instanceId,
                                                      my_byref(attributeGetList),
                                                      byref(instanceIdList),
                                                      byref(attrValueListList),
                                                      byref(self.arsl))
            if self.errnr < 2:
                return (instanceIdList, attrValueListList)
            else:
                self.logger.error('CMDBGetRelatedFederatedInContext failed for %s:%s' % (
                                                 classNameId.namespaceName,
                                                 classNameId.className))
                return None

        def CMDBImportData(self, importOption,
                           importBuf):
            '''CMDBImportDef
Input: int         importOption,           /* IN: import options */
       char        importBuf,              /* IN: XML import data */
Output: errnr'''
            self.logger.debug('enter CMDBImportData...')
            self.errnr = self.cmdbapi.CMDBImportData(byref(self.context),
                                                     importOption,
                                                     importBuf,
                                                     byref(self.arsl))
            return self.errnr

        def CMDBImportDef(self, importItemList,
                          importOption,
                          importBuf):
            '''CMDBImportDef
Input: CMDBXMLImportItemList importItemList,       /* IN: items to import */
       unsigned int          importOption,         /* IN: import options */
       char                  importBuf,            /* IN: XML import data */
Output: errnr
'''
            self.logger.debug('enter CMDBImportDef...')
            self.errnr = self.cmdbapi.CMDBImportDef(byref(self.context),
                                                    my_byref(importItemList),
                                                    importOption,
                                                    importBuf,
                                                    byref(self.arsl))
            return self.errnr

        def CMDBRunQualificationForCI(self, datasetId,
                                      qualifier,
                                      attValueList):
            '''CMDBRunQualificationForCI performs validation.

Validation happens on a list of attributes for a specified CI. The
CMDBRunQualificationForCI function takes qualification parameters in
both structured and encoded modes.
Input: datasetId,           /* IN: dataset Id */
        qualifier,          /* IN: qualifier to be matched against */
        attValueList,       /* IN: attribute value list */
Output: ARBoolean or None in case of failure'''
            self.logger.debug('enter CMDBRunQualificationForCI...')
            qualStatus = cars.ARBoolean()
            self.errnr = self.cmdbapi.CMDBRunQualificationForCI(byref(self.context),
                                                                datasetId,
                                                                my_byref(qualifier),
                                                                my_byref(attValueList),
                                                                byref(qualStatus),
                                                                byref(self.arsl))
            if self.errnr < 2:
                return qualStatus
            else:
                self.logger.error('CMDBRunQualificationForCI failed')
                return None

    class CMDB(CMDB21):
        pass

if ccmdb.cmdbversion in ['cmdbapi75', 'cmdbapi76']:
    class CMDB75(CMDB21):
        '''pythonic wrapper Class for Atrium C API, Version 7.5'''
        def CMDBCreateImpact(self, datasetId,
                              relationshipId,
                              impactInfoStruct,
                              options):
            '''CMDBCreateImpact: no docs found
Input: (ARNameType) datasetId,           /* IN: dataset Id */
       (ARNameType) relationshipId,      /* IN: relationship instance Id */
       (CMDBImpactInfoStruct) impactInfoStruct,    /* IN:OUT impact info structure */
       (c_int) options,             /* IN: get mask */
Output: CMDBImpactInfoStruct or None in case of failure'''
            self.logger.debug('enter CMDBCreateImpact...')
            self.errnr = self.cmdbapi.CMDBCreateImpact(byref(self.context),
                                                      datasetId,
                                                      relationshipId,
                                                      my_byref(impactInfoStruct),
                                                      options,
                                                      byref(self.arsl))
            if self.errnr < 2:
                return impactInfoStruct
            else:
                self.logger.error('CMDBCreateImpact failed')
                return None
            
        def CMDBCreateMultipleInstances(self, datasetId,
                               instances):
            '''CMDBCreateMultipleInstances Creates multiple specified CI or 
relationship instances in the specified dataset.
Input: (ARNameType) datasetId
       (CMDBInstanceList) instances
Output: ARNameList or None in case of failure'''
            self.logger.debug('enter CMDBCreateMultipleInstances...')
            instanceIdList = cars.ARNameList()
            self.errnr = self.cmdbapi.CMDBCreateMultipleInstances(byref(self.context),
                                                                datasetId,
                                                                my_byref(instances),
                                                                byref(instanceIdList),
                                                                byref(self.arsl))
            if self.errnr < 2:
                return instanceIdList
            else:
                self.logger.error('CMDBCreateMultipleInstances failed')
                return None

        def CMDBDeleteImpact(self, datasetId,  
                             relationshipId):
            '''CMDBDeleteImpact: no docs available 
instances in the specified dataset.
Input: (ARNameType) datasetId
       (ARNameType) relationshipId
Output: errnr'''
            self.logger.debug('enter CMDBDeleteImpact...')
            self.errnr = self.cmdbapi.CMDBDeleteImpact(byref(self.context),
                                                               datasetId,
                                                               relationshipId,
                                                               byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBDeleteImpact failed')
            return self.errnr

        def CMDBDeleteMultipleInstances(self, datasetId,  
                                        instances,
                                        deleteOption = ccmdb.CMDB_DERIVED_DELOPTION_NONE):
            '''CMDBDeleteMultipleInstances deletes a list of CI or relationship 
instances in the specified dataset.
Input: (ARNameType) datasetId
       (CMDBInstanceList) instances
       (c_uint) deleteOption (optional, default = ccmdb.CMDB_DERIVED_DELOPTION_NONE)
Output: errnr'''
            self.logger.debug('enter CMDBDeleteMultipleInstances...')
            self.errnr = self.cmdbapi.CMDBDeleteMultipleInstances(byref(self.context),
                                                               datasetId,
                                                               my_byref(instances),
                                                               deleteOption,
                                                               byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBDeleteMultipleInstances failed')
            return self.errnr

        def CMDBGetImpact(self, datasetId,
                          relationshipId):
            '''CMDBGetImpact: no docs available
Input: (ARNameType) datasetId
       (ARNameType) relationshipId
Output: CMDBImpactInfoStruct or None in Case of failure'''
            self.logger.debug('enter CMDBGetImpact...')
            impactInfoStruct = ccmdb.CMDBImpactInfoStruct()
            self.errnr = self.cmdbapi.CMDBGetImpact(byref(self.context),
                                                    datasetId,
                                                    relationshipId,
                                                    byref(impactInfoStruct),
                                                    byref(self.arsl))
            if self.errnr < 2:
                return impactInfoStruct
            else:
                self.logger.error('CMDBGetImpact failed')
                return None

        def CMDBGraphWalkBegin (self, startClassNameId,
                                startInstanceId,
                                graphWalkQueryStruct):
            '''CMDBGraphWalkBegin specifies the start node for retrieving CI 
and relationship instances in a chunk. This function sets up the starting node 
and query parameters for the graph walk.
Input: (CMDBClassNameId) startClassNameId
       (ARNameType) startInstanceId
       (CMDBGraphWalkQueryStruct) graphWalkQueryStruct
Output: CMDBGraphWalkStateStruct or None in case of failure
            '''
            self.logger.debug('enter CMDBGraphWalkBegin...')
            graphWalkStateStruct = ccmdb.CMDBGraphWalkStateStruct()
            self.errnr = self.cmdbapi.CMDBGraphWalkBegin(byref(self.context),
                                                               my_byref(startClassNameId),
                                                               my_byref(startInstanceId),
                                                               my_byref(graphWalkQueryStruct),
                                                               byref(graphWalkStateStruct),
                                                               byref(self.arsl))
            if self.errnr < 2:
                return graphWalkStateStruct
            else:
                self.logger.error('CMDBGraphWalkBegin failed')
                return None

        def CMDBGraphWalkEnd (self):
            '''CMDBGraphWalkEnd ends the graph walk. Use this function after 
you retrieve the CI and relationship information using the CMDBGraphWalkNext 
function.
Input: 
Output: graphWalkStateStruct or None in case of failure'''
            self.logger.debug('enter CMDBGraphWalkEnd...')
            graphWalkStateStruct = ccmdb.CMDBGraphWalkStateStruct()
            self.errnr = self.cmdbapi.CMDBGraphWalkEnd(byref(self.context),
                                                       byref(graphWalkStateStruct),
                                                       byref(self.arsl))
            if self.errnr < 2:
                return graphWalkStateStruct
            else:
                self.logger.error('CMDBGraphWalkEnd failed')
                return None

        def CMDBGraphWalkNext (self, graphWalkStateStruct):
            '''CMDBGraphWalkNext moves to the next chunk of nodes to retrieve 
in the graph walk. This function is used after setting up the start node in the 
CI and relationship graph using the CMDBGraphWalkBegin function.
You do not need to specify values for any of the parameters of the function. You
need to use only the hasNextChunk member of the CMDBGraphWalkStateStruct
structure to retrieve rows in chunks.
Input: (CMDBGraphWalkStateStruct) graphWalkStateStruct
Output: (CMDBGraphWalkStateStruct, CMDBGraphWalkResultStruct) or None in case of failure
            '''
            self.logger.debug('enter CMDBGraphWalkNext...')
            graphWalkResultStruct = ccmdb.CMDBGraphWalkResultStruct()
            self.errnr = self.cmdbapi.CMDBGraphWalkNext(byref(self.context),
                                                        my_byref(graphWalkStateStruct),
                                                        byref(graphWalkResultStruct),
                                                        byref(self.arsl))
            if self.errnr < 2:
                return (graphWalkStateStruct, graphWalkResultStruct)
            else:
                self.logger.error('CMDBGraphWalkNext failed')
                return None

        def CMDBQueryByPath(self, query):
            '''CMDBQueryByPath retrieves a list of instances for the specified 
qualifications. To improve the performance of the queries, add indexes on 
attributes that are frequently used in the qualification.
Input: (CMDBQueryStruct) query
Output: CMDBQueryResultGraph or None in case of failure'''
            self.logger.debug('enter CMDBQueryByPath...')
            result = ccmdb.CMDBQueryResultGraph()
            self.errnr = self.cmdbapi.CMDBQueryByPath(byref(self.context),
                                                               my_byref(query),
                                                               byref(result),
                                                               byref(self.arsl))
            if self.errnr < 2:
                return result
            else:
                self.logger.error('CMDBQueryByPath failed')
                return None

        def CMDBSetImpact(self, datasetId, 
                          relationshipId,
                          impactInfoStruct,
                          options):
            '''CMDBSetImpact no docs
Input: (ARNameType) datasetId
       (ARNameType) relationshipId
       (CMDBImpactInfoStruct) impactInfoStruct
       (c_uint) options
Output: errnr'''
            self.logger.debug('enter CMDBSetImpact...')
            self.errnr = self.cmdbapi.CMDBSetImpact(byref(self.context),
                                                    datasetId,
                                                    relationshipId,
                                                    my_byref(impactInfoStruct),
                                                    options,
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBSetImpact failed')
            return self.errnr

        def CMDBSetMultipleInstances(self, datasetId, 
                                     instances):
            '''CMDBSetMultipleInstances sets attribute values for CI or 
relationship instances in the specified dataset.
Input: (ARNameType) datasetId
       (CMDBInstanceList) instances
Output: errnr'''
            self.logger.debug('enter CMDBSetMultipleInstances...')
            self.errnr = self.cmdbapi.CMDBSetMultipleInstances(byref(self.context),
                                                               datasetId,
                                                               my_byref(instances),
                                                               byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBSetMultipleInstances failed')
            return self.errnr

        def CMDBSetUserSessionGUID(self, guid):
            self.logger.debug('enter CMDBSetUserSessionGUID...')
            self.errnr = self.cmdbapi.CMDBSetUserSessionGUID(byref(self.context),
                                                             my_byref(guid),
                                                             byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('CMDBSetUserSessionGUID failed')
            return self.errnr


    class CMDB(CMDB75):
        pass
    
if ccmdb.cmdbversion in ['cmdbapi76']:
    class CMDB76(CMDB75):
        '''pythonic wrapper Class for Atrium C API, Version 7.6'''
        pass

    class CMDB(CMDB76):
        pass

if __name__ == "__main__":
    print '''pyARS.cmdb does not offer any functionality out of the box. It provides
you with an interface to the Atrium CMDB. 
    
internal information:
found the following api version: %s
''' % (ccmdb.cmdbversion)
    
