#! /usr/bin/env python
# -*- coding: utf-8 -*-
#######################################################################
#
# This is the pythonic layer on top of pyars.
# (C) 2004-2015 by Ergorion
#
# Currently supported Version: V5.1.-V8.1.0 of the Remedy API
#
#######################################################################
#
# known issues:
#

from ctypes import c_ulong, c_long, c_double, c_int, c_uint, byref,\
                    pointer, c_char_p
import exceptions
import time

from pyars import cars
#from pyars.ars import ARS, my_byref, pyARSNotImplemented
from pyars import ars

class ARError(exceptions.Exception):
    def __init__(self, arsSession = None, msgText = None, msgType = cars.AR_RETURN_WARNING):
        '''You can raise an ARError exception with an ars session or a message.
If msgType is set, it is assumed that you do want to use msgText as the
exception text; otherwise, the status list from arsSession will be read 
and used as the message.
Input: (optional) arsSession
       (optional) msgText
       (optional) msgType (can be AR_RETURN_OK, AR_RETURN_WARNING, AR_RETURN_ERROR)
Output: n/a'''
        if msgType is not None:
            self.messageType = msgType
            self.messageNum = 0
            self.messageText =  msgText
            return
        if arsSession is not None and arsSession.arsl is not None and arsSession.arsl.numItems > 0:
            arstatusStruct = arsSession.arsl.statusList[0]
        self.messageType = arstatusStruct.messageType
        self.messageNum = arstatusStruct.messageNum
        self.messageText = arsSession.statusText()
#        arstatusStruct.messageText
#        if arstatusStruct.appendedText:
#                self.messageText =  '%s\n%s' % (self.messageText,
#                                                arstatusStruct.appendedText)
        return
        
    def __str__(self):
        return 'An %s (%d) occured: %s' % (cars.ars_const['AR_RETURN'][self.messageType],
                                     self.messageNum,
                                     self.messageText)

class erARS51(ars.ARS):
    
    def __init__(self, server='', user='', password='', language='', 
               authString = '',
               tcpport = 0,
               rpcnumber = 0):
        super(erARS51, self).__init__(server, user, password, language,
                       authString, tcpport, rpcnumber)
        if server != '':
            self._InitializeCache()

    def __enter__(self):
        self.logger.debug('enter __enter__ of context manager')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.debug('enter __exit__ of context manager')
        if exc_type is not None:
            pass # Exception occurred
        self.Logoff()

    def _InitializeCache(self):
        '''InitializeCache setup the internal cache for objects retrieved
from server. This cache has a common structure:
{ 'type_of_object' : 
    {schema :
        { id : object }
    }
}
as 'type_of_object' are currently supported: alink, fields, filter and schema.
for alink and filter the name is the id, for fields it is the fieldid, for
schema (the schema definition itself) it is the string "default".
With this setup we can define one single function to retrieve objects from
the cache.'''
        self._cacheTimeout = 10 * 60
        self.cache = {'alink' : {},
                      'fields': {},
                      'filter': {},
                      'schema': {}}

    def _RetrieveObjectFromCache(self, typeOfObject,
                                 schema,
                                 objectId):
        '''Return a certain object from the cache if it was retrieved before
and has not timed out yet.
Input: typeOfObject (can be either  'alink', 'fields', 'filter', 'schema', 'fieldtable')
        schema (name of schema that the field belongs to; for alink and filter this is 'default')
        objectId (something to identify (in case of 'schema' or 'fieldtable', this is 'default')
Output: object or None'''
        now = time.time()
        if self.cache[typeOfObject].has_key(schema):
            if self.cache [typeOfObject][schema].has_key(objectId):
                (object_, timestamp) = self.cache [typeOfObject][schema][objectId]
                if now - timestamp < self._cacheTimeout:
                    self.logger.debug('_RetrieveObjectFromCache: return info for %s:%s:%s from cache' % (
                                      schema, typeOfObject, objectId))
                    if object_ is None:
                        self.errnr = 2 # simulate an error
                    return object_
                else: # after cache timeout
                    self.ARFree(object_)
        else: # if the cache does not know this schema yet!
            self.cache [typeOfObject].update({schema: {}})

    def _StoreObjectInCache(self, typeOfObject, schema, objectId, object_):
        self.cache[typeOfObject][schema][objectId] = (object_, time.time())

    def conv2ContainerTypeList(self, containerArray):
        '''take a list of containerTypes and return a ARContainerTypeList

Input: ARContainerTypeList, None, or integer or list of integers
Output: ARContainerTypeList
            if input is an integer, then the list contains just the integer
            if input is None, then the list contains ARCON_ALL
            otherwise, the ARContainerTypeList contains all the values 
            contained in the argument'''
        if isinstance(containerArray, cars.ARContainerTypeList):
            return containerArray
        if containerArray is None:
            containerArray = [cars.ARCON_ALL]
        elif isinstance(containerArray,int):
            containerArray = [containerArray]
        # we have received an array and have to translate it into
        # the remedy structure ARContainerTypeList
        tempArray = (c_int * len(containerArray))()
        tempArray[:] = containerArray[:]
        return cars.ARContainerTypeList(len(containerArray), tempArray)

    def conv2EntryIdList(self, schemaString, entry):
        '''conv2EntryIdList will try to create an AREntryIdList for either
a simple schema/entryid or a joinform/joinentryid or
joinform/list_of_entryids
input: schemaString: name of schema
       entry: can be an integer or a string or a tuple/array/list 
            of (entryid1, entryid2)
output: AREntryIdList'''
        
        def createSchemaIdList(schemaString, entry):
            '''take a schemaString and a list of entryIds; starting
with this schema, try to find out all involved schemas
for the entryids (e.g. simple joins, joins of joins...)
Input: schemaString: name of schema
        entry: array of entry ids
Output: ((schema1, entryid1), (schema2, entryid2), ...) or None in case of failure'''
#            self.logger.debug('createSchemaIdList: %s and %s' % (
#                    schemaString, entry))
            # first check if length of tuple == 1: it's not for a join...
            # it just happens to be in a tuple; this time we just assume
            # it's a string, we don't check for integers any more...
            if len(entry) == 1:
                return ((schemaString, entry[0]), )
            else:
                # self.logger.debug('    assuming a join, fetching schema')
                # Assumption here:
                # it is a join schema;  so we need to find the names of the 
                # underlying forms
                # in order to find out the max. length of the entry ids!
                self.logger.debug('looking up %s' % schemaString)
                try:
                    schema = self.GetSchema(schemaString)
                except ARError:
                    self.logger.error(self.statusText())
                    return None
                # as we can have joins of joins, we need to 
                # call ourselves recursively
                if schema.schema.schemaType == cars.AR_SCHEMA_JOIN:
                    # if one of the following calls fails, the result
                    # exception will not be caught. This is on purpose!
                    # otherwise the cause for not returning a useful result
                    # will not be known. 
                    schemaA = self.GetSchema(schema.schema.u.join.memberA)
                    schemaB = self.GetSchema(schema.schema.u.join.memberB)
                    if schemaA.schema.schemaType == cars.AR_SCHEMA_JOIN and \
                        schemaB.schema.schemaType == cars.AR_SCHEMA_JOIN:
                        return (createSchemaIdList(schema.schema.u.join.memberA,
                                                   entry[:len(entry)/2])+
                                createSchemaIdList(schema.schema.u.join.memberB, 
                                                   entry[len(entry)/2:]))
                    elif schemaA.schema.schemaType == cars.AR_SCHEMA_JOIN:
                        return (createSchemaIdList(schema.schema.u.join.memberA,
                                                   entry[:-1])+
                               ((schema.schema.u.join.memberB, entry[-1]),)
                                )
                    elif schemaB.schema.schemaType == cars.AR_SCHEMA_JOIN:
                        return (((schema.schema.u.join.memberA, entry[0]),)+
                                createSchemaIdList(schema.schema.u.join.memberB,
                                                   entry[1:])
                                )
                    else:
                        return ((schema.schema.u.join.memberA, entry[0]),
                                (schema.schema.u.join.memberB, entry[1]))
                else: # this should actually not happen!
                    # we assume we have a join schema, but the schemaType is not join?
                    # throw an error!
                    self.logger.error('''createSchemaIdList: wrong type of entry id %s 
for this schema %s''' % (entry, schemaString))
                    self.errnr = 2
                    return None

#        self.logger.debug('conv2EntryIdList for %s and %s' % (
#                schemaString, entry))
        if isinstance(entry, cars.AREntryIdList):
            return entry
        if entry is None:
            return None
        self.errnr = 0
        # if we are handed over a tuple as the id, it means that the id is for a join schema
        # in order to handle a single string or tuple the same way, we generate a tuple from the
        # string
        if isinstance(entry, unicode): # try to convert to standard string
            entry = str(entry)
        if isinstance(entry, str) and entry.find('|') < 0: # no | found
            entrylist = ((schemaString, entry), )
        elif isinstance(entry, (long, int)):
            entrylist = ((schemaString, str(entry)), )
        else:
            # we were given a tuple for the entry id
            # either via a tuple or via a concatenated string --> split the string:
            if isinstance(entry, str) and entry.find('|') > -1:
                entry = entry.split('|')
            # this smells like join, so hand it over to the specialized
            # function, that can handle recursion
            entrylist = createSchemaIdList(schemaString, entry)
            self.logger.debug('result of schemaIdList: %s!' % (str(entrylist)))
            if self.errnr > 1:
                return None
        # now generate the AREntryIdList from the handed over ids for the API call
        tempArray = (cars.AREntryIdType * len(entrylist))()
        # construct a temporary array
        for i in range(len(entrylist)):
            # as we had only trouble with the padEntry, I guess 
            # people should do this before calling this function!
            filler = '\0' * (cars.AR_MAX_ENTRYID_SIZE-len(entrylist[i][1])+1)
            tempArray[i][:] = (entrylist[i][1]+filler)[:]
        return cars.AREntryIdList(len(entrylist), tempArray)
#
#
### this used to be the old code that tries to
### do a padEntry as well...
#        fi = self.GetField (entrylist[i][0], 1)
#        if self.errnr > 1:
#            self.logger.error('    : GetField(%s, 1) failed!' % entrylist[i][0])
#            return None
#        # we know that entryIds are chars!
#        # it is important for padEntry not to take the limits of the join
#        # schema, but of the underlying original forms...!
#        try:
#            # for debugging purposes I split this into two lines and
#            # assign a temp variable
#            result = self.padEntryid(entrylist[i][1], 
#                                fi.defaultVal.u.charVal,
#                                fi.limit.u.charLimits.maxLength)
#            # self.logger.debug('padEntryid returned for %d a string of length %d' % (
#            #        (fi.limit.u.charLimits.maxLength, len(result))))
#            
#            tempArray[i][:] = result [:]
#            self.logger.debug('    generating id %s' % (result))
#        except ValueError:
#            self.logger.error('    wrong length of id: %s' % (result))
#            self.errnr = 2
#            return None

        
    def conv2EntryIdListList (self, schema, entryIdArray):
        '''take an array of entryids and convert them to a
AREntryIdListList. 
Input: schema (not used any more)
       entryIdArray (pythonic list of entryids)
Output: AREntryIdListList'''
        if isinstance(entryIdArray, cars.AREntryIdListList):
            return entryIdArray
        tempArray = (cars.AREntryIdType * len(entryIdArray))()
        for i in range(len(entryIdArray)):
            # TODO: here we need the exact field information for
            # padEntryid!
            tempArray[i][:] = self.padEntryid(entryIdArray[i])[:]
        # this is a list of lists!
        # the question now is which one stores the single entry ids
        # to retrieve? First try: the inner list

        secondList = (cars.AREntryIdList * len(entryIdArray))()
        for i in range(len(entryIdArray)):
            secondList[i].numItems = 1
            secondList[i].entryIdList = pointer(tempArray[i])
            
        return cars.AREntryIdListList(len(entryIdArray), secondList)

    def conv2EntryListFieldList(self, fieldList, schema):
        '''conv2EntryListFieldList: take a tuple/array/list of 
(fieldId, column width, seperator)
and return an AREntryListFieldList. This is useful
to control the output of GetListEntry and others...
future improvement: if columnwidth and/or seperator are not given,
take the information from the schema...'''
        if isinstance(fieldList, cars.AREntryListFieldList):
            return fieldList
        if not fieldList:
            return None
        try:
            tempArray = (cars.AREntryListFieldStruct * len(fieldList))()
            for i in range(len(fieldList)):
                if isinstance (fieldList[i], (long, int, str)):
                    # self.logger.debug(' found a fieldid, no additional info')
                    tempArray[i].fieldId = int(fieldList[i])
                    # setting sensible defaults -- we could look them up
                    # in the schema definition!
                    tempArray[i].columnWidth = 10
                    tempArray[i].separator = ''
                elif isinstance (fieldList[i], (tuple, list)): # assuming a tuple with at least the id
                    # self.logger.debug(' found a tuple with fieldid and additional info')
                    tempArray[i].fieldId = int(fieldList[i][0])
                    try:
                        tempArray[i].columnWidth = fieldList[i][1]
                    except KeyError:
                        tempArray[i].columnWidth = 10
                    try:
                        tempArray[i].separator = fieldList[i][2]
                    except KeyError:
                        tempArray[i].separator = ''
                else: # just try to convert to int...
                    try:
                        tempArray[i].fieldId = int(fieldList[i])
                    except ValueError:
                        self.logger.error('conv2EntryListFieldList: TypeError at position %d' % i)
            return cars.AREntryListFieldList (len(fieldList), tempArray)
        except TypeError:
            self.logger.error('conv2EntryListFieldList: TypeError')
            self.errnr = 2
            return None 

    def conv2FieldValueList(self, schema, fieldList):
        '''conv2FieldValueList: take a dict or a tuple/array/list of (fieldId, value)
and return an ARFieldValueList
the schema used to be necessary as this function tried to get
more detailed information about the fields.
Special case attachment: (fieldId, (name, origSize, compSize, filename))
             *please note* only filenames currently supported, no buffers!
Special case coords: (fieldid, (numItems, x1, y1, x2, y2...))'''
        if isinstance(fieldList, cars.ARFieldValueList):
            return fieldList
        if fieldList is None:
            return None
        # create a temporary array that we will assign to the fieldvaluelist
        # afterwards....
        tempArray = (cars.ARFieldValueStruct * len(fieldList))()
        if isinstance(fieldList, (tuple, list)):
            for i in range(len(fieldList)):
                tempArray[i].fieldId = fieldList[i][0]
                self.conv2ValueStruct(tempArray[i].value,
                                      fieldList[i][1])
        elif isinstance(fieldList, dict):
            for (fieldId, i) in zip(fieldList.keys(), range(len(fieldList))):
                tempArray[i].fieldId = fieldId
                self.conv2ValueStruct(tempArray[i].value,
                                      fieldList[fieldId])
        return cars.ARFieldValueList(len(fieldList), tempArray)

            # now create the correct ARValueStruct!
            # first find out which datatype this field has:
#                fi = self.GetField(schema, fieldList[i][0])
#                if self.errnr > 1:
#                    self.logger.error('''conv2FieldValueList: could not lookup field: %d!''' % (
#                                            fieldList[i][0]))
#                    return None
            # tempArray[i].value.dataType = fi.dataType
            # self.logger.debug('''conv2FieldValueList: fieldId: %d, type: %d/%s!!!''' % (
            #       fieldList[i][0], fi.dataType, cars.ars_const['AR_DATA_TYPE'][fi.dataType]))
            # numerical types should not be a problem
            # AR_DATA_TYPE_NULL ???
            # does this work? we hand over the ARValueStruct
            # by reference and conv2ValueStruct sets the members
            # correctly...
#            self.conv2ValueStruct(tempArray[i].value,
#                                  fieldList[i][1],
#                                  fi.dataType)
  

    def conv2FullTextInfoRequestList(self, requestArray):
        '''conv2FullTextInfoRequestList: take a tuple/array/list of integers
and return an ARFullTextInfoRequestList:
    
>>> res=ar.conv2FullTextInfoRequestList((1, 2, 3))
>>> print res.numItems
3
>>> print res.requestList[2]
3'''
        if isinstance(requestArray, cars.ARFullTextInfoRequestList):
            return requestArray
        if isinstance(requestArray, int):
            requestArray = [requestArray]
        elif isinstance(requestArray, str):
            requestArray = [int(requestArray)]
        if isinstance(requestArray, (tuple, list)):
            tempArray = (c_uint * len(requestArray))()
            tempArray[:] = requestArray[:]
            return cars.ARFullTextInfoRequestList(len(requestArray),
                                                       tempArray)
        else:
            return None

    def conv2InternalIdList (self, idList):
        '''take an array of internal fieldids (or a single int)
and return ARInternalIdList'''
        if isinstance(idList, cars.ARInternalIdList):
            return idList
        if isinstance(idList, int):
            idList = [idList]
        elif isinstance(idList, str):
            idList = [int(idList)]
        if isinstance(idList, (tuple, list)):
            tempArray = (cars.ARInternalId * len(idList))()
            for i in range(len(idList)):
                tempArray[i] = idList [i]
            return cars.ARInternalIdList (len(idList), tempArray)
        else:
            return None

    def conv2NameList(self, names):
        '''take a list of names and convert it to an ARNameList'''
        if isinstance(names, cars.ARNameList):
            return names
        if names is None:
            return None
        tempArray = (cars.ARNameType * len(names))()
        temp = '\0' * 255
        for i in range(len(names)):
            tempArray[i][:] = names[i][:]+temp[:255-len(names[i])]
        return cars.ARNameList(len(names), tempArray)

    def conv2PermList(self, permArray):
        '''take a list of (groupid, permission) and turn it
into an ARPermissionList'''
        if isinstance(permArray, cars.ARPermissionList):
            return permArray        
        tempArray = (cars.ARPermissionStruct * len(permArray))()
        for i in range(len(permArray)):
            tempArray[i].groupId = permArray [i][0]
            tempArray[i].permissions = permArray [i][1]
        return cars.ARPermissionList(len(permArray), tempArray)

    def conv2QualifierStruct(self, schema, query, displayTag=None):
        if query is None:
            return None
        elif isinstance(query, cars.ARQualifierStruct):
            return query
        else:
            q = cars.ARQualifierStruct()
            self.errnr = self.arapi.ARLoadARQualifierStruct(byref(self.context),
                                                   schema,
                                                   displayTag,
                                                   query,
                                                   byref(q),
                                                   byref(self.arsl))
            if self.errnr > 1:
                self.logger.error ('conv2QualifierStruct: LoadQualifier failed!')
                raise ARError(self)
            return q

    def conv2ReferenceTypeList(self, refList):
        '''take list of reference types and return an ARReferenceTypeList'''
        if isinstance(refList, cars.ARReferenceTypeList):
            return refList
        if isinstance(refList, int):
            refList = [refList]
        tempArray = (c_int * len(refList))() # FIXME cars.c_int
        try:
            if len(refList) > 1: # bug in ctypes?
                tempArray [:] = refList[:]
            else:
                tempArray [0] = refList[0]
            return cars.ARReferenceTypeList(len(refList), tempArray)
        except ValueError:
            self.logger.error('conv2ReferenceTypeList: received reflist: %s' % (
                                                            refList))

    def conv2ServerInfoList(self, serverInfoList):
        if isinstance(serverInfoList, cars.ARServerInfoList):
            return serverInfoList
        tempArray = (cars.ARServerInfoStruct * len(serverInfoList))()
        if isinstance(serverInfoList, dict):
            for (i, operation) in enumerate(serverInfoList.keys()):
                tempArray[i].operation = operation
                self.conv2ValueStruct(tempArray[i].value, serverInfoList[operation])
        if isinstance(serverInfoList, (list, tuple)):
            for i in range(len(serverInfoList)):
                tempArray[i].operation = serverInfoList[i][0]
                self.conv2ValueStruct(tempArray[i].value, serverInfoList[i][1])
        return cars.ARServerInfoList(len(serverInfoList), tempArray)

    def conv2ServerInfoRequestList(self, requestArray):
        '''take a tuple of serverinforequests and return a ARServerInfoRequestList'''
        if isinstance(requestArray, cars.ARServerInfoRequestList):
            return requestArray
        if isinstance(requestArray, int):
            requestArray = [requestArray]
        tempArray = (c_uint * len(requestArray))()
        try:
            tempArray[:] = requestArray[:]
            return cars.ARServerInfoRequestList(len(requestArray),tempArray)
        except ValueError:
            self.logger.error('conv2ServerInfoRequestList: received requestArray: %s' % (
                                                            requestArray))
            
    def conv2SortList(self, fieldList):
        '''conv2SortList: take a tuple/array/list of (fieldId, de/ascending)
and return an ARSortList; ascending is 1 (or string beginning with 'a'), 
descending is 2 (or string beginning with 'd').
default is ascending order.'''
        if isinstance(fieldList, cars.ARSortList):
            return fieldList        
        if not fieldList:
            return None
        try:
            tempArray = (cars.ARSortStruct * len(fieldList))()
            for i in range(len(fieldList)):
                if isinstance(fieldList[i], (long, int, str)):
                    tempArray[i].fieldId = int(fieldList[i])
                    tempArray[i].sortOrder = cars.AR_SORT_ASCENDING
                else:
                    tempArray[i].fieldId = fieldList[i][0]
                    if isinstance(fieldList[i][1], str):
                        if fieldList[i][1][0] == 'd':
                            tempArray[i].sortOrder = cars.AR_SORT_DESCENDING
                        else:
                            tempArray[i].sortOrder = cars.AR_SORT_ASCENDING
                    else: # assumption: integer 1 or 2
                        tempArray[i].sortOrder = fieldList[i][1]
            return cars.ARSortList (len(fieldList), tempArray)
        except TypeError:
            self.logger.error('conv2SortList: ran into a TypeError with fieldList: %s!' % (
                                                                   fieldList))
            self.errnr = 2
            return None

    def conv2StructItemList(self, itemArray):
        '''conv2StructItemList takes a list of ints and names and converts
it into a ARStructItemList; currently the namelist (as the third entry)
for selected elements is not supported'''
        if isinstance(itemArray, cars.ARStructItemList):
            return itemArray  
        structItems = (cars.ARStructItemStruct * len(itemArray)) ()
        for i in range(len(itemArray)):
            structItems[i].type = itemArray[i][0] # c_uint(itemArray[i][0])
            structItems[i].name = itemArray[i][1] # create_string_buffer(itemArray[i][1], cars.AR_MAX_NAME_SIZE + 1)
            structItems[i].selectedElements = cars.ARNameList()
        return cars.ARStructItemList(len(itemArray), structItems)
            
    def conv2TimestampList (self, ratioTimestamps):
        '''conv2TimestampList takes a list of ints and converts it
into an ARTimestampList; if None is handed over, the default
is to return a list with one entry of AR_CURRENT_CURRENCY_RATIOS.'''
        if isinstance(ratioTimestamps, cars.ARTimestampList):
            return ratioTimestamps  
        if not ratioTimestamps:
            ratioTimestamps = [cars.AR_CURRENT_CURRENCY_RATIOS]
        tempArray = (cars.ARTimestamp * len(ratioTimestamps))()
        tempArray[:] = ratioTimestamps[:]
        return cars.ARTimestampList(len(ratioTimestamps), tempArray)
 
    def conv2ValueStruct(self, valueStruct, value, dataType = None):
        '''take a value and set the members of valueStruct according to
dataType
Input: valueStruct (ARValueStruct that will be modified inplace)
        value (the actual value)
        (optional) dataType (the dataType to be used)
Output: none'''
        if isinstance(value, cars.ARValueStruct):
            return value  
        if dataType is None:
            if isinstance(value, (int, long)):
                valueStruct.dataType = cars.AR_DATA_TYPE_INTEGER
                valueStruct.u.intVal = c_long(value)
                return
            elif isinstance(value, float):
                valueStruct.dataType = cars.AR_DATA_TYPE_REAL
                valueStruct.u.realVal = c_double(value)
                return
            elif isinstance(value, unicode):
                valueStruct.dataType = cars.AR_DATA_TYPE_CHAR
                valueStruct.u.charVal = value
                return
            elif isinstance(value, str):
                valueStruct.dataType = cars.AR_DATA_TYPE_CHAR
                valueStruct.u.charVal = value
                return
            if isinstance(value, tuple) and len(value) == 4:
                # this is an attachment! 
                # value should look like (name, origSize, compSize, filename)
                attachment = cars.ARAttachStruct()
                attachment.name = value[0]
                attachment.origSize = value[1]
                attachment.compSize = value[2]
                attachment.loc = cars.ARLocStruct(cars.AR_LOC_FILENAME)
                attachment.loc.u.filename = value[3]
                valueStruct.dataType = cars.AR_DATA_TYPE_ATTACH
                valueStruct.u.attachVal = pointer(attachment)
            elif value is None:
                valueStruct.dataType = cars.AR_DATA_TYPE_NULL
                return
            else:
                self.logger.error("conv2ValueStruct: don't really know how to handle %s, will try string" % (
                                  value))
                valueStruct.dataType = cars.AR_DATA_TYPE_CHAR
                valueStruct.u.charVal = str(value)
                return

# open issue: what happens when:
# 2) keyword with _INTEGER?
# 3) DATE with _INTEGER?
# solved:
# DECIMAL can be set with integer
# TIME can be set with integer
# enum can be set with integer
# worklog with string...

        else: # dataType is handed over...
            valueStruct.dataType = dataType
            if dataType == cars.AR_DATA_TYPE_KEYWORD:
                valueStruct.u.keyNum = c_uint(int(value))
            elif dataType == cars.AR_DATA_TYPE_INTEGER:
                valueStruct.u.intVal = c_long(int(value))
            elif dataType == cars.AR_DATA_TYPE_REAL:
                valueStruct.u.realVal = c_double(float(value))
            elif dataType == cars.AR_DATA_TYPE_CHAR:
                valueStruct.u.charVal = str(value) # my_byref(value)
            elif dataType == cars.AR_DATA_TYPE_DIARY:
                valueStruct.u.diaryVal = ars.my_byref(value)
            elif dataType == cars.AR_DATA_TYPE_ENUM:
                valueStruct.u.enumVal = c_ulong(int(value))
            elif dataType == cars.AR_DATA_TYPE_TIME:
                valueStruct.u.timeVal = cars.ARTimestamp(long(value))
            elif dataType == cars.AR_DATA_TYPE_BITMASK:
                valueStruct.u.maskVal = c_ulong(int(value))
            elif dataType == cars.AR_DATA_TYPE_TIME_OF_DAY:
                valueStruct.u.timeOfDayVal = cars.ARTime(long(value))
            # this requires an union!!!!
            elif dataType == cars.AR_DATA_TYPE_BYTES:
                valueStruct.u.byteListVal = ars.my_byref(value)
            elif dataType == cars.AR_DATA_TYPE_DECIMAL:
                # this is analog to charVal
                valueStruct.u.decimalVal = str(value) # mybyref
            # this requires an union!!!!
            elif dataType == cars.AR_DATA_TYPE_ATTACH:
                tempLocStruct = cars.ARLocStruct()
                # at this time we only support filenames in here!
                tempLocStruct.locType = cars.AR_LOC_FILENAME
                # FIXME: currently this is not supported!
                self.logger.error('*Attachments not yet supported! inserting default values*')
                tempLocStruct.u.filename = 'testfilename'
                valueStruct.attachVal = None
    #                    tempLocStruct.u.filename = value[3]
    #                    tempAttachStruct = cars.ARAttachStruct(value[0],
    #                                                     value[1],
    #                                                     value[2],
    #                                                     tempLocStruct)
    #                    valueStruct.attachVal = byref(tempAttachStruct)
            # TODO: this requires an union!!!!
            elif dataType == cars.AR_DATA_TYPE_CURRENCY:
                valueStruct.u.currencyVal = value
            elif dataType == cars.AR_DATA_TYPE_DATE:
                valueStruct.u.dateVal = value
            elif dataType == cars.AR_DATA_TYPE_ULONG:
                valueStruct.u.ulongVal = value
            elif dataType == cars.AR_DATA_TYPE_ATTACH_POOL:
                valueStruct.u.keyNum = value
            # TODO: test this!!!
            elif dataType == cars.AR_DATA_TYPE_COORDS:
                tempCoordList = cars.ARCoordList()
                tempCoordList.numItems = value[0]
                tempCoordArray = cars.ARCoordStruct() * tempCoordList.numItems
                for i in range(tempCoordList.numItems):
                    tempCoordArray[i].x = value[i*2+1]
                    tempCoordArray[i].y = value[i*2+2]
                tempCoordList.coords = tempCoordArray
                valueStruct.u.coordListVal = byref(tempCoordList)
            else:
                self.logger.debug('''conv2ValueStruct: unknown type: %d!!!''' % (
                    dataType))
                self.errnr = 2
                return None
