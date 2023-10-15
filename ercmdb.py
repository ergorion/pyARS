#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

#######################################################################
#
# This is the pythonic layer on top of pyars.cmdb.
# (C) 2004-2012 by Ergorion
#
# Currently supported Version: V1.0-7.5 of the Remedy CMDB API
#
#######################################################################
#
# known issues:
#

from ctypes import c_uint, Structure, POINTER
import exceptions

from pyars import cars, ccmdb, erars
from pyars.cmdb import CMDB

class CMDBError(exceptions.Exception):
    def __init__(self):
        return
        
    def __str__(self):
        print "","A CMDBError occured!"
        
class CMDBClassStruct(Structure):
    _fields_ = [("classNameId", ccmdb.CMDBClassNameId),
                 ("classId", ccmdb.ARNameType),
                 ("classTypeInfo", ccmdb.CMDBClassTypeInfo),
                 ("superclassNameId", ccmdb.CMDBClassNameId),
                 ("indexList", ccmdb.CMDBIndexList),
                 ("characList", ccmdb.ARPropList),
                 ("customCharacList", ccmdb.ARPropList)]

class CMDBClassList(Structure):
    _fields_ = [("numItems", c_uint),
                 ("classList", POINTER(CMDBClassStruct))]


# we need to inherit from erARS for the ergorion helper functions
# and from CMDB for the CMDB direct functions. Obviously, thus we inherit
# the standard AR api functions twice, but python can handle that (I believe)
class erCMDB11(CMDB, erars.erARS):
    '''pythonic wrapper Class for Atrium C API, V1.1'''
    def __init__(self, server='', user='', password='', language='', 
               authString = '',
               tcpport = 0,
               rpcnumber = 0):
        CMDB.__init__ (self, server, user, password, language, 
                   authString, tcpport, rpcnumber)
        # dictionary that will hold the information from Atrium
        # baseclass : [list of subclasses]
        # baseclass : superclass
        self.subclasses = {} 
        self.superclass = {}

    def convAttributeValueList2Dict(self, attributeValueList):
        return dict(self.convAttributeValueList2List(attributeValueList))

    def convAttributeValueList2List(self, attributeValueList):
        return [self.convAttributeValueStruct2List(attributeValueList.attributeValueList[i])
                for i in range(attributeValueList.numItems)]

    def convAttributeValueListList2List(self, attributeValueListList):
        return [self.convAttributeValueList2Dict(attributeValueListList.attributeValueListList[i])
                for i in range(attributeValueListList.numItems)]
    
    def convAttributeValueStruct2List(self, attributeValueStruct):
        return (attributeValueStruct.attributeName,
                self.convValueStruct2Value(attributeValueStruct.attributeValue))
        
    def convClassNameIdList2List(self, classNameIdList):
        return ['%s:%s' % (classNameIdList.classNameIdList[i].namespaceName,
                           classNameIdList.classNameIdList[i].className)
                for i in range(classNameIdList.numItems)]

    def convGetObjectList2List(self, getObjectList):
        return [self.convGetObjectStruct2List(getObjectList.objectList[i])
                for i in range(getObjectList.numItems)]
    
    def convGetObjectStruct2List (self, getObjectStruct):
        return ((getObjectStruct.classNameId.namespaceName,
                 getObjectStruct.classNameId.className),
                getObjectStruct.instanceId,
                self.convAttributeValueList2List(getObjectStruct.attributeValueList))

    # unfortunately, I have to declary a copy from erars.convValueStruct2Value
    # here, as ARValueStruct seems to be loaded from ccmdb instead of cars...
    def convValueStruct2Value(self, obj):
        # special handling for unicode
        if obj.dataType == ccmdb.AR_DATA_TYPE_CHAR and \
        self.context.localeInfo.charSet.lower() == 'utf-8':
            return obj.u.charVal.decode('utf-8') 