#        except TypeError:
#            if value == None or value == '':
#                # correc the data type -- we don't have any value to assign
#                valueStruct.dataType = cars.AR_DATA_TYPE_NULL
#            else:
#                self.logger.debug('''conv2ValueStruct: TypeError 
#                 while trying to convert: (%d, %s)''' % (dataType,
#                                                     value))
#                self.errnr = 2
#                return None  

    def convAccessNameList2List(self, obj):
        return [obj.nameList[i].value
                for i in range(obj.numItems)]

    def convBooleanList2List(self, booleanList):
        return [booleanList.booleanList[i]  and True or False 
                for i in range(booleanList.numItems)]

    def convDispInstList2Dict(self, dispInstList):
        '''droppes the common properties and returns as a dict
the VUIds, with the display property lists as dicts
for each VUI'''
        return dict([[dispInstList.dInstanceList[i].vui, 
                     self.convPropList2Dict(dispInstList.dInstanceList[i].props)]
                     for i in range(dispInstList.numItems)])
    
    def convEntryIdList2String(self, entryId):
        '''we received an AREntryIdList (e.g. from GetListEntry) for
a single entry (e.g. in a join form) and need this to be
flatened out in a string'''
        if entryId is None:
            self.logger.error('convEntryIdList2String: received None as entryId')
            return None
        if isinstance (entryId , str):
            self.logger.error('convEntryIdList2String: received simple string')
            return entryId
        return '|'.join([entryId.entryIdList[i].value for i in range(entryId.numItems)])

    def convEntryIdListList2List(self, obj):
        '''if you want to convert an AREntryIdListList (e.g. from ARGetListEntry) for
multiple entries into a pythonic list of entryid strings.'''
        return [self.convEntryIdList2String(obj.entryIdList[i])
                for i in range(obj.numItems)]

    def convEntryListFieldValueList2Dict(self, obj):
        '''take an AREntryListFieldValueList (e.g. result of
GetListEntryWithFields) and return a dictionary:
    {entryid1: {fid1: value, fid2: value...}, entryid2: ....}'''
        return dict([self.convEntryListFieldValueStruct2List(obj.entryList[i])
                    for i in range(obj.numItems)])

    def convEntryListFieldValueList2List(self, obj):
        '''take an AREntryListFieldValueList (e.g. result of
GetListEntryWithFields) and return a list:
    ((entryid1, {fid1: value, fid2: value...}), (entryid2, {}),  ....)'''
        return [self.convEntryListFieldValueStruct2List(obj.entryList[i])
                    for i in range(obj.numItems)]
                            
    def convEntryListFieldValueList2StringDict(self, obj):
        '''take an AREntryListFieldValueList (e.g. result of
GetListEntryWithFields) and return a dictionary:
    {entryid1: {"fid1": value, "fid2": value...}, entryid2: ....} '''
        return dict([self.convEntryListFieldValueStruct2StringList(obj.entryList[i])
                    for i in range(obj.numItems)])

    def convEntryListFieldValueStruct2List(self, obj):
        '''take an AREntryListFieldValueStruct and return 
[entryid, {fid1: value, fid2:value, ...}]'''
        return [self.convEntryIdList2String(obj.entryId), 
                self.convFieldValueList2Dict(obj.entryValues.contents)]

    def convEntryListFieldValueStruct2StringList(self, obj):
        '''take an AREntryListFieldValueStruct and return 
[entryid, {"fid1": value, "fid2":value, ...}]; the dict
can be passed to a template string.'''
        return [self.convEntryIdList2String(obj.entryId), 
                self.convFieldValueList2StringDict(obj.entryValues.contents)]
                
    def convEntryListList2EntryIdListList(self, obj):
        '''EntryListList is returned by GetListEntry, but GetMultipleEntries
expects a EntryIdListList -- this function will convert it'''
        tempArray = (cars.AREntryIdList * obj.numItems)()
        tempArray [:] = [obj.entryList[i].entryId for i in range(obj.numItems)]
        return cars.AREntryIdListList (obj.numItems, tempArray)

    def convEntryListList2Dict(self, obj):
        '''return a dictionary of {entryid: shortdesc, ....} (output of GetListEntry)'''
        return dict(self.convEntryListList2List(obj))

    def convEntryListList2List(self, obj):
        '''return a list of (entryid, shortdesc) (output of GetListEntry)'''
        return [(self.convEntryIdList2String(obj.entryList[i].entryId), 
                obj.entryList[i].shortDesc)
                for i in range(obj.numItems)]

    def convEnumLimitsStruct2Dict (self, eLS):
        return dict(self.convEnumLimitsStruct2List(eLS))
    
    def convEnumLimitsStruct2List (self, eLS):
        '''take an AREnumLimitsStruct and generate a python list out of it.
ATTENTION: For AR_ENUM_STYLE_QUERY style EnumLimitsStruct, we should
    execute the query!
Input: AREnumLimitsStruct
Output: ('execute query on', queryList.server,
                    queryList.schema, 
                    queryList.qualifier,
                    queryList.nameField, 
                    queryList.numberField)'''
        if eLS.listStyle == cars.AR_ENUM_STYLE_REGULAR:
            return [(i, eLS.u.regularList.nameList[i].value)
                        for i in range(eLS.u.regularList.numItems)]
        elif eLS.listStyle == cars.AR_ENUM_STYLE_CUSTOM:
            return [(eLS.u.customList.enumItemList[i].itemNumber,
                     eLS.u.customList.enumItemList[i].itemName)
                    for i in range(eLS.u.customList.numItems)]
        elif eLS.listStyle == cars.AR_ENUM_STYLE_QUERY:
            # TODO: retrieve the list
            return ('execute query on', eLS.u.queryList.server,
                    eLS.u.queryList.schema, 
                    eLS.u.queryList.qualifier,
                    eLS.u.queryList.nameField, 
                    eLS.u.queryList.numberField )
        else:
            self.logger.error('unknown list style (%d) in AREnumLimitsStruct!' %
                              eLS.listStyle)
            raise ValueError

    def convFieldValueStruct2List (self, obj):
        '''take an ARFieldValueStruct and return [fieldid, value]'''
        return [obj.fieldId, self.convValueStruct2Value(obj.value)]

    def convFieldValueStruct2StringList (self, obj):
        '''take an ARFieldValueStruct and return [str(fieldid), value] '''
        return [str(obj.fieldId), self.convValueStruct2Value(obj.value)]
        
    def convFieldValueList2Dict (self, obj):
        '''take an ARFieldValueList and returns a dictionary of
fieldid: value for all fieldids in the list'''
        return dict([self.convFieldValueStruct2List(obj.fieldValueList[i])
                for i in range(obj.numItems)])

    def convFieldValueList2StringDict (self, obj):
        '''take an ARFieldValueList and returns a dictionary of
str(fieldid): value for all fieldids in the list; this is
especially useful in combination with string formatting, then
you can have: 'value of fieldid: %(1)s' % dict'''
        return dict([self.convFieldValueStruct2StringList(obj.fieldValueList[i])
                for i in range(obj.numItems)])
                
    def convFieldValueListList2List (self, obj):
        '''take an ARFieldValueListList and returns a list of
[{fieldid: value for all fieldids in the list}]'''
        return [self.convFieldValueList2Dict(obj.valueListList[i])
                for i in range(obj.numItems)]

    def convGroupInfoList2Dict(self, obj):
        return dict([self.convGroupInfoStruct2List(obj.groupList[i])
                for i in range(obj.numItems)])
    
    def convGroupInfoStruct2List(self, obj):
        return (obj.groupId, (obj.groupType, 
                              self.convAccessNameList2List(obj.groupName), 
                              obj.groupCategory))
        
    def convInternalIdList2List(self, idList):
        return [idList.internalIdList[i] for i in range(idList.numItems)]

    def convNameList2List (self, nameList):
        '''generate a python list out of an ARNameList'''
        return [nameList.nameList[i].value for i in range(nameList.numItems)]

    def convObjectChangeTimestampList2List(self, obj):
        return [(obj.objectChanges[i].objectType,
                 obj.objectChanges[i].createTime,
                 obj.objectChanges[i].changeTime,
                 obj.objectChanges[i].deleteTime) for i in range(obj.numItems)]
        
    def convPermissionList2Dict(self, obj):
        '''convert a permissionList to a dictionary of [groupId: right]'''
        return dict([(obj.permissionList[i].groupId, obj.permissionList[i].permissions)
                     for i in range(obj.numItems)])

    def convPropList2Dict(self, obj):
        return dict([(obj.props[i].prop, self.convValueStruct2Value(obj.props[i].value))
                    for i in range (obj.numItems)])
        
    def convServerInfoList2Dict(self, serverInfoList):
        return dict(self.convServerInfoList2List(serverInfoList))

    def convServerInfoList2ExpDict(self, serverInfoList):
        return dict(self.convServerInfoList2ExpList(serverInfoList))
    
    def convServerInfoList2ExpList(self, serverInfoList):
        '''lookup the operation and return the string explanation for it; if the
lookup fails for any value, we just return the list with the numerical values'''
        try:
            return [(cars.ars_const['AR_SERVER_STAT'][serverInfoList.serverInfoList[i].operation], 
                 self.convValueStruct2Value(serverInfoList.serverInfoList[i].value)) 
                 for i in range(serverInfoList.numItems)]
        except KeyError:
            return self.convServerInfoList2List(serverInfoList)
                 
    def convServerInfoList2List(self, serverInfoList):
        return [(serverInfoList.serverInfoList[i].operation, 
                 self.convValueStruct2Value(serverInfoList.serverInfoList[i].value)) 
                 for i in range(serverInfoList.numItems)]

    def convServerNameList2List (self, serverNameList):
        return [serverNameList.nameList[i].value
                for i in range(serverNameList.numItems)]
        
    def convStatusHistoryList2List(self, statHistList):
        return [self.convStatusHistoryStruct2List(statHistList.statHistList[i]) 
                 for i in range(statHistList.numItems) ]

    def convStatusHistoryStruct2List(self, statHist):
        return [statHist.timeVal, statHist.user]

    def convUserInfoList2dict(self, userInfoList):
        return dict(self.convUserInfoList2List(userInfoList))

    def convUserInfoList2List(self, userInfoList):
        '''takes an ARUserInfoList and returns the following list:
((userName, (license, connectTime, lastAccessTime, defaultNotifier, email)), ...)'''
        return [(userInfoList.userList[i].userName, (userInfoList.userList[i].licenseInfo,
                                                     userInfoList.userList[i].connectTime,
                                                     userInfoList.userList[i].lastAccess,
                                                     userInfoList.userList[i].defaultNotifyMech,
                                                     userInfoList.userList[i].emailAddr))
                    for i in range(userInfoList.numItems)]

    def convUserLicenseList2list(self, userLicenseList):
        return [(userLicenseList.licenseList[i].licenseTag,
                 userLicenseList.licenseList[i].licenseType,
                 userLicenseList.licenseList[i].currentLicenseType,
                 userLicenseList.licenseList[i].licensePool,
                 userLicenseList.licenseList[i].appLicenseDescriptor,
                 userLicenseList.licenseList[i].lastAccess) 
        for i in range(userLicenseList.numItems)]

    def convValueStruct2Value(self, obj):
        # special handling for unicode
        if self.context.localeInfo.charSet.lower() == 'utf-8':
            if obj.dataType == cars.AR_DATA_TYPE_CHAR:
                return obj.u.charVal.decode('utf-8')
            elif  obj.dataType == cars.AR_DATA_TYPE_ATTACH:
                return (obj.u.attachVal.contents.name.decode('utf-8'), 
                        obj.u.attachVal.contents.origSize, 
                        obj.u.attachVal.contents.compSize)
        try:
            if obj.dataType in (cars.AR_DATA_TYPE_NULL,
                                cars.AR_DATA_TYPE_VIEW):
                return None
#            if obj.dataType == cars.AR_DATA_TYPE_ATTACH:
#                return (obj.u.attachVal.contents.name, 
#                        obj.u.attachVal.contents.origSize, 
#                        obj.u.attachVal.contents.compSize)
            return eval('obj.%s' % (cars.ARValueStruct._mapping_so_ [obj.dataType]))
        except KeyError:
            try: 
                return eval('%s' % (cars.ARValueStruct._mapping_co_ [obj.dataType]))
            except KeyError:
                raise ARError(None,
                              'unknown ARValueStruct type: %d!' % obj.dataType,
                              cars.AR_RETURN_ERROR)

    def convValueList2List(self, obj):
        return [self.convValueStruct2Value(obj.valueList[i])
                for i in range(obj.numItems)]

    def convValueListList2List(self, obj):
        '''a SQL command executed through ARSystem API returns a ValueListList. Per result line
you get the values of the query. This function returns a pythonic list of lists.'''
        return [self.convValueList2List(obj.valueListList[i])
                for i in range(obj.numItems)]

    def CreateActiveLink (self, 
                          name, 
                          order, 
                          schemaList, 
                          groupList, 
                          executeMask,
                          controlField = None, 
                          focusField = None, 
                          enable = True, 
                          query = None, 
                          actionList = None, 
                          elseList = None, 
                          helpText = None, 
                          owner = None,
                          changeDiary = None, 
                          objPropList = None):
        '''CreateActiveLink creates a new active link with the indicated name 
on the specified server.

CreateActiveLink creates a new active link with the indicated name 
on the specified server. The active link is added to the server 
immediately and returned to users who request information about 
active links.
Input: name (ARNameType)
       order (c_uint)
       schemaList (ARWorkflowConnectStruct)
       groupList (ARInternalIdList)
       executeMask (c_uint)
       (optional) controlField (ARInternalId, default = None)
       (optional) focusField (ARInternalId, default = None)
       (optional) enable (c_uint, default = None)
       (optional) query (ARQualifierStruct, default = None)
       (optional) actionList (ARActiveLinkActionList, default = None)
       (optional) elseList (ARActiveLinkActionList, default = None)
       (optional) helpText (c_char_p, default = None)
       (optional) owner (ARAccessNameType, default = None)
       (optional) changeDiary (c_char_p, default = None)
       (optional) objPropList (ARPropList, default = None)
Output: errnr'''
        return self.ARCreateActiveLink(name, 
                                        order, 
                                        schemaList, 
                                        groupList, 
                                        executeMask, 
                                        controlField, 
                                        focusField, 
                                        enable, 
                                        query, 
                                        actionList, 
                                        elseList, 
                                        helpText, 
                                        owner,
                                        changeDiary, 
                                        objPropList)
    
    def CreateAlertEvent(self, user, alertText, 
                         priority = 0, 
                         sourceTag = "AR", 
                         serverName = "@",
                         formName = None,
                         objectId = None):
        '''CreateAlertEvent enters an alert event.

CreateAlertEvententers an alert event on the specified server. The AR System server
sends an alert to the specified, registered users.
Input: user (ARAccessNameType)
       alertText (c_char_p)
       (optional) priority (c_int, default = 0)
       (optional) sourceTag (ARNameType, default = AR)
       (optional) serverName (ARServerNameType, default = @)
       (optional) formName (ARNameType, default = None)
       (optional) objectId (c_char_p, default = None)
Output: entryId (AREntryIdType) or None in case of error'''
        return self.ARCreateAlertEvent(user, 
                                       alertText, 
                                         priority, 
                                         sourceTag, 
                                         serverName,
                                         formName,
                                         objectId)

    def CreateCharMenu(self, name, 
                       refreshCode, 
                       menuDefn, 
                       helpText = None, 
                       owner = None,
                       changeDiary = None, 
                       objPropList = None):
        '''CreateCharMenu creates a new character menu with the indicated name.
Input: name (ARNameType)
       refreshCode (c_uint)
       menuDef (ARCharMenuStruct)
       (optional) helpText (c_char_p, default = None)
       (optional) owner (ARAccessNameType, default = None)
       (optional) changeDiary (c_char_p, default = None)
       (optional) objPropList (ARPropList, default = None)
Output: errnr'''
        return self.ARCreateCharMenu(name, 
                                     refreshCode, 
                                     menuDefn, 
                                     helpText, 
                                     owner,
                                     changeDiary, 
                                     objPropList) 

    def CreateContainer(self, name, 
                        groupList, 
                        admingrpList, 
                        ownerObjList, 
                        label, 
                        description,
                        type_,
                        references,
                        removeFlag,
                        helpText = None,
                        owner = None,
                        changeDiary = None,
                        objPropList = None):
        '''CreateContainer a new container with the indicated name.

Use this function to create
applications, active links, active link guides, filter guide, packing lists, guides,
and AR System-defined container types. A container can also be a custom type that you define.
Input: name
       groupList
       admingrpList
       ownerObjList
       label
       description
       type_
       references
       removeFlag
       helpText
       owner
       changeDiary
       objPropList
Output: /'''
        return self.ARCreateContainer(name, groupList, admingrpList, 
                                      ownerObjList, label, description,
                                        type_,references,removeFlag,helpText,
                                        owner,changeDiary,objPropList)

    def CreateEntry(self, schema, fieldList):
        '''CreateEntry creates a new entry in the indicated schema.

You can create 
entries in base schemas only. To add entries to join forms,create them 
in one of the underlying base forms.
pyars will generate the fieldList for you automatically.
Input: schema
       a tuple consisting of (fieldid, value) pairs
Output: entryId (AREntryIdType) (or raise ARError in case of error) '''
        self.errnr = 0
        fieldvalueList = self.conv2FieldValueList(schema, fieldList)
        if self.errnr > 0: # something went wrong during conversion!
            raise ARError(None, 'CreateEntry: converting field list failed!', cars.AR_RETURN_ERROR)
        result = self.ARCreateEntry(schema, fieldvalueList)
        if self.errnr > 1:
            raise ARError (self)
        return result

    def CreateEscalation(self, name, 
                         escalationTm, 
                         schemaList, 
                         enable, 
                         query = None, 
                         actionList = None,
                         elseList = None, 
                         helpText = None, 
                         owner = None, 
                         changeDiary = None, 
                         objPropList = None):
        '''CreateEscalation creates a new escalation with the indicated name.

The escalation condition
is checked regularly based on the time structure defined when it is enabled.
Input: name (ARNameType)
       escalationTm (AREscalationTmStruct)
       schemaList (ARWorkflowConnectStruct)
       enable (c_uint)
       (optional) query (ARQualifierStruct, default = None)
       (optional) actionList (ARFilterActionList, default = None)
       (optional) elseList (ARFilterActionList, default = None)
       (optional) helpText (c_char_p, default = None)
       (optional) owner (ARAccessNameType, default = None)
       (optional) changeDiary (c_char_p, default = None)
       (optional) objPropList (ARPropList, default = None)
Output: errnr'''
        return self.ARCreateEscalation(name, 
                                       escalationTm, 
                                       schemaList, 
                                       enable, 
                                       query, 
                                       actionList,
                                       elseList, 
                                       helpText, 
                                       owner, 
                                       changeDiary, 
                                       objPropList)

    def CreateField(self, schema, 
                    fieldId, 
                    reservedIdOK,
                    fieldName, 
                    fieldMap, 
                    dataType, 
                    option, 
                    createMode, 
                    defaultVal, 
                    permissions,
                    limit=None, 
                    dInstanceList=None,
                    helpText=None, 
                    owner=None, 
                    changeDiary=None):
        '''CreateField creates a new field with the indicated name on the specified server.
Input: schema (ARNameType)
        fieldId (ARInternalId)
        reservedIdOK (ARBoolean)
        fieldName (ARNameType)
        fieldMap (ARFieldMappingStruct)
        dataType (c_uint)
        option (c_uint)
        createMode (c_uint)
        defaultVal (ARValueStruct)
        permissions (ARPermissionList)
        (optional) limit (ARFieldLimitStruct, default = None)
        (optional) dInstanceList (ARDisplayInstanceList, default = None)
        (optional) helpText (c_char_p, default = None)
        (optional) owner (ARAccessNameType, default = None)
        (optional) changeDiary (c_char_p, default = None)
Output: fieldId (or None in case of failure)'''        
        newFieldId = c_int(fieldId)
        return self.ARCreateField(schema, 
                                  newFieldId, 
                                  reservedIdOK,
                                  fieldName, 
                                  fieldMap, 
                                  dataType, 
                                  option, 
                                  createMode, 
                                  defaultVal, 
                                  permissions,
                                  limit, 
                                  dInstanceList,
                                  helpText, 
                                  owner, 
                                  changeDiary)

    def CreateFilter(self, name, order, schemaList, opSet, enable, query,
                     actionList,
                     elseList=None, helpText=None, owner=None, 
                     changeDiary=None, 
                     objPropList=None):
        '''
Input:
Output:'''
        return self.ARCreateFilter(self, name, order, schemaList, opSet, 
                                   enable, query, actionList,
                     elseList, helpText, owner, changeDiary, objPropList)

    def CreateLicense(self, licenseInfo):
        '''
Input: licenseInfo
Output: '''
        return self.ARCreateLicense(licenseInfo)

    def CreateSchema(self, name, 
                     schema, 
                     groupList, 
                     admingrpList, 
                     getListFields,
                     sortList, 
                     indexList, 
                     defaultVui,
                     helpText=None, owner=None, changeDiary=None, objPropList=None):
        '''CreateSchema creates a new form with the indicated name on the specified server.
Input:
Output: '''
        return self.ARCreateSchema(self, name, schema, groupList, admingrpList,
                                   getListFields,
                     sortList, indexList, defaultVui,
                     helpText, owner, changeDiary, objPropList)

    def CreateSupportFile(self, fileType, name, id2, fileId, filePtr):
        '''CreateSupportFile creates a file that clients can retrieve by using the AR System.
Input:
Output:'''
        return self.ARCreateSupportFile(fileType, name, id2, fileId, filePtr)

    def CreateVUI(self, schema, vuiId, 
                  vuiName, 
                  locale, 
                  vuiType=None,
                  dPropList=None, 
                  helpText=None, 
                  owner=None, 
                  changeDiary=None):
        '''CreateVUI reates a new form view (VUI) with the indicated name on
the specified server.
Input:
Output:'''
        return self.ARCreateVUI(schema, vuiId, vuiName, locale, 
                  vuiType,dPropList, helpText, owner, 
                  changeDiary)

    def DateToJulianDate(self, date):
        '''DateToJulianDate converts a year, month, and day value to a Julian date.

DateToJulianDate converts a year, month, and day value to a Julian date. The Julian
date is the number of days since noon, Universal Time, on January 1, 4713
BCE (on the Julian calendar). The changeover from the Julian calendar to the
Gregorian calendar occurred in October, 1582. The Julian calendar is used
for dates on or before October 4, 1582. The Gregorian calendar is used for
dates on or after October 15, 1582.        
Input: date (a list of (year, month, day)
Output: jd'''
        return self.ARDateToJulianDate(date)

    def DecodeAlertMessage(self, message, messageLen):
        '''DecodeAlertMessage decodes a formatted alert message and returns the
component parts of the message to the alert client.

Input: message
       messageLen
Output: a list of (timestamp, sourceType, priority, alertText, sourceTag, serverName,
serverAddr, formName, objectId)'''
        return self.ARDecodeAlertMessage(message, messageLen)

    def DecodeARAssignStruct(self, assignText):
        '''DecodeARAssignStruct converts a serialized assign string in a .def file into an
ARAssignStruct structure to facilitate string import.
Input: assignText
Output: assignStruct'''
        return self.ARDecodeARAssignStruct(assignText)
        
    def DecodeARQualifierStruct(self, qualText):
        '''DecodeARQualifierStruct converts a serialized qualifier string into
an ARQualifierStruct structure.
Input: qualText
Output: qualStruct'''
        return self.ARDecodeARQualifierStruct(qualText)

    def DecodeDiary(self, diaryString):
        '''DecodeDiary parses any diary field (including the changeDiary associated with
every AR System object) into user, time stamp, and text components.

Input: diaryString
Output: diaryList'''
        return self.ARDecodeDiary(diaryString)

    def DecodeStatusHistory(self, statHistString):
        '''DecodeStatusHistory parses the Status History core field into user and
time stamp components.
Input: statHistString
Output: statHistList'''
        return self.ARDecodeStatusHistory(statHistString)

    def DeleteActiveLink(self, name):
        '''DeleteActiveLink deletes the active link with the indicated name from the
specified server and deletes any container references to the active link.
Input: name
Output: errnr'''
        return self.ARDeleteActiveLink(name)

    def DeleteCharMenu(self, name):
        '''DeleteCharMenu deletes the character menu with the indicated name from
the specified server.
Input: name
Output: errnr'''
        return self.ARDeleteCharMenu(name)

    def DeleteContainer(self, name):
        '''DeleteContainer deletes the container with the indicated name from
the specified server and deletes any references to the container from other containers.

Input: name
Output: errnr'''
        return self.ARDeleteContainer(name)

    def DeleteEntry(self, schema, entryId, option = 0):
        '''DeleteEntry deletes the form entry with the indicated ID from
the specified server.

Input: schema
       entryId
       option
Output: errnr'''
        entryIdList = self.conv2EntryIdList (schema, entryId)
        if not entryIdList: # something went wrong with the conversion
            return self.errnr
        return self.ARDeleteEntry(schema, entryIdList, option)

    def DeleteEscalation(self, name):
        '''DeleteEscalation deletes the escalation with the indicated name from the
specified server and deletes any container references to the escalation.
Input:  name
Output: errnr'''
        return  self.ARDeleteEscalation(name)
        
    def DeleteField(self, schema, fieldId, deleteOption = cars.AR_FIELD_CLEAN_DELETE):
        '''DeleteField deletes the form field with the indicated ID 
from the specified server.

Input: schema
       fieldId
       deleteOption
Output: error number'''
        return  self.ARDeleteField(schema, fieldId, deleteOption)

    def DeleteFilter(self, name):
        '''DeleteFilter deletes the filter with the indicated name from the
specified server and deletes any container references to the filter.

Input:  name
Output: errnr'''
        return self.ARDeleteFilter(name)


    def DeleteLicense(self, licenseType, licenseKey):
        '''DeleteLicense deletes an entry from the license file for the current server.

Input: licenseType
       licenseKey
Output: errnr'''
        return self.ARDeleteLicense(licenseType, licenseKey)

    def DeleteMultipleFields(self, schema, fieldList, deleteOption):
        '''DeleteMultipleFields deletes the form fields with the indicated IDs from
the specified server.

Input: schema
       fieldList
       deleteOption
Output: errnr'''
        return self.ARDeleteMultipleFields(schema, fieldList, deleteOption)

    def DeleteSchema(self, name, deleteOption = cars.AR_SCHEMA_CLEAN_DELETE):
        '''DeleteSchema deletes the form with the indicated name from the
specified server and deletes any container references to the form.

Input: name
       deleteOption
Output: errnr'''
        return self.ARDeleteSchema(name, deleteOption)

    def DeleteSupportFile(self, fileType, name, id2, fileId):
        '''DeleteSupportFile deletes a support file in the AR System.

Input: 
       fileType,
       name
       id2 (if name is not a form, set id2 to 0.)
       fileId
Output: errnr'''
        return self.ARDeleteSupportFile(fileType, name, id2, fileId)

    def DeleteVUI(self, schema, vuiId):
        '''DeleteVUI deletes the form view (VUI) with the indicated ID from the specified server.

Input: 
       schema
       vuiId
Output:'''
        return self.ARDeleteVUI(schema, vuiId)

    def DeregisterForAlerts(self, clientPort):
        '''DeregisterForAlerts cancels registration for the specified user on the
specified AR System server and port.

Input: clientPort
Output:'''
        return self.ARDeregisterForAlerts(clientPort)

    def EncodeARAssignStruct(self, assignStruct):
        '''EncodeARAssignStruct converts an ARAssignStruct structure into a serialized
assignment string.

Input: assignStruct
Output: assignText'''
        return self.AREncodeARAssignStruct(assignStruct)

    def EncodeARQualifierStruct(self, qualStruct):
        '''EncodeARQualifierStruct converts an ARQualifierStruct into a serialized qualification string.

Input:  qualStruct
Output: qualText'''
        return self.AREncodeARQualifierStruct(qualStruct)

    def EncodeDiary(self, diaryList):
        '''
Input: diaryList
Output: diaryString'''
        return self.AREncodeDiary(diaryList)

    def EncodeStatusHistory(self, statHistList):
        '''
Input: statHistList
Output: statHistString'''
        return self.AREncodeStatusHistory(statHistList)

    def ExecuteProcess(self, command, runOption):
        '''ExecuteProcess performs the indicated command on the specified server.
        
Input: command
       (optional) runOption (if set to 0 (default), operate synchronously
Output: synchron: (returnStatus, returnString)
       asynchron: (1, '')'''
        return self.ARExecuteProcess(command, runOption)

    def ExpandCharMenu(self, menuIn):
        # TODO: check the argument menuIn; what can we do to support the user? 
        # do not expect ARCharMenuStruct
        '''ExpandCharMenu expands the references for the specified menu definition and
returns a character menu with list-type items only.

Input:  (ARCharMenuStruct) menuIn
Output: ARCharMenuStruct'''
        return self.ARExpandCharMenu(menuIn)

    def Export(self, structArray, 
               displayTag = None, 
               vuiType = cars.AR_VUI_TYPE_NONE):
        '''Export exports AR data structures to a string.
Use this function to copy structure definitions from one AR System server to another.
Note: Form exports do not work the same way with ARExport as they do in
Remedy Administrator. Other than views, you cannot automatically
export related items along with a form. You must explicitly specify the
workflow items you want to export. Also, ARExport cannot export a form
without embedding the server name in the export file (something you can
do with the "Server-Independent" option in Remedy Administrator).
Input: structArray ((cars.AR_STRUCT_ITEM_xxx, name), ...)
       displayTag (optional, default = None)
       vuiType (optional, default = cars.AR_VUI_TYPE_NONE
Output: string (or None in case of failure)'''
        structItems = self.conv2StructItemList(structArray)
        return self.ARExport(structItems, displayTag, vuiType)

    def GetActiveLink (self, name):
        '''GetActiveLink retrieves the active link with the indicated name.

GetActiveLink retrieves the active link with the indicated name on
the specified server.
Input: name
Output: ARActiveLinkStruct (containing): order, schemaList,
           groupList, executeMask, controlField,
           focusField, enable, query, actionList,
           elseList, helpText, timestamp, owner, lastChanged,
           changeDiary, objPropList'''
        alink = self._RetrieveObjectFromCache('alink', 'default', name)
        if alink is not None:
            return alink
        alink = self.ARGetActiveLink (name)
        if self.errnr > 1:
            raise ARError(self)
        self._StoreObjectInCache('alink', 'default', name, alink)
        return alink

    def GetAlertCount (self, qualifier=None):
        '''GetAlertCount retrieves the count of qualifying alert events 
located on the server.

GetAlertCount retrieves the count of qualifying alert events located
on the specified server.
Input: (optional) qualifier (default: None)
Output: count / None'''
        return self.ARGetAlertCount (qualifier)

    def GetCharMenu(self, name):
        '''GetCharMenu retrieves information about the character menu with the indicated name.
        
Input: name
Output: ARMenuStruct (refreshCode, menuDefn, helpText,timestamp,owner,lastChanged,
changeDiary,objPropList)'''
        return self.ARGetCharMenu(name)

    def GetContainer(self, 
                     name, 
                     refTypes=cars.ARREF_ALL):
        '''
Input: name
       (optional) refTypes (a list of ARREF types, e.g. (ARREF_SCHEMA,
                            ARREF_FILTER, ARREF_ESCALATION))
Output: ARContainerStruct (groupList, admingrpList, ownerObjList, label, description,
type,references,helpText,owner,timestamp,lastChanged,changeDiary,objPropList)'''
        return self.ARGetContainer(name, 
                                   self.conv2ReferenceTypeList(refTypes))


    def GetCurrencyRatio(self, currencyRatios, fromCurrencyCode, toCurrencyCode):
        '''
GetCurrencyRatio retrieves a selected currency ratio from a set of ratios returned
when the client program makes a call to GetMultipleCurrencyRatioSets.
Input: currencyRatios
       fromCurrencyCode
       toCurrencyCode
Output: currencyRatio'''
        return self.ARGetCurrencyRatio(currencyRatios, 
                                       fromCurrencyCode, toCurrencyCode)

    def GetCurrentServer (self):
        return self.ARGetCurrentServer()
    
    def GetEntry(self, schemaString, entry, idList = None):
        '''GetEntry retrieves the form entry with the indicated ID.

GetEntry retrieves the form entry with the indicated ID on
the specified server.
Input: schemaString
       entry: string with id (or tuple for join)
       (optional) idList (default: None, retrieve no fields)
Output: python dictionary or raise ARError in case of failure'''
        self.errnr = 0
        if entry is None:
            self.errnr = 2
            raise ARError(None, 'GetEntry: entry is empty!', cars.AR_RETURN_ERROR)
        entryId = self.conv2EntryIdList(schemaString, entry)
        if self.errnr > 1:
            self.logger.error('GetEntry: could not convert EntryIdList')
            raise ARError(None, 'GetEntry: could not convert EntryIdList', cars.AR_RETURN_ERROR)
        fieldIds = self.conv2InternalIdList(idList)
        result = self.ARGetEntry(schemaString, entryId, fieldIds)
        if self.errnr > 1:
            raise ARError(self)
        pythonicResult = self.convFieldValueList2Dict(result)
        self.Free(result)
        return pythonicResult
    
    def GetEntryBLOB(self, schema, entry, id_, loc):
        '''GetEntryBLOB
Input: schema: schema name
       entry: entry id(s)
       id_: fieldId
       loc: ARLocStruct
Output: (in loc)'''
        if entry is None:
            self.errnr = 2
            return None
        entryId = self.conv2EntryIdList(schema, entry)
        return self.ARGetEntryBLOB(schema, entryId, id_, loc)

    def GetEntryStatistics(self, schema, query=None, target=None, 
                            statistic=cars.AR_STAT_OP_COUNT, 
                            groupByList=None):
        '''GetEntryStatistics computes the indicated statistic for the form entries 
that match the conditions specified by the qualifier parameter.
Input: schema
       query
       target
       statistic
       groupByList
Output: results'''
        self.errnr = 0
        q = self.conv2QualifierStruct(schema, query)
        groupbylist = self.conv2InternalIdList(groupByList)
        return self.ARGetEntryStatistics(schema, q, target, 
                            statistic, groupbylist)

    def GetEscalation(self, name):
        '''GetEscalation
Input: name
Output: AREscalationStruct'''
        return self.ARGetEscalation(name)

    def GetField (self, schema, fieldId):
        '''GetField retrieves the information for one field on a form and stores
the information in the internal cache.

GetField returns a ARFieldInfoStruct for a given fieldid.
Input: schema
       fieldId
Output: ARFieldInfoStruct or None in case of failure'''
        if schema is None:
            self.errnr = 2
            return None
        field = self._RetrieveObjectFromCache('fields', schema, fieldId)
        if field is not None:
            return field
        self.logger.debug('GetField: no info in cache for %s:%d, need to lookup' % (
                          schema, fieldId))
        field = self.ARGetField (schema, fieldId)
        if self.errnr > 1:
            raise ARError(self)
        self._StoreObjectInCache('fields', schema, fieldId, field)
        return field

    def GetFilter (self, name):
        '''GetFilter retrieves a filter with a given name and stores
the information in the internal cache.

Input: filter name
Output: ARFilterStruct (order, schemaList, opSet, enable, query, actionList,
           elseList, helpText, timestamp, owner, lastChanged,
           changeDiary, objPropList)'''
        filter_ = self._RetrieveObjectFromCache('filter', 'default', name)
        if filter_ is not None:
            return filter_
        self.logger.debug('GetFilter: no info in cache, need to lookup')
        filter_ =  self.ARGetFilter (name)
        if self.errnr > 1:
            raise ARError(self)
        self._StoreObjectInCache('filter', 'default', name, filter_)
        return filter_ 
        
    def GetFullTextInfo(self, requestArray):
        '''GetFullTextInfo
Input: requestArray: array of integers representing the requested information
Output: fullTextInfo'''
        # we received an array of integers as parameter; we have
        # to construct an array of c_uints and then assign this
        # array to the struct
        return self.ARGetFullTextInfo(
                    self.conv2FullTextInfoRequestList(requestArray))

    def GetListActiveLink (self, schema=None, changedSince=0):
        '''GetListActiveLink retrieves a list of active links for a schema/server.

Input: (optional) schema (default: None)
       (optional) changeSince (default: 0)
Output: (name1, name2, ...) or None in case of failure'''
        result = self.ARGetListActiveLink (schema, changedSince)
        if result is None:
            return None
        else:
            pythonicResult = self.convNameList2List(result)
            self.Free(result)
            return pythonicResult 

    def GetListAlertUser (self):
        '''GetListAlertUser retrieves a list of all users that are registered 
for alerts.

Input: 
Output: (name1, name2, ...) or None in case of failure'''
        result = self.ARGetListAlertUser()
        if result is None:
            return None
        else:
            pythonicResult = self.convAccessNameList2List(result)
            self.Free(result)
            return pythonicResult

    def GetListCharMenu(self, changedSince=0):
        '''GetListCharMenu
Input: changedSince
Output: (name1, name2, ...) or None in case of failure'''
        result = self.ARGetListCharMenu(changedSince)
        if result is None:
            return None
        else:
            pythonicResult = self.convNameList2List(result)
            self.Free(result)
            return pythonicResult

    def GetListContainer (self, changedSince=0,
                          containerArray=cars.ARCON_ALL,
                          attributes=cars.AR_HIDDEN_INCREMENT,
                          ownerObjList=None):
        '''GetListContainer retrieves a list of containers.

Input: (optional) changedSince (default: 0)
       (optional) containerArray: array of values representing
       container types (default: ARCON_ALL)
       (optional) attributes (default: )
       (optional) ownerObjList (default: None)
Output: ARContainerInfoList
Please note: I'm not sure about the parameter configuration;
I've implemented according to the C API documentation, but
the exact usage of attributes & containerTypes is still
a secret to me... Beware... has not been tested well!'''
        
        containerTypes = self.conv2ContainerTypeList(containerArray)
        return self.ARGetListContainer(changedSince,
                                     containerTypes,
                                     attributes,
                                     ownerObjList)

    def GetListEntry(self, schema, 
                     query=None,
                     getListFields=None, 
                     sortList=None,
                     firstRetrieve=cars.AR_START_WITH_FIRST_ENTRY,
                     maxRetrieve=cars.AR_NO_MAX_LIST_RETRIEVE):
        '''GetListEntry retrieves a list of entries for a schema.

GetListEntry retrieves a list of entries/objects for a specific schema
according to specific search query.

Input: schema/form name
       (optional) query string
       (optional) getListFields (default: None)
       (optional) sortList (default: None; can be 
               ((fieldid, 1), (id2, 0), ...) 
               with sec. parameter 0 = ascending
       (optional) firstRetrieve (default: AR_START_WITH_FIRST_ENTRY)
       (optional) maxRetrieve (default: AR_NO_MAX_LIST_RETRIEVE)
Output: (list ((entryid , shortdesc) , ...), numMatches) or raise ARError in case of failure.
It is important that the query looks something like this:
'field' = "value" (please note the quotation marks).'''
        self.errnr = 0
        q = self.conv2QualifierStruct(schema, query)
        arGetListFields = self.conv2EntryListFieldList(getListFields, schema)
        if self.errnr > 1:
            self.logger.error('GetListEntry: converting getListFields failed!')
            raise ARError(None, 'GetListEntry: converting getListFields failed!', cars.AR_RETURN_ERROR)
        arSortList = self.conv2SortList (sortList)
        if self.errnr > 1:
            self.logger.error('GetListEntry: converting sort list failed!')
            raise ARError(None, 'GetListEntry: converting sort list failed!', cars.AR_RETURN_ERROR)
        result = self.ARGetListEntry(schema, 
                                       q,
                                       arGetListFields,
                                       arSortList,
                                       firstRetrieve,
                                       maxRetrieve)
        if result is None:
            raise ARError(self)
        else:
            (entryListFieldValueList, numMatches) = result
            pythonicResult = self.convEntryListList2List(entryListFieldValueList)
            self.Free(entryListFieldValueList)
            return (pythonicResult, numMatches)

    def GetListEntryWithFields (self, schema, 
                                query = None,
                                getListFields=None, 
                                sortList=None,
                                firstRetrieve=cars.AR_START_WITH_FIRST_ENTRY,
                                maxRetrieve=cars.AR_NO_MAX_LIST_RETRIEVE):
        '''GetListEntryWithFields retrieve a list of entries for a schema.

GetListEntryWithFields retrieve a list of entries/objects for a
specific schema according to specific search query together with
their fields and values.
It is important that the query looks something like this:
'field' = "value" (please note the quotation marks).
Input: schema/form name
       query string
       (optional) getListFields: list of fieldids (fid1, fid2, ...) (default: None)
       (optional) sortList (default: None)
       (optional) firstRetrieve (default: AR_START_WITH_FIRST_ENTRY)
       (optional) maxRetrieve (default: AR_NO_MAX_LIST_RETRIEVE)
Output: (list ((entryid , { fid1 : value1, ...}), ()....), numMatches) or raise ARError
    in case of failure'''
        self.errnr = 0
        q = self.conv2QualifierStruct(schema, query)
        arGetListFields = self.conv2EntryListFieldList(getListFields, schema)
        if self.errnr > 1:
            self.logger.error('GetListEntryWithFields: converting getListFields failed!')
            raise ARError(None, 'GetListEntry: converting getListFields failed!', cars.AR_RETURN_ERROR)
        arSortList = self.conv2SortList (sortList)
        if self.errnr > 1:
            self.logger.error('GetListEntryWithFields: converting sort list failed!')
            raise ARError(None, 'GetListEntry: converting sort list failed!', cars.AR_RETURN_ERROR)
        result = self.ARGetListEntryWithFields(schema, 
                                             q,
                                             arGetListFields,
                                             arSortList,
                                             firstRetrieve,
                                             maxRetrieve)
        if result is None:
            raise ARError(self)
        else:
            (entryListFieldValueList, numMatches) = result
            pythonicResult = self.convEntryListFieldValueList2List(entryListFieldValueList)
            self.Free(entryListFieldValueList)
            return (pythonicResult, numMatches)
    
    def GetListEscalation (self, schema=None,
                           changedSince = 0):
        '''GetListEscalation retrieves a list of all escalations.

Input: (optional) schema (default: None)
       (optional): changedSince (default: 0)
Output: (name1, name2, ...) or None in case of failure'''
        result = self.ARGetListEscalation (schema, changedSince)
        if result is None:
            return None
        else:
            pythonicResult = self.convNameList2List(result)
            self.Free(result)
            return pythonicResult 

    def GetListExtSchemaCandidates(self, schemaType=cars.AR_SCHEMA_VIEW |
                                                    cars.AR_SCHEMA_VENDOR |
                                                    cars.AR_HIDDEN_INCREMENT):
        '''GetListExtSchemaCandidates retrieves a list of all available external data
source tables (schema candidates).
Input: schemaType
Output: ARCompoundSchemaList (or None in case of failure)'''
        return self.ARGetListExtSchemaCandidates(schemaType)

    def GetListField(self, schema,
                     changedSince=0,
                     fieldType=cars.AR_FIELD_TYPE_DATA):
        '''GetListField returns a list of field ids for a schema.
        
Input: string: schema
       (optional) timestamp: changedSince (dfault: 0)
       (optional) fieldType (default: AR_FIELD_TYPE_DATA)
Output: (fieldid1, fieldid2, ...) or None in case of failure'''
        result = self.ARGetListField(schema, changedSince, fieldType)
        if result is None:
            return None
        else:
            pythonicResult = self.convInternalIdList2List(result)
            self.Free(result)
            return pythonicResult

    def GetListFilter(self, schema=None, changedSince=0):
        '''GetListFilter return a list of all available filter for a schema.

Input: (optional) schema (default: None -- retrieve all filter names)
       (optional) changedSince (default: 0)
Output: (name1, name2, ...) or None in case of failure'''
        result = self.ARGetListFilter(schema, changedSince)
        if result is None:
            return None
        else:
            pythonicResult = self.convNameList2List(result)
            self.Free(result)
            return pythonicResult

    def GetListGroup(self, userName=None, password=None):
        '''GetListGroup retrieves a list of access control groups.

GetListGroup retrieves a list of access control groups on the specified server.
You can retrieve all groups or limit the list to groups associated with a particular user.        
Input: (optional) userName
       (optional) password
Output: python dictionary of {groupid: (cars.AR_GROUP_TYPE, # read or change
            (list of names), 
            AR_GROUP_CATEGORY)} # regular, dynamic or computed'''
        result = self.ARGetListGroup(userName, password)
        if result is None:
            return None
        else:
            pythonicResult = self.convGroupInfoList2Dict(result)
            self.Free(result)
            return pythonicResult

    def GetListLicense(self, licenseType=None):
        '''GetListLicense return a list of entries from the license file.

GetListLicense return a list of entries from the license file.
Input: (optional) licenseType (str, default: None)
Output: ARLicenseInfoList or None in case of failure
'''
        return self.ARGetListLicense(licenseType)

    def GetListSchema(self, changedSince=0, 
                      schemaType=cars.AR_LIST_SCHEMA_ALL | cars.AR_HIDDEN_INCREMENT,
                      name='', 
                      fieldIdArray=None):
        '''GetListSchema return a list of all available schemas

GetListSchema returns a list of all available schemas
Input: (optional) changedSince: a timestamp (default: 0)
       (optional) schemaType (default: AR_LIST_SCHEMA_ALL | AR_HIDDEN_INCREMENT)
       (optional) name (default "", only necessary if schemaType is
       AR_LIST_SCHEMA_UPLINK
       (optional) fieldIdArray (list of fieldids; default: None; ARS then only returns the
               forms that contain all the fields in this list)
Output: (name1, name2, ...) or None in case of failure'''
        # if the fieldIdArray is a tuple or array, convert this into a ARInternalIdList
        fieldIdList = self.conv2InternalIdList(fieldIdArray)
        result = self.ARGetListSchema(changedSince, 
                                      schemaType, 
                                      name, 
                                      fieldIdList)
        if result is None:
            return None
        else:
            pythonicResult = self.convNameList2List(result)
            self.Free(result)
            return pythonicResult

    def GetListSchemaWithAlias(self, changedSince=0, 
                               schemaType=cars.AR_HIDDEN_INCREMENT, 
                               name='', 
                               fieldIdArray=None, 
                               vuiLabel=None):
        '''GetListSchemaWithAlias retrieves a list of form definitions and 
their corresponding aliases.
Input: (optional) changedSince: a timestamp (default: 0)
       (optional) schemaType (default: AR_LIST_SCHEMA_ALL | AR_HIDDEN_INCREMENT)
       (optional) name (default "", only necessary if schemaType is
       AR_LIST_SCHEMA_UPLINK
       (optional) fieldIdArray (list of fieldids; default: None; ARS then only returns the
               forms that contain all the fields in this list)
       vuiLabel
Output: (nameList [(name1, name2, ...)], aliasList[(name1, name2, ...)])'''
        fieldIdList = self.conv2InternalIdList(fieldIdArray)
        result = self.ARGetListSchemaWithAlias(changedSince, 
                                               schemaType,
                                               name,
                                               fieldIdList,
                                               vuiLabel)
        if result is None:
            raise ARError(self)
        else:
            nameList = self.convNameList2List(result [0])
            aliasList = self.convNameList2List(result[1])
            self.Free(result [0])
            self.Free(result [1])
            return (nameList, aliasList)        

    def GetListServer (self):
        '''GetListServer retrieve the list of available AR System servers.

GetListServer retrieves the list of available AR System servers.
Input: 
Output: (name1, name2, ...) or None in case of failure'''
        result = self.ARGetListServer()
        if result is None:
            return None
        else:
            pythonicResult = self.convServerNameList2List(result)
            self.Free(result)
            return pythonicResult
        
    def GetListSQL(self, sqlCommand, maxRetrieve=cars.AR_NO_MAX_LIST_RETRIEVE):
        '''GetListSQL retrieves a list of rows from the underlying 
SQL database on the specified server.

Input: sqlCommand
       maxRetrieve
Output: a tuple of (line1, line2, line3, ...) with line being a tuple of
        the columns (col1, col2, col3, ...)'''
        result = self.ARGetListSQL(sqlCommand, maxRetrieve)
        if result is None:
            return None
        else:
            pythonicResult = self.convValueListList2List(result[0])
            self.Free(result[0])
            return pythonicResult

    def GetListSupportFile(self, fileType, name, id2=0, changedSince=0):
        '''GetListSupportFile retrieves a list of support file IDs for a specified type of object.

GetListSupportFile retrieves a list of support file IDs for a specified type of object.        
Input: 
       fileType
       name
       id2
       changedSince
Output: fileIdList'''
        return self.ARGetListSupportFile(fileType, name, id2, changedSince)

    def GetListUser(self, userListType=cars.AR_USER_LIST_CURRENT, 
                    changedSince=0):
        '''GetListUser retrieves a list of users.

GetListUser retrieves a list of users. You can retrieve information about the
current user, all registered users, or all users currently accessing the server.        
Input: userListType (default: AR_USER_LIST_CURRENT)
       changedSince (default: 0)
Output: ARUserInfoList'''
        return self.ARGetListUser(userListType, changedSince)

    def GetListVUI(self, schema, changedSince=0):
        '''
Input: schema
       changedSince
Output: idList'''
        return self.ARGetListVUI(schema, changedSince)

    def GetLocalizedValue(self, localizedRequest):
        '''
Input:  localizedRequest
Output: a tuple of (localizedValue, timestamp)'''
        return self.ARGetLocalizedValue(localizedRequest)

    def GetMultipleActiveLinks(self, changedSince=0, nameList=None,
                                orderListP = True,
                                schemaListP = True,
                                groupListListP = False,
                                executeMaskListP = False,
                                controlFieldListP = False,
                                focusFieldListP = False,
                                enableListP = False,
                                queryListP = False,
                                actionListListP = False,
                                elseListListP = False,
                                helpTextListP = False,
                                timestampListP = False,
                                ownersListP = False,
                                lastChangedListP = False,
                                changeDiaryListP = False,
                                objPropListListP = False):
        '''GetMultipleActiveLinks
Input: changedSince=0, 
        (optional) nameList = None,
        (optional) orderListP = True,
        (optional) schemaListP = True,
        (optional) groupListListP = True,
        (optional) executeMaskListP = True,
        (optional) controlFieldListP = True,
        (optional) focusFieldListP = True,
        (optional) enableListP = True,
        (optional) queryListP = True,
        (optional) actionListListP = True,
        (optional) elseListListP = True,
        (optional) helpTextListP = True,
        (optional) timestampListP = True,
        (optional) ownersListP = True,
        (optional) lastChangedListP = True,
        (optional) changeDiaryListP = True,
        (optional) objPropListListP = True
Output: ARActiveLinkList'''
        nameList = self.conv2NameList(nameList)
        orderList = schemaList = groupListList = executeMaskList = None
        controlFieldList = focusFieldList = enableList = queryList = None
        actionListList = elseListList = helpTextList = timestampList = None
        ownersList = lastChangedList = changeDiaryList = objPropListList = None
        if orderListP: orderList = cars.ARUnsignedIntList()
        if schemaListP: schemaList = cars.ARWorkflowConnectList()
        if groupListListP: groupListList = cars.ARInternalIdListList()
        if executeMaskListP: executeMaskList = cars.ARUnsignedIntList()
        if controlFieldListP: controlFieldList = cars.ARInternalIdList()
        if focusFieldListP: focusFieldList = cars.ARInternalIdList()
        if enableListP: enableList = cars.ARUnsignedIntList()
        if queryListP: queryList = cars.ARQualifierList()
        if actionListListP: actionListList = cars.ARActiveLinkActionListList()
        if elseListListP: elseListList = cars.ARActiveLinkActionListList()
        if helpTextListP: helpTextList = cars.ARTextStringList()
        if timestampListP: timestampList = cars.ARTimestampList()
        if ownersListP: ownersList = cars.ARAccessNameList()
        if lastChangedListP: lastChangedList = cars.ARAccessNameList()
        if changeDiaryListP: changeDiaryList = cars.ARTextStringList()
        if objPropListListP: objPropListList = cars.ARPropListList()
        return self.ARGetMultipleActiveLinks(changedSince, nameList,
                    orderList,
                    schemaList,
                    groupListList,
                    executeMaskList,
                    controlFieldList,
                    focusFieldList,
                    enableList,
                    queryList,
                    actionListList,
                    elseListList,
                    helpTextList,
                    timestampList,
                    ownersList,
                    lastChangedList,
                    changeDiaryList,
                    objPropListList)

    def GetMultipleCurrencyRatioSets(self, ratioTimestamps=None):
        '''GetMultipleCurrencyRatioSets retrieves a list of formatted currency ratio sets
valid for the times specified in the ratioTimestamps argument.

GetMultipleCurrencyRatioSets retrieves a list of formatted currency ratio sets
valid for the times specified in the ratioTimestamps argument. You can use
ARGetCurrencyRatio to extract a specific currency ratio from a ratio set that
this call (ARGetMultipleCurrencyRatioSets) returns.    
Input:  ratioTimestamps
Output: currencyRatioSets
'''
        return self.ARGetMultipleCurrencyRatioSets(
                self.conv2TimestampList(ratioTimestamps))

    def GetMultipleEntries(self, schema, 
                           entryIdArray, 
                           idList=None):
        '''GetMultipleEntries retrieve a list of entries.

GetMultipleEntries retrieve a list of entries/objects for a
specific schema according to an array of specific ids together
with their fields and values.

Input: schema/form name
       entryIdArray: array of entry ids to be retrieved; this can either be
           a pythonic array of entryids, or an AREntryListList (as returned
           by ARGetListEntry) or an AREntryIdListList (as required by ARGetMultipleEntries)
       (optional) idList: an array of zero or more field IDs  to be retrieved, this can either
           be a pythonic array of fieldIds or an ARInternalIdList       
Output: (ARBooleanList, ARFieldValueListList)'''
        if isinstance(entryIdArray, cars.AREntryIdListList):
            entryIdList = entryIdArray
        elif isinstance(entryIdArray, cars.AREntryListList):
            entryIdList = self.convEntryListList2EntryIdListList(entryIdArray)
        else:
            entryIdList = self.conv2EntryIdListList(schema, entryIdArray)
        arIdList = self.conv2InternalIdList (idList)
        result = self.ARGetMultipleEntries(schema, entryIdList, arIdList)
        if self.errnr > 1:
            raise ARError(self)
        return result

    def GetMultipleExtFieldCandidates(self, schema):
        '''GetMultipleExtFieldCandidates

Input:  schema
Output: a tuple of (fieldMapping, limit, dataType)'''
        return self.ARGetMultipleExtFieldCandidates(schema)

    def GetMultipleFields (self, schemaString, 
                           idList=None,
                           fieldId2P = True,
                           fieldNameP = True,
                           fieldMapP = False,
                           dataTypeP = False,
                           optionP = False,
                           createModeP = False,
                           defaultValP = False,
                           permissionsP = False,
                           limitP = False,
                           dInstanceListP = False,
                           helpTextP = False,
                           timestampP = False,
                           ownerP = False,
                           lastChangedP = False,
                           changeDiaryP = False):
        '''GetMultipleFields returns a list of the fields and their attributes.
   
GetMultipleFields returns list of field definitions for a specified form.
In contrast to the C APi this function constructs an ARFieldInfoList
for the form and returns all information this way.
Input:  schemaString
        (optional) idList (ARInternalIdList; default: None) we currently
                  expect a real ARInternalIdList, because then it's very
                  easy to simply hand over the result of a GetListField
                  call
      (optional) fieldId2P and all others (Boolean) set to False (default,
                   only fieldNameP is set to True)
                  if you are not interested in those values, to True
                  otherwise (the aprameters have names with 'P' appended
                  as in Predicate)
Output: ARFieldInfoList
'''
        # initialize the structures to default values
        
        # we could receive idLIst as an InternalIdList (as a result of GetListField)
        # or as a python list/array - then we need to convert it first
        if idList != None and idList.__class__ != cars.ARInternalIdList:
            idList = self.conv2InternalIdList(idList)
        fieldId2 = fieldName = fieldMap = dataType = option = None
        createMode = defaultVal = permissions = limit = None
        dInstanceList = helpText = timestamp = owner = None
        lastChanged = changeDiary = None
        if fieldId2P: fieldId2 = cars.ARInternalIdList()
        if fieldNameP: fieldName = cars.ARNameList()
        if fieldMapP: fieldMap = cars.ARFieldMappingList()
        if dataTypeP: dataType = cars.ARUnsignedIntList()
        if optionP: option = cars.ARUnsignedIntList()
        if createModeP: createMode = cars.ARUnsignedIntList()
        if defaultValP: defaultVal = cars.ARValueList()
        if permissionsP: permissions = cars.ARPermissionListList()
        if limitP: limit = cars.ARFieldLimitList()
        if dInstanceListP: dInstanceList = cars.ARDisplayInstanceListList()
        if helpTextP: helpText = cars.ARTextStringList()
        if timestampP: timestamp = cars.ARTimestampList()
        if ownerP: owner = cars.ARAccessNameList()
        if lastChangedP: lastChanged = cars.ARAccessNameList()
        if changeDiaryP: changeDiary = cars.ARTextStringList()
        return self.ARGetMultipleFields (schemaString, idList,
                                         fieldId2,
                                         fieldName,
                                         fieldMap,
                                         dataType,
                                         option,
                                         createMode,
                                         defaultVal,
                                         permissions,
                                         limit,
                                         dInstanceList,
                                         helpText,
                                         timestamp,
                                         owner,
                                         lastChanged,
                                         changeDiary)

    def GetMultipleLocalizedValues(self, localizedRequestList):
        '''GetMultipleLocalizedValues Retrieves multiple localized text strings 
from the BMC Remedy Message Catalog.
The messages that the server retrieves depend on the user locale in the control
structure. This function performs the same action as ARGetLocalizedValues but
is easier to use and more efficient than retrieving multiple values one by one.

Input:  localizedRequestList (ARLocalizedRequestList)
Output: tuple of (localizedValueList, timestampList) or None in case of failure'''
        return self.ARGetMultipleLocalizedValues(localizedRequestList)

    def GetMultipleSchemas(self, changedSince=0, 
                            schemaTypeList=None,
                            nameList=None, 
                            fieldIdList=None,
                            schemaListP = True,
                            groupListListP = False,
                            admingrpListListP = False,
                            getListFieldsListP = False,
                            sortListListP = False,
                            indexListListP = False,
                            defaultVuiListP = False,
                            helpTextListP = False,
                            timestampListP = False,
                            ownerListP = False,
                            lastChangedListP = False,
                            changeDiaryListP = False,
                            objPropListListP = False):
        '''GetMultipleSchemas

Input:                  
Output: '''
        nameList = self.conv2NameList(nameList)
        schemaList = groupListList = None
        admingrpListList = getListFieldsList = sortListList = None
        indexListList = defaultVuiList = None
        helpTextList = timestampList = ownerList = None
        lastChangedList = changeDiaryList = objPropListList = None
        if schemaListP: schemaList = cars.ARCompoundSchemaList()
        if groupListListP: groupListList = cars.ARPermissionListList()
        if admingrpListListP: admingrpListList = cars.ARInternalIdListList()
        if getListFieldsListP: getListFieldsList = cars.AREntryListFieldListList()
        if sortListListP: sortListList = cars.ARSortListList()
        if indexListListP: indexListList = cars.ARIndexListList()
        if defaultVuiListP: defaultVuiList = cars.ARNameList()
        if helpTextListP: helpTextList = cars.ARTextStringList()
        if timestampListP: timestampList = cars.ARTimestampList()
        if ownerListP: ownerList = cars.ARAccessNameList()
        if lastChangedListP: lastChangedList = cars.ARAccessNameList()
        if changeDiaryListP: changeDiaryList = cars.ARTextStringList()
        if objPropListListP: objPropListList = cars.ARPropListList()
        return self.ARGetMultipleSchemas(changedSince, 
                    schemaTypeList, 
                    nameList, 
                    fieldIdList,
                    schemaList, 
                    groupListList,
                    admingrpListList,
                    getListFieldsList,
                    sortListList,
                    indexListList,
                    defaultVuiList,
                    helpTextList,
                    timestampList,
                    ownerList,
                    lastChangedList,
                    changeDiaryList,
                    objPropListList)

    def GetSchema (self, name):
        '''GetSchema returns all information about a schema and stores
the information in the internal cache.

GetSchema returns all information about a schema.
Input: string (schema)
Output: (schema, groupList, admingrpList,
                getListFields, sortList, indexList,
                defaultVui, helpText, timestamp, owner,
                lastChanged, changeDiary, objPropList)
(example: to access the list of fields: use result[3])'''
        schema = self._RetrieveObjectFromCache('schema', 'default', name)
        if schema is not None:
            return schema
        self.logger.debug('GetSchema: no info in cache, need to lookup')
        schema =  self.ARGetSchema (name)
        if self.errnr > 1:
            raise ARError(self)
        self._StoreObjectInCache('schema', 'default', name, schema)
        return schema 

    def GetServerInfo(self, requestArray = None):
        '''GetServerInfo retrieves the requested configuration information
Input:  requestArray of integer (AR_SERVER_INFO_*)
Output: dictionary {requestedInfoField: Value...}'''
        # convert the parameter array into the remedy data structure...
        if requestArray is None:
            requestArray = range(1, cars.AR_MAX_SERVER_INFO_USED + 1)
        result = self.ARGetServerInfo(
                            self.conv2ServerInfoRequestList(requestArray))
        if result is None:
            raise ARError(self)
        else:
            pythonicResult = self.convServerInfoList2Dict(result)
            self.ARFree(result)
            return pythonicResult
        
    def GetSessionConfiguration(self, variableId):
        '''GetSessionConfiguration

Input:  variableId
Output: ARValueStruct'''
        return self.ARGetSessionConfiguration(variableId)

    def GetServerStatistics (self, requestArray = None):
        '''GetServerStatistics returns server statistics.

GetServerStatistics retrieves server statistics ; we expect an array of
AR_SERVER_STAT_ (c_uint) values, that this method converts into a
ARServerInfoRequestList.
Input: (optional) array of integer (AR_SERVER_STAT_*); if not given,
        will be replaced by all AR_SERVER_STAT_ entries
Output: dictionary {requestedStatisticField: Value...}'''
        if requestArray is None:
            requestArray = range(1, cars.AR_MAX_SERVER_STAT_USED + 1)
        result= self.ARGetServerStatistics(
                self.conv2ServerInfoRequestList(requestArray))
        if self.errnr > 1:
            raise ARError(self)
        else:
            pythonicResult = self.convServerInfoList2Dict(result)
            self.ARFree(result)
            return pythonicResult

    def GetSupportFile(self, ):
        '''GetSupportFile

Input:  context
        
Output: 
'''
        return self.ARGetSupportFile()

    def GetTextForErrorMessage(self, msgId):
        '''GetTextForErrorMessage

Input:  msgId
Output: String with the (localized) error message'''
        return self.ARGetTextForErrorMessage(msgId)

    def GetVUI(self, schema, vuiId):
        '''GetVUI

Input:  schema: name of schema
        vuiId: internalId
Output: ARVuiInfoStruct (or None in case of failure)'''
        return self.ARGetVUI(schema, vuiId)

    def Import(self, structArray, 
               importBuf, 
               importOption=cars.AR_IMPORT_OPT_CREATE):
        '''Import

Input:  structItems
        importBuf
        optional: importOption (Default=cars.AR_IMPORT_OPT_CREATE)
        Output: errnr'''
        structItems = self.conv2StructItemList(structArray)
        return self.ARImport(structItems, importBuf, importOption)

    def JulianDateToDate(self, jd):
        '''JulianDateToDate

Input:  jd
Output: ARDateStruct
'''
        return self.ARJulianDateToDate(jd)

    def LoadARQualifierStruct(self, schema, qualString, displayTag=None):
        '''LoadARQualifierStruct

Input:  schema
        qualString: containing the qualification to load (following the syntax
                        rules for entering qualifications in the AR System Windows 
                        User Tool query bar).
        displayTag: name of the form view (VUI) to use for resolving field names.
Output: ARQualifierStruct'''
        return self.ARLoadARQualifierStruct(schema, qualString, displayTag)

    def Login (self,
               server,
               username,
               password,
               language='', 
               authString = '',
               tcpport = 0,
               rpcnumber = 0,
               cacheId = 0,
               operationTime = 0,
               sessionId = 0):
        ars.ARS.Login(self, server, username, password, language, 
               authString, tcpport, rpcnumber, cacheId,
               operationTime, sessionId)
        if self.errnr < 2:
            self._InitializeCache()
            
    def MergeEntry(self, schema,
                   fieldList,
                   mergeType = cars.AR_MERGE_ENTRY_DUP_ERROR):
        '''MergeEntry merges an existing database entry into the indicated form.

You can merge entries into base forms only. To add entries to join
forms, merge them into one of the underlying base forms.
Input:  schema (name of schema)
        fieldList (list or dictionary of {fieldid1: value1, ...}
        mergeType (default: cars.AR_MERGE_ENTRY_DUP_ERROR)
Output: entryId (AREntryIdType) or raise ARError in case of failure'''
        fvl = self.conv2FieldValueList(schema, fieldList)
        if fvl is None:
            self.logger.error('MergeEntry: converting to fieldvaluelist failed')
            raise ARError(None, 'MergeEntry: converting field list failed!', cars.AR_RETURN_ERROR)
        result = self.ARMergeEntry(schema, 
                                 fvl,
                                 mergeType)
        if self.errnr > 1:
            raise ARError (self)
        return result

    def RegisterForAlerts(self, clientPort, registrationFlags=0):
        '''RegisterForAlerts registers the specified user with the AR System 
server to receive alerts.

Input:  clientPort
        registrationFlags (reserved for future use and should be set to zero)
Output: errnr'''
        return self.ARRegisterForAlerts(clientPort, registrationFlags)

    def SetActiveLink(self,  name, 
                        newName = None, 
                        order = None, 
                        workflowConnect = None,
                        groupList = None,
                        executeMask = None,
                        controlField = None,
                        focusField = None,
                        enable = None,
                        query = None,
                        actionList = None,
                        elseList = None,
                        helpText = None,
                        owner = None,
                        changeDiary = None,
                        objPropList = None):
        '''SetActiveLink updates the active link with the indicated name on the specified server. The
changes are added to the server immediately and returned to users who request
information about active links. Because active links operate on clients, individual
clients do not receive the updated definition until they reconnect to the form (thus
reloading the form from the server).

Input:  name, 
        newName, 
        order = None, 
        workflowConnect = None,
        groupList = None,
        executeMask = None,
        controlField = None,
        focusField = None,
        enable = None,
        query = None,
        actionList = None,
        elseList = None,
        helpText = None,
        owner = None,
        changeDiary = None,
        objPropList = None
Output: errnr'''
        return self.ARSetActiveLink(name, 
                                    newName, 
                                    order, 
                                    workflowConnect,
                                    groupList,
                                    executeMask,
                                    controlField,
                                    focusField,
                                    enable,
                                    query,
                                    actionList,
                                    elseList,
                                    helpText,
                                    owner,
                                    changeDiary,
                                    objPropList)

    def SetCharMenu(self, name, 
                      newName = None, 
                      refreshCode = None, 
                      menuDefn = None, 
                      helpText = None, 
                      owner = None,
                      changeDiary = None, 
                      objPropList = None):
        '''SetCharMenu updates the character menu.

The changes are added to the server immediately and returned to users who
request information about character menus. Because character menus
operate on clients, individual clients do not receive the updated definition
until they reconnect to the form (thus reloading the form from the server).
        
Input:name, 
      newName = None, 
      refreshCode = None, 
      menuDefn = None, 
      helpText = None, 
      owner = None,
      changeDiary = None, 
      objPropList = None
Output: errnr'''
        return self.ARSetCharMenu(name,
                                  newName,
                                  refreshCode,
                                  menuDefn,
                                  helpText,
                                  owner,
                                  changeDiary,
                                  objPropList)

    def SetContainer(self, name,
                       newName = None,
                       groupList = None,
                       admingrpList = None,
                       ownerObjList = None,
                       label = None,
                       description = None,
                       type_ = None,
                       references = None,
                       removeFlag = None,
                       helpText = None,
                       owner = None,
                       changeDiary = None,
                       objPropList = None                      ):
        '''SetContainer  updates the definition for the container.

Input:  Input:  name
       (optional) newName (default = None)
       (optional) groupList (default = None)
       (optional) admingrpList (default = None)
       (optional) ownerObjList (default = None)
       (optional) label (default = None)
       (optional) description (default = None)
       (optional) type_ (default = None)
       (optional) references (default = None)
       (optional) removeFlag (default = None)
       (optional) helpText (default = None)
       (optional) owner (default = None)
       (optional) changeDiary (default = None)
       (optional) objPropList (default = None)
Output: errnr'''
        return self.ARSetContainer(name,
                       newName,
                       groupList,
                       admingrpList,
                       ownerObjList,
                       label,
                       description,
                       type_,
                       references,
                       removeFlag,
                       helpText,
                       owner,
                       changeDiary,
                       objPropList)

    def SetEntry(self, schema, 
                 entryId, 
                 fieldList, 
                 getTime = 0, 
                 option = None):
        '''SetEntry updates the form entry with the indicated ID on the 
specified server.
Input:  schema
        entryId: entryId to be updated or for join forms: a list of tuples ((schema, entryid), ...)
        fieldList: a dict or a list of tuples: ((fieldid, value), (fieldid, value), ...)
        (optional) getTime (the server compares this value with the 
                    value in the Modified Date core field to
                    determine whether the entry has been changed 
                    since the last retrieval.)
        (optional) option (for join forms only; can be AR_JOIN_SETOPTION_NONE
                    or AR_JOIN_SETOPTION_REF)
Output: errnr or raise ARError in case of failure'''
        entryIdList = self.conv2EntryIdList (schema, entryId)
        if not entryIdList:
            self.logger.error( "SetEntry: entryIdList could not be constructed")
            raise ARError(None, 'SetEntry: converting entryIdList failed!', cars.AR_RETURN_ERROR)
        fvl = self.conv2FieldValueList(schema, fieldList)
        if not fvl: # something went wrong during conversion!
            raise ARError(None, 'SetEntry: converting field list failed!', cars.AR_RETURN_ERROR)
        result = self.ARSetEntry(schema, entryIdList, fvl, getTime, option)
        if result > 1:
            raise ARError(self)
        return result

    def SetEscalation(self, name, 
                        newName = None,
                        escalationTm = None, 
                        schemaList = None, 
                        enable = None,
                        query = None, 
                        actionList = None,
                        elseList = None, 
                        helpText = None, 
                        owner = None, 
                        changeDiary = None, 
                        objPropList = None):
        '''SetEscalation updates the escalation with the indicated name on the specified server. The
changes are added to the server immediately and returned to users who request
information about escalations.

Input:  (ARNameType) name, 
        (ARNameType) newName,
       (AREscalationTmStruct) escalationTm, 
       (ARWorkflowConnectStruct) schemaList, 
       (c_uint) enable, 
       (ARQualifierStruct) query, 
       (ARFilterActionList) actionList,
       (ARFilterActionList) elseList, 
       (c_char_p) helpText, 
       (ARAccessNameType) owner, 
       (c_char_p) changeDiary, 
       (ARPropList) objPropList
Output: errnr'''
        return self.ARSetEscalation(name, 
                                    newName,
                                    escalationTm, 
                                    schemaList, 
                                    enable, 
                                    query, 
                                    actionList,
                                    elseList, 
                                    helpText, 
                                    owner, 
                                    changeDiary, 
                                    objPropList)

    def SetField(self, schema, 
                   fieldId, 
                   fieldName = None, 
                   fieldMap = None, 
                   option = None, 
                   createMode = None, 
                   defaultVal = None,
                   permissions = None, 
                   limit = None, 
                   dInstanceList = None, 
                   helpText = None, 
                   owner = None, 
                   changeDiary = None):
        '''SetField updates the definition for the form field.

Input:  schema, 
           fieldId, 
           fieldName = None, 
           fieldMap = None, 
           option = None, 
           createMode = None, 
           defaultVal = None,
           permissions = None, 
           limit = None, 
           dInstanceList = None, 
           helpText = None, 
           owner = None, 
           changeDiary = None
Output: errnr'''
        return self.ARSetField(schema, 
                               fieldId, 
                               fieldName, 
                               fieldMap, 
                               option, 
                               createMode, 
                               defaultVal, 
                               permissions, 
                               limit, 
                               dInstanceList, 
                               helpText, 
                               owner, 
                               changeDiary)

    def SetFilter(self, name, 
                    newName = None,
                    order = None,
                    workflowConnect = None,
                    opSet = None,
                    enable = None,
                    query = None,
                    actionList = None,
                    elseList = None,
                    helpText = None,
                    owner = None,
                    changeDiary = None,
                    objPropList = None):
        '''SetFilter updates the filter.

The changes are added to the server immediately and returned to users who
request information about filters.
Input:  (ARNameType) name (optional, default: None), 
        (ARNameType) newName (optional, default: None), 
        (unsigned int) order (optional, default: None), 
        (ARWorkflowConnectStruct) workflowConnect (optional, default: None), 
        (unsigned int) opSet (optional, default: None), 
        (unsigned int) enable (optional, default: None), 
        (ARQualifierStruct) query (optional, default: None), 
        (ARFilterActionList) actionList (optional, default: None), 
        (ARFilterActionList) elseList (optional, default: None), 
        (c_char_p) helpText (optional, default: None), 
        (ARAccessNameType) owner (optional, default: None), 
        (c_char_p) changeDiary (optional, default: None), 
        (ARPropList) objPropList  (optional, default: None), 
Output: errnr'''
        return self.ARSetFilter(name, 
                                newName,
                                order,
                                workflowConnect,
                                opSet,
                                enable,
                                query,
                                actionList,
                                elseList,
                                helpText,
                                owner,
                                changeDiary,
                                objPropList)

    def SetFullTextInfo(self, fullTextInfo):
        '''SetFullTextInfo updates the indicated FTS information

Note: Full text search (FTS) is documented for backward compatibility only,
and is not supported in AR System 6.3.
Input:  fullTextInfo
Output: errnr'''
        return self.ARSetFullTextInfo(fullTextInfo)

    def SetLogging(self, 
                   logTypeMask = cars.AR_DEBUG_SERVER_NONE, 
                   whereToWriteMask = cars.AR_WRITE_TO_STATUS_LIST, 
                   file_ = None):
        '''SetLogging activates and deactivates client-side logging of server activity.

Input:  context
        (optional) logTypeMask:  what to log (default: nothing)
        (optional) whereToWriteMask: to log file or (default) status list
        (optional) file: FileHandle (default: None)
Output: errnr'''
        return self.ARSetLogging(logTypeMask, whereToWriteMask, file_)

    def SetSchema(self, name,
                    newName = None,
                    schema = None,
                    groupList = None,
                    admingrpList = None,
                    getListFields = None,
                    sortList = None,
                    indexList = None,
                    defaultVui = None,
                    helpText = None,
                    owner = None,
                    changeDiary = None,
                    objPropList = None,
                    setOption = None):
        '''SetSchema updates the definition for the form.

If the schema is locked, only the indexList and the defaultVui can be
set.
Input:  name,
        (optional) newName = None,
        (optional) schema = None,
        (optional) groupList = None,
        (optional) admingrpList = None,
        (optional) getListFields = None,
        (optional) sortList = None,
        (optional) indexList = None,
        (optional) defaultVui = None,
        (optional) helpText = None,
        (optional) owner = None,
        (optional) changeDiary = None,
        (optional) objPropList = None,
        (optional) setOption = None
Output: errnr'''
        return self.ARSetSchema(name,
                                newName,
                                schema,
                                groupList,
                                admingrpList,
                                getListFields,
                                sortList,
                                indexList,
                                defaultVui,
                                helpText,
                                owner,
                                changeDiary,
                                objPropList,
                                setOption)

    def SetServerInfo(self, serverInfo):
        '''SetServerInfo updates the indicated configuration information for the specified server.

Input:  serverInfo (can be ARServerInfoList or a pythonic dictionary or list)
Output: errnr'''
        serverInfoList = self.conv2ServerInfoList(serverInfo)
        return self.ARSetServerInfo(serverInfoList)

    def SetServerPort(self, server, port = 0, rpcProgNum = 0):
        '''SetServerPort specifies the port that your program will use to communicate with the
AR System server and whether to use a private server.

Input:  server
        port
        rpcProgNum
Output: errnr'''
        return self.ARSetServerPort(server, port, rpcProgNum)


    def SetSessionConfiguration(self, variableId,
                                  variableValue):
        '''SetSessionConfiguration sets an API session variable.

Input:  variableId,
        variableValue
Output: errnr'''
        return self.ARSetSessionConfiguration(variableId,
                                              variableValue)

    def SetSupportFile(self, fileType, 
                        name, 
                        id2, 
                        fileId, 
                        filePtr):
        '''SetSupportFile sets a support file in the AR System.

Input:  fileType, 
        name, 
        id2, 
        fileId, 
        filePtr
Output: errnr'''
        return self.ARSetSupportFile(fileType, 
                                    name, 
                                    id2, 
                                    fileId, 
                                    filePtr)

    def SetVUI(self, schema, 
               vuiId, 
               vuiName = None, 
               locale = None, 
               vuiType=None,
               dPropList=None, 
               helpText=None, 
               owner=None, 
               changeDiary=None):
        '''SetVUI

Input:  schema, 
        newVuiId, 
        vuiName, 
        locale, 
          vuiType,
          dPropList, 
          helpText, 
          owner, 
          changeDiary
Output: errnr'''
        newVuiId = c_int(vuiId)
        return self.ARSetVUI(schema, 
                    newVuiId, 
                    vuiName, 
                    locale, 
                  vuiType,
                  dPropList, 
                  helpText, 
                  owner, 
                  changeDiary)

    def Signal(self, signalArray):
        '''Signal causes the server to reload information.
        
Input:  (ARSignalList) signalList 
Output: errnr'''
        return self.ARSignal(signalArray)

    def Termination(self):
        '''Termination performs environment-specific cleanup routines and disconnects
from the specified Action Request System session.'''
        return self.ARTermination()

    def ValidateFormCache(self, form, 
                          mostRecentActLink = 0, 
                          mostRecentMenu = 0, 
                          mostRecentGuide = 0):
        '''ValidateFormCache

Input:  form
        (ARTimestamp) mostRecentActLink (optional, default = 0)
        (ARTimestamp) mostRecentMenu (optional, default = 0)
        (ARTimestamp) mostRecentGuide (optional, default = 0)
Output: tuple of (formLastModified, numActLinkOnForm, numActLinkSince, menuSinceList
            groupsLastChanged, userLastChanged, guideSinceList)'''
        return self.ARValidateFormCache(form, 
                                        mostRecentActLink, 
                                        mostRecentMenu, 
                                        mostRecentGuide)

    def ValidateLicense(self, licenseType):
        '''ValidateLicense confirms whether the current server holds a valid license.
        
Input:  (ARLicenseNameType) licenseType 
Output: ARLicenseValidStruct (or None in case of failure)'''
        return self.ARValidateLicense(licenseType)

    def ValidateMultipleLicenses(self, licenseTypeList):
        '''ValidateMultipleLicenses checks whether the current server holds a license for several specified license
types. This function performs the same action as ARValidateLicense, but it is easier
to use and more efficient than validating licenses one by one.

Input:  (ARLicenseNameList) licenseTypeList 
Output: ARLicenseValidList or None in case of failure'''
        return self.ARValidateMultipleLicenses(licenseTypeList)

    def VerifyUser(self):
        '''VerifyUser checks the cache on the specified server
to determine whether the specified user is registered
with the current server. THe three boolean flags are
ignored in this simplified version.
Input:  
Output: tuple of (adminFlag, subAdminFlag, customFlag) 
        or None in case of failure'''
        return self.ARVerifyUser()

    def Free(self, obj, freeStruct=False):
        return self.ARFree(obj, freeStruct)