#            string = obj.u.charVal
#            self.logger.debug('before unicode conversion: %s' % string)
#            ustring = string.decode('utf-8') 
#            self.logger.debug('after unicode conversion: %s' % ustring)
#            return ustring
        try:
            if obj.dataType == ccmdb.AR_DATA_TYPE_NULL:
                return None
            return eval('obj.%s' % (ccmdb.ARValueStruct._mapping_so_ [obj.dataType]))
        except KeyError:
            try: 
                return eval('obj.%s' % (ccmdb.ARValueStruct._mapping_co_ [obj.dataType]))
            except KeyError:
                self.logger.error('unknown ARValueStruct type!')
                return None

    def getClassHierarchy(self, namespace = ccmdb.BMC_namespace, 
                          baseclass = ccmdb.BMC_baseclass):
        '''starting from baseclass, go through the hierarchy of subclasses and build two
dictionary structures that hold all the information about the sub/superclasses:
    subclasses [baseclass] = [list of all subclasses]
    superclass [baseclass] = superclass
the dictionaries are implemented as member variables of this class, and will be updated
with each call of getClassHierarchy - in other words, this is not completely safe
unless you know what you do!'''
        self.errnr = 0
        superclassname = ccmdb.CMDBClassNameId(namespace, baseclass)
        r=self.CMDBGetListClass(namespaceName = None,
                                superclassName = superclassname)
        if self.errnr > 1:
            self.logger.error('GetListClass failed for class: %s:%s' % (namespace, baseclass))
            return

        self.superclass ['%s:%s' % (namespace, baseclass)] = None
                
        self.subclasses ['%s:%s' % (namespace, baseclass)] = ['%s:%s' % (
                              r.classNameIdList[i].namespaceName, 
                              r.classNameIdList[i].className)
                              for i in range(r.numItems)]
        for i in range(r.numItems):
            # go into recursion to find subclasses in each tree down the hierarchy
            self.logger.debug('going into recursion for %s:%s...' % (
                                    r.classNameIdList[i].namespaceName,
                                    r.classNameIdList[i].className))
            self.getClassHierarchy (r.classNameIdList[i].namespaceName,
                                    r.classNameIdList[i].className)
            # now set the super class relationship
            # make sure to do this _after_ calling myself recursively!
            self.superclass ['%s:%s' % (r.classNameIdList[i].namespaceName, 
                                   r.classNameIdList[i].className)] = '%s:%s' % (namespace, baseclass)

            
    def findDirectCSCs (self, namespace = ccmdb.BMC_namespace, 
                        baseclass = ccmdb.BMC_baseclass):
        '''for a given class, find all directly related categorization subclasses'''
        tempArray = (cars.ARPropStruct * 1)()
        value = cars.ARValueStruct()
        value.dataType = cars.AR_DATA_TYPE_INTEGER
        value.u.intVal = 1
        tempArray [0] = (ccmdb.CMDB_CLASS_CHARAC_CATEGORIZATION_SUBCLASS, value)
        propList = cars.ARPropList(1, tempArray)
        superclassname = ccmdb.CMDBClassNameId(namespace, baseclass)
        r=self.CMDBGetListClass(superclassName = superclassname, characQueryList = propList)
        if self.errnr > 1:
            self.logger.error('findDirectCSCs failed for class: %s:%s' % (namespace, baseclass))
            return []
        return ['%s:%s' % (r.classNameIdList[i].namespaceName, 
                              r.classNameIdList[i].className)
                              for i in range(r.numItems)]

    def findAllCSCs (self, namespace = ccmdb.BMC_namespace, 
                     baseclass = ccmdb.BMC_baseclass):
        '''for a given class, find all directly and indirectly related categorization subclasses,
but there must not be any other type of class in between!'''
        directSubClasses = self.findDirectCSCs (namespace, baseclass)
        for i in range(len(directSubClasses)):
            namesp, classNa = directSubClasses[i].split(':')
            furtherSubCSCs = self.findDirectCSCs(namesp, classNa)
            if furtherSubCSCs == []:
                continue
            directSubClasses[i] = [directSubClasses[i], self.findAllCSCs(namesp, classNa)]
        return directSubClasses

    def findAbstractSuperClass(self, namespace = ccmdb.BMC_namespace, 
                               baseclass = ccmdb.BMC_baseclass):
        '''return the list of immediate abstract superclasses; if only the immediate 
superclass is abstract, returns [superclassName], otherwise
[superclassName1, superclassname2], although currently we assume, that
Atrium does not really support abstract subclasses of abstract classes.'''
        # if ths dictionaries of super/subclasses have not been filled yet, do
        # it now. Assumption is, that if they have been filled, they have been filled
        # starting with AssetBase
        if len(self.superclass) == 0:
            self.getClassHierarchy()
        try:
            superCl = self.superclass['%s:%s' % (namespace, baseclass)]
        except KeyError:
            self.logger.error('findAbstractSuperClass: cannot find any superclass for %s:%s' % (
                              namespace, baseclass))
            return []
        if superCl == None:
            return []
        cl = self.GetClass (superCl)
        characts = self.convPropList2Dict(cl.characList)
        if characts[ccmdb.CMDB_CLASS_CHARAC_ABSTRACT] == 0:
            return []
        else:
            return [superCl]

    def BeginBulkEntryTransaction(self):
        '''BeginBulkEntryTransaction indicates that subsequent API 
calls are part of the bulk transaction. 

Any API calls that arrive after this function call are placed in a queue. Metadata
function calls are not part of the bulk transaction.
Input: 
Output: errnr'''
        return self.CMDBBeginBulkEntryTransaction()

    def CreateAttribute(self, namespace,
                            className,
                            attributeName,
                            attributeId,
                            dataType,
                            arFieldId = 0,
                            entryMode = ccmdb.CMDB_ATTR_ENTRYMODE_OPTIONAL,
                            attributeLimit = None,
                            defaultValue = None, 
                            characList = None,
                            customCharacList = None):
        '''CreateAttribute creates a new attribute with the indicated 
name for the specified class.

Input:  (string) namespace (if the namespace contains a ":", assume it contains the complete name)
        (string) className, 
        (ARNameType) attributeName,
        (ARNameType) attributeId,
        (c_uint) dataType (should be one of CMDB_ATTR_DATA_TYPE_*),
        (ARInternalId) arFieldId (optional, default = 0),
        (c_uint) entryMode (optional, default = ccmdb.CMDB_ATTR_ENTRYMODE_OPTIONAL),
        (CMDBAttributeLimit) attributeLimit (optional, default = None),
        (ARValueStruct) defaultValue (optional, default = None), 
        (ARPropList) characList (optional, default = None),
        (ARPropList) customCharacList (optional, default = None)
Output: errnr'''
        if namespace is None:
            self.logger.error('CreateAttribute: namespace is None!')
            raise CMDBError
        if namespace.find(':') > -1:
            namespace, className = namespace.split(':')
        classNameId = ccmdb.CMDBClassNameId(namespace, className)
        return self.CMDBCreateAttribute(classNameId, 
                                attributeName,
                                attributeId,
                                dataType,
                                arFieldId,
                                entryMode,
                                attributeLimit,
                                defaultValue, 
                                characList,
                                customCharacList)

    def EndBulkEntryTransaction(self,
                                actionType = ccmdb.AR_BULK_ENTRY_ACTION_SEND):
        '''EndBulkEntryTransaction commits the bulk 
transaction, depending on the action type.

For an action type of SEND, the API call will be executed as part of the
transaction. For an action type of CANCEL, the transaction will be canceled.
Input: (optional) actionType (default = ccmdb.AR_BULK_ENTRY_ACTION_SEND)
Output: bulkEntryReturnList or None in case of failure'''
        return self.CMDBEndBulkEntryTransaction(actionType)

    def GetAttribute(self, namespace = ccmdb.BMC_namespace, 
                     className = ccmdb.BMC_baseclass, 
                     attributeName = None):
        '''GetAttribute retrieves a single attribute.
            
Input: namespace (if the namespace contains a ":", assume it contains the complete name)
       className 
       attributeName (optional, default = None)
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
        if namespace is None:
            self.logger.error('GetAttribute: namespace is None!')
            raise CMDBError
        if namespace.find(':') > -1:
            namespace, className = namespace.split(':')
        classNameId = ccmdb.CMDBClassNameId(namespace, className)
        return self.CMDBGetAttribute(classNameId, 
                             attributeName)

    def GetClass(self, namespace = ccmdb.BMC_namespace, 
                 className = ccmdb.BMC_baseclass):
        '''GetClass: retrieve class information.