#########################################################################
#
#
# some more comfort functions
#
#
#########################################################################


###########################################################################
#
#
# XML support functions
#
#
    def GetActiveLinkFromXML(self, parsedStream, 
                               activeLinkName):
        return self.ARGetActiveLinkFromXML(parsedStream, activeLinkName)
        
    def GetContainerFromXML(self, parsedStream, containerName):
        return self.ARGetContainerFromXML(parsedStream, containerName)                

    def GetDSOMappingFromXML(self, parsedStream, 
                               mappingName):
        return self.ARGetDSOMappingFromXML(parsedStream, mappingName)
        
    def GetEscalationFromXML(self, parsedStream, escalationName):
        return self.ARGetEscalationFromXML(parsedStream, escalationName)
        
    def SetActiveLinkToXML(self, activeLinkName):
        al = self.GetActiveLink(activeLinkName)
        if self.errnr > 1:
            self.logger.error ('SetActiveLinkToXML: GetActiveLink failed!')
            return None
        return self.ARSetActiveLinkToXML(cars.ARBoolean(True), al.name,
                c_uint(al.order),
                al.schemaList,
                al.groupList,
                c_uint(al.executeMask),
                cars.ARInternalId(al.controlField),
                cars.ARInternalId(al.focusField),
                c_uint(al.enable),
                al.query,
                al.actionList,
                al.elseList,
                ### TODO! where does this come from???
                None, # supportFileList,???
                c_char_p(al.owner),
                c_char_p(al.lastChanged),
                cars.ARTimestamp(al.timestamp),
                c_char_p(al.helpText),
                c_char_p(al.changeDiary),
                al.objPropList,
                c_uint(8))

    def SetSchemaToXML (self, schemaName, xmlDocHdrFtrFlag=0,
                        compoundSchema=None,
                        permissionList=None,
                        subAdminGrpList=None,
                        getListFields=None,
                        sortList=None,
                        indexList=None,
                        defaultVui=None,
                        nextFieldID=None,
                        coreVersion = 0,
                        upgradeVersion=0,
                        fieldInfoList=None,
                        vuiInfoList=None,
                        owner=None,
                        lastModifiedBy=None,
                        modifiedDate=None,
                        helpText=None,
                        changeHistory=None,
                        objPropList=None,
                        arDocVersion = 0):
        '''Dump Schema to XML according...

This function dumps a schema definition into a string in
XML format; this implementation takes as  arguments the structs
that drive the xml output.
If you want the more convenient XML output, call ERSetSchemaToXML
It is important to understand that this function is executed on the
client side; in other words, the user is responsible for fetching
all relevant information and handing it over to this function.
This call really only transforms the information into XML.
Input: context
       schemaName
       (optional) xmlDocHdrFtrFlag (default: 0)
       (optional) compoundSchema (default: None)
       (optional) permissionList (default: None)
       (optional) subAdminGrpList (default: None)
       (optional) getListFields (default: None)
       (optional) sortList (default: None)
       (optional) indexList (default: None)
       (optional) defaultVui (default: None)
       (optional) nextFieldID (default: None)
       (optional) coreVersion (default: 0)
       (optional) upgradeVersion (default: 0)
       (optional) fieldInfoList (default: None)
       (optional) vuiInfoList (default: None)
       (optional) owner (default: None)
       (optional) lastModifiedBy (default: None)
       (optional) modifiedDate (default: None)
       (optional) helpText (default: None)
       (optional) changeHistory (default: None)
       (optional) objPropList (default: None)
       (optional) arDocVersion (default: 0)
Output: string containing the XML.
'''
        schema = self.GetSchema (schemaName)
        if self.errnr > 1:
            self.logger.error("GetSchema failed for schema: %s " % (schemaName))
            return None
        vuiInfoList = self.ARGetListVUI(schemaName)
        if self.errnr > 1:
            self.logger.error ('ARGetListVui failed for schema %s' % (schemaName))
            return None
        fieldInfoList = self.GetMultipleFields(schemaName)
        if self.errnr > 1:
            self.logger.error("GetMultipleFields failed with error: %d " % (self.errnr))
            return None
#        schemaName = cars.ARNameType()
#        schemaName = create_string_buffer(schema.name, 255)
        owner = cars.ARAccessNameType()
        owner = (schema.owner+'\0'*(31-len(schema.owner)))[:]
        lastChanged = cars.ARAccessNameType()
        lastChanged = (schema.lastChanged+'\0'*(31-len(schema.lastChanged)))[:]
        return self.ARSetSchemaToXML(schemaName,
                                             xmlDocHdrFtrFlag,
                                             schema.schema,
                                             schema.groupList,
                                             schema.admingrpList,
                                             schema.getListFields,
                                             schema.sortList,
                                             schema.indexList,
                                             None, # c_char_p(schema.defaultVui),
                                             c_uint(0), # nextFieldID,
                                             c_ulong(0), # coreVersion,
                                             c_ulong(0), # upgradeVersion,
                                             fieldInfoList,
                                             vuiInfoList,
                                             c_char_p(schema.owner),
                                             c_char_p(schema.lastChanged),
                                             cars.ARTimestamp(schema.timestamp),
                                             c_char_p(schema.helpText),
                                             c_char_p(schema.changeDiary),
                                             schema.objPropList,
                                             c_ulong(8))
    def foo(self):
        self.errstr = ''
        self.errnr = 0
        return "foo", "bar"

    def moo(self):
        self.errstr = ''
        self.errnr = 0
        return "Moo!"

    def errstr(self):
        return self.statusText()

    def APIVersion(self):
        return cars.version/10
    
    def GetAllApplicationNames (self):
        '''return a list of all containers of type application'''
        r = self.GetListContainer(containerArray=cars.ARCON_APP)
        # r is a ARContainerInfoList that we need to massage
        result = [r.conInfoList[i].name for i in range(r.numItems)]
        self.Free(r)
        return result
        
    def GetAllFieldNames (self, schema, 
                          idList=None, 
                          fieldType=cars.AR_FIELD_TYPE_DATA):
        '''GetAllFieldNames retrieves all fieldids and names of a given field type 
for a given schema; this is the opposite function of GetFieldTable.

GetAllFieldNames returns dictionary of field ids and field names. If you do not
supply a list of fieldIds, GetFieldTable will retrieve the fields for you
by calling ARGetListField, using the option specified in fieldType (defaults
to cars.AR_FIELD_TYPE_DATA, i.o.w., it will fetch the info for all data fields).
input: schema
        (optional) idList (default: None; can be an ARInternalIdList or a tuple of fieldids)
        fieldType: (default: data fields)
output: dictionary {fieldid1: name1, fieldid2: name2,...} or None in case of failure'''
        # if not given, retrieve all field ids for this table
        if idList is None:
            idList = self.ARGetListField(schema, fieldType=fieldType)
            if self.errnr > 1:
                raise ARError(self)
        idList = self.conv2InternalIdList(idList)
        existList = cars.ARBooleanList()
        fieldId2  = cars.ARInternalIdList()
        fieldName = cars.ARNameList()
        fieldInfos = self.ARGetMultipleFields(schema,
                                              idList,
                                              None,
                                              fieldName)
        
        if self.errnr > 1:
            self.logger.error('GetMultipleFields failed!')
            raise ARError(self)
        fieldNames = dict([(fieldInfos.fieldList[i].fieldId, fieldInfos.fieldList[i].fieldName) 
                           for i in range(fieldInfos.numItems)])
        self.Free(existList)
        self.Free(fieldId2)
        self.Free(fieldName)
        return fieldNames

    def GetControlStructFields(self):
        '''GetControlStructFields returns the single pieces of the control record.
    
ARGetControlStructFields returns the single pieces of the control
record. This method actually is not necessary in python, as we have
direct access to the members of the struct; however to be
compatible with arsjython and ARSPerl, we implement this method.
Input:
Output: (cacheId, errnr, operationTime, user, password, localeInfo, ,
         sessionId, authString, server)'''
        return self.ARGetControlStructFields()

    def GetFieldByName(self, schemaString, fieldName):
        '''GetFieldByName is a shortcut function that combines ars_GetListField 
and ars_GetField. Given a schema name and field name, it returns the field id. 
If you need more than a few field id's, use GetFieldTable. 
Input: schemaString
       fieldName
Output: fieldid or None in case of failure'''
        fields = self.GetFieldTable(schemaString, 
                                    fieldType=cars.AR_FIELD_TYPE_ALL)
        try:
            return fields[fieldName]
        except KeyError:
            return None
    
    def GetFieldTable (self, schemaString, idList=None, 
                       fieldType=cars.AR_FIELD_TYPE_DATA):
        """GetFieldTable returns a dictionary of field name and field ID.
This is the opposite function of GetAllFieldNames.
        
GetFieldTable returns dictionary of field names and field ids. If you do not
supply a list of fieldIds, GetFieldTable will retrieve the fields for you
by calling ARGetListField, using the option specified in fieldType (defaults
to cars.AR_FIELD_TYPE_DATA, i.o.w., it will fetch the info for all data fields).

Input: schemaString
       (optional) idList (default: None; can be an ARInternalIdList or a tuple of fieldids)
       (optional) fieldType (default: cars.AR_FIELD_TYPE_DATA)
Output: dictionary of {field_name : field_id, ...} or None in case of failure"""
        # if not given, retrieve all field ids for this table

        if idList is None:
            idList = self.ARGetListField(schemaString, fieldType=fieldType)
            if self.errnr > 1:
                raise ARError(self)
        idList = self.conv2InternalIdList(idList)
        existList = cars.ARBooleanList()
        fieldName = cars.ARNameList()
        fieldInfos = self.ARGetMultipleFields(schemaString,
                                              idList,
                                              None,
                                              fieldName)
        if self.errnr > 1:
            raise ARError(self)
        fieldNames = dict([(fieldInfos.fieldList[i].fieldName, fieldInfos.fieldList[i].fieldId) 
                           for i in range(fieldInfos.numItems)])
        self.Free(existList)
        self.Free(fieldName)
        return fieldNames

class erARS(erARS51):
    pass

if float(cars.version) >= 60:    
    class erARS60(erARS51):
        def CreateSchema(self, 
                         name, 
                         schema, 
                         schemaInheritanceList, 
                         groupList, 
                         admingrpList, 
                         getListFields,
                         sortList, 
                         indexList, 
                         archiveInfo,
                         defaultVui,
                         helpText=None, 
                         owner=None, 
                         changeDiary=None, 
                         objPropList=None):
            '''
            CreateSchema creates a new form with the indicated name on the
specified server.
Input: name, 
     schema, 
     schemaInheritanceList (will be set to None)
     groupList, 
     admingrpList, 
     getListFields,
     sortList, 
     indexList, 
     archiveInfo,
     defaultVui,
     optional: helpText (default =None), 
     optional: owner (default =None, 
     optional: changeDiary (default =None    
     optional: objPropList (default =None
Output: errnr
'''
            return self.ARCreateSchema(self, 
                    name, 
                    schema, 
                    schemaInheritanceList,
                    groupList, 
                    admingrpList,
                    getListFields,
                    sortList, 
                    indexList, 
                    archiveInfo,
                    defaultVui,
                    helpText, 
                    owner, 
                    changeDiary, 
                    objPropList)

        def DeleteActiveLink(self, name, deleteOption = cars.AR_DEFAULT_DELETE_OPTION):
            '''
DeleteActiveLink deletes the active link with the indicated name from the
specified server and deletes any container references to the active link.
Input: 
       name
Output: errnr'''
            return self.ARDeleteActiveLink(name, deleteOption)
    
        def DeleteCharMenu(self, name, deleteOption = cars.AR_DEFAULT_DELETE_OPTION):
            '''
DeleteCharMenu deletes the character menu with the indicated name from
the specified server.
Input: 
       name
Output: errnr'''
            return self.ARDeleteCharMenu(name, deleteOption)
    
        def DeleteContainer(self, name, deleteOption = cars.AR_DEFAULT_DELETE_OPTION):
            '''
DeleteContainer deletes the container with the indicated name from
the specified server and deletes any references to the container from other containers.

Input: 
       name
Output: errnr
'''
            return self.ARDeleteContainer(name, deleteOption)
    
        def DeleteEscalation(self, name, deleteOption = cars.AR_DEFAULT_DELETE_OPTION):
            '''
DeleteEscalation deletes the escalation with the indicated name from the
specified server and deletes any container references to the escalation.
Input:  name
Output: errnr
'''
            return  self.ARDeleteEscalation(name, deleteOption)
            
        def DeleteFilter(self, name, deleteOption = cars.AR_DEFAULT_DELETE_OPTION):
            '''DeleteFilter deletes the filter with the indicated name from the
specified server and deletes any container references to the filter.
Input:  name
        deleteOption
Output: errnr'''
            return self.ARDeleteFilter(name, deleteOption)

        def Export(self, structArray, 
                   displayTag = None, 
                   vuiType = cars.AR_VUI_TYPE_NONE, 
                   lockinfo = None):
            '''Export exports AR data structures to a string.
Use this function to copy structure definitions from one AR System server to another.
Note: Form exports do not work the same way with ARExport as they do in
Remedy Administrator. Other than views, you cannot automatically
export related items along with a form. You must explicitly specify the
workflow items you want to export. Also, ARExport cannot export a form
without embedding the server name in the export file (something you can
do with the "Server-Independent" option in Remedy Administrator).
Input: structArray ((cars.AR_STRUCT_ITEM_xxx, name), ...)
       displayTag (optional, default = None)
       vuiType (optional, default = cars.AR_VUI_TYPE_NONE
       (list) lockInfo: (optional, default = None) a list of (lockType, lockKey)
Output: string (or None in case of failure)'''
            structItems = self.conv2StructItemList(structArray)
            if lockinfo is None:
                lockinfo = cars.ARWorkflowLockStruct()
            else:
                lockinfo = cars.ARWorkflowLockStruct(lockinfo[0], lockinfo[1])
            return self.ARExport(structItems, displayTag, vuiType, lockinfo)
    
        def ExportLicense(self):
            '''ARExportLicense specifies a pointer that is set to malloced 
space and contains the full contents of the license file currently 
on the server. This buffer can be written to a file to produce 
an exact replication of the license file, including all checksums
and encryption.'''
            return self.ARExportLicense()
    
        def GetApplicationState(self, applicationName):
            '''Retrieves the application state: maintenance (admin only), 
test, or production.'''
            return self.ARGetApplicationState(applicationName)
    
        def GetListActiveLink (self, schema=None, 
                               changedSince=0, 
                               objPropList = None):
            '''GetListActiveLink retrieves a list of active links for a schema/server.

GetListActiveLink retrieves a list of active links for a schema/server
Input: 
       (optional) schema (default: None)
       (optional) changedSince (default: 0)
       (optional) objPropList  (default: None)
Output: (name1, name2, ...) or None in case of failure'''
            result = self.ARGetListActiveLink (schema, 
                                               changedSince, 
                                               objPropList)
            if result is None:
                return None
            else:
                pythonicResult = self.convNameList2List(result)
                self.Free(result)
                return pythonicResult 
            
        def GetListApplicationState(self):
            '''GetListApplicationState retrieves the list of application states 
(maintenance, test, or production) that an application on this server 
can assume. This list is server-dependent.
Input: 
Output: (name1, name2, ...) or None in case of failure'''
            result = self.ARGetListApplicationState()
            if result is None:
                return None
            else:
                pythonicResult = self.convNameList2List(result)
                self.Free(result)
                return pythonicResult            

        def GetListCharMenu(self, changedSince=0, 
                            formList = None,
                            actLinkList = None, 
                            objPropList = None):
            '''GetListCharMenu retrieves a list of character menus.

Input: (int) changedSince (optional, default = 0)
       (tuple of names) formList (optional, default = None)
       (tuple of names) actLinkList (optional, default = None)
       (ARPropList) objPropList (optional, default = None)
Output: (name1, name2, ...) or None in case of failure'''
            formList = self.conv2NameList(formList)
            actLinkList = self.conv2NameList(actLinkList)
            result = self.ARGetListCharMenu(changedSince, 
                                            formList,
                                            actLinkList,
                                            objPropList)
            if result is None:
                return None
            else:
                pythonicResult = self.convNameList2List(result)
                self.Free(result)
                return pythonicResult
    
        def GetListContainer (self, changedSince = 0,
                              containerArray = cars.ARCON_ALL,
                              attributes = cars.AR_HIDDEN_INCREMENT,
                              ownerObjList = None, 
                              objPropList = None):
            '''GetListContainer retrieves a list of containers.

GetListContainer retrieves a list of containers.
Input: (optional) changedSince (default: 0)
       (optional) containerArray: array of values representing
       container types (default: ARCON_ALL)
       (optional) attributes (default: cars.AR_HIDDEN_INCREMENT)
       (optional) ownerObjList (default: None)
       (optional) objPropList (Default: None)
Output: ARContainerInfoList (or None in case of failure)'''
            
            containerTypes = self.conv2ContainerTypeList(containerArray)
            return self.ARGetListContainer(changedSince,
                                           containerTypes,
                                           attributes,
                                           ownerObjList)
    
        def GetListEntry(self, schema, 
                         query=None,
                          getListFields=None, 
                          sortList=None,
                          firstRetrieve=cars.AR_START_WITH_FIRST_ENTRY,
                          maxRetrieve=cars.AR_NO_MAX_LIST_RETRIEVE,
                          useLocale = False):
            '''GetListEntry retrieves a list of entries for a schema.

GetListEntry retrieves a list of entries/objects for a specific schema
according to specific search query.

Input: schema/form name
       (optional) query string
       (optional) getListFields (default: None)
       (optional) sortList (default: None; can be 
               ((fieldid, 1), (id2, 0), ...) 
               with sec. parameter 0 = ascending
       (optional) firstRetrieve (default: AR_START_WITH_FIRST_ENTRY)
       (optional) maxRetrieve (default: AR_NO_MAX_LIST_RETRIEVE)
       (optional) useLocale (default: False)
Output: (list ((entryid , shortdesc) , ...), numMatches) or raise ARError in case of failure.
It is important that the query looks something like this:
'field' = "value" (please note the quotation marks).
'''
            q = self.conv2QualifierStruct(schema, query)
            arGetListFields = self.conv2EntryListFieldList(getListFields, schema)
            if self.errnr > 1:
                self.logger.error('GetListEntry: converting getListFields failed!')
                raise ARError(None, 'GetListEntry: converting getListFields failed!', cars.AR_RETURN_ERROR)
            arSortList = self.conv2SortList (sortList)
            if self.errnr > 1:
                self.logger.error('GetListEntry: converting sort list failed!')
                raise ARError(None, 'GetListEntry: converting sort list failed!', cars.AR_RETURN_ERROR)
            result = self.ARGetListEntry(schema, 
                                       q,
                                       arGetListFields,
                                       arSortList,
                                       firstRetrieve,
                                       maxRetrieve,
                                       useLocale)
            if result is None:
                raise ARError(self)
            else:
                (entryListFieldValueList, numMatches) = result
                pythonicResult = self.convEntryListList2List(entryListFieldValueList)
                self.Free(entryListFieldValueList)
                return (pythonicResult, numMatches)
    
        def GetListEntryWithFields (self, schema, 
                                    query,
                                    getListFields=None, 
                                    sortList=None,
                                    firstRetrieve=cars.AR_START_WITH_FIRST_ENTRY,
                                    maxRetrieve=cars.AR_NO_MAX_LIST_RETRIEVE,
                                    useLocale = False):
            '''GetListEntryWithFields retrieve a list of entries for a schema.

GetListEntryWithFields retrieve a list of entries/objects for a
specific schema according to specific search query together with
their fields and values.

Input: schema/form name
       query string
       (optional) getListFields (default: None)
       (optional) sortList (default: None)
       (optional) firstRetrieve (default: AR_START_WITH_FIRST_ENTRY)
       (optional) maxRetrieve (default: AR_NO_MAX_LIST_RETRIEVE)
       (optional) useLocale (default: False)
Output: (list ((entryid , { fid1 : value1, ...}), ()....), numMatches) or raise ARError in case of failure.
It is important that the query looks something like this:
'field' = "value" (please note the quotation marks).'''
            q = self.conv2QualifierStruct(schema, query)
            arGetListFields = self.conv2EntryListFieldList(getListFields, schema)
            if self.errnr > 1:
                self.logger.error('GetListEntryWithFields: converting getListFields failed!')
                raise ARError(None, 'GetListEntry: converting getListFields failed!', cars.AR_RETURN_ERROR)
            arSortList = self.conv2SortList (sortList)
            if self.errnr > 1:
                self.logger.error('GetListEntryWithFields: converting sort list failed!')
                raise ARError(None, 'GetListEntry: converting sort list failed!', cars.AR_RETURN_ERROR)
            result = self.ARGetListEntryWithFields(schema, 
                                                     q,
                                                     arGetListFields,
                                                     arSortList,
                                                     firstRetrieve,
                                                     maxRetrieve,
                                                     useLocale)
            if result is None:
                raise ARError(self)
            else:
                (entryListFieldValueList, numMatches) = result
                pythonicResult = self.convEntryListFieldValueList2List(entryListFieldValueList)
                self.Free(entryListFieldValueList)
                return (pythonicResult, numMatches)
    
        def GetListEscalation (self, schema=None,
                               changedSince = 0,
                               objPropList = None):
            '''GetListEscalation retrieves a list of all escalations.

GetListEscalation retrieves a list of all escalations.
Input: 
       (optional) schema (default: None)
       (optional): changedSince (default: 0)
       (optional) objPropList (default: None)
Output: (name1, name2, ...) or None in case of failure'''
            result = self.ARGetListEscalation (schema, changedSince, objPropList)
            if result is None:
                return None
            else:
                pythonicResult = self.convNameList2List(result)
                self.Free(result)
                return pythonicResult 
    
        def GetListFilter(self, schema=None, 
                          changedSince=0, 
                          objPropList = None):
            '''GetListFilter return a list of all available filter for a schema.

GetListFilter return a list of all available filter for a schema/server.
Input: 
       (optional) schema (default: None -- retrieve filter for server)
       (optional) changedSince (default: 0)
       (optional) objPropList (default: None)
Output: (name1, name2, ...) or None in case of failure'''
            result = self.ARGetListFilter(schema, changedSince, objPropList)
            if result is None:
                return None
            else:
                pythonicResult = self.convNameList2List(result)
                self.Free(result)
                return pythonicResult

        def GetListRole (self, applicationName, 
                         userName = None, 
                         password = None):
            '''GetListRole retrieves a list of roles for a deployable application 
or returns a list of roles for a user for a deployable application.'''
            return self.ARGetListRole(applicationName, userName, password)
    
    
        def GetListSchema(self, changedSince=0, 
                          schemaType=cars.AR_HIDDEN_INCREMENT,
                          name='', 
                          fieldIdArray=None, 
                          objPropList=None):
            '''GetListSchema return a list of all available schemas

GetListSchema returns a list of all available schemas
Input: (optional) changedSince: a timestamp (default: 0)
       (optional) schemaType (default: AR_LIST_SCHEMA_ALL | AR_HIDDEN_INCREMENT)
       (optional) name (default "", only necessary if schemaType is
       AR_LIST_SCHEMA_UPLINK
       (optional) fieldIdArray (default: None) ARS then only returns the
       forms that contain all the fields in this list.
Output: (name1, name2, ...) or None in case of failure'''
            # if the fieldIdArray is a tuple or array, convert this into a ARInternalIdList
            fieldIdList = self.conv2InternalIdList(fieldIdArray)
            result = self.ARGetListSchema(changedSince, 
                                          schemaType, 
                                          name, 
                                          fieldIdList,
                                          objPropList)
            if result is None:
                return None
            else:
                pythonicResult = self.convNameList2List(result)
                self.Free(result)
                return pythonicResult
    
        def GetListSchemaWithAlias(self, changedSince=0, 
                                   schemaType=cars.AR_HIDDEN_INCREMENT, 
                                   name='', 
                                   fieldIdArray=None, 
                                   vuiLabel=None,
                                   objPropList=None):            
            """GetListSchemaWithAlias retrieves a list of form definitions and 
their corresponding aliases.
Input: (optional) changedSince: a timestamp (default: 0)
       (optional) schemaType (default: AR_LIST_SCHEMA_ALL | AR_HIDDEN_INCREMENT)
       (optional) name (default "", only necessary if schemaType is
       AR_LIST_SCHEMA_UPLINK
       (optional) fieldIdArray (list of fieldids; default: None; ARS then only returns the
               forms that contain all the fields in this list)
       vuiLabel
       objPropList
Output: ((name1, alias1), (name2, alias2),...)
            or None in case of failure"""

            fieldIdList = self.conv2InternalIdList(fieldIdArray)
            result = self.ARGetListSchemaWithAlias(changedSince, 
                                                 schemaType,
                                                 name,
                                                 fieldIdList,
                                                 vuiLabel,
                                                 objPropList)
            if result is None:
                return None
            else:
                nameList = self.convNameList2List(result [0])
                aliasList = self.convNameList2List(result[1])
                self.Free(result [0])
                self.Free(result [1])
                return zip(nameList, aliasList)
            
        def GetMultipleCharMenus(self, changedSince = 0, 
                                 nameList = None):
            '''GetMultipleCharMenus retrieves information about a group of 
character menus on the specified server with the names specified 
by the nameList parameter.
'''
            nameList = self.conv2NameList (nameList)
            return self.ARGetMultipleCharMenus(changedSince, nameList)
    
        def GetMultipleContainers(self, 
                                    changedSince = 0, 
                                    nameList = None,
                                    containerTypes = None,
                                    attributes = cars.AR_HIDDEN_INCREMENT,
                                    ownerObjList = None,
                                    refTypes = None,
                                    containerNameListP = True,
                                    groupListListP = False,
                                    admingrpListListP = False,
                                    ownerObjListListP = False,
                                    labelListP = False,
                                    descriptionListP = False,
                                    typeListP = False,
                                    referenceListP = False,
                                    helpTextListP = False,
                                    ownerListP = False,
                                    timestampListP = False,
                                    lastChangedListP = False,
                                    changeDiaryListP = False,
                                    objPropListListP = False):
            '''GetMultipleContainers retrieves multiple container objects.
            '''
            nameList = self.conv2NameList (nameList)
            containerNameList = groupListList = admingrpListList = None
            ownerObjListList = labelList = descriptionList = None
            typeList = referenceList = helpTextList = None
            ownerList = timestampList = lastChangedList = None
            changeDiaryList = objPropListList = None
            if containerNameListP: containerNameList = cars.ARNameList()
            if groupListListP: groupListList = cars.ARPermissionListList()
            if admingrpListListP: admingrpListList = cars.ARInternalIdListList()
            if ownerObjListListP: ownerObjListList = cars.ARContainerOwnerObjListList()
            if labelListP: labelList = cars.ARTextStringList()
            if descriptionListP: descriptionList = cars.ARTextStringList()
            if typeListP: typeList = cars.ARUnsignedIntList()
            if referenceListP: referenceList = cars.ARReferenceListList()
            if helpTextListP: helpTextList = cars.ARTextStringList()
            if ownerListP: ownerList = cars.ARAccessNameList()
            if timestampListP: timestampList = cars.ARTimestampList()
            if lastChangedListP: lastChangedList = cars.ARAccessNameList()
            if changeDiaryListP: changeDiaryList = cars.ARTextStringList()
            if objPropListListP: objPropListList = cars.ARPropListList()
            return self.ARGetMultipleContainers(changedSince, 
                            nameList,
                            containerTypes,
                            attributes,
                            ownerObjList,
                            refTypes,
                            containerNameList,
                            groupListList,
                            admingrpListList,
                            ownerObjListList,
                            labelList,
                            descriptionList,
                            typeList,
                            referenceList,
                            helpTextList,
                            ownerList,
                            timestampList,
                            lastChangedList,
                            changeDiaryList,
                            objPropListList)
            
        def GetMultipleEntryPoints(self, changedSince,
                                     appNameList,
                                     refTypeList,
                                     displayTag = None,
                                     vuiType = cars.AR_VUI_TYPE_NONE,
                                     entryPointNameListP = False,
                                     entryPointTypeListP = False,
                                     entryPointDLabelListP = False,
                                     ownerAppNameListP = False,
                                     ownerAppDLabelListP = False,
                                     groupListListP = False,
                                     ownerObjListListP = False,
                                     descriptionListP = False,
                                     referencesListP = False,
                                     helpTextListP = False,
                                     timestampListP = False,
                                     objPropListListP = False):
            '''GetMultipleEntryPoints retrieves the entry points of multiple 
applications. It returns the entry points that are accessible by 
the user, taking into account user permissions, licenses,
and application states.'''
            entryPointNameList = entryPointTypeList = entryPointDLabelList = None
            ownerAppNameList = ownerAppDLabelList = groupListList = None
            ownerObjListList = descriptionList = referencesList = None
            helpTextList = timestampList = objPropListList = None
            if entryPointNameListP: entryPointNameList = cars.ARNameList()
            if entryPointTypeListP: entryPointTypeList = cars.ARNameList()
            if entryPointDLabelListP: entryPointDLabelList = cars.ARNameList()
            if ownerAppNameListP: ownerAppNameList = cars.ARNameList()
            if ownerAppDLabelListP: ownerAppDLabelList = cars.ARNameList()
            if groupListListP: groupListList = cars.ARNameList()
            if ownerObjListListP: ownerObjListList = cars.ARNameList()
            if descriptionListP: descriptionList = cars.ARNameList()
            if referencesListP: referencesList = cars.ARNameList()
            if helpTextListP: helpTextList = cars.ARNameList()
            if timestampListP: timestampList = cars.ARNameList()
            if objPropListListP: objPropListList = cars.ARNameList()
            return self.ARGetMultipleEntryPoints(changedSince,
                                     appNameList,
                                     refTypeList,
                                     displayTag,
                                     vuiType,
                                     entryPointNameList,
                                     entryPointTypeList,
                                     entryPointDLabelList,
                                     ownerAppNameList,
                                     ownerAppDLabelList,
                                     groupListList,
                                     ownerObjListList,
                                     descriptionList,
                                     referencesList,
                                     helpTextList,
                                     timestampList,
                                     objPropListList)
    
        def GetMultipleEscalations (self, changedSince = 0, 
                                    nameList = None,
                                    esclTmListP = True,
                                    workflowConnectListP = True,
                                    enableListP = False,
                                    queryListP = False,
                                    actionListListP = False,
                                    elseListListP = False,
                                    helpTextListP = False,
                                    timestampListP = False,
                                    ownerListP = False,
                                    lastChangedListP = False,
                                    changeDiaryListP = False,
                                    objPropListListP = False):
            '''GetMultipleEscalations retrieves information about a group 
of escalations on the specified server with the names specified by 
the nameList parameter.'''
            nameList = self.conv2NameList (nameList)
            esclTmList = workflowConnectList = None
            enableList = queryList = actionListList = None
            elseListList = helpTextList = timestampList = None
            ownerList = lastChangedList = changeDiaryList = None
            objPropListList = None
            if esclTmListP: esclTmList = cars.AREscalationTmList()
            if workflowConnectListP: workflowConnectList = cars.ARWorkflowConnectList()
            if enableListP: enableList = cars.ARUnsignedIntList()
            if queryListP: queryList = cars.ARQualifierList()
            if actionListListP: actionListList = cars.ARFilterActionListList()
            if elseListListP: elseListList = cars.ARFilterActionListList()
            if helpTextListP: helpTextList = cars.ARTextStringList()
            if timestampListP: timestampList = cars.ARTimestampList()
            if ownerListP: ownerList = cars.ARAccessNameList()
            if lastChangedListP: lastChangedList = cars.ARAccessNameList()
            if changeDiaryListP: changeDiaryList = cars.ARTextStringList()
            if objPropListListP: objPropListList = cars.ARPropListList()
            return self.ARGetMultipleEscalations (changedSince, 
                                                  nameList,
                                                  esclTmList,
                                                  workflowConnectList,
                                                  enableList,
                                                  queryList,
                                                  actionListList,
                                                  elseListList,
                                                  helpTextList,
                                                  timestampList,
                                                  ownerList,
                                                  lastChangedList,
                                                  changeDiaryList,
                                                  objPropListList)
    
        def GetMultipleSchemas(self, changedSince=0, 
                               schemaTypeList=None,
                               nameList=None, 
                               fieldIdList=None,
                               schemaListP = True,
                               schemaInheritanceListListP = False, 
                               groupListListP = False,
                               admingrpListListP = False,
                               getListFieldsListP = False,
                               sortListListP = False,
                               indexListListP = False,
                               archiveInfoListP = False,
                               defaultVuiListP = False,
                               helpTextListP = False,
                               timestampListP = False,
                               ownerListP = False,
                               lastChangedListP = False,
                               changeDiaryListP = False,
                               objPropListListP = False):
            '''GetMultipleSchemas

Input:  changedSince 
        schemaTypeList
        nameList 
        fieldIdList
        archiveInfoList    
        
Output: ARSchemaList'''
            nameList = self.conv2NameList(nameList)
            schemaList = schemaInheritanceListList = groupListList = None
            admingrpListList = getListFieldsList = sortListList = None
            indexListList = archiveInfoList = defaultVuiList = None
            helpTextList = timestampList = ownerList = None
            lastChangedList = changeDiaryList = objPropListList = None
            if schemaListP: schemaList = cars.ARCompoundSchemaList()
            if schemaInheritanceListListP: 
                schemaInheritanceListList = cars.ARSchemaInheritanceListList()
            if groupListListP: groupListList = cars.ARPermissionListList()
            if admingrpListListP: admingrpListList = cars.ARInternalIdListList()
            if getListFieldsListP: getListFieldsList = cars.AREntryListFieldListList()
            if sortListListP: sortListList = cars.ARSortListList()
            if indexListListP: indexListList = cars.ARIndexListList()
            if archiveInfoListP: archiveInfoList = cars.ARArchiveInfoList()
            if defaultVuiListP: defaultVuiList = cars.ARNameList()
            if helpTextListP: helpTextList = cars.ARTextStringList()
            if timestampListP: timestampList = cars.ARTimestampList()
            if ownerListP: ownerList = cars.ARAccessNameList()
            if lastChangedListP: lastChangedList = cars.ARAccessNameList()
            if changeDiaryListP: changeDiaryList = cars.ARTextStringList()
            if objPropListListP: objPropListList = cars.ARPropListList()
            return self.ARGetMultipleSchemas(changedSince, 
                                schemaTypeList, 
                                nameList, 
                                fieldIdList,
                                schemaList, 
                                schemaInheritanceListList,
                                groupListList,
                                admingrpListList,
                                getListFieldsList,
                                sortListList,
                                indexListList,
                                archiveInfoList,
                                defaultVuiList,
                                helpTextList,
                                timestampList,
                                ownerList,
                                lastChangedList,
                                changeDiaryList,
                                objPropListList)
    
        def ImportLicense(self, importBuf, importOption = cars.AR_LICENSE_IMPORT_APPEND):
            '''ImportLicense imports a buffer, which is the contents of a license file, including checksums
and encryption and an option, which tells whether to overwrite the existing
license file or append to it.
When called, the server validates that the buffer is a valid license file and
either appends the licenses in the file to the existing license file or replaces the
existing license file with the new file.
            Input:  importBuf, 
                    importOption
            Output: errnr'''
            return self.ARImportLicense(importBuf, importOption)
    
        def SetApplicationState(self, applicationName, stateName):
            '''SetApplicationState sets the application state (maintenance, test, or production) 
in the AR System Application State form.

Input:  applicationName, 
        stateName
Output: errnr'''
            return self.ARSetApplicationState(applicationName, stateName)   
            
    ###########################################################################
    #
    #
    # XML support functions
    #
    #
    
        def SetSchemaToXML (self, schemaName, xmlDocHdrFtrFlag=0,
                            compoundSchema=None,
                            permissionList=None,
                            subAdminGrpList=None,
                            getListFields=None,
                            sortList=None,
                            indexList=None,
                            archiveInfo=None,
                            defaultVui=None,
                            nextFieldID=None,
                            coreVersion = 0,
                            upgradeVersion=0,
                            fieldInfoList=None,
                            vuiInfoList=None,
                            owner=None,
                            lastModifiedBy=None,
                            modifiedDate=None,
                            helpText=None,
                            changeHistory=None,
                            objPropList=None,
                            arDocVersion = 0):
            '''Dump Schema to XML according...

This function dumps a schema definition into a string in
XML format; this implementation takes as  arguments the structs
that drive the xml output.
If you want the more convenient XML output, call ERSetSchemaToXML
It is important to understand that this function is executed on the
client side; in other words, the user is responsible for fetching
all relevant information and handing it over to this function.
This call really only transforms the information into XML.
Input: context
       schemaName
       (optional) xmlDocHdrFtrFlag (default: 0)
       (optional) compoundSchema (default: None)
       (optional) permissionList (default: None)
       (optional) subAdminGrpList (default: None)
       (optional) getListFields (default: None)
       (optional) sortList (default: None)
       (optional) indexList (default: None)
       (optional) archiveInfo (default: None)
       (optional) defaultVui (default: None)
       (optional) nextFieldID (default: None)
       (optional) coreVersion (default: 0)
       (optional) upgradeVersion (default: 0)
       (optional) fieldInfoList (default: None)
       (optional) vuiInfoList (default: None)
       (optional) owner (default: None)
       (optional) lastModifiedBy (default: None)
       (optional) modifiedDate (default: None)
       (optional) helpText (default: None)
       (optional) changeHistory (default: None)
       (optional) objPropList (default: None)
       (optional) arDocVersion (default: 0)
Output: string containing the XML.'''
            schema = self.GetSchema (schemaName)
            if self.errnr > 1:
                self.logger.error("GetSchema failed for schema: %s " % (schemaName))
                return None
            vuiInfoList = self.ARGetListVUI(schemaName)
            if self.errnr > 1:
                self.logger.error ('GetListVui failed for schema %s' % (schemaName))
                return None
            fieldInfoList = self.GetMultipleFields(schemaName)
            if self.errnr > 1:
                self.logger.error("GetMultipleFields failed with error: %d " % (self.errnr))
                return None
    #        schemaName = cars.ARNameType()
    #        schemaName = create_string_buffer(schema.name, 255)
            owner = cars.ARAccessNameType()
            owner = (schema.owner+'\0'*(31-len(schema.owner)))[:]
            lastChanged = cars.ARAccessNameType()
            lastChanged = (schema.lastChanged+'\0'*(31-len(schema.lastChanged)))[:]
            return self.ARSetSchemaToXML(schemaName,
                                             xmlDocHdrFtrFlag,
                                             schema.schema,
                                             schema.groupList,
                                             schema.admingrpList,
                                             schema.getListFields,
                                             schema.sortList,
                                             schema.indexList,
                                             schema.archiveInfo,
                                             None, # c_char_p(schema.defaultVui),
                                             c_uint(0), # nextFieldID,
                                             c_ulong(0), # coreVersion,
                                             c_ulong(0), # upgradeVersion,
                                             fieldInfoList,
                                             vuiInfoList,
                                             c_char_p(schema.owner),
                                             c_char_p(schema.lastChanged),
                                             cars.ARTimestamp(schema.timestamp),
                                             c_char_p(schema.helpText),
                                             c_char_p(schema.changeDiary),
                                             schema.objPropList,
                                             c_ulong(8)) # arDocVersion)
                                         
            return self.ARSetSchemaToXML(xmlDocHdrFtrFlag,
                                         schemaName,
                                         compoundSchema,
                                         permissionList,
                                         subAdminGrpList,
                                         getListFields,
                                         sortList,
                                         indexList,
                                         archiveInfo,
                                         defaultVui,
                                         nextFieldID,
                                         coreVersion,
                                         upgradeVersion,
                                         fieldInfoList,
                                         vuiInfoList,
                                         owner,
                                         lastModifiedBy,
                                         modifiedDate,
                                         helpText,
                                         changeHistory,
                                         objPropList,
                                         arDocVersion)

    class erARS(erARS60):
        pass
if float(cars.version) >= 63: 
    
    class erARS63(erARS60):
    
        def BeginBulkEntryTransaction (self):
            '''BeginBulkEntryTransaction marks the beginning of a series of 
entry API function calls.

Those function calls will be grouped together and sent 
to the AR System server as part of one transaction. All calls 
related to create, set, delete, and merge operations made between 
this API call and a trailing AREndBulkEntryTransaction call will 
not be sent to the server until the trailing call is made.
Input:
Output: errnr'''
            return self.ARBeginBulkEntryTransaction()
    
        def EndBulkEntryTransaction(self, actionType = cars.AR_BULK_ENTRY_ACTION_SEND):
            '''EndBulkEntryTransaction marks the ending of a series of entry API function calls that 
are grouped together and sent to the AR System server as part 
of one transaction. All calls related to create, set, delete, 
and merge operations made before this API call and after the 
preceding ARBeginBulkEntryTransaction call will be sent to the
server when this call is issued and executed within a single 
database transaction.'''
            return self.AREndBulkEntryTransaction()

        def GetEntryBlock(self, entryBlockList, blockNumber = 0):
            '''GetEntryBlock retrieves a list of entries contained in a block of entries 
retrieved using ARGetListEntryBlocks.

Input: entryBlockList
       (optional) blockNumber (default = 0)
Output: dictionary {entryid: {fieldid1 : value, ...}, ...} 
        or None in case of failure'''
            result = self.ARGetEntryBlock(entryBlockList, blockNumber)
            if self.errnr > 1:
                raise ARError(self)
            pythonicResult = self.convEntryListFieldValueList2Dict(result)
            self.Free(result)
            return pythonicResult
    
        def GetListEntryBlocks(self, schema, 
                                 query = None, 
                                 getListFields = None,
                                 sortList = None,
                                 numRowsPerBlock = 50,
                                 firstRetrieve = cars.AR_START_WITH_FIRST_ENTRY,
                                 maxRetrieve = cars.AR_NO_MAX_LIST_RETRIEVE,
                                 useLocale = False):
            '''GetListEntryBlocks retrieves a list of blocks of entries from 
the specified server. Data is returned as a data structure, 
AREntryListBlock. Entries are encapsulated in the AREntryListBlock 
data structure and divided into blocks of entries. You call
ARGetEntryBlock with a block number to return a list of entries for 
that block.
Input:
Output: (entryBlockList (AREntryBlockList), 
         numReturnedRows, 
         numMatches) 
         or None in case of failure'''
            q = self.conv2QualifierStruct(schema, query)
            arGetListFields = self.conv2EntryListFieldList(getListFields, schema)
            if self.errnr > 1:
                self.logger.error('GetListEntryBlocks: ERROR: converting getListFields failed!')
                raise ARError(None, 'GetListEntryBlocks: ERROR: converting getListFields failed!', cars.AR_RETURN_ERROR)
            arSortList = self.conv2SortList (sortList)
            if self.errnr > 1:
                self.logger.error('GetListEntryBlocks: ERROR: converting sort list failed!')
                raise ARError(None, 'GetListEntryBlocks: ERROR: converting sort list failed!', cars.AR_RETURN_ERROR)
            result = self.ARGetListEntryBlocks(schema, 
                                             q,
                                             arGetListFields,
                                             arSortList,
                                             numRowsPerBlock,
                                             firstRetrieve,
                                             maxRetrieve,
                                             useLocale)
            if self.errnr > 1:
                raise ARError(self)
            return result

        def GetMultipleFilters(self, changedSince = 0, 
                               nameList = None,
                               orderListP = True,
                               workflowConnectListP = True,
                               opSetListP = False,
                               enableListP = False,
                               queryListP = False,
                               actionListListP = False,
                               elseListListP = False,
                               helpTextListP = False,
                               timestampListP = False,
                               ownerListP = False,
                               lastChangedListP = False,
                               changeDiaryListP = False,
                               objPropListListP = False):
            '''GetMultipleFilters retrieves information about a group of filters 
on the specified server with the names specified by the nameList 
parameter.'''
            nameList = self.conv2NameList(nameList)
            orderList = workflowConnectList = opSetList = None
            enableList = queryList = actionListList = None
            elseListList = helpTextList = timestampList = None
            ownerList = lastChangedList = changeDiaryList = None
            objPropListList = None
            if orderListP: orderList = cars.ARUnsignedIntList()
            if workflowConnectListP: workflowConnectList = cars.ARWorkflowConnectList()
            if opSetListP: opSetList = cars.ARUnsignedIntList()
            if enableListP: enableList = cars.ARUnsignedIntList()
            if queryListP: queryList = cars.ARQualifierList()
            if actionListListP: actionListList = cars.ARFilterActionListList()
            if elseListListP: elseListList = cars.ARFilterActionListList()
            if helpTextListP: helpTextList = cars.ARTextStringList()
            if timestampListP: timestampList = cars.ARTimestampList()
            if ownerListP: ownerList = cars.ARAccessNameList()
            if lastChangedListP: lastChangedList = cars.ARAccessNameList()
            if changeDiaryListP: changeDiaryList = cars.ARTextStringList()
            if objPropListListP: objPropListList = cars.ARPropListList()
            return self.ARGetMultipleFilters(changedSince,
                                             nameList,
                                             orderList,
                                             workflowConnectList,
                                             opSetList,
                                             enableList,
                                             queryList,
                                             actionListList,
                                             elseListList,
                                             helpTextList,
                                             timestampList,
                                             ownerList,
                                             lastChangedList,
                                             changeDiaryList,
                                             objPropListList)
            
        def GetMultipleVUIs(self, schema, 
                            wantList = None, 
                            changedSince = 0):
            '''GetMultipleVUIs retrieves information about a group of form views 
(VUIs) on the specified server with the names specified by 
the nameList parameter.'''
            dPropListList = cars.ARPropListList()
            helpTextList = cars.ARTextStringList()
            timestampList = cars.ARTimestampList()
            ownerList = cars.ARAccessNameList()
            lastChangedList = cars.ARAccessNameList()
            changeDiaryList = cars.ARTextStringList()
            return self.ARGetMultipleVUIs(schema, 
                                            wantList, 
                                            changedSince,
                                            dPropListList,
                                            helpTextList,
                                            timestampList,
                                            ownerList,
                                            lastChangedList,
                                            changeDiaryList)

        def Login (self,
                   server,
                   username,
                   password,
                   language='', 
                   authString = '',
                   tcpport = 0,
                   rpcnumber = 0,
                   charSet = '',
                   timeZone = '',
                   customDateFormat = '',
                   customTimeFormat = '',
                   separators = '',
                   cacheId = 0,
                   operationTime = 0,
                   sessionId = 0):
            ars.ARS.Login(self, server, username, password, language, 
               authString, tcpport, rpcnumber, charSet, timeZone,customDateFormat,
               customTimeFormat, separators, cacheId,
               operationTime, sessionId)
            if self.errnr < 2:
                self._InitializeCache()

    class erARS(erARS63):
        pass
    