Input: namespace (if the namespace contains a ":", assume it contains the complete name)
       className
Output: CMDBClassStruct'''
        if namespace is None:
            self.logger.error('GetClass: namespace is None!')
            raise CMDBError
        if namespace.find(':') > -1:
            namespace, className = namespace.split(':')
        classNameId = ccmdb.CMDBClassNameId(namespace, className)
        classId = ccmdb.ARNameType()
        classTypeInfo = ccmdb.CMDBClassTypeInfo()
        superclassNameId = ccmdb.CMDBClassNameId()
        indexList = ccmdb.CMDBIndexList()
        characList = ccmdb.ARPropList()
        customCharacList = ccmdb.ARPropList()
        self.errnr = self.CMDBGetClass(classNameId,
                                     classId,
                                     classTypeInfo,
                                     superclassNameId,
                                     indexList,
                                     characList,
                                     customCharacList)
        if self.errnr < 2:
            return CMDBClassStruct(classNameId, 
                                    classId.value, 
                                    classTypeInfo, 
                                    superclassNameId, 
                                    indexList,
                                    characList, 
                                    customCharacList)
        else:
            raise CMDBError

    def GetInstance(self, namespace, 
                    className, 
                    instanceId, 
                    attributeGetList = None):
        '''GetInstance retrieves information about the instance.
            