if float(cars.version) >= 70: 
    
    class erARS70(erARS63):
        
        def CreateField(self, schema, fieldId, 
                          reservedIdOK,
                          fieldName, 
                          fieldMap, 
                          dataType, 
                          option, 
                          createMode, 
                          fieldOption, 
                          defaultVal, 
                          permissions,
                          limit=None, 
                          dInstanceList=None,
                          helpText=None, 
                          owner=None, 
                          changeDiary=None):
            '''CreateField creates a new field.
Input: schema (ARNameType)
        fieldId (ARInternalId)
        reservedIdOK (ARBoolean)
        fieldName (ARNameType)
        fieldMap (ARFieldMappingStruct)
        dataType (c_uint)
        option (c_uint)
        createMode (c_uint)
        fieldOption (c_uint) 
        defaultVal (ARValueStruct)
        permissions (ARPermissionList)
        (optional) limit (ARFieldLimitStruct, default = None)
        (optional) dInstanceList (ARDisplayInstanceList, default = None)
        (optional) helpText (c_char_p, default = None)
        (optional) owner (ARAccessNameType, default = None)
        (optional) changeDiary (c_char_p, default = None)
Output: fieldId (or None in case of failure)'''
            newFieldId = c_int(fieldId)
            return self.ARCreateField(schema, 
                                      newFieldId, 
                                      reservedIdOK,
                                      fieldName, 
                                      fieldMap, 
                                      dataType, 
                                      option, 
                                      createMode, 
                                      fieldOption, 
                                      defaultVal, 
                                      permissions,
                                      limit, 
                                      dInstanceList,
                                      helpText, 
                                      owner, 
                                      changeDiary)
        
        def CreateSchema(self, name, 
                           schema, 
                           schemaInheritanceList, 
                           groupList, 
                           admingrpList, 
                           getListFields,
                           sortList, 
                           indexList, 
                           archiveInfo,
                           auditInfo, 
                           defaultVui,
                           helpText=None, 
                           owner=None, 
                           changeDiary=None, 
                           objPropList=None):
            return self.ARCreateSchema(name, 
                           schema, 
                           schemaInheritanceList, 
                           groupList, 
                           admingrpList, 
                           getListFields,
                           sortList, 
                           indexList, 
                           archiveInfo,
                           auditInfo, 
                           defaultVui,
                           helpText, 
                           owner, 
                           changeDiary, 
                           objPropList)
        
        def GetClientCharSet(self):
            return self.ARGetClientCharSet()

        def GetMultipleFields (self, schemaString, 
                                 idList=None,
                                 fieldId2P=True,
                                 fieldNameP=True,
                                 fieldMapP=False,
                                 dataTypeP=False,
                                 optionP=False,
                                 createModeP=False,
                                 fieldOptionP=False,
                                 defaultValP=False,
                                 permissionsP=False,
                                 limitP=False,
                                 dInstanceListP=False,
                                 helpTextP=False,
                                 timestampP=False,
                                 ownerP=False,
                                 lastChangedP=False,
                                 changeDiaryP=False):
            if idList != None and idList.__class__ != cars.ARInternalIdList:
                idList = self.conv2InternalIdList(idList)
            fieldId2 = fieldName = fieldMap = dataType = option = None
            createMode = fieldOption = defaultVal = permissions = limit = None
            dInstanceList = helpText = timestamp = owner = None
            lastChanged = changeDiary = None
            if fieldId2P: fieldId2 = cars.ARInternalIdList()
            if fieldNameP: fieldName = cars.ARNameList()
            if fieldMapP: fieldMap = cars.ARFieldMappingList()
            if dataTypeP: dataType = cars.ARUnsignedIntList()
            if optionP: option = cars.ARUnsignedIntList()
            if createModeP: createMode = cars.ARUnsignedIntList()
            if fieldOptionP: fieldOption = cars.ARUnsignedIntList()
            if defaultValP: defaultVal = cars.ARValueList()
            if permissionsP: permissions = cars.ARPermissionListList()
            if limitP: limit = cars.ARFieldLimitList()
            if dInstanceListP: dInstanceList = cars.ARDisplayInstanceListList()
            if helpTextP: helpText = cars.ARTextStringList()
            if timestampP: timestamp = cars.ARTimestampList()
            if ownerP: owner = cars.ARAccessNameList()
            if lastChangedP: lastChanged = cars.ARAccessNameList()
            if changeDiaryP: changeDiary = cars.ARTextStringList()
            return self.ARGetMultipleFields (schemaString, 
                                             idList,
                                             fieldId2,
                                             fieldName,
                                             fieldMap,
                                             dataType,
                                             option,
                                             createMode,
                                             fieldOption,
                                             defaultVal,
                                             permissions,
                                             limit,
                                             dInstanceList,
                                             helpText,
                                             timestamp,
                                             owner,
                                             lastChanged,
                                             changeDiary)

        def GetMultipleSchemas(self, changedSince=0, 
                                schemaTypeList = None,
                                nameList=None, 
                                fieldIdList=None,
                                schemaListP = True,
                                schemaInheritanceListListP = False, # reserved for future use
                                groupListListP = False,
                                admingrpListListP = False,
                                getListFieldsListP = False,
                                sortListListP = False,
                                indexListListP = False,
                                archiveInfoListP = False,
                                auditInfoListP = False,
                                defaultVuiListP = False,
                                helpTextListP = False,
                                timestampListP = False,
                                ownerListP = False,
                                lastChangedListP = False,
                                changeDiaryListP = False,
                                objPropListListP = False):
            '''GetMultipleSchemas

Input:  changedSince 
        schemaTypeList
        nameList 
        fieldIdList
        archiveInfoList    
        
Output: ARSchemaList'''
            nameList = self.conv2NameList(nameList)
            schemaList = schemaInheritanceListList = groupListList = None
            admingrpListList = getListFieldsList = sortListList = None
            indexListList = archiveInfoList = auditInfoList = defaultVuiList = None
            helpTextList = timestampList = ownerList = None
            lastChangedList = changeDiaryList = objPropListList = None
            if schemaListP: schemaList = cars.ARCompoundSchemaList()
            if schemaInheritanceListListP: schemaInheritanceListList = cars.ARSchemaInheritanceListList()
            if groupListListP: groupListList = cars.ARPermissionListList()
            if admingrpListListP: admingrpListList = cars.ARInternalIdListList()
            if getListFieldsListP: getListFieldsList = cars.AREntryListFieldListList()
            if sortListListP: sortListList = cars.ARSortListList()
            if indexListListP: indexListList = cars.ARIndexListList()
            if archiveInfoListP: archiveInfoList = cars.ARArchiveInfoList()
            if auditInfoListP: auditInfoList = cars.ARAuditInfoList()
            if defaultVuiListP: defaultVuiList = cars.ARNameList()
            if helpTextListP: helpTextList = cars.ARTextStringList()
            if timestampListP: timestampList = cars.ARTimestampList()
            if ownerListP: ownerList = cars.ARAccessNameList()
            if lastChangedListP: lastChangedList = cars.ARAccessNameList()
            if changeDiaryListP: changeDiaryList = cars.ARTextStringList()
            if objPropListListP: objPropListList = cars.ARPropListList()
            return self.ARGetMultipleSchemas(changedSince, 
                                schemaTypeList,
                                nameList, 
                                fieldIdList,
                                schemaList,
                                schemaInheritanceListList, # reserved for future use
                                groupListList,
                                admingrpListList,
                                getListFieldsList,
                                sortListList,
                                indexListList,
                                archiveInfoList,
                                auditInfoList,
                                defaultVuiList,
                                helpTextList,
                                timestampList,
                                ownerList,
                                lastChangedList,
                                changeDiaryList,
                                objPropListList)

        def GetServerCharSet(self):
            return self.ARGetServerCharSet()

        def ServiceEntry(self, schema,
                           entryId = None,
                           fieldValueList = None,
                           internalIdList = None):
            '''ServiceEntry retrieves the form entry with the indicated ID.

ServiceEntry retrieves the form entry with the indicated ID on
the specified server.
Input: schema: string
       entry: list of (fieldid, value)
       (optional) idList: list of fieldids (default: None, retrieve no fields)
Output: python dictionary'''
            entryIdList = self.conv2EntryIdList (schema, entryId)
            arFieldValueList = self.conv2FieldValueList(schema, fieldValueList)
            arInternalIdList = self.conv2InternalIdList(internalIdList)
            result = self.ARServiceEntry(schema,
                                       entryIdList,
                                       arFieldValueList,
                                       arInternalIdList)
            if self.errnr > 1:
                raise ARError(self)
            pythonicResult = self.convFieldValueList2Dict(result)
            self.Free(result)
            return pythonicResult

        def SetField(self, schema, 
                       fieldId, 
                       fieldName = None, 
                       fieldMap = None, 
                       option = None, 
                       createMode = None, 
                       fieldOption = None, 
                       defaultVal = None,
                       permissions = None, 
                       limit = None, 
                       dInstanceList = None, 
                       helpText = None, 
                       owner = None, 
                       changeDiary = None):
            return self.ARSetField(schema, 
                       fieldId, 
                       fieldName,
                       fieldMap,
                       option,
                       createMode,
                       fieldOption,
                       defaultVal,
                       permissions,
                       limit,
                       dInstanceList,
                       helpText,
                       owner,
                       changeDiary)

        def SetImpersonatedUser(self, name):
            return self.ARSetImpersonatedUser(name)
    
        def SetSchema(self, name,
                        newName = None,
                        schema = None,
                        schemaInheritanceList = None,
                        groupList = None,
                        admingrpList = None,
                        getListFields = None,
                        sortList = None,
                        indexList = None,
                        archiveInfo = None,
                        auditInfo = None,
                        defaultVui = None,
                        helpText = None,
                        owner = None,
                        changeDiary = None,
                        objPropList = None,
                        setOption = None):
            return self.ARSetSchema(name,
                        newName,
                        schema,
                        schemaInheritanceList,
                        groupList,
                        admingrpList,
                        getListFields,
                        sortList,
                        indexList,
                        archiveInfo,
                        auditInfo,
                        defaultVui,
                        helpText,
                        owner,
                        changeDiary,
                        objPropList,
                        setOption)

        def SetSchemaToXML (self, schemaName, xmlDocHdrFtrFlag=0,
                            compoundSchema=None,
                            permissionList=None,
                            subAdminGrpList=None,
                            getListFields=None,
                            sortList=None,
                            indexList=None,
                            archiveInfo = None,
                            auditInfo = None,
                            defaultVui=None,
                            nextFieldID=None,
                            coreVersion = 0,
                            upgradeVersion=0,
                            fieldInfoList=None,
                            vuiInfoList=None,
                            owner=None,
                            lastModifiedBy=None,
                            modifiedDate=None,
                            helpText=None,
                            changeHistory=None,
                            objPropList=None,
                            arDocVersion = 0):
            '''Dump Schema to XML according...
    
This function dumps a schema definition into a string in
XML format; this implementation takes as  arguments the structs
that drive the xml output.
If you want the more convenient XML output, call ERSetSchemaToXML
It is important to understand that this function is executed on the
client side; in other words, the user is responsible for fetching
all relevant information and handing it over to this function.
This call really only transforms the information into XML.
Input: context
       schemaName
       (optional) xmlDocHdrFtrFlag (default: 0)
       (optional) compoundSchema (default: None)
       (optional) permissionList (default: None)
       (optional) subAdminGrpList (default: None)
       (optional) getListFields (default: None)
       (optional) sortList (default: None)
       (optional) indexList (default: None)
       (optional) auditInfo (default: None)
       (optional) indexList (default: None)
       (optional) defaultVui (default: None)
       (optional) nextFieldID (default: None)
       (optional) coreVersion (default: 0)
       (optional) upgradeVersion (default: 0)
       (optional) fieldInfoList (default: None)
       (optional) vuiInfoList (default: None)
       (optional) owner (default: None)
       (optional) lastModifiedBy (default: None)
       (optional) modifiedDate (default: None)
       (optional) helpText (default: None)
       (optional) changeHistory (default: None)
       (optional) objPropList (default: None)
       (optional) arDocVersion (default: 0)
Output: string containing the XML.'''
            schema = self.GetSchema (schemaName)
            if self.errnr > 1:
                self.logger.error("GetSchema failed for schema: %s " % (schemaName))
                return None
            vuiInfoList = self.ARGetListVUI(schemaName)
            if self.errnr > 1:
                self.logger.error ('GetListVui failed for schema %s' % (schemaName))
                return None
            fieldInfoList = self.GetMultipleFields(schemaName)
            if self.errnr > 1:
                self.logger.error("GetMultipleFields failed with error: %d " % (self.errnr))
                return None
    #        schemaName = cars.ARNameType()
    #        schemaName = create_string_buffer(schema.name, 255)
            owner = cars.ARAccessNameType()
            owner = (schema.owner+'\0'*(31-len(schema.owner)))[:]
            lastChanged = cars.ARAccessNameType()
            lastChanged = (schema.lastChanged+'\0'*(31-len(schema.lastChanged)))[:]
            
            return self.ARSetSchemaToXML(schemaName,
                                        xmlDocHdrFtrFlag,
                                             schema.schema,
                                             schema.groupList,
                                             schema.admingrpList,
                                             schema.getListFields,
                                             schema.sortList,
                                             schema.indexList,
                                             schema.archiveInfo,
                                             schema.auditInfo,
                                             c_char_p(schema.defaultVui),
                                             c_uint(0), # nextFieldID,
                                             c_ulong(0), # coreVersion,
                                             c_ulong(0), # upgradeVersion,
                                             fieldInfoList,
                                             vuiInfoList,
                                             c_char_p(owner),
                                             c_char_p(lastModifiedBy),
                                             modifiedDate,
                                             c_char_p(helpText),
                                             changeHistory,
                                             objPropList,
                                             c_ulong(8)) # arDocVersion)

    class erARS(erARS70):
        pass
    
if float(cars.version) >= 71: 
    
    class erARS71(erARS70):
        def CreateFilter(self, 
                           name, 
                           order, 
                           schemaList, 
                           opSet, 
                           enable, 
                           query,
                           actionList,
                           elseList=None, 
                           helpText=None, 
                           owner=None, 
                           changeDiary=None, 
                           objPropList=None,
                           errorFilterOptions = 0,
                           errorFilterName = None):
            return self.ARCreateFilter(name, order, schemaList, opSet, 
                                       enable, query, actionList,
                                       elseList, helpText, owner, 
                                       changeDiary, 
                                       objPropList,
                                       errorFilterOptions,
                                       errorFilterName)

        def CreateMultipleFields (self, 
                                    schema,
                                    fieldIdList,
                                    reservedIdOKList,
                                    fieldNameList,
                                    fieldMapList,
                                    dataTypeList,
                                    optionList,
                                    createModeList,
                                    fieldOptionList,
                                    defaultValList,
                                    permissionListList,
                                    limitList = None,
                                    dInstanceListList = None,
                                    helpTextList = None,
                                    ownerList = None,
                                    changeDiaryList = None):
            return self.ARCreateMultipleFields (schema,
                                    fieldIdList,
                                    reservedIdOKList,
                                    fieldNameList,
                                    fieldMapList,
                                    dataTypeList,
                                    optionList,
                                    createModeList,
                                    fieldOptionList,
                                    defaultValList,
                                    permissionListList,
                                    limitList,
                                    dInstanceListList,
                                    helpTextList,
                                    ownerList,
                                    changeDiaryList)

        def ExportToFile(self, structItems,
                           displayTag = None,
                           vuiType = cars.AR_VUI_TYPE_WINDOWS,
                           lockinfo = None,
                           filePtr = None):
            '''ExportToFile exports the indicated structure definitions 
from the specified server to a file. Use this function to copy structure 
definitions from one AR System server to another.
Input: (tuple) structItems
       (ARNameType) displayTag (optional, default = None)
       (c_uint) vuiType  (optional, default = AR_VUI_TYPE_WINDOWS)
       (ARWorkflowLockStruct or tuple) lockinfo  (optional, default = None)
       (FILE) filePtr  (optional, default = None, resulting in an error)
Output: errnr'''
            structItems = self.conv2StructItemList(structItems)
            if lockinfo is None:
                lockinfo = cars.ARWorkflowLockStruct()
            else:
                lockinfo = cars.ARWorkflowLockStruct(lockinfo[0], lockinfo[1])
            return self.ARExportToFile(structItems,
                           displayTag,
                           vuiType,
                           lockinfo,
                           filePtr)

        def GetMultipleFilters(self, changedSince = 0, 
                               nameList = None,
                               orderListP = True,
                               workflowConnectListP = True,
                               opSetListP = False,
                               enableListP = False,
                               queryListP = False,
                               actionListListP = False,
                               elseListListP = False,
                               helpTextListP = False,
                               timestampListP = False,
                               ownerListP = False,
                               lastChangedListP = False,
                               changeDiaryListP = False,
                               objPropListListP = False,
                               errorFilterOptionsListP = False,
                               errorFilterNameListP = False):
            '''GetMultipleFilters retrieves information about a group of filters 
on the specified server with the names specified by the nameList 
parameter.'''
            nameList = self.conv2NameList (nameList)
            orderList = workflowConnectList = opSetList = None
            enableList = queryList = actionListList = None
            elseListList = helpTextList = timestampList = None
            ownerList = lastChangedList = changeDiaryList = None
            objPropListList = errorFilterOptionsList = errorFilterNameList = None
            
            if orderListP: orderList = cars.ARUnsignedIntList()
            if workflowConnectListP: workflowConnectList = cars.ARWorkflowConnectList()
            if opSetListP: opSetList = cars.ARUnsignedIntList()
            if enableListP: enableList = cars.ARUnsignedIntList()
            if queryListP: queryList = cars.ARQualifierList()
            if actionListListP: actionListList = cars.ARFilterActionListList()
            if elseListListP: elseListList = cars.ARFilterActionListList()
            if helpTextListP: helpTextList = cars.ARTextStringList()
            if timestampListP: timestampList = cars.ARTimestampList()
            if ownerListP: ownerList = cars.ARAccessNameList()
            if lastChangedListP: lastChangedList = cars.ARAccessNameList()
            if changeDiaryListP: changeDiaryList = cars.ARTextStringList()
            if objPropListListP: objPropListList = cars.ARPropListList()
            if errorFilterOptionsListP: errorFilterOptionsList = cars.ARUnsignedIntList()
            if errorFilterNameListP: errorFilterNameList = cars.ARNameList()
            return self.ARGetMultipleFilters(changedSince,
                                             nameList,
                                             orderList,
                                             workflowConnectList,
                                             opSetList,
                                             enableList,
                                             queryList,
                                             actionListList,
                                             elseListList,
                                             helpTextList,
                                             timestampList,
                                             ownerList,
                                             lastChangedList,
                                             changeDiaryList,
                                             objPropListList,
                                             errorFilterOptionsList,
                                             errorFilterNameList)

        def SetFilter(self, name, 
                    newName = None,
                    order = None,
                    workflowConnect = None,
                    opSet = None,
                    enable = None,
                    query = None,
                    actionList = None,
                    elseList = None,
                    helpText = None,
                    owner = None,
                    changeDiary = None,
                    objPropList = None,
                    errorFilterOptions = None,
                    errorFilterName = None):
            '''SetFilter updates the filter.

The changes are added to the server immediately and returned to users who
request information about filters.
Input:  name, 
        newName (optional, default = None)
        order (optional, default = None)
        workflowConnect (optional, default = None)
        opSet (optional, default = None)
        enable (optional, default = None)
        query (optional, default = None)
        actionList (optional, default = None)
        elseList (optional, default = None)
        helpText (optional, default = None)
        owner (optional, default = None)
        changeDiary (optional, default = None)
        objPropList (optional, default = None)
        errorFilterOptions (optional, default = None)
        errorFilterName (optional, default = None)
Output: errnr'''
            return self.ARSetFilter(name, 
                                    newName,
                                    order,
                                    workflowConnect,
                                    opSet,
                                    enable,
                                    query,
                                    actionList,
                                    elseList,
                                    helpText,
                                    owner,
                                    changeDiary,
                                    objPropList,
                                    errorFilterOptions,
                                    errorFilterName)
        
        def SetMultipleFields(self, schema,
                                     fieldIdList,
                                     fieldNameList = None,
                                     fieldMapList = None,
                                     optionList = None,
                                     createModeList = None,
                                     fieldOptionList = None,
                                     defaultValList = None,
                                     permissionListList = None,
                                     limitList = None,
                                     dInstanceListList = None,
                                     helpTextList = None,
                                     ownerList = None,
                                     changeDiaryList = None,
                                     setFieldOptionList = None,
                                     setFieldStatusList = None):
            '''SetMultipleFields updates the definition for a list of fields 
with the specified IDs on the specified form on the specified server. 

This call produces the same result as a sequence of
ARSetField calls to update the individual fields, but it can be more efficient
because it requires only one call from the client to the AR System server and
because the server can perform multiple database operations in a single
transaction and avoid repeating operations such as those performed at the end of
each individual call.'''
            return self.ARSetMultipleFields(schema,
                                             fieldIdList,
                                             fieldNameList,
                                             fieldMapList,
                                             optionList,
                                             createModeList,
                                             fieldOptionList,
                                             defaultValList,
                                             permissionListList,
                                             limitList,
                                             dInstanceListList,
                                             helpTextList,
                                             ownerList,
                                             changeDiaryList,
                                             setFieldOptionList,
                                             setFieldStatusList)
    
        def GetFilterFromXML(self, parsedStream, 
                                   filterName):
            '''GetFilterFromXML retrieves a filter from an XML document.

Input: (ARXMLParsedStream) parsedStream
       (ARNameType) filterName
Output: (ARFilterStruct, arDocVersion)
        or None in case of failure'''
            return self.ARGetFilterFromXML(parsedStream, filterName)

    class erARS(erARS71):
        pass

if float(cars.version) >= 75: 
    
    class erARS75(erARS71):
        def CreateActiveLink (self, name, 
                                order, 
                                schemaList, 
                                groupList, 
                                executeMask,
                                controlField = None, 
                                focusField = None, 
                                enable = True, 
                                query = None, 
                                actionList = None, 
                                elseList = None, 
                                helpText = None, 
                                owner = None,
                                changeDiary = None, 
                                objPropList = None,
                                errorActlinkOptions = None,
                                errorActlinkName = None):
            '''ARCreateActiveLink creates a new active link.

ARCreateActiveLink creates a new active link with the indicated name on the specified
server. The active link is added to the server immediately and returned to
users who request information about active links.
Input: name (ARNameType)
       order (c_uint)
       schemaList (ARWorkflowConnectStruct)
       groupList (ARInternalIdList)
       executeMask (c_uint)
       (optional) controlField (ARInternalId, default = None)
       (optional) focusField (ARInternalId, default = None)
       (optional) enable (c_uint, default = None)
       (optional) query (ARQualifierStruct, default = None)
       (optional) actionList (ARActiveLinkActionList, default = None)
       (optional) elseList (ARActiveLinkActionList, default = None)
       (optional) helpText (c_char_p, default = None)
       (optional) owner (ARAccessNameType, default = None)
       (optional) changeDiary (c_char_p, default = None)
       (optional) objPropList (ARPropList, default = None)
       errorActlinkOptions (Reserved for future use. Set to NULL.)
       errorActlinkName (Reserved for future use. Set to NULL.)
Output: errnr'''
            return self.ARCreateActiveLink(name, 
                                        order, 
                                        schemaList, 
                                        groupList, 
                                        executeMask, 
                                        controlField, 
                                        focusField, 
                                        enable, 
                                        query, 
                                        actionList, 
                                        elseList, 
                                        helpText, 
                                        owner,
                                        changeDiary, 
                                        objPropList,
                                        errorActlinkOptions,
                                        errorActlinkName)

        def CreateImage(self, name,
                          imageBuf,
                          imageType,
                          description = None,
                          helpText = None,
                          owner = None,
                          changeDiary = None,
                          objPropList = None):
            '''CreateImage creates a new image with the indicated name on the specified server
Input: name (ARNameType)
       imageBuf (ARImageDataStruct)
       imageType (c_char_p, Valid values are: BMP, GIF, JPEG or JPG, and PNG.)
       (optional) description (c_char_p, default: None)
       (optional) helpText (c_char_p, default: None)
       (optional) owner (ARAccessNameType, default: None)
       (optional) changeDiary (c_char_p, default: None)
       (optional) objPropList (ARPropList, default: None)
Output: errnr'''
            return self.ARCreateImage(name,
                                          imageBuf,
                                          imageType,
                                          description,
                                          helpText,
                                          owner,
                                          changeDiary,
                                          objPropList)
        
        def DeleteImage(self, name,
                        updateRef):
            '''DeleteImage deletes the image with the indicated name from the specified server.
Input: name (ARNameType)
       updateRef (ARBoolean, specify TRUE to remove all references to the image)
Output: errnr'''
            return self.ARDeleteImage(name,
                                      updateRef)

#        def GetActiveLink (self, name):
#            '''GetActiveLink retrieves the active link with the indicated name.
#
#ARGetActiveLink retrieves the active link with the indicated name on
#the specified server.
#Input: name
#Output: ARActiveLinkStruct (containing: order, schemaList,
#           groupList, executeMask, controlField,
#           focusField, enable, query, actionList,
#           elseList, helpText, timestamp, owner, lastChanged,
#           changeDiary, objPropList) or None in case of failure'''
#            self.logger.debug('enter GetActiveLink...')
#            return self.ARGetActiveLink(name)

        def GetCacheEvent(self, eventIdList, 
                          returnOption = cars.AR_GCE_OPTION_NONE):
            '''GetCacheEvent retrieves the list of events that occurred in the 
AR System server cache and the number of server caches, and indicates when 
administrative operations become public. You can direct this API call to either 
return the results immediately or when the next event occurs. This call is useful 
for detecting cache events in production cache mode.
In developer cache mode, the call always returns immediately regardless of the
value of the return option. In developer cache mode, there can only ever be one
copy of the cache and it is always public.
Input: eventIdList (ARInternalIdList)
       returnOption (c_uint, default = 0, call returns the information immediately)
Output: (eventIdOccuredList (ARInternalIdList), cacheCount (c_uint)) or 
        None in case of failure'''
            return self.ARGetCacheEvent(eventIdList, 
                                              returnOption)
        
        def GetImage(self, name):
            '''GetImage retrieves information about the specified image from 
the specified server.
Input: name (ARNameType)
Output: (content (ARImageDataStruct),
    imageType (c_char_p),
    timestamp (ARTimeStamp),
    checkSum (c_char_p),
    description (c_char_p),
    helpText (c_char_p),
    owner (ARAccessNameType),
    changeDiary (c_char_p),
    objPropList (ARPropList)) or None in case of failure'''
            return self.ARGetImage(name)
        
        def GetListEntryWithMultiSchemaFields (self, queryFromList, 
                                      getListFields=None, 
                                      qualifier = None,
                                      sortList=None,
                                      firstRetrieve=cars.AR_START_WITH_FIRST_ENTRY,
                                      maxRetrieve=cars.AR_NO_MAX_LIST_RETRIEVE,
                                      useLocale = False):
            '''GetListEntryWithMultiSchemaFields performs dynamic joins by querying across multiple forms—including view and
vendor forms—at run time.
Input: queryFromList (ARMultiSchemaQueryFromList)
       (optional) getListFields (ARMultiSchemaFieldIdList, deafult =None), 
       (optional) qualifier (ARMultiSchemaQualifierStruct, default = None),
       (optional) sortList (ARMultiSchemaSortList, default = None),
       (optional) firstRetrieve (c_uint, default=cars.AR_START_WITH_FIRST_ENTRY),
       (optional) maxRetrieve (c_uint, default=cars.AR_NO_MAX_LIST_RETRIEVE),
       (optional) useLocale (ARBoolean, default = False)
Output: (ARMultiSchemaFieldValueListList, numMatches (c_uint))'''
            raise ars.pyARSNotImplemented

        def GetListImage(self, schemaList = None, 
                         changedSince = 0,
                         imageType = None):
            '''GetListImage retrieves a list of image names from the specified 
server. You can retrieve all images or limit the list to those images associated 
with particular schemas, those modified after a specified time, and those of a 
specific type.
Input: schemaList (list of names),
       changedSince (ARTimestamp, default = 0),
       imageType (c_char_p, default = None)
Output: imageList (ARNameList) or raise ARError in case of failure'''
            schemas = self.conv2NameList(schemaList)
            result = self.ARGetListImage(schemas, 
                                         changedSince,
                                         imageType)
            if self.errnr > 1:
                raise ARError(self)
            images = self.convNameList2List(result)
            self.Free(result)
            return images

        def GetMultipleActiveLinks(self, changedSince=0, 
                                   nameList=None,
                                    orderListP = True,
                                    schemaListP = True,
                                    groupListListP = True,
                                    executeMaskListP = True,
                                    controlFieldListP = True,
                                    focusFieldListP = True,
                                    enableListP = True,
                                    queryListP = True,
                                    actionListListP = True,
                                    elseListListP = True,
                                    helpTextListP = True,
                                    timestampListP = True,
                                    ownersListP = True,
                                    lastChangedListP = True,
                                    changeDiaryListP = True,
                                    objPropListListP = True,
                                    errorActlinkOptionsListP = True,
                                    errorActlinkNameListP = True):
            '''GetMultipleActiveLinks
Input: changedSince=0, 
        nameList=None,
        (optional) orderListP = True,
        (optional) schemaListP = True,
        (optional) groupListListP = True,
        (optional) executeMaskListP = True,
        (optional) controlFieldListP = True,
        (optional) focusFieldListP = True,
        (optional) enableListP = True,
        (optional) queryListP = True,
        (optional) actionListListP = True,
        (optional) elseListListP = True,
        (optional) helpTextListP = True,
        (optional) timestampListP = True,
        (optional) ownersListP = True,
        (optional) lastChangedListP = True,
        (optional) changeDiaryListP = True,
        (optional) objPropListListP = True,
        (optional) errorActlinkOptionsListP = True
        (optional) errorActlinkNameListP = True
Output: ARActiveLinkList'''
            nameList = self.conv2NameList(nameList)
            orderList = schemaList = groupListList = executeMaskList = None
            controlFieldList = focusFieldList = enableList = queryList = None
            actionListList = elseListList = helpTextList = timestampList = None
            ownersList = lastChangedList = changeDiaryList = objPropListList = None
            errorActlinkOptionsList = errorActlinkNameList = None
            if orderListP: orderList = cars.ARUnsignedIntList()
            if schemaListP: schemaList = cars.ARWorkflowConnectList()
            if groupListListP: groupListList = cars.ARInternalIdListList()
            if executeMaskListP: executeMaskList = cars.ARUnsignedIntList()
            if controlFieldListP: controlFieldList = cars.ARInternalIdList()
            if focusFieldListP: focusFieldList = cars.ARInternalIdList()
            if enableListP: enableList = cars.ARUnsignedIntList()
            if queryListP: queryList = cars.ARQualifierList()
            if actionListListP: actionListList = cars.ARActiveLinkActionListList()
            if elseListListP: elseListList = cars.ARActiveLinkActionListList()
            if helpTextListP: helpTextList = cars.ARTextStringList()
            if timestampListP: timestampList = cars.ARTimestampList()
            if ownersListP: ownersList = cars.ARAccessNameList()
            if lastChangedListP: lastChangedList = cars.ARAccessNameList()
            if changeDiaryListP: changeDiaryList = cars.ARTextStringList()
            if objPropListListP: objPropListList = cars.ARPropListList()
            if errorActlinkOptionsListP: errorActlinkOptionsList = cars.ARUnsignedIntList()
            if errorActlinkNameListP: errorActlinkNameList = cars.ARNameList()
            return self.ARGetMultipleActiveLinks(changedSince, nameList = nameList,
                        orderList = orderList,
                        schemaList = schemaList,
                        groupListList = groupListList,
                        executeMaskList = executeMaskList,
                        controlFieldList = controlFieldList,
                        focusFieldList = focusFieldList,
                        enableList = enableList,
                        queryList = queryList,
                        actionListList = actionListList,
                        elseListList = elseListList,
                        helpTextList = helpTextList,
                        timestampList = timestampList,
                        ownersList = ownersList,
                        lastChangedList = lastChangedList,
                        changeDiaryList = changeDiaryList,
                        objPropListList = objPropListList,
                        errorActlinkOptionsList = errorActlinkOptionsList,
                        errorActlinkNameList = errorActlinkNameList)

        def GetMultipleImages(self, changedSince = 0,
                              nameList = None):
            '''GetMultipleImages retrieves information from the specified server 
about the images whose names are specified in the nameList parameter. This function 
performs the same action as ARGetImage, but it is more efficient than retrieving 
information about multiple images one by one.
Input: (optional) changedSince (c_uint, default = 0),
       (optional) nameList (ARNameList, default = None)
Output: '''
            nameList = self.conv2NameList(nameList)
            return self.ARGetMultipleImages(changedSince, 
                                            nameList)
            
        def GetObjectChangeTimes(self):
            '''GetObjectChangeTimes retrieves timestamps for the last create, 
modify, and delete operations for each type of server object.
Input:
Output: ARObjectChangeTimestampList or None in case of failure'''
            result = self.ARGetObjectChangeTimes()
            if self.errnr > 1:
                raise ARError(self)
            pythonicResult = self.convObjectChangeTimestampList2List(result)