Input: (string) namespace (if the namespace contains a ":", assume it contains the complete name)
       (string) className
       (string) instanceId
       (ARNameList) attributeGetList (optional, default = None)    
Output: dictionary of {attribute : value, ...}'''
        if namespace is None:
            self.logger.error('GetInstance: namespace is None!')
            raise CMDBError
        if namespace.find(':') > -1:
            namespace, className = namespace.split(':')
        classNameId = ccmdb.CMDBClassNameId(namespace, className)
        result = self.CMDBGetInstance(classNameId,
                                    instanceId,
                                    attributeGetList)
        if self.errnr > 1:
            raise CMDBError
        pythonicResult = self.convAttributeValueList2Dict(result)
        # self.ARFree(result)
        return pythonicResult

    def GetListClass(self, namespaceName = ccmdb.BMC_namespace,
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
Output: list of class names'''
        result = self.CMDBGetListClass(namespaceName,
                                       classNameIdRelation,
                                       superclassName,
                                       characQueryList,
                                       getHiddenClasses)
        if self.errnr > 2:
            raise CMDBError
        else:
            pythonicResult = self.convClassNameIdList2List(result)
            self.Free(result)
            return pythonicResult
    
    def GetListInstance(self, namespace = ccmdb.BMC_namespace, 
                        className = ccmdb.BMC_baseclass,
                        qualifier = None,
                        attributeGetList = None,
                        sortList = None,
                        firstRetrieve = ccmdb.CMDB_START_WITH_FIRST_INSTANCE,
                        maxRetrieve = ccmdb.CMDB_NO_MAX_LIST_RETRIEVE):
        '''GetListInstance retrieves a list of instances. You can limit 
the list to entries that match particular conditions by specifying the qualifier 
parameter.

Input: (string) namespace (if it contains a ":", we assume that it is the complete classname)
       (string) className
       (CMDBQualifierStruct) qualifier (optional, default = None),
       (ARNameList) attributeGetList (optional, default = None),
       (CMDBSortList) sortList (optional, default = None),
       (c_uint) firstRetrieve (optional, default = ccmdb.CMDB_START_WITH_FIRST_INSTANCE),
       (c_uint) maxRetrieve (optional, default = ccmdb.CMDB_NO_MAX_LIST_RETRIEVE) 
Output: (list of (instance id1, dict1 {attr: value, ...}), (instance id2, dict2), ...
         numMatches)'''
        if namespace is None:
            self.logger.error('GetListInstance: namespace is None!')
            raise CMDBError
        if namespace.find(':') > -1:
            namespace, className = namespace.split(':')
        classNameId = ccmdb.CMDBClassNameId(namespace, className)
        if qualifier is None:
            quali = None
        elif isinstance(qualifier, str):
            quali = ccmdb.CMDBQualifierStruct(ccmdb.CMDB_QUALIFIER_TYPE_STRING) 
            quali.u.qualifierString = qualifier
        elif isinstance(qualifier, ccmdb.CMDBQualifierStruct):
            quali = qualifier
        result = self.CMDBGetListInstance(classNameId,
                                        quali,
                                        attributeGetList,
                                        sortList,
                                        firstRetrieve,
                                        maxRetrieve)
        if self.errnr > 1:
            raise CMDBError
        (nameList, attributeValueListList, numMatches) = result
        names = self.convNameList2List(nameList)
        values = self.convAttributeValueListList2List(attributeValueListList)
        self.Free(nameList)
        return (zip(names, values), numMatches)