#            self.Free(result)
            return pythonicResult
        
        def GetOneEntryWithFields(self, schema,
                                    qualifier = None,
                                    getListFields = None,
                                    sortList = None,
                                    useLocale = False):
            '''GetOneEntryWithFields retrieves one entry from AR System matching a given qualification. Similar to
ARGetListEntryWithFields, with the following behavioral changes:
- If the qualifier in the API call matches multiple records, only the first is returned.
- Get filters on the form being queried are fired for that one record.
This function is equivalent to issuing an ARGetListEntry call followed by
ARGetEntry with one of the entry IDs.
The keyword $LASTCOUNT$ is set to the number of entries matched, even though
only one is returned.
Input: schema (ARNameType)
       (default) qualifier (ARQualifierStruct, default = None)
       (default) getListFields (AREntryListFieldList, default = None)
       (default) sortList (ARSortList, default = None)
       (default) useLocale (ARBoolean, default = False)
Output: (entryList (AREntryListFieldValueList), numMatches (c_uint))'''
            q = self.conv2QualifierStruct(schema, query)
            arGetListFields = self.conv2EntryListFieldList(getListFields, schema)
            arSortList = self.conv2SortList(sortList)
            result = self.ARGetOneEntryWithFields(schema,
                                                  q,
                                                  arGetListFields,
                                                  arSortList,
                                                  useLocale)
            if self.errnr > 1:
                raise ARError(self)
            else:
                (entryListFieldValueList, numMatches) = result
                pythonicResult = self.convEntryListList2List(entryListFieldValueList)
                self.Free(entryListFieldValueList)
                return (pythonicResult, numMatches)

        def RunEscalation(self):
            return self.ARRunEscalation()

        def SetActiveLink(self, name, 
                            newName = None, 
                            order = None, 
                            workflowConnect = None,
                            groupList = None,
                            executeMask = None,
                            controlField = None,
                            focusField = None,
                            enable = None,
                            query = None,
                            actionList = None,
                            elseList = None,
                            helpText = None,
                            owner = None,
                            changeDiary = None,
                            objPropList = None,
                            errorActlinkOptions = None,
                            errorActlinkName = None):
            '''SetActiveLink updates the active link.

The changes are added to the server immediately and returned to users who
request information about active links. Because active links operate on
clients, individual clients do not receive the updated definition until they
reconnect to the form (thus reloading the form from the server).
Input:  name, 
        (optional) newName = None, 
        (optional) order = None, 
        (optional) workflowConnect = None,
        (optional) groupList = None,
        (optional) executeMask = None,
        (optional) controlField = None,
        (optional) focusField = None,
        (optional) enable = None,
        (optional) query = None,
        (optional) actionList = None,
        (optional) elseList = None,
        (optional) helpText = None,
        (optional) owner = None,
        (optional) changeDiary = None,
        (optional) objPropList = None
        (optional) errorActlinkOptions = None,
        (optional) errorActlinkName = None
Output: errnr'''
            return self.ARSetActiveLink(name, 
                                    newName, 
                                    order, 
                                    workflowConnect,
                                    groupList,
                                    executeMask,
                                    controlField,
                                    focusField,
                                    enable,
                                    query,
                                    actionList,
                                    elseList,
                                    helpText,
                                    owner,
                                    changeDiary,
                                    objPropList,
                                    errorActlinkOptions,
                                    errorActlinkName)

        def SetImage(self, name,
                        newName = None,
                        imageBuf = None,
                        imageType = None,
                        description = None,
                        helpText = None,
                        owner = None,
                        changeDiary = None,
                        objPropList = None):
            '''SetImage updates the image with the indicated name on the specified server. After the
image is updated, the server updates all references and object property timestamps
for schemas affected by the change.
Input: name (ARNameType)
       newName (ARNameType, default = None)
       imageBuf (ARImageDataStruct, default = None)
       imageType (c_char_p, default = None)
       description (c_char_p, default= None)
       helpText (c_char_p, default = None)
       owner (ARAccessNameType, dfault = None)
       changeDiary (c_char_p, default = None)
       objPropList (ARPropList, default = None)
Output: errnr'''
            return self.ARSetImage(name,
                                newName,
                                imageBuf,
                                imageType,
                                description,
                                helpText,
                                owner,
                                changeDiary,
                                objPropList)
        
        def WfdClearAllBreakpoints(self):
            '''WfdClearAllBreakpoints removes all breakpoints from the server..

Input: 
Output: errnr'''
            return self.ARWfdClearAllBreakpoints()

        def WfdClearBreakpoint(self, bpId):
            '''WfdClearBreakpoint removes the specified breakpoint from the server.

Input: bpId (c_uint)
Output: errnr'''
            return self.ARWfdClearBreakpoint(bpId)

        def WfdExecute(self, mode = cars.WFD_EXECUTE_STEP):
            '''WfdExecute instructs the debug server to begin execution.
Input: (optional) mode  (c_uint, default: single step)
Output: errnr'''
            return self.ARWfdExecute(mode)
        
        def WfdGetCurrentLocation(self, howFarBack = 0):
            '''WfdGetCurrentLocation description Requests the current location 
of the worker thread during debugging.
Input: (optional) howFarBack (c_uint, default = 0)
Output: location'''
            return self.ARWfdGetCurrentLocation(howFarBack)
        
        def WfdGetDebugMode(self):
            '''WfdGetDebugMode returns the current debug mode.
Input:
Output: integer (current debug mode)'''
            return self.ARWfdGetDebugMode()
        
        def WfdGetFieldValues(self, howFarBack = 0):
            '''WfdGetFieldValues Requests the field-value list associated with 
the current schema at the current location.
Input: (optional) howFarBack (c_uint, default = 0)
Output: '''
            return self.ARWfdGetFieldValues(howFarBack)
        
        def WfdGetFilterQual(self):
            '''WfdGetFilterQual requests the field-value list associated with 
the current schema at the current location.
Input:
Output: filterQual (ARQualifierStruct)'''
            return self.ARWfdGetFilterQual()
        
        def WfdGetKeywordValue(self, keywordId):
            '''WfdGetKeywordValue retrieves the value of a keyword, if possible.
Input: keywordId (c_uint)
Output: ARValueStruct'''
            return self.ARWfdGetKeywordValue(keywordId)

        def WfdGetUserContext(self, mask = 0):
            '''ARWfdGetUserContext retrieves information associated with the workflow user.
Input: mask (c_uint)
Output: ARWfdUserContext'''
            return self.ARWfdGetUserContext(mask)

        def WfdListBreakpoints(self):
            '''ARWfdListBreakpoints returns a list of server breakpoints.
Input:
Output: ARWfdRmtBreakpointList (or None in case of failure)'''
            return self.ARWfdListBreakpoints()

        def WfdSetBreakpoint(self, inBp):
            '''WfdSetBreakpoint sets a breakpoint on the server, and overwrites 
if needed.
Input: inBp (ARWfdRmtBreakpoint)
Output: errnr'''
            return self.ARWfdSetBreakpoint(inBp)
        
        def WfdSetDebugMode(self, mode = cars.WFD_EXECUTE_STEP):
            '''WfdSetDebugMode sets a new debug mode.
Input: (optional) mode (c_uint, default: WFD_EXECUTE_STEP)
Output: errnr'''
            return self.ARWfdSetDebugMode(mode)

        def WfdSetFieldValues(self, trFieldList, dbFieldList):
            '''WfdSetFieldValues overwrites the field-value list associated 
with the current schema at the current location.
Input: trFieldList (ARFieldValueList)
       dbFieldList (ARFieldValueList)
Output: errnr'''
            # FIXME!
            return self.ARWfdSetFieldValues(trFieldList, dbFieldList)

        def WfdSetQualifierResult(self, result):
            '''ARWfdSetQualifierResult forces the qualifier result to the specified 
Boolean value.
Input: result (ARBoolean)
Output: errnr'''
            return self.ARWfdSetQualifierResult(result)
        
        def WfdTerminateAPI(self, errorCode):
            '''WfdTerminateAPI causes workflow to return with an optionally 
specified error at the next opportunity. If an error is not specified, a generic 
TERMINATED_BY_DEBUGGER error will be returned
Input: errorCode (c_uint)
Output: errnr'''
            return self.ARWfdTerminateAPI(errorCode)

        def GetActiveLinkFromXML(self, parsedStream, 
                                   activeLinkName,
                                   appBlockName = None):
            '''GetActiveLinkFromXML retrieves an active link from an XML document.

Input: parsedStream
       activeLinkName
       appBlockName
Output: (ARActiveLinkStruct, supportFileList, arDocVersion) or 
    None in case of failure'''
            raise ars.pyARSNotImplemented

        def GetDSOPoolFromXML(self, parsedStream, poolName, appBlockName):
            '''ARGetDSOPoolFromXML retrieves information about a DSO pool from a 
definition in an XML document.
Input: parsedStream (ARXMLParsedStream)
       poolName (ARNameType)
       appBlockName (ARNameType)
Output: (enabled (c_uint),
    defaultPool (c_uint),
    threadCount (c_long),
    connection (c_char_p),
    polling (c_uint),
    pollingInterval (c_uint),
    owner (ARAccessNameType),
    lastModifiedBy (ARAccessNameType),
    modifiedDate (ARTimestamp),
    helpText (c_char_p),
    changeHistory (c_char_p),
    objPropList (ARPropList),
    arDocVersion (c_uint)) or None in case of failure'''
            raise ars.pyARSNotImplemented
        
        def GetImageFromXML(self, parsedStream, imageName, appBlockName):
            '''ARGetImageFromXML retrieves information about an image from an XML 
document.
Input: parsedStream (ARXMLParsedStream)
       imageName (ARNameType)
       appBlockName (ARNameType)
Output: (imageType (c_char_p),
        contentLength (c_uint),
        checksum (c_char_p),
        timestamp (ARTimestamp),
        description (c_char_p),
        owner (ARAccessNameType),
        lastModifiedBy (ARAccessNameType),
        helpText (c_char_p),
        changeHistory (c_char_p),
        objPropList (ARPropList),
        imageCon (c_char_p)) or None in case of failure'''
            raise ars.pyARSNotImplemented
        
        def SetActiveLinkToXML(self, activeLinkName):
            '''SetActiveLinkToXML converts active links to XML.
    
Input: activeLinkName (ARNameType),
Output: string containing the XML
        or None in case of failure'''
            al = self.GetActiveLink(activeLinkName)
            if self.errnr > 1:
                self.logger.error ('SetActiveLinkToXML: GetActiveLink failed!')
                return None
            return self.ARSetActiveLinkToXML(cars.ARBoolean(True), al.name,
                    c_uint(al.order),
                    al.schemaList,
                    al.groupList,
                    c_uint(al.executeMask),
                    cars.ARInternalId(al.controlField),
                    cars.ARInternalId(al.focusField),
                    c_uint(al.enable),
                    al.query,
                    al.actionList,
                    al.elseList,
                    ### TODO! where does this come from???
                    None, # supportFileList,???
                    c_char_p(al.owner),
                    c_char_p(al.lastChanged),
                    cars.ARTimestamp(al.timestamp),
                    c_char_p(al.helpText),
                    c_char_p(al.changeDiary),
                    al.objPropList,
                    c_uint(8),
                    al.errorActlinkOptions,
                    al.errorActlinkName)

        def SetDSOPoolToXML(self, poolName, 
                              xmlDocHdrFtrFlag = False,
                              enabled = 0,
                              defaultPool = True,
                              threadCount = 0,
                              connection = None,
                              polling = c_uint(0),
                              pollingInterval = c_uint(0),
                              owner = None,
                              lastModifiedBy = None,
                              modifiedDate = 0,
                              helpText = None,
                              changeHistory = None,
                              objPropList = None,
                              arDocVersion = c_uint(0)):
            '''SetDSOPoolToXML retrieves information about the DSO pool.

Input: 
Output: string containing the XML
        or None in case of failure'''
            raise ars.pyARSNotImplemented

        def SetImageToXML(self, imageName,
                            xmlDocHdrFtrFlag,
                            imageType,
                            description,
                            owner,
                            lastModifiedBy,
                            helpText,
                            changeHistory,
                            objPropList,
                            checksum,
                            modifiedDate,
                            imageContent):
            '''SetImageToXML saves information about an image to an XML document.
Input: ARNameType imageName
       ARBoolean xmlDocHdrFtrFlag
char *imageType,
char *description
ARAccessNameType owner,
ARAccessNameType lastModifiedBy,
char *helpText,
char *changeHistory,
ARPropList *objPropList,
char checksum,
ARTimestamp *modifiedDate,
ARImageDataStruct imageContent
Output: errnr'''
            raise ars.pyARSNotImplemented
                    
    class erARS(erARS75):
        pass 