class erCMDB(erCMDB11):
    pass

if ccmdb.cmdbversion in ['cmdbapi20', 'cmdbapi21', 'cmdbapi75', 'cmdbapi76']:
    
    class CMDBClassStruct(Structure):
        _fields_ = [("classNameId", ccmdb.CMDBClassNameId),
                     ("classId", ccmdb.ARNameType),
                     ("classTypeInfo", ccmdb.CMDBClassTypeInfo),
                     ("superclassNameId", ccmdb.CMDBClassNameId),
                     ("indexList", ccmdb.CMDBIndexList),
                     ("auditInfo",  ccmdb.CMDBAuditInfoStruct),
                     ("characList", ccmdb.ARPropList),
                     ("customCharacList", ccmdb.ARPropList)]
    class CMDBClassList(Structure):
        _fields_ = [("numItems", c_uint),
                     ("classList", POINTER(CMDBClassStruct))]
 
    class erCMDB20(erCMDB11):
        '''pythonic wrapper Class for Atrium C API, V2.0'''
        def GetClass(self, namespace = ccmdb.BMC_namespace, 
                 className = ccmdb.BMC_baseclass):
            '''GetClass: retrieve class information.
Input: namespace (if the namespace contains a ":", assume it contains the complete name)
       className
Output: CMDBClassStruct or None in case of failure'''
            if namespace is None:
                self.logger.error('GetClass: namespace is None!')
                return
            if namespace.find(':') > -1:
                namespace, className = namespace.split(':')
            classNameId = ccmdb.CMDBClassNameId(namespace, className)
            classId = ccmdb.ARNameType()
            classTypeInfo = ccmdb.CMDBClassTypeInfo()
            superclassNameId = ccmdb.CMDBClassNameId()
            indexList = ccmdb.CMDBIndexList()
            auditInfo = ccmdb.CMDBAuditInfoStruct()
            characList = ccmdb.ARPropList()
            customCharacList = ccmdb.ARPropList()
            self.errnr = self.CMDBGetClass(classNameId,
                                         classId,
                                         classTypeInfo,
                                         superclassNameId,
                                         indexList,
                                         auditInfo,
                                         characList,
                                         customCharacList)
            if self.errnr < 2:
                return CMDBClassStruct(classNameId, 
                                        classId.value, 
                                        classTypeInfo, 
                                        superclassNameId, 
                                        indexList,
                                        auditInfo,
                                        characList, 
                                        customCharacList)
            else:
                raise CMDBError

        def GetInstance(self, namespace, 
                        className, 
                        datasetId = ccmdb.BMC_dataset,
                        getMask = ccmdb.CMDB_GET_MASK_NONE,
                        instanceId = '', 
                        attributeGetList = None):
            '''GetInstance retrieves information about the instance.

Input: (string) namespace (if the namespace contains a ":", assume it contains the complete name)
       (string) className
       (ARNameType) datasetId (optional, default: ccmdb.BMC_dataset)
       (c_uint) getMask (optional, default: ccmdb.CMDB_GET_MASK_NONE)
       (ARNameType) instanceId 
       (ARNameList) attributeGetList (optional, default = None) 
Output: dictionary of {attribute : value, ...}'''
            if namespace is None:
                self.logger.error('GetInstance: namespace is None!')
                raise CMDBError
            if namespace.find(':') > -1:
                namespace, className = namespace.split(':')
            classNameId = ccmdb.CMDBClassNameId(namespace, className)
            result = self.CMDBGetInstance(classNameId,
                                          datasetId,
                                          getMask,
                                          instanceId,
                                          attributeGetList)
            if self.errnr > 1:
                raise CMDBError
            pythonicResult = self.convAttributeValueList2Dict(result)
            # self.ARFree(result)
            return pythonicResult
    
        def GetListInstance(self, namespace = ccmdb.BMC_namespace, 
                            className = ccmdb.BMC_baseclass,
                            datasetId = ccmdb.BMC_dataset,
                            getMask = ccmdb.CMDB_GET_MASK_NONE,
                            qualifier = None,
                            attributeGetList = None,
                            sortList = None,
                            firstRetrieve = ccmdb.CMDB_START_WITH_FIRST_INSTANCE,
                            maxRetrieve = ccmdb.CMDB_NO_MAX_LIST_RETRIEVE):
            '''GetListInstance retrieves a list of instances. 

You can limit the list to entries that match particular conditions by 
specifying the qualifier parameter.
Input: (string) namespace (optional, default: ccmdb.BMC_namespace); if it 
            contains a ":" it is assumed to be the full class name
       (string) className (optional, default: ccmdb.BMC_baseclass)
       (ARNameType) datasetId (optional, default: ccmdb.BMC_dataset),
       (c_uint) getMask (optional, default CMDB_GET_MASK_NONE, based on the datasetId being passed, 
instances are retrieved from either the overlay or the original dataset.
       (string) qualifier (optional, default = None),
       (ARNameList) attributeGetList (optional, default = None),
       (CMDBSortList) sortList (optional, default = None),
       (c_uint) firstRetrieve (optional, default = ccmdb.CMDB_START_WITH_FIRST_INSTANCE),
       (c_uint) maxRetrieve (optional, default = ccmdb.CMDB_NO_MAX_LIST_RETRIEVE) 
Output: (list of (instance id1, dict1 {attr: value, ...}), (instance id2, dict2), ...
         numMatches)'''
            if namespace is None:
                self.logger.error('GetListInstance: namespace is None!')
                raise CMDBError
            if namespace.find(':') > -1:
                namespace, className = namespace.split(':')
            classNameId = ccmdb.CMDBClassNameId(namespace, className)
            if qualifier is None:
                quali = None
            elif isinstance(qualifier, str):
                quali = ccmdb.CMDBQualifierStruct(ccmdb.CMDB_QUALIFIER_TYPE_STRING) 
                quali.u.qualifierString = qualifier
            elif isinstance(qualifier, ccmdb.CMDBQualifierStruct):
                quali = qualifier
            result= self.CMDBGetListInstance(classNameId,
                                            datasetId,
                                            getMask,
                                            quali,
                                            attributeGetList,
                                            sortList,
                                            firstRetrieve,
                                            maxRetrieve)
            if self.errnr > 1:
                raise CMDBError
            (nameList, attributeValueListList, numMatches) = result
            names = self.convNameList2List(nameList)
            values = self.convAttributeValueListList2List(attributeValueListList)
            self.Free(nameList)
            # FIXME! # according to cmdbfree.h there is no FreeCMDBattributeValueListList!
            # self.Free(attributeValueListList)
            return (zip(names, values), numMatches)

    class erCMDB(erCMDB20):
        pass