if float(cars.version) >= 76.03:
    class erARS7603(erARS75):
        def CreateActiveLink (self, name, 
                                order, 
                                schemaList, 
                                groupList, 
                                executeMask,
                                controlField = None, 
                                focusField = None, 
                                enable = True, 
                                query = None, 
                                actionList = None, 
                                elseList = None, 
                                helpText = None, 
                                owner = None,
                                changeDiary = None, 
                                objPropList = None,
                                errorActlinkOptions = None,
                                errorActlinkName = None,
                                objectModificationLogLabel = None):
            '''ARCreateActiveLink creates a new active link.

ARCreateActiveLink creates a new active link with the indicated name on the specified
server. The active link is added to the server immediately and returned to
users who request information about active links.
Input: name (ARNameType)
       order (c_uint)
       schemaList (ARWorkflowConnectStruct)
       groupList (ARInternalIdList)
       executeMask (c_uint)
       (optional) controlField (ARInternalId, default = None)
       (optional) focusField (ARInternalId, default = None)
       (optional) enable (c_uint, default = None)
       (optional) query (ARQualifierStruct, default = None)
       (optional) actionList (ARActiveLinkActionList, default = None)
       (optional) elseList (ARActiveLinkActionList, default = None)
       (optional) helpText (c_char_p, default = None)
       (optional) owner (ARAccessNameType, default = None)
       (optional) changeDiary (c_char_p, default = None)
       (optional) objPropList (ARPropList, default = None)
       (optional) errorActlinkOptions (Reserved for future use. Set to NULL.)
       (optional) errorActlinkName (Reserved for future use. Set to NULL.)
       (optional) objectModificationLogLabel (c_char_p, default = None)
Output: errnr'''
            return self.ARCreateActiveLink(name, 
                                        order, 
                                        schemaList, 
                                        groupList, 
                                        executeMask, 
                                        controlField, 
                                        focusField, 
                                        enable, 
                                        query, 
                                        actionList, 
                                        elseList, 
                                        helpText, 
                                        owner,
                                        changeDiary, 
                                        objPropList,
                                        errorActlinkOptions,
                                        errorActlinkName,
                                        objectModificationLogLabel)

        def CreateCharMenu(self, name, 
                           refreshCode, 
                           menuDefn, 
                           helpText = None, 
                           owner = None,
                           changeDiary = None, 
                           objPropList = None,
                           objectModificationLogLabel = None):
            '''CreateCharMenu creates a new character menu with the indicated name.
Input: name (ARNameType)
       refreshCode (c_uint)
       menuDef (ARCharMenuStruct)
       (optional) helpText (c_char_p, default = None)
       (optional) owner (ARAccessNameType, default = None)
       (optional) changeDiary (c_char_p, default = None)
       (optional) objPropList (ARPropList, default = None)
       (optional) objectModificationLogLabel (c_char_p, default = None)
Output: errnr'''
            return self.ARCreateCharMenu(name, 
                                         refreshCode, 
                                         menuDefn, 
                                         helpText, 
                                         owner,
                                         changeDiary, 
                                         objPropList,
                                         objectModificationLogLabel) 

        def CreateContainer(self, name, 
                            groupList, 
                            admingrpList, 
                            ownerObjList, 
                            label, 
                            description,
                            type_,
                            references,
                            removeFlag,
                            helpText = None,
                            owner = None,
                            changeDiary = None,
                            objPropList = None,
                            objectModificationLogLabel = None):
            '''CreateContainer a new container with the indicated name.

Use this function to create
applications, active links, active link guides, filter guide, packing lists, guides,
and AR System-defined container types. A container can also be a custom type that you define.
Input: name
       groupList
       admingrpList
       ownerObjList
       label
       description
       type_
       references
       removeFlag
       helpText
       owner
       changeDiary
       objPropList
       (optional) objectModificationLogLabel (c_char_p, default = None)
Output: errnr'''
            return self.ARCreateContainer(name, groupList, admingrpList, 
                                          ownerObjList, label, description,
                                            type_,references,removeFlag,helpText,
                                            owner,changeDiary,objPropList)

        def CreateEscalation(self, name, 
                             escalationTm, 
                             schemaList, 
                             enable, 
                             query = None, 
                             actionList = None,
                             elseList = None, 
                             helpText = None, 
                             owner = None, 
                             changeDiary = None, 
                             objPropList = None,
                             objectModificationLogLabel = None):
            '''CreateEscalation creates a new escalation with the indicated name.

The escalation condition
is checked regularly based on the time structure defined when it is enabled.
Input: name (ARNameType)
       escalationTm (AREscalationTmStruct)
       schemaList (ARWorkflowConnectStruct)
       enable (c_uint)
       (optional) query (ARQualifierStruct, default = None)
       (optional) actionList (ARFilterActionList, default = None)
       (optional) elseList (ARFilterActionList, default = None)
       (optional) helpText (c_char_p, default = None)
       (optional) owner (ARAccessNameType, default = None)
       (optional) changeDiary (c_char_p, default = None)
       (optional) objPropList (ARPropList, default = None)
       (optional) objectModificationLogLabel (c_char_p, default = None)
Output: errnr'''
            return self.ARCreateEscalation(name, 
                                           escalationTm, 
                                           schemaList, 
                                           enable, 
                                           query, 
                                           actionList,
                                           elseList, 
                                           helpText, 
                                           owner, 
                                           changeDiary, 
                                           objPropList,
                                           objectModificationLogLabel)

        def CreateField(self, schema, fieldId, 
                                  reservedIdOK,
                                  fieldName, 
                                  fieldMap, 
                                  dataType, 
                                  option, 
                                  createMode, 
                                  fieldOption, 
                                  defaultVal, 
                                  permissions,
                                  limit=None, 
                                  dInstanceList=None,
                                  helpText=None, 
                                  owner=None, 
                                  changeDiary=None,
                                  objPropList=None):
            '''CreateField creates a new field.
Input: schema (ARNameType)
        fieldId (ARInternalId)
        reservedIdOK (ARBoolean)
        fieldName (ARNameType)
        fieldMap (ARFieldMappingStruct)
        dataType (c_uint)
        option (c_uint)
        createMode (c_uint)
        fieldOption (c_uint) 
        defaultVal (ARValueStruct)
        permissions (ARPermissionList)
        (optional) limit (ARFieldLimitStruct, default = None)
        (optional) dInstanceList (ARDisplayInstanceList, default = None)
        (optional) helpText (c_char_p, default = None)
        (optional) owner (ARAccessNameType, default = None)
        (optional) changeDiary (c_char_p, default = None)
        (optional) objPropList (ARPropList, default = None)
Output: fieldId (or None in case of failure)'''
            newFieldId = c_int(fieldId)
            return self.ARCreateField(schema, 
                                      newFieldId, 
                                      reservedIdOK,
                                      fieldName, 
                                      fieldMap, 
                                      dataType, 
                                      option, 
                                      createMode, 
                                      fieldOption, 
                                      defaultVal, 
                                      permissions,
                                      limit, 
                                      dInstanceList,
                                      helpText, 
                                      owner, 
                                      changeDiary,
                                      objPropList)

        def CreateFilter(self, 
                           name, 
                           order, 
                           schemaList, 
                           opSet, 
                           enable, 
                           query,
                           actionList,
                           elseList=None, 
                           helpText=None, 
                           owner=None, 
                           changeDiary=None, 
                           objPropList=None,
                           errorFilterOptions = 0,
                           errorFilterName = None,
                           objectModificationLogLabel = None):
            '''CreateFilter creates a new filter.

CreateFilter creates a new filter with the indicated name on the specified 
server. The filter takes effect immediately and remains in effect until changed 
or deleted.
Input: name, 
       (unsigned int) order,
       (ARWorkflowConnectStruct) schemaList,
       (unsigned int) opSet,
       (unsigned int) enable,
       (ARQualifierStruct) query,
       (ARFilterActionList) actionList
       (ARFilterActionList) elseList  (optional, default = None)
       (char) helpText  (optional, default = None)
       (ARAccessNameType) owner  (optional, default = None)
       (char) changeDiary  (optional, default = None)
       (ARPropList) objPropList  (optional, default = None)
       (unsigned int) errorFilterOptions (optional, default = None)
       (ARNameType) errorFilterName (optional, default = None)
       (c_char) objectModificationLogLabel (optional, default = None)
Output: errnr'''
            return self.ARCreateFilter(name, order, schemaList, opSet, 
                                       enable, query, actionList,
                                       elseList, helpText, owner, 
                                       changeDiary, 
                                       objPropList,
                                       errorFilterOptions,
                                       errorFilterName,
                                       objectModificationLogLabel)

        def CreateImage(self, name,
                          imageBuf,
                          imageType,
                          description = None,
                          helpText = None,
                          owner = None,
                          changeDiary = None,
                          objPropList = None,
                          objectModificationLogLabel = None):
            '''CreateImage creates a new image with the indicated name on the specified server
Input: name (ARNameType)
       imageBuf (ARImageDataStruct)
       imageType (c_char_p, Valid values are: BMP, GIF, JPEG or JPG, and PNG.)
       (optional) description (c_char_p, default: None)
       (optional) helpText (c_char_p, default: None)
       (optional) owner (ARAccessNameType, default: None)
       (optional) changeDiary (c_char_p, default: None)
       (optional) objPropList (ARPropList, default: None)
       (c_char) objectModificationLogLabel (optional, default = None)
Output: errnr'''
            return self.ARCreateImage(name,
                                          imageBuf,
                                          imageType,
                                          description,
                                          helpText,
                                          owner,
                                          changeDiary,
                                          objPropList,
                                          objectModificationLogLabel)

        def CreateMultipleFields (self, 
                                    schema,
                                    fieldIdList,
                                    reservedIdOKList,
                                    fieldNameList,
                                    fieldMapList,
                                    dataTypeList,
                                    optionList,
                                    createModeList,
                                    fieldOptionList,
                                    defaultValList,
                                    permissionListList,
                                    limitList = None,
                                    dInstanceListList = None,
                                    helpTextList = None,
                                    ownerList = None,
                                    changeDiaryList = None,
                                    objPropListList = None):
            '''CreateMultipleFields creates multiple fields in a form. 

This function produces the same result as a
sequence of ARCreateField calls to create the individual fields, but it can be more
efficient. This function requires only one call from the client to the AR System
server. The server can perform multiple database operations in a single transaction
and avoid repeating operations such as those performed at the end of each
individual call. If an error occurs creating an individual field, no fields are created.
Input: ARNameType schema,
       (ARInternalIdList) fieldIdList,
       (ARBooleanList) reservedIdOKList
       (ARNamePtrList) fieldNameList,
       (ARFieldMappingList) fieldMapList,
       (ARUnsignedIntList) dataTypeList,
       (ARUnsignedIntList) optionList,
       (ARUnsignedIntList) createModeList,
       (ARUnsignedIntList) fieldOptionList,
       (ARValuePtrList) defaultValList,
       (ARPermissionListPtrList) permissionListList,
       (ARFieldLimitPtrList) limitList,
       (ARDisplayInstanceListPtrList) dInstanceListList,
       (ARTextStringList) helpTextList,
       (ARAccessNamePtrList) ownerList,
       (ARTextStringList) changeDiaryList
       (ARPropListList) objPropListList
Output: errnr'''
            return self.ARCreateMultipleFields (schema,
                                    fieldIdList,
                                    reservedIdOKList,
                                    fieldNameList,
                                    fieldMapList,
                                    dataTypeList,
                                    optionList,
                                    createModeList,
                                    fieldOptionList,
                                    defaultValList,
                                    permissionListList,
                                    limitList,
                                    dInstanceListList,
                                    helpTextList,
                                    ownerList,
                                    changeDiaryList,
                                    objPropListList)

        def CreateSchema(self, name, 
                           schema, 
                           schemaInheritanceList, 
                           groupList, 
                           admingrpList, 
                           getListFields,
                           sortList, 
                           indexList, 
                           archiveInfo,
                           auditInfo, 
                           defaultVui,
                           helpText=None, 
                           owner=None, 
                           changeDiary=None, 
                           objPropList=None,
                           objectModificationLogLabel = None):
            return self.ARCreateSchema(name, 
                           schema, 
                           schemaInheritanceList, 
                           groupList, 
                           admingrpList, 
                           getListFields,
                           sortList, 
                           indexList, 
                           archiveInfo,
                           auditInfo, 
                           defaultVui,
                           helpText, 
                           owner, 
                           changeDiary, 
                           objPropList,
                           objectModificationLogLabel)

        def CreateVUI(self, schema, vuiId, 
                      vuiName, 
                      locale, 
                      vuiType=None,
                      dPropList=None, 
                      helpText=None, 
                      owner=None, 
                      changeDiary=None,
                      smObjProp=None):
            '''CreateVUI reates a new form view (VUI) with the indicated name on
the specified server.
Input: schema
       vuiId (can be 0 or a value between 536870912 and 2147483647)
       vuiName
       locale
       optional: vuiType (default = None)
       optional: dPropList (default = None)
       optional: helpText (default = None)
       optional: owner (default = None)
       optional: changeDiary (default = None)
       optional: smObjProp (default = None)
Output: vuiId (or None in case of failure)'''
            return self.ARCreateVUI(schema, vuiId, vuiName, locale, 
                      vuiType,dPropList, helpText, owner, 
                      changeDiary)

        def DeleteActiveLink(self, name, deleteOption = cars.AR_DEFAULT_DELETE_OPTION,
                             objectModificationLogLabel = None):
            '''DeleteActiveLink deletes the active link.
        
DeleteActiveLink deletes the active link with the indicated name from the
specified server and deletes any container references to the active link.
Input: name
       (optional) deleteOption (default = cars.AR_DEFAULT_DELETE_OPTION)
       (optional) objectModificationLogLabel (c_char_p, default = None)
Output: errnr'''
            return self.ARDeleteActiveLink(name, deleteOption, objectModificationLogLabel)

        def DeleteCharMenu(self, name, deleteOption = cars.AR_DEFAULT_DELETE_OPTION,
                           objectModificationLogLabel = None):
            '''DeleteCharMenu deletes the character menu with the indicated name from
the specified server.

Input: name
       (optional) deleteOption (default = cars.AR_DEFAULT_DELETE_OPTION)
       (optional) objectModificationLogLabel (c_char_p, default = None)
Output: errnr'''
            return self.ARDeleteCharMenu(name, deleteOption, objectModificationLogLabel)

        def DeleteContainer(self, name, deleteOption = cars.AR_DEFAULT_DELETE_OPTION,
                            objectModificationLogLabel = None):
            '''DeleteContainer deletes the container .
        
DeleteContainer deletes the container with the indicated name from
the specified server and deletes any references to the container from other containers.
Input: name
       (optional) deleteOption (default = cars.AR_DEFAULT_DELETE_OPTION)
       (optional) objectModificationLogLabel (default = None)
Output: errnr'''
            return self.ARDeleteContainer(name, deleteOption, objectModificationLogLabel)

        def DeleteEscalation(self, name, deleteOption = cars.AR_DEFAULT_DELETE_OPTION,
                             objectModificationLogLabel = None):
            '''DeleteEscalation deletes the escalation.
        
DeleteEscalation deletes the escalation with the indicated name from the
specified server and deletes any container references to the escalation.
Input:  name
       (optional) deleteOption (default = cars.AR_DEFAULT_DELETE_OPTION)
       (optional) objectModificationLogLabel (c_char_p, default = None)
Output: errnr'''
            return  self.ARDeleteEscalation(name, deleteOption, objectModificationLogLabel)

        def DeleteFilter(self, name, deleteOption = cars.AR_DEFAULT_DELETE_OPTION,
                         objectModificationLogLabel = None):
            '''DeleteFilter deletes the filter with the indicated name from the
specified server and deletes any container references to the filter.
Input:  name
       (optional) deleteOption (default = cars.AR_DEFAULT_DELETE_OPTION)
       (c_char_p) objectModificationLogLabel (optional, default = None)   
Output: errnr'''
            return self.ARDeleteFilter(name, deleteOption, objectModificationLogLabel)

        def DeleteImage(self, name,
                        updateRef,
                        objectModificationLogLabel = None):
            '''DeleteImage deletes the image with the indicated name from the specified server.
Input: name (ARNameType)
       updateRef (ARBoolean, specify TRUE to remove all references to the image)
       (c_char_p) objectModificationLogLabel (optional, default = None)
Output: errnr'''
            return self.ARDeleteImage(name,
                                      updateRef,
                                      objectModificationLogLabel)

        def DeleteSchema(self, name, deleteOption = cars.AR_SCHEMA_CLEAN_DELETE,
                         objectModificationLogLabel = None):
            '''DeleteSchema deletes the form with the indicated name from the
specified server and deletes any container references to the form.

Input: name
       deleteOption
       (c_char_p) objectModificationLogLabel (optional, default = None)
Output: errnr'''
            return self.ARDeleteSchema(name, deleteOption, objectModificationLogLabel)

        def Export(self, structArray, 
                   displayTag = None, 
                   vuiType = cars.AR_VUI_TYPE_NONE, 
                   exportOption = cars.AR_EXPORT_DEFAULT,
                   lockinfo = None):
            '''Export exports AR data structures to a string.
Use this function to copy structure definitions from one AR System server to another.
Note: Form exports do not work the same way with ARExport as they do in
Remedy Administrator. Other than views, you cannot automatically
export related items along with a form. You must explicitly specify the
workflow items you want to export. Also, ARExport cannot export a form
without embedding the server name in the export file (something you can
do with the "Server-Independent" option in Remedy Administrator).
Input: structArray ((cars.AR_STRUCT_ITEM_xxx, name), ...)
       displayTag (optional, default = None)
       vuiType (optional, default = cars.AR_VUI_TYPE_NONE
       (c_uint) exportOption (optional, default = cars.EXPORT_DEFAULT)
       (list) lockInfo: (optional, default = None) a list of (lockType, lockKey)
Output: string (or None in case of failure)'''
            structItems = self.conv2StructItemList(structArray)
            if lockinfo is None:
                lockinfo = cars.ARWorkflowLockStruct()
            else:
                lockinfo = cars.ARWorkflowLockStruct(lockinfo[0], lockinfo[1])
            return self.ARExport(structItems, displayTag, vuiType, exportOption, lockinfo)

        def ExportToFile(self, structItems,
                           displayTag = None,
                           vuiType = cars.AR_VUI_TYPE_WINDOWS,
                           exportOption = cars.AR_EXPORT_DEFAULT,
                           lockinfo = None,
                           filePtr = None):
            '''ExportToFile exports the indicated structure definitions 
from the specified server to a file. Use this function to copy structure 
definitions from one AR System server to another.
Input: (tuple) structItems
       (ARNameType) displayTag (optional, default = None)
       (c_uint) vuiType  (optional, default = AR_VUI_TYPE_WINDOWS)
       (c_uint) exportOption (optional, default = cars.EXPORT_DEFAULT)
       (ARWorkflowLockStruct or tuple) lockinfo  (optional, default = None)
       (FILE) filePtr  (optional, default = None, resulting in an error)
Output: errnr'''
            structItems = self.conv2StructItemList(structItems)
            if lockinfo is None:
                lockinfo = cars.ARWorkflowLockStruct()
            else:
                lockinfo = cars.ARWorkflowLockStruct(lockinfo[0], lockinfo[1])
            return self.ARExportToFile(structItems,
                           displayTag,
                           vuiType,
                           exportOption,
                           lockinfo,
                           filePtr)

        def GetMultipleActiveLinks(self, changedSince=0, nameList=None,
                                    orderListP = True,
                                    schemaListP = True,
                                    assignedGroupListListP = True,
                                    groupListListP = True,
                                    executeMaskListP = True,
                                    controlFieldListP = True,
                                    focusFieldListP = True,
                                    enableListP = True,
                                    queryListP = True,
                                    actionListListP = True,
                                    elseListListP = True,
                                    helpTextListP = True,
                                    timestampListP = True,
                                    ownersListP = True,
                                    lastChangedListP = True,
                                    changeDiaryListP = True,
                                    objPropListListP = True,
                                    errorActlinkOptionsListP = True,
                                    errorActlinkNameListP = True):
            '''GetMultipleActiveLinks
Input: changedSince=0, 
        nameList=None,
        (optional) orderListP = True,
        (optional) schemaListP = True,
        (optional) assignedGroupListListP = True,
        (optional) groupListListP = True,
        (optional) executeMaskListP = True,
        (optional) controlFieldListP = True,
        (optional) focusFieldListP = True,
        (optional) enableListP = True,
        (optional) queryListP = True,
        (optional) actionListListP = True,
        (optional) elseListListP = True,
        (optional) helpTextListP = True,
        (optional) timestampListP = True,
        (optional) ownersListP = True,
        (optional) lastChangedListP = True,
        (optional) changeDiaryListP = True,
        (optional) objPropListListP = True,
        (optional) errorActlinkOptionsListP = True
        (optional) errorActlinkNameListP = True
Output: ARActiveLinkList'''
            nameList = self.conv2NameList(nameList)
            orderList = schemaList = groupListList = executeMaskList = None
            controlFieldList = focusFieldList = enableList = queryList = None
            actionListList = elseListList = helpTextList = timestampList = None
            ownersList = lastChangedList = changeDiaryList = objPropListList = None
            assignedGroupListList = errorActlinkOptionsList = errorActlinkNameList = None
            if orderListP: orderList = cars.ARUnsignedIntList()
            if schemaListP: schemaList = cars.ARWorkflowConnectList()
            if assignedGroupListListP: assignedGroupListList = cars.ARInternalIdListList()
            if groupListListP: groupListList = cars.ARInternalIdListList()
            if executeMaskListP: executeMaskList = cars.ARUnsignedIntList()
            if controlFieldListP: controlFieldList = cars.ARInternalIdList()
            if focusFieldListP: focusFieldList = cars.ARInternalIdList()
            if enableListP: enableList = cars.ARUnsignedIntList()
            if queryListP: queryList = cars.ARQualifierList()
            if actionListListP: actionListList = cars.ARActiveLinkActionListList()
            if elseListListP: elseListList = cars.ARActiveLinkActionListList()
            if helpTextListP: helpTextList = cars.ARTextStringList()
            if timestampListP: timestampList = cars.ARTimestampList()
            if ownersListP: ownersList = cars.ARAccessNameList()
            if lastChangedListP: lastChangedList = cars.ARAccessNameList()
            if changeDiaryListP: changeDiaryList = cars.ARTextStringList()
            if objPropListListP: objPropListList = cars.ARPropListList()
            if errorActlinkOptionsListP: errorActlinkOptionsList = cars.ARUnsignedIntList()
            if errorActlinkNameListP: errorActlinkNameList = cars.ARNameList()
            return self.ARGetMultipleActiveLinks(changedSince, nameList = nameList,
                        orderList = orderList,
                        schemaList = schemaList,
                        assignedGroupListList = assignedGroupListList,
                        groupListList = groupListList,
                        executeMaskList = executeMaskList,
                        controlFieldList = controlFieldList,
                        focusFieldList = focusFieldList,
                        enableList = enableList,
                        queryList = queryList,
                        actionListList = actionListList,
                        elseListList = elseListList,
                        helpTextList = helpTextList,
                        timestampList = timestampList,
                        ownersList = ownersList,
                        lastChangedList = lastChangedList,
                        changeDiaryList = changeDiaryList,
                        objPropListList = objPropListList,
                        errorActlinkOptionsList = errorActlinkOptionsList,
                        errorActlinkNameList = errorActlinkNameList)

        def GetMultipleFields (self, schemaString, 
                               idList=None,
                               fieldId2P = True,
                               fieldNameP = True,
                               fieldMapP = False,
                               dataTypeP = False,
                               optionP = False,
                               createModeP = False,
                               fieldOptionP = False,
                               defaultValP = False,
                               assignedGroupListListP = False,
                               permissionsP = False,
                               limitP = False,
                               dInstanceListP = False,
                               helpTextP = False,
                               timestampP = False,
                               ownerP = False,
                               lastChangedP = False,
                               changeDiaryP = False,
                               objPropListListP = False):
            '''GetMultipleFields returns a list of the fields and their attributes.
   
GetMultipleFields returns list of field definitions for a specified form.
In contrast to the C APi this function constructs an ARFieldInfoList
for the form and returns all information this way.
Input:  schemaString
        (optional) idList (ARInternalIdList; default: None) we currently
                  expect a real ARInternalIdList, because then it's very
                  easy to simply hand over the result of a GetListField
                  call
      (optional) fieldId2P and all others (Boolean) set to False (default,
                   only fieldNameP is set to True)
                  if you are not interested in those values, to True
                  otherwise (the aprameters have names with 'P' appended
                  as in Predicate)
Output: ARFieldInfoList
'''
            # initialize the structures to default values
            
            # we could receive idLIst as an InternalIdList (as a result of GetListField)
            # or as a python list/array - then we need to convert it first
            if idList != None and idList.__class__ != cars.ARInternalIdList:
                idList = self.conv2InternalIdList(idList)
            fieldId2 = fieldName = fieldMap = dataType = option = None
            createMode = fieldOption = defaultVal = assignedGroupListList = permissions = limit = None
            dInstanceList = helpText = timestamp = owner = None
            lastChanged = changeDiary = objPropListList = None
            if fieldId2P: fieldId2 = cars.ARInternalIdList()
            if fieldNameP: fieldName = cars.ARNameList()
            if fieldMapP: fieldMap = cars.ARFieldMappingList()
            if dataTypeP: dataType = cars.ARUnsignedIntList()
            if optionP: option = cars.ARUnsignedIntList()
            if createModeP: createMode = cars.ARUnsignedIntList()
            if fieldOptionP: fieldOption = cars.ARUnsignedIntList()
            if defaultValP: defaultVal = cars.ARValueList()
            if assignedGroupListListP: assignedGroupListList = cars.ARPermissionListList()
            if permissionsP: permissions = cars.ARPermissionListList()
            if limitP: limit = cars.ARFieldLimitList()
            if dInstanceListP: dInstanceList = cars.ARDisplayInstanceListList()
            if helpTextP: helpText = cars.ARTextStringList()
            if timestampP: timestamp = cars.ARTimestampList()
            if ownerP: owner = cars.ARAccessNameList()
            if lastChangedP: lastChanged = cars.ARAccessNameList()
            if changeDiaryP: changeDiary = cars.ARTextStringList()
            if objPropListListP: objPropListListP = cars.ARPropListList()
            return self.ARGetMultipleFields (schemaString, idList,
                                             fieldId2,
                                             fieldName,
                                             fieldMap,
                                             dataType,
                                             option,
                                             createMode,
                                             fieldOption, 
                                             defaultVal,
                                             assignedGroupListList,
                                             permissions,
                                             limit,
                                             dInstanceList,
                                             helpText,
                                             timestamp,
                                             owner,
                                             lastChanged,
                                             changeDiary,
                                             objPropListList)

        def GetMultipleSchemas(self, changedSince=0, 
                                schemaTypeList = None,
                                nameList=None, 
                                fieldIdList=None,
                                schemaListP = True,
                                schemaInheritanceListListP = False, # reserved for future use
                                assignedGroupListListP = False,
                                groupListListP = False,
                                admingrpListListP = False,
                                getListFieldsListP = False,
                                sortListListP = False,
                                indexListListP = False,
                                archiveInfoListP = False,
                                auditInfoListP = False,
                                defaultVuiListP = False,
                                helpTextListP = False,
                                timestampListP = False,
                                ownerListP = False,
                                lastChangedListP = False,
                                changeDiaryListP = False,
                                objPropListListP = False):
            '''GetMultipleSchemas

Input:  changedSince 
        schemaTypeList
        nameList 
        fieldIdList
        archiveInfoList    
        
Output: ARSchemaList'''
            nameList = self.conv2NameList(nameList)
            schemaList = schemaInheritanceListList = groupListList = None
            admingrpListList = getListFieldsList = sortListList = None
            indexListList = archiveInfoList = auditInfoList = defaultVuiList = None
            helpTextList = timestampList = ownerList = None
            lastChangedList = changeDiaryList = objPropListList = None
            assignedGroupListList = None
            if schemaListP: schemaList = cars.ARCompoundSchemaList()
            if schemaInheritanceListListP: schemaInheritanceListList = cars.ARSchemaInheritanceListList()
            if assignedGroupListListP: assignedGroupListList = cars.ARPermissionListList()
            if groupListListP: groupListList = cars.ARPermissionListList()
            if admingrpListListP: admingrpListList = cars.ARInternalIdListList()
            if getListFieldsListP: getListFieldsList = cars.AREntryListFieldListList()
            if sortListListP: sortListList = cars.ARSortListList()
            if indexListListP: indexListList = cars.ARIndexListList()
            if archiveInfoListP: archiveInfoList = cars.ARArchiveInfoList()
            if auditInfoListP: auditInfoList = cars.ARAuditInfoList()
            if defaultVuiListP: defaultVuiList = cars.ARNameList()
            if helpTextListP: helpTextList = cars.ARTextStringList()
            if timestampListP: timestampList = cars.ARTimestampList()
            if ownerListP: ownerList = cars.ARAccessNameList()
            if lastChangedListP: lastChangedList = cars.ARAccessNameList()
            if changeDiaryListP: changeDiaryList = cars.ARTextStringList()
            if objPropListListP: objPropListList = cars.ARPropListList()
            return self.ARGetMultipleSchemas(changedSince = changedSince, 
                                schemaTypeList = schemaTypeList,
                                nameList = nameList, 
                                fieldIdList = fieldIdList,
                                schemaList = schemaList,
                                schemaInheritanceListList = schemaInheritanceListList, # reserved for future use
                                assignedGroupListList = assignedGroupListList,
                                groupListList = groupListList,
                                admingrpListList = admingrpListList,
                                getListFieldsList = getListFieldsList,
                                sortListList = sortListList,
                                indexListList = indexListList,
                                archiveInfoList = archiveInfoList,
                                auditInfoList = auditInfoList,
                                defaultVuiList = defaultVuiList,
                                helpTextList = helpTextList,
                                timestampList = timestampList,
                                ownerList = ownerList,
                                lastChangedList = lastChangedList,
                                changeDiaryList = changeDiaryList,
                                objPropListList = objPropListList)

        def Import(self, structArray, 
                   importBuf, 
                   importOption=cars.AR_IMPORT_OPT_CREATE,
                   objectModificationLogLabel = None):
            '''Import

Input:  structItems
        importBuf
        optional: importOption (Default=cars.AR_IMPORT_OPT_CREATE)
        (optional) objectModificationLogLabel (c_char_p, default = None)
Output: errnr'''
            structItems = self.conv2StructItemList(structArray)
            return self.ARImport(structItems, importBuf, importOption, objectModificationLogLabel)

        def SetActiveLink(self, name, 
                            newName = None, 
                            order = None, 
                            workflowConnect = None,
                            groupList = None,
                            executeMask = None,
                            controlField = None,
                            focusField = None,
                            enable = None,
                            query = None,
                            actionList = None,
                            elseList = None,
                            helpText = None,
                            owner = None,
                            changeDiary = None,
                            objPropList = None,
                            errorActlinkOptions = None,
                            errorActlinkName = None,
                            objectModificationLogLabel = None):
            '''SetActiveLink updates the active link.

The changes are added to the server immediately and returned to users who
request information about active links. Because active links operate on
clients, individual clients do not receive the updated definition until they
reconnect to the form (thus reloading the form from the server).
Input:  name (ARNameType), 
        (optional) newName (ARNameType, default = None)
        (optional) order (c_uint, default = None)
        (optional) workflowConnect (ARWorkflowConnectStruct, default = None)
        (optional) groupList (ARInternalIdList, default = None)
        (optional) executeMask (c_uint, default = None)
        (optional) controlField (ARInternalId, default = None)
        (optional) focusField (ARInternalId, default = None)
        (optional) enable (c_uint, default = None)
        (optional) query (ARQualifierStruct, default = None)
        (optional) actionList (ARActiveLinkActionList, default = None)
        (optional) elseList (ARActiveLinkActionList, default = None)
        (optional) helpText (c_char_p, default = None)
        (optional) ARAccessNameType (ARNameType, default = None)
        (optional) changeDiary (c_char_p, default = None)
        (optional) objPropList (ARPropList, default = None)
        (optional) errorActlinkOptions (c_uint, default = None)
        (optional) errorActlinkName (ARNameType, default = None)
        (optional) objectModificationLogLabel (c_char_p, default = None)
Output: errnr'''
            return self.ARSetActiveLink(name, 
                                    newName, 
                                    order, 
                                    workflowConnect,
                                    groupList,
                                    executeMask,
                                    controlField,
                                    focusField,
                                    enable,
                                    query,
                                    actionList,
                                    elseList,
                                    helpText,
                                    owner,
                                    changeDiary,
                                    objPropList,
                                    errorActlinkOptions,
                                    errorActlinkName,
                                    objectModificationLogLabel)

        def SetCharMenu(self, name, 
                          newName = None, 
                          refreshCode = None, 
                          menuDefn = None, 
                          helpText = None, 
                          owner = None,
                          changeDiary = None, 
                          objPropList = None,
                          objectModificationLogLabel = None):
            '''SetCharMenu updates the character menu.

The changes are added to the server immediately and returned to users who
request information about character menus. Because character menus
operate on clients, individual clients do not receive the updated definition
until they reconnect to the form (thus reloading the form from the server).
Input:  name, 
        (optional) newName,
        (optional) refreshCode, 
        (optional) menuDefn, 
        (optional) helpText, 
        (optional) owner,
        (optional) changeDiary, 
        (optional) objPropList
        (optional) objectModificationLogLabel
Output: errnr'''
            return self.ARSetCharMenu(name,
                                      newName,
                                      refreshCode,
                                      menuDefn,
                                      helpText,
                                      owner,
                                      changeDiary,
                                      objPropList,
                                      objectModificationLogLabel)

        def SetContainer(self, name,
                           newName = None,
                           groupList = None,
                           admingrpList = None,
                           ownerObjList = None,
                           label = None,
                           description = None,
                           type_ = None,
                           references = None,
                           removeFlag = None,
                           helpText = None,
                           owner = None,
                           changeDiary = None,
                           objPropList = None,
                           objectModificationLogLabel = None):
            '''SetContainer  updates the definition for the container.

Input:  Input:  name
       (optional) newName (default = None)
       (optional) groupList (default = None)
       (optional) admingrpList (default = None)
       (optional) ownerObjList (default = None)
       (optional) label (default = None)
       (optional) description (default = None)
       (optional) type_ (default = None)
       (optional) references (default = None)
       (optional) removeFlag (default = None)
       (optional) helpText (default = None)
       (optional) owner (default = None)
       (optional) changeDiary (default = None)
       (optional) objPropList (default = None)
       (optional) objectModificationLogLabel (default = None)
Output: errnr'''
            return self.ARSetContainer(name,
                           newName,
                           groupList,
                           admingrpList,
                           ownerObjList,
                           label,
                           description,
                           type_,
                           references,
                           removeFlag,
                           helpText,
                           owner,
                           changeDiary,
                           objPropList,
                           objectModificationLogLabel)

        def SetGetEntry(self, schema, 
                       entryId, 
                       fieldList, 
                       getTime = 0, 
                       option = None,
                       idList = None):
            '''SetGetEntry bundles the following API calls into one call:
SetEntry and GetEntry

Please note: self.arsl will be set to the geStatus list! 
Input:  schema
        entryId: entryId to be updated or for join forms: a list of tuples ((schema, entryid), ...)
        fieldList: a dict or a list of tuples: ((fieldid, value), (fieldid, value), ...)
        (optional) getTime (the server compares this value with the 
                    value in the Modified Date core field to
                    determine whether the entry has been changed 
                    since the last retrieval.)
        (optional) option (for join forms only; can be AR_JOIN_SETOPTION_NONE
                    or AR_JOIN_SETOPTION_REF)
        (optional) idList (list of ids or ARInternalIdList)
Output: (getFieldList, seStatus, geStatus) or raise ARErrir in case of Failure'''
            entryIdList = self.conv2EntryIdList (schema, entryId)
            if not entryIdList:
                self.logger.error("SetGetEntry: entryIdList could not be constructed")
                raise ARError (None, "SetGetEntry: entryIdList could not be constructed", cars.AR_RETURN_ERROR)
            fvl = self.conv2FieldValueList(schema, fieldList)
            if not fvl: # something went wrong during conversion!
                raise ARError (None, "SetGetEntry:converting the field list failed", cars.AR_RETURN_ERROR)
            if idList != None and idList.__class__ != cars.ARInternalIdList:
                idList = self.conv2InternalIdList(idList)
            result =  self.ARSetGetEntry(schema, 
                                       entryIdList, 
                                       fieldList, 
                                       getTime, 
                                       option,
                                       idList)
            if self.errnr > 1:
                raise ARError (self)
            return result

        def SetEscalation(self, name, 
                            newName = None,
                            escalationTm = None, 
                            schemaList = None, 
                            enable = None,
                            query = None, 
                            actionList = None,
                            elseList = None, 
                            helpText = None, 
                            owner = None, 
                            changeDiary = None, 
                            objPropList = None,
                            objectModificationLogLabel = None):
            '''SetEscalation updates the escalation with the indicated name on the specified server. The
changes are added to the server immediately and returned to users who request
information about escalations.

Input:  (ARNameType) name, 
        (ARNameType) newName,
       (AREscalationTmStruct) escalationTm, 
       (ARWorkflowConnectStruct) schemaList, 
       (c_uint) enable, 
       (ARQualifierStruct) query, 
       (ARFilterActionList) actionList,
       (ARFilterActionList) elseList, 
       (c_char_p) helpText, 
       (ARAccessNameType) owner, 
       (c_char_p) changeDiary, 
       (ARPropList) objPropList
       (c_char_p) objectModificationLogLabel
Output: errnr'''
            return self.ARSetEscalation(name, 
                                        newName,
                                        escalationTm, 
                                        schemaList, 
                                        enable, 
                                        query, 
                                        actionList,
                                        elseList, 
                                        helpText, 
                                        owner, 
                                        changeDiary, 
                                        objPropList,
                                        objectModificationLogLabel)
        def SetField(self, schema, 
                       fieldId, 
                       fieldName = None, 
                       fieldMap = None, 
                       option = None, 
                       createMode = None, 
                       fieldOption = None, 
                       defaultVal = None,
                       permissions = None, 
                       limit = None, 
                       dInstanceList = None, 
                       helpText = None, 
                       owner = None, 
                       changeDiary = None,
                       objPropList = None):
            '''SetField updates the definition for the form field.
            
arextern.h says the new attribute fieldOption is handed over
to the server as the second to last argument, whereas the
pdf file claims it comes before defaultVal. I'll trust the .h
file more for now...

Input: schema, 
       fieldId, 
       fieldName = None, 
       fieldMap = None, 
       option = None, 
       createMode = None, 
       fieldOption = None, 
       defaultVal = None,
       permissions = None, 
       limit = None, 
       dInstanceList = None, 
       helpText = None, 
       owner = None, 
       changeDiary = None
       setFieldOptions = 0
       objPropList = None
Output: errnr'''
            return self.ARSetField(schema, 
                       fieldId, 
                       fieldName,
                       fieldMap,
                       option,
                       createMode,
                       fieldOption,
                       defaultVal,
                       permissions,
                       limit,
                       dInstanceList,
                       helpText,
                       owner,
                       changeDiary,
                       objPropList)
            
        def SetFilter(self, name, 
                    newName = None,
                    order = None,
                    workflowConnect = None,
                    opSet = None,
                    enable = None,
                    query = None,
                    actionList = None,
                    elseList = None,
                    helpText = None,
                    owner = None,
                    changeDiary = None,
                    objPropList = None,
                    errorFilterOptions = None,
                    errorFilterName = None,
                    objectModificationLogLabel = None):
            '''SetFilter updates the filter.

The changes are added to the server immediately and returned to users who
request information about filters.
Input:  name, 
        newName (optional, default = None)
        order (optional, default = None)
        workflowConnect (optional, default = None)
        opSet (optional, default = None)
        enable (optional, default = None)
        query (optional, default = None)
        actionList (optional, default = None)
        elseList (optional, default = None)
        helpText (optional, default = None)
        owner (optional, default = None)
        changeDiary (optional, default = None)
        objPropList (optional, default = None)
        errorFilterOptions (optional, default = None)
        errorFilterName (optional, default = None)
        (c_char) objectModificationLogLabel (optional, default = None)
Output: errnr'''
            return self.ARSetFilter(name, 
                                    newName,
                                    order,
                                    workflowConnect,
                                    opSet,
                                    enable,
                                    query,
                                    actionList,
                                    elseList,
                                    helpText,
                                    owner,
                                    changeDiary,
                                    objPropList,
                                    errorFilterOptions,
                                    errorFilterName,
                                    objectModificationLogLabel)
        def SetImage(self, name,
                        newName = None,
                        imageBuf = None,
                        imageType = None,
                        description = None,
                        helpText = None,
                        owner = None,
                        changeDiary = None,
                        objPropList = None,
                        objectModificationLogLabel = None):
            '''SetImage updates the image with the indicated name on the specified server. After the
image is updated, the server updates all references and object property timestamps
for schemas affected by the change.
Input: name (ARNameType)
       newName (ARNameType, default = None)
       imageBuf (ARImageDataStruct, default = None)
       imageType (c_char_p, default = None)
       description (c_char_p, default= None)
       helpText (c_char_p, default = None)
       owner (ARAccessNameType, dfault = None)
       changeDiary (c_char_p, default = None)
       objPropList (ARPropList, default = None)
       (c_char) objectModificationLogLabel (optional, default = None)
Output: errnr'''
            return self.ARSetImage(name,
                                newName,
                                imageBuf,
                                imageType,
                                description,
                                helpText,
                                owner,
                                changeDiary,
                                objPropList,
                                objectModificationLogLabel)
            
        def SetMultipleFields(self, schema,
                                     fieldIdList,
                                     fieldNameList = None,
                                     fieldMapList = None,
                                     optionList = None,
                                     createModeList = None,
                                     fieldOptionList = None,
                                     defaultValList = None,
                                     permissionListList = None,
                                     limitList = None,
                                     dInstanceListList = None,
                                     helpTextList = None,
                                     ownerList = None,
                                     changeDiaryList = None,
                                     setFieldOptionList = None,
                                     objPropListList = None,
                                     setFieldStatusList = None):
            '''SetMultipleFields updates the definition for a list of fields 
with the specified IDs on the specified form on the specified server. 

This call produces the same result as a sequence of
ARSetField calls to update the individual fields, but it can be more efficient
because it requires only one call from the client to the AR System server and
because the server can perform multiple database operations in a single
transaction and avoid repeating operations such as those performed at the end of
each individual call.'''
            return self.ARSetMultipleFields(schema,
                                             fieldIdList,
                                             fieldNameList,
                                             fieldMapList,
                                             optionList,
                                             createModeList,
                                             fieldOptionList,
                                             defaultValList,
                                             permissionListList,
                                             limitList,
                                             dInstanceListList,
                                             helpTextList,
                                             ownerList,
                                             changeDiaryList,
                                             setFieldOptionList,
                                             objPropListList,
                                             setFieldStatusList)

        def SetSchema(self, name,
                        newName = None,
                        schema = None,
                        schemaInheritanceList = None,
                        groupList = None,
                        admingrpList = None,
                        getListFields = None,
                        sortList = None,
                        indexList = None,
                        archiveInfo = None,
                        auditInfo = None,
                        defaultVui = None,
                        helpText = None,
                        owner = None,
                        changeDiary = None,
                        objPropList = None,
                        setOption = None,
                        objectModificationLogLabel = None):
            '''SetSchema updates the definition for the form.

If the schema is locked, only the indexList and the defaultVui can be set.
Input:  (ARNameType) name,
        (ARNameType) newName (optional, default = None),
        (ARCompoundSchema) schema (optional, default = None),
        (ARSchemaInterheritanceList) schemaInheritanceList (optional, default = None),
        (ARPermissionList) groupList (optional, default = None),
        (ARInternalIdList) admingrpList (optional, default = None),
        (AREntryListFieldList) getListFields (optional, default = None),
        (ARSortList) sortList (optional, default = None),
        (ARIndexList) indexList (optional, default = None),
        (ARArchiveInfoStruct) archiveInfo (optional, default = None),
        (ARAuditInfoStruct) auditInfo (optional, default = None),
        (ARNameType) defaultVui (optional, default = None),
        (c_char_p) helpText (optional, default = None),
        (ARAccessNameType) owner (optional, default = None),
        (c_char_p) changeDiary (optional, default = None),
        (c_uint) objPropList (optional, default = None),
        (c_uint) setOption (optional, default = None)
        (c_char_p) objectModificationLogLabel (optional, default = None)
Output: errnr'''
            return self.ARSetSchema(name,
                        newName,
                        schema,
                        schemaInheritanceList,
                        groupList,
                        admingrpList,
                        getListFields,
                        sortList,
                        indexList,
                        archiveInfo,
                        auditInfo,
                        defaultVui,
                        helpText,
                        owner,
                        changeDiary,
                        objPropList,
                        setOption,
                        objectModificationLogLabel)

        def SetVUI(self, schema, 
                   vuiId, 
                   vuiName = None, 
                   locale = None, 
                   vuiType=None,
                   dPropList=None, 
                   helpText=None, 
                   owner=None, 
                   changeDiary=None,
                   smObjProp=None):
            '''SetVUI updates the form view (VUI).

Input: schema, 
       vuiId, 
       (optional) vuiName = None, 
       (optional) locale = None, 
       (optional) vuiType=None,
       (optional) dPropList=None, 
       (optional) helpText=None, 
       (optional) owner=None, 
       (optional) changeDiary=None
       (optional) smObjProp=None
Output: errnr'''
            newVuiId = c_int(vuiId)
            return self.ARSetVUI(schema, 
                                newVuiId, 
                                vuiName, 
                                locale, 
                                vuiType,
                                dPropList, 
                                helpText, 
                                owner, 
                                changeDiary,
                                smObjProp)

        def CreateTask(self, name, 
                         chars = None, 
                         objProperties = None, 
                         versionControlList = None):
            '''CreateTask: undocumented function

Input: (ARNameType) name
       (c_char)  chars
       (ARPropList) objProperties
       (ARVercntlObjectList) versionControlList
Output: errnr'''
            return self.ARCreateTask(name, chars, objProperties, versionControlList)

        def SetTask(self, name, newName, chars = None, owner = None, objProperties = None):
            '''SetTask: undocumented function

Input: (ARNameType) name
       (ARNameType) newName
       (c_char)  chars
       (ARAccessNameType) owner
       (ARPropList) objProperties
Output: errnr'''
            return self.ARSetTask(name, newName, chars, owner, objProperties)

        def DeleteTask(self, name):
            '''DeleteTask: undocumented function

Input: (ARNameType) name
Output: errnr'''
            return self.ARDeleteTask(name)

        def CommitTask(self, name):
            '''CommitTask: undocumented function

Input: (ARNameType) name
Output: errnr'''
            return self.ARCommitTask(name)

        def RollbackTask(self, name):
            '''RollbackTask: undocumented function

Input: (ARNameType) name
Output: errnr'''
            return self.ARRollbackTask(name)
   
    class erARS(erARS7603):
        pass

if float(cars.version) >= 76.04:
    class erARS7604(erARS7603):
        pass
    class erARS(erARS7604):
        pass

if float(cars.version) >= 80: 
    class erARS80(erARS7604):
        pass
    class erARS(erARS80):
        pass

if float(cars.version) >= 81: 
    class erARS81(erARS80):
        pass
    class erARS(erARS81):
        pass
