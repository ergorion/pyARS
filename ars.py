#! /usr/bin/env python
# -*- coding: utf-8 -*-
#######################################################################
#
# This is the high level implementation of the Remedy C-API in Python.
# (C) 2004-2015 by Ergorion
#
# Currently supported Version: V5.1.x - V8.1.0 of the Remedy API
#
#
#######################################################################
# known issues
#    - ARGetMultipleVUIs (new in 6.3) seems to be buggy in any ARS 6.3 DLL
#      that I have come across yet, in that the locale list seems to be
#      corrupted. Therefore, use this function with caution!
#    - ARGetSupportFile, 3 XML support calls are not implemented yet
#    - There was a bug in ctypes before 0.9.9.7 with large struct arrays. 
#      So make sure to use a version 0.9.9.7 or later
#    - ctypes is compatible with python 2.3 and later.
#######################################################################
#
#
# This program is free software; you can redistribute it and/or modify it under 
# the terms of the GNU General Public License as published by the Free Software 
# Foundation; either version 2 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or 
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with 
# this program; if not, write to the 
# Free Software Foundation, Inc., 
# 59 Temple Place, Suite 330, 
# Boston, MA 02111-1307 USA
#

from ctypes import byref, c_char_p, c_uint, c_int, c_ulong,\
                    Structure, POINTER, c_long,  set_conversion_mode
import logging
import sys

# try:
from pyars import cars
#except ImportError: # Python3
#    from . import cars

#######################################################################
# small helper function

def my_byref(someObject):
    '''my_byref returns the ctypes implementation byref of an object
unless it is None; in this case, m_byref returns None (whereas
ctypes implementation raises an error).'''
    if not someObject is None:
        return byref(someObject)
    else:
        return None
    
# there is no structure defined (at least not up to ARS V5.1.2)
# that holds all the information for an ActiveLink or Filter. Therefore
# I create my own class...
# this is taken vom ARGetActiveLink
class ARActiveLinkStruct(Structure):
    _fields_ = [("name", cars.ARNameType),
                ("order", c_uint),
                ("schemaList", cars.ARWorkflowConnectStruct),
                ("groupList", cars.ARInternalIdList),
                ("executeMask", c_uint),
                ("controlField", cars.ARInternalId),
                ("focusField",  cars.ARInternalId),
                ("enable", c_uint),
                ("query", cars.ARQualifierStruct),
                ("actionList", cars.ARActiveLinkActionList),
                ("elseList", cars.ARActiveLinkActionList),
                ("helpText", c_char_p),
                ("timestamp", cars.ARTimestamp),
                ("owner", cars.ARAccessNameType),
                ("lastChanged", cars.ARAccessNameType),
                ("changeDiary", c_char_p),
                ("objPropList", cars.ARPropList)]

   
class ARActiveLinkList(Structure):
    _fields_ = [('numItems', c_uint),
                ('activeLinkList',POINTER(ARActiveLinkStruct))]

class ARContainerStruct(Structure):
    _fields_ = [("name", cars.ARNameType),
        ("groupList", cars.ARPermissionList),
        ("admingrpList", cars.ARInternalIdList),
        ("ownerObjList", cars.ARContainerOwnerObjList),
        ("label", c_char_p),
        ("description", c_char_p),
        ("type", c_uint),
        ("references", cars.ARReferenceList),
        ("helpText", c_char_p),
        ("owner", cars.ARAccessNameType),
        ("timestamp", cars.ARTimestamp),
        ("lastChanged", cars.ARAccessNameType),
        ("changeDiary", c_char_p),
        ("objPropList", cars.ARPropList)]

class ARContainerList(Structure):
    _fields_ = [('numItems', c_uint),
                ('containerList',POINTER(ARContainerStruct))]

class AREscalationStruct(Structure):
    _fields_ = [('name', cars.ARNameType),
        ('escalationTm', cars.AREscalationTmStruct),
        ('schemaList', cars.ARWorkflowConnectStruct),
        ('enable', c_uint),
        ('query', cars.ARQualifierStruct),
        ('actionList', cars.ARFilterActionList),
        ('elseList', cars.ARFilterActionList),
        ('helpText', c_char_p),
        ('timestamp', cars.ARTimestamp),
        ('owner', cars.ARAccessNameType),
        ('lastChanged', cars.ARAccessNameType),
        ('changeDiary', c_char_p),
        ('objPropList', cars.ARPropList)]

class AREscalationList(Structure):
    _fields_ = [('numItems', c_uint),
                ('escalationList',POINTER(AREscalationStruct))]

class ARFilterStruct(Structure):
    _fields_ = [("name", cars.ARNameType),
                ("order", c_uint),
                ("schemaList", cars.ARWorkflowConnectStruct),
                ("opSet", c_uint),
                ("enable", c_uint),
                ("query", cars.ARQualifierStruct),
                ("actionList", cars.ARFilterActionList),
                ("elseList", cars.ARFilterActionList),
                ("helpText", c_char_p),
                ("timestamp", cars.ARTimestamp),
                ("owner", cars.ARAccessNameType),
                ("lastChanged", cars.ARAccessNameType),
                ("changeDiary", c_char_p),
                ("objPropList", cars.ARPropList)]

class ARFilterList(Structure):
    _fields_ = [('numItems', c_uint),
                ('filterList',POINTER(ARFilterStruct))]    

class ARMenuStruct(Structure):
    _fields_ = [("name", cars.ARNameType),
                ("refreshCode", c_uint),
                ("menuDefn", cars.ARCharMenuStruct),
                ("helpText", c_char_p),
                ("timestamp", cars.ARTimestamp),
                ("owner", cars.ARAccessNameType),
                ("lastChanged", cars.ARAccessNameType),
                ("changeDiary", c_char_p),
                ("objPropList", cars.ARPropList)]

class ARMenuList(Structure):
    _fields_ = [('numItems', c_uint),
                ('menuList',POINTER(ARMenuStruct))] 

class ARSchema(Structure):
    _fields_ = [("name", cars.ARNameType),
                ("schema", cars.ARCompoundSchema),
                ("groupList", cars.ARPermissionList),
                ("admingrpList", cars.ARInternalIdList),
                ("getListFields",  cars.AREntryListFieldList),
                ("sortList", cars.ARSortList),
                ("indexList", cars.ARIndexList),
                ("defaultVui", cars.ARNameType),
                ("helpText", c_char_p),
                ("timestamp", cars.ARTimestamp),
                ("owner", cars.ARAccessNameType),
                ("lastChanged", cars.ARAccessNameType),
                ("changeDiary", c_char_p),
                ("objPropList", cars.ARPropList)]

class ARSchemaList(Structure):
    _fields_ = [('numItems', c_uint),
                ('schemaList',POINTER(ARSchema))]    

class pyARSNotImplemented(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class  mylogger(object):
    '''my own poor man's logger to support IronPython that currently has
a bug in the log module'''
    def __init__(self, level=logging.DEBUG):
        self.level = level
        return self
    def setLevel(self, level=logging.DEBUG):
        self.level = level
    def debug(self, logMessage):
        if self.level <= logging.DEBUG:
            print (logMessage)
    def info(self, logMessage):
        if self.level <= logging.INFO:
            print (logMessage)
    def warn(self, logMessage):
        if self.level <= logging.WARN:
            print (logMessage)
    def error(self, logMessage):
        if self.level <= logging.ERROR:
            print (logMessage)

class ARS51(object):
    '''pythonic wrapper Class for Remedy C API, V5.1

Create an instance of ars and call its methods...
similar to ARSPerl and ARSJython'''

    def __init__(self, server='', user='', password='', language='', 
               authString = '',
               tcpport = 0,
               rpcnumber = 0):
        '''Class constructor
'''
        self.__version__ = '1.8.2'
        self.arversion = cars.version # set in cars
        self.arapi = cars.arapi # set in cars
        self.oldCharset = None
        self.context = None
        self.arsl = cars.ARStatusList()
        if sys.platform == 'cli': # special handling for IronPython
            self.logger = mylogger(level=logging.INFO)
        else:
            try: # for python2.4 and later
                logging.basicConfig(level=logging.INFO,
                                    format='%(asctime)s %(name)s %(levelname)s %(message)s')
                self.logger = logging.getLogger("pyars.ars")
            except: # for python 2.3; potentially results in several handlers
                # when initialized several times in one session...
                logging.basicConfig()
                self.logger = logging.getLogger("pyars.ars")
                hdlr = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
                hdlr.setFormatter(formatter)
                self.logger.addHandler(hdlr) 
                self.logger.setLevel(logging.INFO)
        if server != '':
            self.Login(server, user, password, 
                       language = language,
                       authString = authString,
                       tcpport = tcpport,
                       rpcnumber = rpcnumber)

##############################################################
#
# small helper function to check if a schema exists
#

    def schemaExists (self, schemaString):
        '''schemaExists decides if a schema exists on the server.

Input: string (name of a schema)
  :returns: Boolean or None in case of failure'''
        namelist = self.ARGetListSchema()
        if self.errnr > 1:
            return None
        result = [namelist.nameList[i].value for i in range(namelist.numItems) 
                  if namelist.nameList[i].value == schemaString]
        return len(result) > 0 and True or False

##############################################################
#
# small helper function to bring ids to the required length
#

    def padEntryid (self, entryId, prefix='', length=cars.AR_MAX_ENTRYID_SIZE):
        '''padEntryid fills an id with leading zeroes.
        
padEntryid pads entry id string with leading zeros. Accepts optional
prefix. Illegal prefixes are cheerfully ignored. Default length
of 15 can be shortened. Script will fill the string as necessary with
'\0' until it reaches length+1 so that assignment to 
a fieldId works without problems, using ctypes.
Input: string entryId
       string prefix
       int length
  :returns: string'''
        self.errnr = 0
        entryId = str(entryId)# make sure, it's a string (not e.g. an int)
        if entryId.find('|') != -1: # if it is a join assume that its finished already
            return entryId
            
        if length > cars.AR_MAX_ENTRYID_SIZE:
            self.logger.debug ('padEntryId: size of entryid beyond system limit: AR_MAX_ENTRYID_SIZE < %d' %(
                        length))
            length = cars.AR_MAX_ENTRYID_SIZE

        
        # keep in mind that the entryid's here are not necessarily of maximum length
        # however, ctypes requries for easy assignments via [:] (in our calling
        # functions) that the string we return here is of maximum length
        # therefore we append '\0' to fill the string up to AR_MAX_ENTRYID_SIZE
        
        # there are a couple of cases, where we want to return
        # the entryid unchanged:

        # - if the first char is "0", we assume leading zero's
        # - if entryId is empty anyway
        if entryId == '' or entryId[0] == '0':
            filler = '\0' * (cars.AR_MAX_ENTRYID_SIZE-len(entryId)+1)
            return entryId + filler
        # second option: the prefix is already contained in the id, return...
        elif prefix and entryId[:len(prefix)] == prefix:
            filler = '\0' * (cars.AR_MAX_ENTRYID_SIZE-len(entryId)+1)
            return entryId + filler

        entryId = str(entryId).zfill(length)

        # - if there is no prefix, simply return the entryid
        if not prefix or prefix == '':
            filler = '\0' * (cars.AR_MAX_ENTRYID_SIZE-len(entryId)+1)
            return entryId + filler
        # last option: we filled the string to the necessary length with zeros,
        # but still have to prepend the prefix (and maybe fill up with \0)
        if prefix.__class__ == ''.__class__ and len(prefix) <= cars.AR_MAX_ENTRYID_SIZE-len(prefix):
            entryId = prefix + entryId[len(prefix):]
            filler = '\0' * (cars.AR_MAX_ENTRYID_SIZE-len(entryId)+1)
            return entryId + filler
        else:
            self.logger.error('Invalid entry-id prefix. Ignored.')
        self.errnr = 2
        return None

    def statusText(self):
        text = ['Status: ']
        for i in range(self.arsl.numItems):
            text.append ('%s (%d): %s' % (cars.ars_const['AR_RETURN'][self.arsl.statusList[i].messageType],
                                          self.arsl.statusList[i].messageNum,
                                          self.arsl.statusList[i].messageText))
            if self.arsl.statusList[i].appendedText:
                text.append (self.arsl.statusList[i].appendedText)
        return '\n'.join(text)

##############################################################
#
# here start the normal AR... API functions
#

    def ARCreateActiveLink (self, name, 
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
  :returns: errnr
'''
        self.logger.debug('enter ARCreateActiveLink...')
        self.errnr = self.arapi.ARCreateActiveLink(byref(self.context),
                                                   name, 
                                                   order, 
                                                   my_byref(schemaList), 
                                                   my_byref(groupList),
                                                   executeMask,
                                                   my_byref(controlField),
                                                   my_byref(focusField),
                                                   enable, 
                                                   my_byref(query),
                                                   my_byref(actionList),
                                                   my_byref(elseList),
                                                   helpText,
                                                   owner,
                                                   changeDiary,
                                                   my_byref(objPropList),
                                                   byref(self.arsl))
        if self.errnr > 1:
            self.logger.error('ARCreateActiveLink failed for %s' % name)
        return self.errnr

    def ARCreateAlertEvent(self, user, alertText, 
                         priority = 0, 
                         sourceTag = "AR", 
                         serverName = "@",
                         formName = None,
                         objectId = None):
        '''ARCreateAlertEvent enters an alert event.

ARCreateAlertEvent enters an alert event on the specified server. 
The AR System server sends an alert to the specified, registered users.
Input: user (ARAccessNameType)
       alertText (c_char_p)
       (optional) priority (c_int, default = 0)
       (optional) sourceTag (ARNameType, default = AR)
       (optional) serverName (ARServerNameType, default = @)
       (optional) formName (ARNameType, default = None)
       (optional) objectId (c_char_p, default = None)
  :returns: entryId (AREntryIdType) or None in case of error'''
        self.logger.debug('enter ARCreateAlertEvent...')
        entryId = cars.AREntryIdType()
        self.errnr = self.arapi.ARCreateAlertEvent(byref(self.context),
                                                   user,
                                                   alertText,
                                                   priority,
                                                   sourceTag,
                                                   serverName,
                                                   formName,
                                                   objectId,
                                                   my_byref(entryId),
                                                   byref(self.arsl))
        if self.errnr < 2:
            return entryId
        else:
            self.logger.error('ARCreateAlertEvent: failed')
            return None 

    def ARCreateCharMenu(self, 
                         name, 
                         refreshCode, 
                         menuDefn, 
                         helpText = None, 
                         owner = None,
                         changeDiary = None, 
                         objPropList = None):
        '''ARCreateCharMenu creates a new character menu.

ARCreateCharMenu creates a new character menu with the indicated name
Input: name (ARNameType)
       refreshCode (c_uint)
       menuDef (ARCharMenuStruct)
       (optional) helpText (c_char_p, default = None)
       (optional) owner (ARAccessNameType, default = None)
       (optional) changeDiary (c_char_p, default = None)
       (optional) objPropList (ARPropList, default = None)
  :returns: errnr'''
        self.logger.debug('enter ARCreateCharMenu...')
        self.errnr = self.arapi.ARCreateCharMenu(byref(self.context),
                                                 name, 
                                                 refreshCode, 
                                                 my_byref(menuDefn), 
                                                 helpText, 
                                                 owner,
                                                 changeDiary, 
                                                 my_byref(objPropList),
                                                 byref(self.arsl))
        if self.errnr > 1:
            self.logger.error('ARCreateCharMenu failed for %s' % name)
        return self.errnr 

    def ARCreateContainer(self, 
                          name, 
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
        '''ARCreateContainer creates a new container.

ARCreateContainer creates a new container with the indicated name. Use this 
function to create applications, active links, active link guides, filter 
guide, packing lists, guides, and AR System-defined container types. 
A container can also be a custom type_ that you define.
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
  :returns: errnr'''
        self.logger.debug('enter ARCreateContainer...')
        self.errnr = self.arapi.ARCreateContainer(byref(self.context),
                                                  name, 
                                                  my_byref(groupList), 
                                                  my_byref(admingrpList), 
                                                  my_byref(ownerObjList), 
                                                  my_byref(label), 
                                                  my_byref(description),
                                                  my_byref(type_),
                                                  my_byref(references),
                                                  removeFlag,
                                                  helpText,
                                                  owner,
                                                  changeDiary,
                                                  my_byref(objPropList),
                                                  byref(self.arsl))
        if self.errnr < 2:
            self.logger.error('ARCreateContainer failed for %s' % name)
        return self.errnr

    def ARCreateEntry(self, schema, fieldList):
        '''ARCreateEntry creates a new entry.

ARCreateEntry creates a new entry in the indicated schema. You can create 
entries in base schemas only. To add entries to join forms, create them 
in one of the underlying base forms.
Input: schema (ARNameType)
       fieldList (ARFieldValueList)
  :returns: entryId (AREntryIdType) (or none in case of error)'''
        self.logger.debug('enter ARCreateEntry...')
        entryId = cars.AREntryIdType()
        self.errnr = self.arapi.ARCreateEntry(byref(self.context),
                                              schema,
                                              my_byref(fieldList),
                                              entryId, 
                                              byref(self.arsl))
        if self.errnr < 2:
            return entryId.value
        else:
            self.logger.error('ARCreateEntry for schema %s failed' % schema)
            return None

    def ARCreateEscalation(self, 
                           name, 
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
        '''ARCreateEscalation creates a new escalation.

ARCreateEscalation creates a new escalation with the indicated name. The escalation condition
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
  :returns: errnr'''
        self.logger.debug('enter ARCreateEscalation...')
        self.errnr = self.arapi.ARCreateEscalation(byref(self.context),
                                                   name, 
                                                   my_byref(escalationTm), 
                                                   my_byref(schemaList), 
                                                   enable, 
                                                   my_byref(query), 
                                                   my_byref(actionList),
                                                   my_byref(elseList), 
                                                   helpText, 
                                                   owner, 
                                                   changeDiary, 
                                                   my_byref(objPropList),
                                                   byref(self.arsl))
        if self.errnr > 1:
            self.logger.error('ARCreateEscalation failed for %s' % name)
        return self.errnr

    def ARCreateField(self, schema, 
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
        '''ARCreateField creates a new field.

ARCreateField creates a new field with the indicated name on the specified server. Forms
can contain data and nondata fields. Nondata fields serve several purposes.
Trim fields enhance the appearance and usability of the form (for example,
lines, boxes, or static text). Control fields provide mechanisms for executing
active links (for example, menus, buttons, or toolbar buttons). Other
nondata fields organize data for viewing (for example, pages and page
holders) or show data from another form (for example, tables and columns).
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
  :returns: fieldId (or None in case of failure)'''
        self.logger.debug('enter ARCreateField...')
        if not isinstance(fieldId, c_ulong):
            fieldId = c_ulong(fieldId)
        self.errnr = self.arapi.ARCreateField(byref(self.context),
                                              schema, 
                                              byref(fieldId), 
                                              reservedIdOK,
                                              fieldName, 
                                              my_byref(fieldMap), 
                                              dataType, 
                                              option, 
                                              createMode, 
                                              my_byref(defaultVal), 
                                              my_byref(permissions),
                                              my_byref(limit), 
                                              my_byref(dInstanceList),
                                              helpText, 
                                              owner, 
                                              changeDiary,
                                              byref(self.arsl))
        if self.errnr < 2:
            return fieldId
        else:
            self.logger.error('ARCreateField: failed for %s on %s' % (fieldName, schema))
            return None
        
    def ARCreateFilter(self, 
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
                       objPropList=None):
        '''ARCreateFilter creates a new filter.

ARCreateFilter creates a new filter with the indicated name on the specified 
server. The filter takes effect immediately and remains in effect until changed 
or deleted.
Input: name, 
       (unsigned int) order,
       (ARWorkflowConnectStruct) schemaList,
       (unsigned int) opSet,
       (unsigned int) enable,
       (ARQualifierStruct) query,
       (ARFilterActionList) actionList,
       (ARFilterActionList) elseList,
       (char) helpText,
       (ARAccessNameType) owner,
       (char) changeDiary,
       (ARPropList) objPropList
  :returns: errnr'''
        self.logger.debug('enter ARCreateFilter...')
        self.errnr = self.arapi.ARCreateFilter(byref(self.context),
                                               name, 
                                               order, 
                                               my_byref(schemaList),
                                               opSet, 
                                               enable, 
                                               my_byref(query),
                                               my_byref(actionList),
                                               my_byref(elseList),
                                               helpText,
                                               owner, 
                                               changeDiary,
                                               my_byref(objPropList),
                                               byref(self.arsl))
        if self.errnr > 1:
            self.logger.error('ARCreateFilter failed for %s' % name)
        return self.errnr

    def ARCreateLicense(self, licenseInfo):
        '''ARCreateLicense adds an entry to the license file for the current server.

Input: licenseInfo
  :returns: errnr'''
        self.logger.debug('enter ARCreateLicense...')
        self.errnr = self.arapi.ARCreateLicense(byref(self.context),
                                               my_byref(licenseInfo), 
                                               byref(self.arsl))
        if self.errnr > 1:
            self.logger.error('ARCreateLicense failed ')
        return self.errnr

    def ARCreateSchema(self, 
                       name, 
                       schema, 
                       groupList, 
                       admingrpList, 
                       getListFields,
                       sortList, 
                       indexList, 
                       defaultVui,
                       helpText=None, 
                       owner=None, 
                       changeDiary=None, 
                       objPropList=None):
        '''ARCreateSchema creates a new form.

ARCreateSchema creates a new form with the indicated name on the specified 
server. The nine required core fields are automatically associated with the 
new form.
Input: name, 
       schema, 
       groupList, 
       admingrpList, 
       getListFields,
       sortList, 
       indexList, 
       defaultVui,
       helpText=None, 
       owner=None, 
       changeDiary=None, 
       objPropList=None    
  :returns: errnr
        '''
        self.logger.debug('enter ARCreateSchema...')
        self.errnr = self.arapi.ARCreateSchema(byref(self.context),
                                               name, 
                                               my_byref(schema), 
                                               my_byref(groupList), 
                                               my_byref(admingrpList), 
                                               my_byref(getListFields),
                                               my_byref(sortList), 
                                               my_byref(indexList), 
                                               defaultVui,
                                               helpText, 
                                               owner, 
                                               changeDiary, 
                                               my_byref(objPropList),
                                               byref(self.arsl))
        if self.errnr > 1:
            self.logger.error('ARCreateSchema failed for schema %s.' % name)
        return self.errnr

    def ARCreateSupportFile(self, 
                            fileType, 
                            name, 
                            id2, 
                            fileId, 
                            filePtr):
        '''ARCreateSupportFile creates a file.
        
ARCreateSupportFile creates a file that clients can retrieve by using the AR 
System. Such files are commonly used for reports (to store them separately 
from the active link that calls them, preventing large downloads of unneeded 
information), but this function can store any file on the server. Each support 
file is associated with a server object.
Input: fileType, 
        name, 
        id2, 
        fileId, 
        filePtr    
  :returns: errnr'''
        self.logger.debug('enter ARCreateSupportFile...')
        self.errnr = self.arapi.ARCreateSupportFile(byref(self.context),
                                                    fileType, 
                                                    name, 
                                                    id2, 
                                                    fileId, 
                                                    byref(filePtr), 
                                                    byref(self.arsl))
        if self.errnr > 1:
            self.logger.error('ARCreateSupportFile failed ')
        return self.errnr

    def ARCreateVUI(self, schema, 
                    vuiId, vuiName, locale, 
                  vuiType=None,
                  dPropList=None, 
                  helpText=None, 
                  owner=None, 
                  changeDiary=None):
        '''ARCreateVUI creates a new form view (VUI).
        
ARCreateVUI creates a new form view (VUI) with the indicated name on
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
  :returns: vuiId (or None in case of failure)'''
        self.logger.debug('enter ARCreateVUI with type %s and #dProps: %d' % (
                          vuiType, dPropList.numItems))
        tempVuiId = cars.ARInternalId(vuiId)
        self.errnr = self.arapi.ARCreateVUI(byref(self.context),
                                            schema,
                                            byref(tempVuiId), 
                                            vuiName, 
                                            locale, 
                                            vuiType,
                                            my_byref(dPropList), 
                                            helpText, 
                                            owner, 
                                            changeDiary,
                                            byref(self.arsl))
        if self.errnr < 2:
            return tempVuiId.value
        else:
            self.logger.error('ARCreateVUI: failed for schema %s and vui %s' % (
                              schema, vuiName))
            return None

    def ARDateToJulianDate(self, date):
        '''ARDateToJulianDate converts a year, month, and day value to a Julian date.

ARDateToJulianDate converts a year, month, and day value to a Julian date. The Julian
date is the number of days since noon, Universal Time, on January 1, 4713
BCE (on the Julian calendar). The changeover from the Julian calendar to the
Gregorian calendar occurred in October, 1582. The Julian calendar is used
for dates on or before October 4, 1582. The Gregorian calendar is used for
dates on or after October 15, 1582.        
Input: date (a list of (year, month, day)
  :returns: jd or None in case of failure'''
        self.logger.debug('enter ARDateToJulianDate...')
        ardate = cars.ARDateStruct()
        ardate.year = date[0]
        ardate.month = date[1]
        ardate.day = date[2]
        jd = c_int(0)
        self.errnr = self.arapi.ARDateToJulianDate(byref(self.context),
                                              byref(ardate),
                                              byref(jd),
                                              byref(self.arsl))
        if self.errnr < 2:
            return jd.value
        else:
            self.logger.error ('ARDateToJulianDate failed')
            return None

    def ARDecodeAlertMessage(self, message, messageLen):
        '''ARDecodeAlertMessage decodes a formatted alert message and returns the
component parts of the message to the alert client.

Input: message
       messageLen
  :returns: a list of (timestamp, sourceType, priority, alertText, sourceTag, serverName,
serverAddr, formName, objectId)'''
        self.logger.debug('enter ARDecodeAlertMessage...')
        timestamp = cars.ARTimestamp()
        sourceType = c_uint()
        priority = c_uint()
        alertText, sourceTag, serverName,serverAddr,formName,objectId = c_char_p()
        self.errnr = self.arapi.ARDecodeAlertMessage(byref(self.context),
                                                byref(message),
                                                messageLen,
                                                byref(timestamp),
                                                byref(sourceType),
                                                byref(priority),
                                                byref(alertText),
                                                byref(sourceTag),
                                                byref(serverName),
                                                byref(serverAddr),
                                                byref(formName),
                                                byref(objectId),
                                                byref(self.arsl))
        if self.errnr < 2:
            return (timestamp, sourceType, priority, alertText, sourceTag, serverName, serverAddr, formName,
                    objectId)
        else:
            self.logger.error('ARDecodeAlertMessage: failed')
            return None


    def ARDecodeARAssignStruct(self, assignText):
        '''ARDecodeARAssignStruct converts a serialized assign string in a .def file into an
ARAssignStruct structure to facilitate string import.

Input: AassignText
  :returns: assignStruct (or None in case of failure)'''
        self.logger.debug('enter ARDecodeARAssignStruct...')
        assignStruct = cars.ARAssignStruct()
        self.errnr = self.arapi.ARDecodeARAssignStruct(byref(self.context),
                                                byref(assignText),
                                                byref(assignStruct),
                                                byref(self.arsl))
        if self.errnr < 2:
            return assignStruct
        else:
            self.logger.error('ARDecodeARAssignStruct: failed')
            return None

    def ARDecodeARQualifierStruct(self, qualText):
        '''ARDecodeARQualifierStruct converts a serialized qualifier string into
an ARQualifierStruct structure.

Input: qualText
  :returns: qualStruct (or None in case of failure)'''
        self.logger.debug('enter ARDecodeARQualifierStruct...')
        qualStruct = cars.ARQualifierStruct()
        # qualPointer = cars.c_char_p(qualText)
        self.errnr = self.arapi.ARDecodeARQualifierStruct(byref(self.context),
                                                qualText, # qualPointer,
                                                byref(qualStruct),
                                                byref(self.arsl))
        if self.errnr < 2:
            return qualStruct
        else:
            self.logger.error('ARDecodeARQualifierStruct: failed')
            return None

    def ARDecodeDiary(self, diaryString):
        '''ARDecodeDiary parses any diary field.

ARDecodeDiary parses any diary field (including the changeDiary associated with every
AR System object) into user, time stamp, and text components. The function
takes the formatted string returned for all diary fields and decodes it into an
array of diary entries.
        
Input: diaryString
  :returns: diaryList (or None in case of failure)'''
        self.logger.debug('enter ARDecodeDiary...')
        diaryList = cars.ARDiaryList()
        self.errnr = self.arapi.ARDecodeDiary(byref(self.context),
                                                diaryString,
                                                byref(diaryList),
                                                byref(self.arsl))
        if self.errnr < 2:
            return diaryList
        else:
            self.logger.error('ARDecodeDiary: failed')
            return None

    def ARDecodeStatusHistory(self, statHistString):
        '''ARDecodeStatusHistory parses the Status History core field into user and
time stamp components.

Input:  statHistString
  :returns: statHistList (or None in case of failure)'''
        self.logger.debug('enter ARDecodeStatusHistory...')
        statHistList = cars.ARStatusHistoryList()
        self.errnr = self.arapi.ARDecodeStatusHistory(byref(self.context),
                                                statHistString,
                                                byref(statHistList),
                                                byref(self.arsl))
        if self.errnr < 2:
            return statHistList
        else:
            self.logger.error('ARDecodeStatusHistory: failed')
            return None

    def ARDeleteActiveLink(self, name):
        '''ARDeleteActiveLink deletes the active link.
        
ARDeleteActiveLink deletes the active link with the indicated name from the
specified server and deletes any container references to the active link.
Input: name
  :returns: errnr'''
        self.logger.debug('enter ARDeleteActiveLink: %s...' % (name))
        self.errnr = self.arapi.ARDeleteActiveLink(byref(self.context),
                                                   name,
                                                   byref(self.arsl))
        return self.errnr

    def ARDeleteCharMenu(self, name):
        '''ARDeleteCharMenu deletes the character menu with the indicated name from
the specified server.
        
Input: name
  :returns: errnr'''
        self.logger.debug('enter ARDeleteCharMenu...')
        self.errnr = self.arapi.DeleteCharMenu(byref(self.context),
                                               name,
                                               byref(self.arsl))
        return self.errnr

    def ARDeleteContainer(self, name):
        '''ARDeleteContainer deletes the container .
        
ARDeleteContainer deletes the container with the indicated name from
the specified server and deletes any references to the container from other containers.
Input: name
  :returns: errnr'''
        self.logger.debug('enter ARDeleteContainer...')
        self.errnr = self.arapi.DeleteContainer(byref(self.context),
                                               name,
                                               byref(self.arsl))
        return self.errnr

    def ARDeleteEntry(self, schema, entryIdList, option = 0):
        '''ARDeleteEntry deletes the form entry.
ARDeleteEntry deletes the form entry with the indicated ID from
the specified server.

Input: schema
       entryIdList
       option
  :returns: errnr'''
        self.logger.debug('enter ARDeleteEntry...')
        self.errnr = self.arapi.ARDeleteEntry(byref (self.context),
                                              schema,
                                              byref(entryIdList),
                                              option,
                                              byref(self.arsl))
        return self.errnr
        
    def ARDeleteEscalation(self, name):
        '''ARDeleteEscalation deletes the escalation.
        
ARDeleteEscalation deletes the escalation with the indicated name from the
specified server and deletes any container references to the escalation.
Input:  name
  :returns: errnr'''
        self.logger.debug('enter ARDeleteEscalation...')
        self.errnr = self.arapi.ARDeleteEscalation(byref(self.context),
                                                   name,
                                                   byref(self.arsl))
        return self.errnr

    def ARDeleteField(self, schema, 
                      fieldId, 
                      deleteOption = cars.AR_FIELD_CLEAN_DELETE):
        '''ARDeleteField deletes the form field.
        
ARDeleteField deletes the form field with the indicated ID 
from the specified server.
Input: schema
       fieldId
       deleteOption
  :returns: errnr'''
        self.logger.debug('enter ARDeleteField...')
        self.errnr = self.arapi.ARDeleteField(byref(self.context),
                                              schema,
                                              fieldId,
                                              deleteOption,
                                              byref(self.arsl))
        return self.errnr

    def ARDeleteFilter(self, name):
        '''ARDeleteFilter deletes the filter.
        
ARDeleteFilter deletes the filter with the indicated name from the
specified server and deletes any container references to the filter.
Input:  name
  :returns: errnr'''
        self.logger.debug('enter ARDeleteFilter...')
        self.errnr = self.arapi.ARDeleteFilter(byref(self.context),
                                               name,
                                               byref(self.arsl))
        return self.errnr

    def ARDeleteLicense(self, licenseType, licenseKey):
        '''ARDeleteLicense deletes an entry from the license file for the current server.
        
Input: 
       licenseType
       licenseKey
  :returns: errnr'''
        self.logger.debug('enter ARDeleteLicense...')
        self.errnr = self.arapi.ARDeleteLicense(byref(self.context),
                                                licenseType,
                                                licenseKey,
                                                byref(self.arsl))
        return self.errnr

    def ARDeleteMultipleFields(self, 
                               schema, 
                               fieldList, 
                               deleteOption = cars.AR_FIELD_CLEAN_DELETE):
        '''ARDeleteMultipleFields deletes the form fields.
        
ARDeleteMultipleFields deletes the form fields with the indicated IDs from
the specified server.
Input:  schema
       fieldList
       deleteOption
  :returns: errnr'''
        self.logger.debug('enter ARDeleteMultipleFields...')
        self.errnr = self.arapi.ARDeleteMultipleFields(byref(self.context),
                                               schema,
                                               my_byref(fieldList),
                                               deleteOption,
                                               byref(self.arsl))
        return self.errnr

    def ARDeleteSchema(self, name, deleteOption = cars.AR_SCHEMA_CLEAN_DELETE):
        '''ARDeleteSchema deletes the form.
        
ARDeleteSchema deletes the form with the indicated name from the
specified server and deletes any container references to the form.
Input: 
       name
       deleteOption
  :returns: errnr'''
        self.logger.debug('enter ARDeleteSchema...')
        self.errnr = self.arapi.ARDeleteSchema(byref(self.context),
                                               name,
                                               deleteOption,
                                               byref(self.arsl))
        return self.errnr

    def ARDeleteSupportFile(self, fileType, name, id2, fileId):
        '''ARDeleteSupportFile deletes a support file in the AR System.
        
Input: fileType,
       name
       id2 (if name is not a form, set id2 to 0.)
       fileId
  :returns: errnr'''
        self.logger.debug('enter ARDeleteSupportFile...')
        self.errnr = self.arapi.ARDeleteSupportFile(byref(self.context),
                                                    fileType,
                                                    name,
                                                    id2,
                                                    fileId,
                                                    byref(self.arsl))
        return self.errnr

    def ARDeleteVUI(self, schema, vuiId):
        '''ARDeleteVUI deletes the form view (VUI).
        
ARDeleteVUI deletes the form view (VUI) with the indicated ID from the specified server.
Input: 
       schema
       vuiId
  :returns: errnr'''
        self.logger.debug('enter ARDeleteVUI...')
        self.errnr = self.arapi.ARDeleteVUI (byref(self.context),
                                             schema,
                                             vuiId,
                                             byref(self.arsl))
        return self.errnr

    def ARDeregisterForAlerts(self, clientPort):
        '''ARDeregisterForAlerts cancels registration for the specified user.

ARDeregisterForAlerts cancels registration for the specified user on the
specified AR System server and port.
Input: clientPort
  :returns: errnr'''
        self.logger.debug('enter ARDeregisterForAlerts...')
        self.errnr = self.arapi.ARDeregisterForAlerts(byref(self.context),
                                            clientPort,
                                            byref(self.arsl))
        return self.errnr

    def AREncodeARAssignStruct(self, assignStruct):
        '''AREncodeARAssignStruct converts an ARAssignStruct structure into a serialized
assignment string.
        
Input: assignStruct
  :returns: assignText (or None in case of failure)'''
        self.logger.debug('enter AREncodeARAssignStruct...')
        assignText = c_char_p()
        self.errnr = self.arapi.AREncodeARAssignStruct (byref(self.context),
                                                byref(assignStruct),
                                                byref(assignText),
                                                byref(self.arsl))
        if self.errnr < 2:
            return assignText.value
        else:
            self.logger.error('AREncodeARAssignStruct: failed')
            return None


    def AREncodeARQualifierStruct(self, qualStruct):
        '''AREncodeARQualifierStruct converts an ARQualifierStruct into a 
serialized qualification string.

Input:  qualStruct
  :returns: qualText (or None in case of failure)'''
        self.logger.debug('enter AREncodeARQualifierStruct...')
        qualText = c_char_p()
        self.errnr = self.arapi.AREncodeARQualifierStruct (byref(self.context),
                                                my_byref(qualStruct),
                                                byref(qualText),
                                                byref(self.arsl))
        if self.errnr < 2:
            return qualText.value
        else:
            self.logger.error('AREncodeARQualifierStruct: failed')
            return None

    def AREncodeDiary(self, diaryList):
        '''AREncodeDiary converts an ARDiaryList into a diary string.
        
The resulting string is stored in a
DEF file and is used for exporting definitions of ARServer objects.
Input:  diaryList
  :returns: diaryString'''
        self.logger.debug('enter AREncodeDiary...')
        diaryString = c_char_p()
        self.errnr = self.arapi.AREncodeDiary (byref(self.context),
                                                byref(diaryList),
                                                byref(diaryString),
                                                byref(self.arsl))
        if self.errnr < 2:
            return diaryString.value
        else:
            self.logger.error('AREncodeDiary: failed')
            return None

    def AREncodeStatusHistory(self, statHistList):
        '''AREncodeStatusHistory converts an ARStatusHistoryList into a status 
history string.

The resulting string is stored in a DEF file and is used for exporting 
definitions of ARServer objects.
Input: statHistList
  :returns: statHistString'''
        self.logger.debug('enter AREncodeStatusHistory...')
        statHistString = c_char_p()
        self.errnr = self.arapi.AREncodeStatusHistory (byref(self.context),
                                                byref(statHistList),
                                                byref(statHistString),
                                                byref(self.arsl))
        if self.errnr < 2:
            return statHistString.value
        else:
            self.logger.error('AREncodeStatusHistory: failed')
            return None

    def ARExecuteProcess(self, command, runOption = 0):
        '''ARExecuteProcess performs the indicated command on the specified server.

Depending on the
values you specify for the returnStatus and returnString parameters, you can
execute the command as an independent process or wait for the process to
complete and return the result to the client. The system executes the
command based on the access privileges of the user who launched the
AR System server.
Input: command
       (optional) runOption (if set to 0 (default), operate synchronously)
  :returns: synchron: (returnStatus, returnString)
       asynchron: (1, '')
       in case of an error: (errnr, None)'''
        self.logger.debug('enter ARExecuteProcess...')
        if runOption == 0:
            returnStatus = c_int()
            returnString = c_char_p()
        else:
            returnStatus = None
            returnString = None
        self.errnr = self.arapi.ARExecuteProcess(byref(self.context),
                                                 command,
                                                 my_byref(returnStatus),
                                                 my_byref(returnString),
                                                 byref(self.arsl))
        if self.errnr > 1:
            self.logger.error('ARExecuteProcess failed')
            return (self.errnr, None)
        else:
            if runOption == 0:
                return (returnStatus.value, returnString.value)
            else:
                return (1, '')

    def ARExpandCharMenu(self, menuIn):
        '''ARExpandCharMenu expands the references for the specified menu 
definition and returns a character menu with list-type items only.

Input:  (ARCharMenuStruct) menuIn
  :returns: ARCharMenuStruct (or None in case of failure)'''
        self.logger.debug('enter ARExpandCharMenu...')
        menuOut = cars.ARCharMenuStruct()
        self.errnr = self.arapi.ARExpandCharMenu(byref(self.context),
                                                 my_byref(menuIn),
                                                 byref(menuOut),
                                                 byref(self.arsl))
        if self.errnr < 2:
            return menuOut
        else:
            self.logger.error('ARExpandCharMenu: failed')
            return None

    def ARExport(self, 
                 structItems, 
                 displayTag = None, 
                 vuiType = cars.AR_VUI_TYPE_WINDOWS):
        '''ARExport exports the indicated structure definitions.

Use this function to copy structure definitions from one AR System server to another.
Note: Form exports do not work the same way with ARExport as they do in
Remedy Administrator. Other than views, you cannot automatically
export related items along with a form. You must explicitly specify the
workflow items you want to export. Also, ARExport cannot export a form
without embedding the server name in the export file (something you can
do with the "Server-Independent" option in Remedy Administrator).
Input: (ARStructItemList) structItems
       (ARNameType) displayTag (optional, default = None)
       (c_uint) vuiType (optional, default = cars.AR_VUI_TYPE_WINDOWS)
  :returns: string (or None in case of failure)'''
        self.logger.debug('enter ARExport...')
        exportBuf = c_char_p()
        self.errnr = self.arapi.ARExport(byref(self.context),
                                         byref(structItems),
                                         displayTag,
                                         vuiType,
                                         byref(exportBuf),
                                         byref(self.arsl))
        if self.errnr < 2:
            return exportBuf.value
        else:
            self.logger.error('ARExport: failed')
            return None

    def ARGetActiveLink (self, name):
        '''ARGetActiveLink retrieves the active link with the indicated name.

ARGetActiveLink retrieves the active link with the indicated name on
the specified server.
Input: name
  :returns: ARActiveLinkStruct (containing: order, schemaList,
           groupList, executeMask, controlField,
           focusField, enable, query, actionList,
           elseList, helpText, timestamp, owner, lastChanged,
           changeDiary, objPropList) or None in case of failure'''
        self.logger.debug('enter ARGetActiveLink...')
        order = c_uint()
        schemaList = cars.ARWorkflowConnectStruct()
        groupList = cars.ARInternalIdList()
        executeMask = c_uint()
        controlField = cars.ARInternalId()
        focusField = cars.ARInternalId()
        enable = c_uint()
        query = cars.ARQualifierStruct()
        actionList = cars.ARActiveLinkActionList()
        elseList = cars.ARActiveLinkActionList()
        helpText = c_char_p()
        timestamp = cars.ARTimestamp()
        owner = cars.ARAccessNameType()
        lastChanged = cars.ARAccessNameType()
        changeDiary = c_char_p()
        objPropList = cars.ARPropList()
        self.errnr = self.arapi.ARGetActiveLink(byref(self.context),
                                  name,
                                  byref(order),
                                  byref(schemaList),
                                  byref(groupList),
                                  byref(executeMask),
                                  byref(controlField),
                                  byref(focusField),
                                  byref(enable),
                                  byref(query),
                                  byref(actionList),
                                  byref(elseList),
                                  byref(helpText),
                                  byref(timestamp),
                                  owner,
                                  lastChanged,
                                  byref(changeDiary),
                                  byref(objPropList),
                                  byref(self.arsl))
        if self.errnr < 2:
            result = ARActiveLinkStruct(name,
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
                                    timestamp,
                                    owner.value,
                                    lastChanged.value,
                                    changeDiary,
                                    objPropList)
            return result
        else:
            self.logger.error('ARGetActiveLink: failed for %s' % name)
            return None
        
    def ARGetAlertCount (self, qualifier=None):
        '''ARGetAlertCount retrieves the count of qualifying alert events .
Input: (optional) qualifier (default: None)
  :returns: count (or None in case of failure)'''
        self.logger.debug('enter ARGetAlertCount...')
        count = c_uint()
        self.errnr = self.arapi.ARGetAlertCount(byref(self.context),
                                           my_byref(qualifier),
                                           byref(count),
                                           byref(self.arsl))
        if self.errnr < 2:
            return count.value
        else:
            self.logger.error('ARGetAlertCount: failed')
            return None
        
        
    def ARGetCharMenu(self, name):
        '''ARGetCharMenu retrieves information about the character menu with 
the indicated name.

Input: name
  :returns: ARMenuStruct (containing: refreshCode, menuDefn, helpText,timestamp,owner,lastChanged,
changeDiary,objPropList) or None in case of failure'''
        self.logger.debug('enter ARGetCharMenu...')
        refreshCode = c_uint()
        menuDefn = cars.ARCharMenuStruct()
        helpText = c_char_p()
        timestamp = cars.ARTimestamp()
        owner = cars.ARAccessNameType()
        lastChanged = cars.ARAccessNameType()
        changeDiary = c_char_p()
        objPropList = cars.ARPropList()
        self.errnr = self.arapi.ARGetCharMenu(byref(self.context),
                                              name,
                                              byref(refreshCode),
                                              byref(menuDefn),
                                              byref(helpText),
                                              byref(timestamp),
                                              owner,
                                              lastChanged,
                                              byref(changeDiary),
                                              byref(objPropList),
                                              byref(self.arsl))
        if self.errnr < 2:
            return ARMenuStruct(name,
                                refreshCode,
                                menuDefn,
                                helpText,
                                timestamp,
                                owner.value,
                                lastChanged.value,
                                changeDiary,
                                objPropList)
        else:
            self.logger.error('ARGetCharMenu: failed for %s' % name)
            return None

    def ARGetContainer(self, name, refTypes = None):
        '''ARGetContainer retrieves the contents of the container.

It can return references of a single, specified type, of all types,
or of an exclude reference type. The system returns information for
accessible references and does nothing for references for which the user does
not have access.        
Input: name
       (optional) refTypes (None)
  :returns: ARContainerStruct (groupList, admingrpList, ownerObjList, label, description,
type,references,helpText,owner,timestamp,lastChanged,changeDiary,objPropList)
or None in case of failure'''
        self.logger.debug('enter ARGetContainer...')
        groupList = cars.ARPermissionList()
        admingrpList = cars.ARInternalIdList()
        ownerObjList = cars.ARContainerOwnerObjList()
        label = c_char_p()
        description = c_char_p()
        type_ = c_uint()
        references = cars.ARReferenceList()
        helpText = c_char_p()
        owner = cars.ARAccessNameType()
        timestamp = cars.ARTimestamp()
        lastChanged = cars.ARAccessNameType()
        changeDiary = c_char_p()
        objPropList = cars.ARPropList()
        self.errnr = self.arapi.ARGetContainer(byref(self.context),
                                               name,
                                               my_byref(refTypes),
                                               byref(groupList),
                                               byref(admingrpList),
                                               byref(ownerObjList),
                                               byref(label),
                                               byref(description),
                                               byref(type_),
                                               byref(references),
                                               byref(helpText),
                                               owner,
                                               byref(timestamp),
                                               lastChanged,
                                               byref(changeDiary),
                                               byref(objPropList),
                                               byref(self.arsl))
        if self.errnr < 2:
            return ARContainerStruct(name,
                                       groupList,
                                       admingrpList,
                                       ownerObjList,
                                       label,
                                       description,
                                       type_,
                                       references,
                                       helpText,
                                       owner.value,
                                       timestamp,
                                       lastChanged.value,
                                       changeDiary.value,
                                       objPropList)
        else:
            self.logger.error('ARGetContainer: failed for %s' % name)
            return None
    
    def ARGetControlStructFields (self):
        '''ARGetControlStructFields returns the single pieces of the control record.

This method actually is not necessary in python, as we have
direct access to the members of the struct; however to be
compatible with arsjython, we implement this method.
Input: 
  :returns: (cacheId, errnr, user, password, language, server)'''
        self.logger.debug('enter ARGetControlStructFields...')
        self.errnr = 0
        return (self.context.cacheId, 
                self.errnr, 
                self.context.operationTime,
                self.context.user,
                self.context.password, 
                self.context.language, 
                self.context.sessionId,
                self.context.authString, 
                self.context.server)

    def ARGetCurrencyRatio(self, currencyRatios, 
                           fromCurrencyCode, 
                           toCurrencyCode):
        '''ARGetCurrencyRatio retrieves a selected currency ratio from a set of ratios returned
when the client program makes a call to GetMultipleCurrencyRatioSets.
Input: currencyRatios
       fromCurrencyCode
       toCurrencyCode
  :returns: currencyRatio (or None in case of failure)'''
        self.logger.debug('enter ARGetCurrencyRatio...')
        currencyRatio = cars.ARValueStruct()
        self.errnr = self.arapi.ARGetCurrencyRatio(byref(self.context),
                                                    currencyRatios,
                                                    fromCurrencyCode,
                                                    toCurrencyCode,
                                                    byref(currencyRatio),
                                                    byref(self.arsl))
        if self.errnr < 2:
            return currencyRatio
        else:
            self.logger.error('ARGetCurrencyRatio: failed')
            return None

    def ARGetCurrentServer (self):
        self.logger.debug('enter ARGetCurrentServer...')
        self.errnr = 0
        return self.context.server

    def ARGetEntry (self, schemaString, entryId, idList = None):
        '''ARGetEntry retrieves the form entry with the indicated ID.

ARGetEntry retrieves the form entry with the indicated ID on
the specified server.
Input: schemaString: string
       entry: AREntryIdList
       (optional) idList: ARInternalIdList (default: None, retrieve no fields)
  :returns: ARFieldValueList (or None in case of failure)'''
        self.logger.debug('enter ARGetEntry')
        fieldValueList = cars.ARFieldValueList()
        self.errnr = self.arapi.ARGetEntry (byref(self.context),
                                 schemaString,
                                 byref(entryId),
                                 my_byref(idList),
                                 byref(fieldValueList),
                                 byref(self.arsl))
        if self.errnr < 2:
            return fieldValueList
        else:
            self.logger.error('ARGetEntry: failed for %s' % (schemaString))
            return None

    def ARGetEntryBLOB(self, schema, entryId, id_, loc):
        '''ARGetEntryBLOB retrieves the attachment, or binary large object (BLOB).

Retrieves the attachment, or binary large object (BLOB), stored for the
attachment field with the indicated ID on the specified server. The BLOB can
be placed in a buffer or a file.
Input: schema: schema name
       entryId: AREntryIdList
       id_: fieldId
       loc: ARLocStruct
  :returns: (in loc) (or None in case of failure)'''
        self.logger.debug('enter ARGetEntryBLOB')
        self.errnr = self.arapi.ARGetEntryBLOB(byref(self.context),
                                               schema,
                                               byref(entryId),
                                               id_,
                                               my_byref(loc),
                                               byref(self.arsl))
        if self.errnr < 2:
            return loc
        else:
            self.logger.error('ARGetEntryBLOB: failed for schema %s' % (schema))
            return None

    def ARGetEntryStatistics(self, schema, 
                             qualifier=None, 
                             target=None, 
                             statistic=cars.AR_STAT_OP_COUNT, 
                             groupByList=None):
        '''ARGetEntryStatistics computes the indicated statistic for the form entries 
that match the conditions specified by the qualifier parameter.

Input: schema
       qualifier
       target
       statistic
       groupByList
  :returns: results (or None in case of failure)'''
        self.logger.debug('enter ARGetEntryStatistics...')
        results = cars.ARStatisticsResultList()
        self.errnr = self.arapi.ARGetEntryStatistics (byref(self.context),
                                                        schema,
                                                        my_byref(qualifier),
                                                        my_byref(target),
                                                        statistic,
                                                        my_byref(groupByList),
                                                        byref(results),
                                                        byref(self.arsl))
        if self.errnr < 2:
            return results
        else:
            self.logger.error('ARGetEntryStatistics: failed')
            return None

    def ARGetEscalation(self, name):
        '''ARGetEscalation retrieves information about the escalation.
        
Input: name
  :returns: AREscalationStruct (or None in case of failure)'''
        self.logger.debug('enter ARGetEscalation...')
        escalationTm = cars.AREscalationTmStruct()
        schemaList = cars.ARWorkflowConnectStruct()
        enable = c_uint()
        query = cars.ARQualifierStruct()
        actionList = cars.ARFilterActionList()
        elseList = cars.ARFilterActionList()
        helpText = c_char_p()
        timestamp = cars.ARTimestamp()
        owner = cars.ARAccessNameType()
        lastChanged = cars.ARAccessNameType()
        changeDiary = c_char_p()
        objPropList = cars.ARPropList()
        self.errnr = self.arapi.ARGetEscalation(byref(self.context),
                                                name,
                                                byref(escalationTm),
                                                byref(schemaList),
                                                byref(enable),
                                                byref(query),
                                                byref(actionList),
                                                byref(elseList),
                                                byref(helpText),
                                                byref(timestamp),
                                                owner,
                                                lastChanged,
                                                byref(changeDiary),
                                                byref(objPropList),
                                                byref(self.arsl))

        if self.errnr < 2:
            return AREscalationStruct(name,
                        escalationTm,
                        schemaList,
                        enable,
                        query,
                        actionList,
                        elseList,
                        helpText,
                        timestamp,
                        owner.value,
                        lastChanged.value,
                        changeDiary,
                        objPropList)
        else:
            self.logger.error('ARGetEscalation: failed for %s' % name)
            return None

    def ARGetField (self, schema, fieldId):
        '''ARGetField retrieves the information for one field on a form.

ARGetField returns a ARFieldInfoStruct filled for a given fieldid.
Input: schema
       fieldId
  :returns: ARFieldInfoStruct (or None in case of failure)'''
        self.logger.debug('enter ARGetField: %s:%s' % (schema, fieldId))
        if schema.strip() == '':
            self.logger.error('ARGetField: no schema given')
            self.errnr = 2
            return None
        try:
            if not isinstance(fieldId,int):
                fieldId=int(fieldId)
        except:
            self.logger.error('ARGetField: no valid fieldid given')
            self.errnr = 2
            return None
        fieldName = cars.ARNameType()
        fieldMap = cars.ARFieldMappingStruct()
        dataType = c_uint()
        option = c_uint()
        createMode = c_uint()
        defaultVal = cars.ARValueStruct()
        # if we ask for permissions we need admin rights...
        permissions = cars.ARPermissionList()
        limit = cars.ARFieldLimitStruct()
        dInstanceList = cars.ARDisplayInstanceList()
        helpText = c_char_p()
        timestamp = cars.ARTimestamp()
        owner = cars.ARAccessNameType()
        lastChanged = cars.ARAccessNameType()
        changeDiary = c_char_p()
        self.errnr = self.arapi.ARGetField(byref(self.context),
                                      schema,
                                      fieldId,
                                      fieldName,
                                      byref(fieldMap),
                                      byref(dataType),
                                      byref(option),
                                      byref(createMode),
                                      byref(defaultVal),
                                      byref(permissions),
                                      byref(limit),
                                      byref(dInstanceList),
                                      byref(helpText),
                                      byref(timestamp),
                                      owner,
                                      lastChanged,
                                      byref(changeDiary),
                                      byref(self.arsl))
        if self.errnr < 2:
            return cars.ARFieldInfoStruct(fieldId,
                                       fieldName.value,
                                       timestamp,
                                       fieldMap,
                                       dataType,
                                       option,
                                       createMode,
                                       defaultVal,
                                       permissions,
                                       limit,
                                       dInstanceList,
                                       owner.value,
                                       lastChanged.value,
                                       helpText, # .value,
                                       changeDiary) # .value)
        else:
            self.logger.error('ARGetField: failed for schema %s and fieldid %d' % (
                    schema, fieldId))
            return None
       
    def ARGetFilter (self, filter_):
        '''ARGetFilter retrieves a filter with a given name.

Input: filter name
  :returns: ARFilterStruct (order, schemaList, opSet, enable, query, actionList,
           elseList, helpText, timestamp, owner, lastChanged,
           changeDiary, objPropList) or None in case of failure'''
        self.logger.debug('enter ARGetFilter...')
        order = c_uint()
        schemaList = cars.ARWorkflowConnectStruct()
        opSet = c_uint()
        enable = c_uint()
        query = cars.ARQualifierStruct()
        actionList = cars.ARFilterActionList()
        elseList = cars.ARFilterActionList()
        helpText = c_char_p()
        timestamp = cars.ARTimestamp()
        owner = cars.ARAccessNameType()
        lastChanged = cars.ARAccessNameType()
        changeDiary = c_char_p()
        objPropList = cars.ARPropList()
        self.errnr = self.arapi.ARGetFilter(byref(self.context),
                                       filter_,
                                       byref(order),
                                       byref(schemaList),
                                       byref(opSet),
                                       byref(enable),
                                       byref(query),
                                       byref(actionList),
                                       byref(elseList),
                                       byref(helpText),
                                       byref(timestamp),
                                       owner,
                                       lastChanged,
                                       byref(changeDiary),
                                       byref(objPropList),
                                       byref(self.arsl))
        if self.errnr < 2:
            return ARFilterStruct(filter_,
                                    order,
                                    schemaList,
                                    opSet,
                                    enable,
                                    query,
                                    actionList,
                                    elseList,
                                    helpText,
                                    timestamp,
                                    owner.value,
                                    lastChanged.value,
                                    changeDiary,
                                    objPropList)
        else:
            self.logger.error('ARGetFilter: failed for %s' % filter_)
            return None
       
    def ARGetFullTextInfo(self, requestList):
        '''Retrieves the requested full text search (FTS) information.

Note: Full text search (FTS) is documented for backward compatibility only,
and is not supported in AR System 6.3.
Input: requestList: ARFullTextInfoRequestList
  :returns: fullTextInfo (or None in case of failure)'''
        self.logger.debug('enter ARGetFullTextInfo...')
        fullTextInfo = cars.ARFullTextInfoList()
        self.errnr = self.arapi.ARGetFullTextInfo(byref(self.context),
                                                my_byref(requestList),
                                                byref(fullTextInfo),
                                                byref(self.arsl))
        if self.errnr < 2:
            return fullTextInfo
        else:
            self.logger.debug('ARGetFullTextInfo: failed')
            return None

    def ARGetListActiveLink (self, schema=None, changedSince=0):
        '''ARGetListActiveLink retrieves a list of active links for a schema/server.

You can retrieve all
(accessible) active links or limit the list to active links associated with a
particular form or modified after a specified time.
Input: (optional) schema (default: None)
       (optional) changeSince (default: 0)
  :returns: ARNameList (or None in case of failure)'''
        self.logger.debug('enter ARGetListActiveLink...')
        nameList = cars.ARNameList()
        self.errnr = self.arapi.ARGetListActiveLink (byref(self.context),
                                                schema,
                                                changedSince,
                                                byref(nameList),
                                                byref(self.arsl))
        if self.errnr < 2:
            return nameList
        else:
            self.logger.error('ARGetListActiveLink: failed')
            return None

    def ARGetListAlertUser (self):
        '''ARGetListAlertUser retrieves a list of all users that are registered for alerts.

Input: 
  :returns: ARAccessNameList (or None in case of failure)'''
        self.logger.debug('enter ARGetListAlertUser...')
        userList = cars.ARAccessNameList()
        self.errnr = self.arapi.ARGetListAlertUser (byref(self.context),
                                                byref(userList),
                                                byref(self.arsl))
        if self.errnr < 2:
            return userList
        else:
            self.logger.error('ARGetListCharMenu: failed')
            return None

    def ARGetListCharMenu(self, changedSince=0):
        '''ARGetListCharMenu retrieves a list of character menus.

You can retrieve all
character menus or limit the list to character menus modified after a specified
time.
Input: (optional) changedSince (default = 0)
  :returns: ARNameList (or None in case of failure)'''
        self.logger.debug('enter ARGetListCharMenu...')
        nameList = cars.ARNameList()
        self.errnr =self.arapi.ARGetListCharMenu(byref(self.context),
                                                changedSince,
                                                byref(nameList),
                                                byref(self.arsl))
        if self.errnr < 2:
            return nameList
        else:
            self.logger.error('ARGetListCharMenu: failed')
            return None

    def ARGetListContainer (self, changedSince=0,
                          containerTypes = None,
                          attributes= cars.AR_HIDDEN_INCREMENT,
                          ownerObjList=None):
        '''ARGetListContainer retrieves a list of containers.

You can retrieve all
(accessible) containers or limit the list to containers of a particular type,
containers owned by a specified form, or containers modified after a
specified time.
Input: (ARTimestamp) changedSince (default: 0)
       (ARContainerTypeList) containerTypes: (optional)
       (c_uint) attributes (optional, default: cars.AR_HIDDEN_INCREMENT)
       (ARContainerOwnerObjList) ownerObjList (optional, default: None)
  :returns: ARContainerInfoList (or None in case of failure)'''
        self.logger.debug('enter ARGetListContainer...')
        conList = cars.ARContainerInfoList()
        self.errnr = self.arapi.ARGetListContainer(byref(self.context),
                                                   changedSince,
                                                   my_byref(containerTypes),
                                                   attributes,
                                                   my_byref(ownerObjList),
                                                   byref(conList),
                                                   byref(self.arsl))
        if self.errnr < 2:
            return conList
        else:
            self.logger.error('ARGetListContainer: failed')
            return None

    def ARGetListEntry (self, schema, 
                        query=None,
                        getListFields=None, 
                        sortList=None,
                        firstRetrieve=cars.AR_START_WITH_FIRST_ENTRY,
                        maxRetrieve=cars.AR_NO_MAX_LIST_RETRIEVE):
        '''ARGetListEntry retrieves a list of entries for a schema.

The AR System Server
returns data from each entry as a string containing the concatenated values
of selected fields. You can limit the list to entries that match particular
conditions by specifying the qualifier parameter. ARGetListEntryWithFields
also returns a qualified list of entries, but as field/value pairs.
Input: schema/form name
       (optional) query (ARQualifierStruct)
       (optional) getListFields (default: None)
       (optional) sortList (default: None)
       (optional) firstRetrieve (default: AR_START_WITH_FIRST_ENTRY)
       (optional) maxRetrieve (default: AR_NO_MAX_LIST_RETRIEVE)
  :returns: (AREntryListList, numMatches) (or None in case of failure)'''
        self.logger.debug('enter ARGetListEntry...')
        entryList = cars.AREntryListList()
        numMatches = c_uint()
        self.errnr = self.arapi.ARGetListEntry(byref(self.context),
                                              schema,
                                              my_byref(query),
                                              my_byref(getListFields),
                                              my_byref(sortList),
                                              firstRetrieve,
                                              maxRetrieve,
                                              byref(entryList),
                                              byref(numMatches),
                                              byref(self.arsl))
        if self.errnr < 2:
            return (entryList, numMatches.value)                                     
        else:
            self.logger.error("ARGetListEntry failed: schema: %s/query: %s" % (schema, query))
            return None

    def ARGetListEntryWithFields (self, schema, 
                                  query = None,
                                  getListFields=None, 
                                  sortList=None,
                                  firstRetrieve=cars.AR_START_WITH_FIRST_ENTRY,
                                  maxRetrieve=cars.AR_NO_MAX_LIST_RETRIEVE):
        '''ARGetListEntryWithFields retrieve a list of entries for a schema.

Data from each entry
is returned as field/value pairs for all fields. You can limit the list to entries
that match particular conditions by specifying the qualifier parameter.
ARGetListEntry also returns a qualified list of entries, but as a string for each
entry containing the concatenated values of selected fields.
Note: It is important that the query looks something like this:
'field' = "value" (please note the quotation marks).
Input: 
       schema/form name
       (optional) query string (default: None)
       (optional) getListFields (default: None)
       (optional) sortList (default: None)
       (optional) firstRetrieve (default: AR_START_WITH_FIRST_ENTRY)
       (optional) maxRetrieve (default: AR_NO_MAX_LIST_RETRIEVE)
  :returns: (AREntryListFieldValueList, numMatches) or None in case of failure'''
        self.logger.debug('enter ARGetListEntryWithFields...')
        entryList = cars.AREntryListFieldValueList()
        numMatches = c_uint()
        self.errnr = self.arapi.ARGetListEntryWithFields(byref(self.context),
                                                      schema,
                                                      my_byref(query),
                                                      my_byref(getListFields),
                                                      my_byref(sortList),
                                                      firstRetrieve,
                                                      maxRetrieve, 
                                                      byref(entryList),
                                                      byref(numMatches),
                                                      byref(self.arsl))
        if self.errnr < 2:
            return (entryList, numMatches.value)
        else:
            self.logger.error ("ARGetListEntryWithFields: failed!")
            return None
            
    def ARGetListEscalation (self, schema=None,
                           changedSince = 0):
        '''ARGetListEscalation retrieves a list of all escalations.

You can retrieve all
escalations or limit the list to escalations associated with a particular form.
The call returns all escalations modified on or after the timestamp.
Input: 
       (optional) schema (default: None)
       (optional): changedSince (default: 0)
  :returns: ARAccessNameList (or None in case of failure)'''
        self.logger.debug('enter ARGetListEscalation...')
        nameList = cars.ARNameList()
        self.errnr = self.arapi.ARGetListEscalation (byref(self.context),
                                                     schema,
                                                     changedSince,
                                                     byref(nameList),
                                                     byref(self.arsl))
        if self.errnr < 2:
            return nameList
        else:
            self.logger.error ("ARGetListEscalation: failed!")
            return None

    def ARGetListExtSchemaCandidates(self, schemaType=cars.AR_SCHEMA_VIEW |
                                                    cars.AR_SCHEMA_VENDOR |
                                                    cars.AR_HIDDEN_INCREMENT):
        '''ARGetListExtSchemaCandidates retrieves a list of all available external data
source tables (schema candidates).

Users choose fields from these candidates to populate the
vendor form.
Input: schemaType
  :returns: ARCompoundSchemaList (or None in case of failure)'''
        self.logger.debug('enter ARGetListExtSchemaCandidates...')
        schemaList = cars.ARCompoundSchemaList()
        self.errnr = self.arapi.ARGetListExtSchemaCandidates(byref(self.context),
                                                             schemaType,
                                                             byref(schemaList),
                                                             byref(self.arsl))
        if self.errnr < 2:
            return schemaList
        else:
            self.logger.error ("ARGetListExtSchemaCandidates: failed for schemaType %d!" % schemaType)
            return None

    def ARGetListField(self, schema,
                     changedSince=0,
                     fieldType=cars.AR_FIELD_TYPE_DATA):
        '''ARGetListField returns a list of field ids for a schema.
        
You can
retrieve all fields or limit the list to fields of a particular type or fields
modified after a specified time.
Input: string: schema
       (optional) timestamp: changedSince (default: 0)
       (optional) fieldType (default: AR_FIELD_TYPE_DATA)
  :returns: ARInternalIdList (or None in case of failure)'''
        self.logger.debug('enter ARGetListField...')
        idList = cars.ARInternalIdList()
        if not isinstance(schema,str):
            self.errnr=2
            self.logger.error ("ARGetListField: wrong argument!")
            return None
        
        self.errnr = self.arapi.ARGetListField(byref(self.context),
                                               schema,
                                               fieldType,
                                               changedSince,
                                               byref(idList),
                                               byref(self.arsl))
        if self.errnr < 2:
            return idList
        else:
            self.logger.error ("ARGetListField: failed for schema %s!" % (schema))
            return None

    def ARGetListFilter(self, schema=None, 
                        changedSince=0):
        '''ARGetListFilter return a list of all available filter for a schema.

You can retrieve all filters or
limit the list to filters associated with a particular form or modified after a
specified time.
Input: (optional) schema (default: None -- retrieve filter for server)
       (optional) changedSince (default: 0)
  :returns: ARNameList (or None in case of failure)'''
        self.logger.debug('enter ARGetListFilter...')
        nameList = cars.ARNameList()
        self.errnr = self.arapi.ARGetListFilter(byref(self.context),
                                                schema, 
                                                changedSince,
                                                byref(nameList),
                                                byref(self.arsl))
        if self.errnr < 2:
            return nameList
        else:
            self.logger.error ("ARGetListFilter: failed!")
            return None

    def ARGetListGroup(self, userName=None, password=None):
        '''ARGetListGroup retrieves a list of access control groups.

You can retrieve all groups or limit the list to groups associated with a particular user.        
Input: (optional) userName
       (optional) password
  :returns: ARGroupInfoList (or None in case of failure)'''
        self.logger.debug('enter ARGetListGroup...')
        groupList = cars.ARGroupInfoList()
        self.errnr = self.arapi.ARGetListGroup (byref(self.context),
                                                userName,
                                                password,
                                                byref(groupList),
                                                byref(self.arsl))
        if self.errnr < 2:
            return groupList
        else:
            self.logger.error ("ARGetListGroup: failed!")
            return None

    def ARGetListLicense(self, licenseType=None):
        '''ARGetListLicense return a list of entries from the license file.

The list contains license information for all the types of licenses, including DSO,
flashboards, SMU applications, and servers.
Input: (optional) licenseType (ARLicenseNameType, default: None)
  :returns: ARLicenseInfoList (or None in case of failure)'''
        self.logger.debug('enter ARGetListLicense...')
        licenseInfoList = cars.ARLicenseInfoList()
        self.errnr = self.arapi.ARGetListLicense(byref(self.context),
                                                 licenseType,
                                                 byref(licenseInfoList),
                                                 byref(self.arsl))
        if self.errnr < 2:
            return licenseInfoList
        else:
            self.logger.error ("ARGetListLicense: failed!")
            return None
        
    def ARGetListSchema(self, changedSince=0, 
                        schemaType=cars.AR_HIDDEN_INCREMENT,
                        name='', 
                        fieldIdList=None):
        '''ARGetListSchema return a list of all available schemas.

You can retrieve all (accessible) forms or limit the list to forms of a 
particular type or forms modified after a specified time.
Input: (optional) changedSince (ARTimestamp, default: 0)
       (optional) schemaType (c_uint, default: AR_LIST_SCHEMA_ALL | AR_HIDDEN_INCREMENT)
       (optional) name (ARNameType, default "", only necessary if schemaType is
       AR_LIST_SCHEMA_UPLINK
       (optional) fieldIdList (ARInternalIdList, default: None) ARS then only returns the
       forms that contain all the fields in this list.
  :returns: ARNameList (or None in case of failure)'''
        self.logger.debug('enter ARGetListSchema...')
        nameList = cars.ARNameList()
        self.errnr = self.arapi.ARGetListSchema(byref(self.context),
                                                changedSince,
                                                schemaType,
                                                name,
                                                my_byref(fieldIdList),
                                                byref(nameList),
                                                byref(self.arsl))
        if self.errnr < 2:
            return nameList
        else:
            self.logger.error ("ARGetListSchema: failed!")
            return None
        
    def ARGetListSchemaWithAlias(self, changedSince=0, 
                                 schemaType=cars.AR_HIDDEN_INCREMENT, 
                                 name='', 
                                 fieldIdList=None, 
                                 vuiLabel=None):
        '''ARGetListSchemaWithAlias retrieves a list of form definitions 
and their corresponding aliases.

You can retrieve all (accessible) forms or limit the list to
forms of a particular type or forms modified after a specified time.
Input: (optional) changedSince (ARTimestamp, default: 0)
       (optional) schemaType (c_uint, default: AR_LIST_SCHEMA_ALL | AR_HIDDEN_INCREMENT)
       (optional) name (ARNameType, default "", only necessary if schemaType is
       AR_LIST_SCHEMA_UPLINK
       (optional) fieldIdList (ARInternalIdList, default: None) ARS then only returns the
       forms that contain all the fields in this list.
       (optional) vuiLabel (ARNameType, default: None)
  :returns: a tuple of (nameList, aliasList) (or None in case of failure)'''
        self.logger.debug('enter ARGetListSchemaWithAlias...')
        nameList = cars.ARNameList()
        aliasList = cars.ARNameList()
        self.errnr = self.arapi.ARGetListSchemaWithAlias(byref(self.context),
                                                        changedSince,
                                                        schemaType,
                                                        name,
                                                        my_byref(fieldIdList),
                                                        vuiLabel,
                                                        byref(nameList),
                                                        byref(aliasList),
                                                        byref(self.arsl))
        if self.errnr < 2:
            return (nameList, aliasList)
        else:
            self.logger.error ("ARGetListSchemaWithAlias: failed!")
            return None

    def ARGetListServer (self):
        '''ARGetListServer retrieve the list of available AR System servers.

Retrieves the list of available AR System servers defined in the ar directory file
(UNIX only). Remedy User, Remedy Administrator, Remedy Alert, and
Remedy Import connect to these servers automatically if no servers are
specified at startup. If the ar file is under NIS control, the system uses the file
specified by the NIS map instead of the local ar file. For information about
the ar file, see the Configuring AR System guide.
Note: In the Windows API, server information is retrieved from the registry
instead of the ar file. API programs that run on the server (for example,
through a filter or escalation) can use this function to retrieve the name of
that local server only. Programs that run on a Windows client, however,
cannot. In this case, the function always returns a list of zero servers.
Input: 
  :returns: ARServerNameList (or None in case of failure)'''
        self.logger.debug('enter ARGetListServer...')
        serverList = cars.ARServerNameList()
        self.errnr = self.arapi.ARGetListServer(byref(self.context),
                                                byref(serverList),
                                                byref(self.arsl))
        if self.errnr < 2:
            return serverList
        else:
            self.logger.error( "ARGetListServer: failed")
            return None

    def ARGetListSQL(self, sqlCommand, 
                     maxRetrieve=cars.AR_NO_MAX_LIST_RETRIEVE):
        '''ARGetListSQL retrieves a list of rows from the underlying 
SQL database on the specified server.

The server executes the SQL command you specify and returns the
matching rows. A list with zero items and a warning message are returned if
no SQL database resides on the server. The system returns information based
on the access privileges of the user who launched the AR System server.
Input: sqlCommand
       (optional) maxRetrieve (default: cars.AR_NO_MAX_LIST_RETRIEVE)
  :returns: a tuple of (valueListList, numMatches) or None in case of failure'''
        self.logger.debug('enter ARGetListSQL...')
        valueListList = cars.ARValueListList()
        numMatches = c_uint()
        self.errnr = self.arapi.ARGetListSQL(byref(self.context),
                                            sqlCommand,
                                            maxRetrieve,
                                            byref(valueListList),
                                            byref(numMatches),
                                            byref(self.arsl))
        if self.errnr < 2:
            return (valueListList, numMatches.value)
        else:
            self.logger.error( "ARGetListSQL: failed")
            return None

    def ARGetListSupportFile(self, fileType, 
                             name, 
                             id2=0, 
                             changedSince=0):
        '''ARGetListSupportFile retrieves a list of support file IDs for a 
specified type of object.
        
Input: fileType
       name
       (optional) id2
       (optional) changedSince
  :returns: fileIdList (or None in case of failure)'''
        self.logger.debug('enter ARGetListSupportFile...')
        fileIdList = cars.ARInternalIdList()
        self.errnr = self.arapi.ARGetListSupportFile(byref(self.context),
                                                    fileType,
                                                    name,
                                                    id2,
                                                    changedSince,
                                                    byref(fileIdList),
                                                    byref(self.arsl))
        if self.errnr < 2:
            return fileIdList
        else:
            self.logger.error( "ARGetListSupportFile: failed")
            return None

    def ARGetListUser(self, userListType=cars.AR_USER_LIST_CURRENT, 
                      changedSince=0):
        '''ARGetListUser retrieves a list of users.

You can retrieve information about the
current user, all registered users, or all users currently accessing the server.        
Input: userListType (default: AR_USER_LIST_CURRENT)
       changedSince (default: 0)
  :returns: ARUserInfoList (or None in case of failure)'''
        self.logger.debug('enter ARGetListUser...')
        userList = cars.ARUserInfoList()
        self.errnr = self.arapi.ARGetListUser(byref(self.context),
                                              userListType,
                                              changedSince,
                                              byref(userList),
                                              byref(self.arsl))
        if self.errnr < 2:
            return userList
        else:
            self.logger.error( "ARGetListUser: failed")
            return None

    def ARGetListVUI(self, schema, changedSince=0):
        '''ARGetListVUI retrieves a list of form views (VUI) for a particular form.

You can retrieve all views or limit the list to views modified after a
specified time.
Input: schema
       (optional) changedSince
  :returns: ARInternalIdList (or None in case of failure)'''
        self.logger.debug('enter ARGetListVUI...')
        idList = cars.ARInternalIdList()
        self.errnr = self.arapi.ARGetListVUI(byref(self.context),
                                             schema,
                                             changedSince,
                                             byref(idList),
                                             byref(self.arsl))
        if self.errnr < 2:
            return idList
        else:
            self.logger.error( "ARGetListVUI: failed")
            return None

    def ARGetLocalizedValue(self, localizedRequest):
        '''ARGetLocalizedValue retrieves a localized text string from the Remedy 
Message Catalog.

The message that the server retrieves depends on the user locale.
Input:  localizedRequest
  :returns: a tuple of (localizedValue, timestamp) or None in case of failure'''
        self.logger.debug('enter ARGetLocalizedValue...')
        localizedValue = cars.ARValueStruct()
        timestamp = cars.ARTimestamp()
        self.errnr = self.arapi.ARGetLocalizedValue (byref(self.context),
                                                     byref(localizedRequest),
                                                     byref(localizedValue),
                                                     byref(timestamp),
                                                     byref(self.arsl))
        if self.errnr < 2:
            return (localizedValue, timestamp)
        else:
            self.logger.error( "ARGetLocalizedValue: failed")
            return None

    def ARGetMultipleActiveLinks(self, changedSince=0, 
                                 nameList = None,
                                 orderList = None,
                                 schemaList = None,
                                 groupListList = None,
                                 executeMaskList = None,
                                 controlFieldList = None,
                                 focusFieldList = None,
                                 enableList = None,
                                 queryList = None,
                                 actionListList = None,
                                 elseListList = None,
                                 helpTextList = None,
                                 timestampList = None,
                                 ownersList = None,
                                 lastChangedList = None,
                                 changeDiaryList = None,
                                 objPropListList = None):
        '''ARGetMultipleActiveLinks retrieves multiple active link definitions.

This function performs the same
action as ARGetActiveLink but is easier to use and more efficient than
retrieving multiple entries one by one.
Please note: While the ARSystem returns the information in lists for each item, 
pyars will convert this into an ARActiveLinkList of its own.
Input: changedSince 
         nameList (ARNameList)
         orderList (ARUnsignedIntList)
         schemaList (ARWorkflowConnectList)
         groupListList (ARInternalIdListList)
         executeMaskList (ARUnsignedIntList)
         controlFieldList (ARInternalIdList)
         focusFieldList (ARInternalIdList)
         enableList (ARUnsignedIntList)
         queryList (ARQualifierList)
         actionListList (ARActiveLinkActionListList)
         elseListList (ARActiveLinkActionListList)
         helpTextList (ARTextStringList)
         timestampList (ARTimestampList)
         ownersList (ARAccessNameList)
         lastChangedList (ARAccessNameList)
         changeDiaryList (ARTextStringList)
         objPropListList (ARPropListList)
  :returns: ARActiveLinkList (or None in case of failure)'''
        self.logger.debug('enter ARGetMultipleActiveLinks...')
        existList = cars.ARBooleanList()
        actLinkNameList = cars.ARNameList()
        self.errnr = self.arapi.ARGetMultipleActiveLinks(byref(self.context),
                                                    changedSince,
                                                    my_byref(nameList),
                                                    byref(existList),
                                                    byref(actLinkNameList),
                                                    my_byref(orderList),
                                                    my_byref(schemaList),
                                                    my_byref(groupListList),
                                                    my_byref(executeMaskList),
                                                    my_byref(controlFieldList),
                                                    my_byref(focusFieldList),
                                                    my_byref(enableList),
                                                    my_byref(queryList),
                                                    my_byref(actionListList),
                                                    my_byref(elseListList),
                                                    my_byref(helpTextList),
                                                    my_byref(timestampList),
                                                    my_byref(ownersList),
                                                    my_byref(lastChangedList),
                                                    my_byref(changeDiaryList),
                                                    my_byref(objPropListList),
                                                    byref(self.arsl))
        if self.errnr < 2:
            tempArray = (ARActiveLinkStruct * existList.numItems)()
#            self.logger.debug(' num of entries: existList: %d, nameList: %d, order: %d' % (
#                              existList.numItems, actLinkNameList.numItems, orderList.numItems))
            for i in range(existList.numItems):
                if existList.booleanList[i]:
                    tempArray[i].name=actLinkNameList.nameList[i].value
                    if orderList: tempArray[i].order = orderList.intList[i]
                    if schemaList: tempArray[i].schemaList = schemaList.workflowConnectList[i]
                    if groupListList: tempArray[i].groupList = groupListList.internalIdListList[i]
                    if executeMaskList: tempArray[i].executeMask = executeMaskList.intList[i]
                    if controlFieldList: tempArray[i].controlField = controlFieldList.internalIdList[i]
                    if focusFieldList: tempArray[i].focusField = focusFieldList.internalIdList[i]
                    if enableList: tempArray[i].enable = enableList.intList[i]
                    if queryList: tempArray[i].query = queryList.qualifierList[i]
                    if actionListList: tempArray[i].actionList = actionListList.actionListList[i]
                    if elseListList: tempArray[i].elseList = elseListList.actionListList[i]
                    if helpTextList: 
                        tempArray[i].helpText = helpTextList.stringList[i]
                        if not tempArray[i].helpText == helpTextList.stringList[i]:
                            self.logger.error('''   1) %s is buggy: %s 
                            original helptext: %s''' % (tempArray[i].name,
                                      tempArray[i].helpText, helpTextList.stringList[i]))
                    if timestampList: tempArray[i].timestamp = timestampList.timestampList[i]
                    if ownersList: tempArray[i].owner = ownersList.nameList[i].value
                    if lastChangedList: tempArray[i].lastChanged = lastChangedList.nameList[i].value
                    if changeDiaryList: tempArray[i].changeDiary = changeDiaryList.stringList[i]
                    if objPropListList: tempArray[i].objPropList = objPropListList.propsList[i]
                else:
                    self.logger.error('ARGetMultipleActiveLinks: "%s" does not exist! %s' % (nameList.nameList[i].value,
                                                                                             self.statusText()))

            if not helpTextList is None:
                for j in range(existList.numItems):
                    if tempArray[j].helpText != helpTextList.stringList[j]:
                        self.logger.error('''   2) %d(%s) is buggy: %s
                         original helptext: %s''' % (j, tempArray[j].name,
                                          tempArray[j].helpText, helpTextList.stringList[j]))
            return ARActiveLinkList(existList.numItems, tempArray)
        else:
            self.logger.error( "ARGetMultipleActiveLinks: failed")
            return None
            
    def ARGetMultipleCurrencyRatioSets(self, ratioTimestamps=None):
        '''ARGetMultipleCurrencyRatioSets retrieves a list of formatted currency ratio sets
valid for the times specified in the ratioTimestamps argument.

You can use ARGetCurrencyRatio to extract a specific currency ratio from a 
ratio set that this call (ARGetMultipleCurrencyRatioSets) returns.    
Input: (ARTimestampList) ratioTimestamps (optional, default = None)
  :returns: (ARTextStringList) currencyRatioSets (or None in case of failure)'''
        self.logger.debug('enter ARGetMultipleCurrencyRatioSets...')
        currencyRatioSets = cars.ARTextStringList()
        self.errnr = self.arapi.ARGetMultipleCurrencyRatioSets(byref(self.context),
                                                    my_byref(ratioTimestamps),
                                                    byref(currencyRatioSets),
                                                    byref(self.arsl))
        if self.errnr < 2:
            return currencyRatioSets
        else:
            self.logger.error( "ARGetMultipleCurrencyRatioSets: failed")
            return None

    def ARGetMultipleEntries(self, schema, entryIdList, idList=None):
        '''ARGetMultipleEntries retrieve a list of entries.
        
ARGetMultipleEntries retrieve a list of entries/objects for a
specific schema according to an array of specific ids together
with their fields and values.
NOTE: A maximum of 100 entries can be returned by this function. If you need to return
more than 100 entries, call this function multiple times.
Input: (ARNameType) schema
       (AREntryIdListList) entryIdList: entry ids to be retrieved
       (ARInternalIdList) idList field ids to be retrieved(optional, default = None)
  :returns: (ARBooleanList, ARFieldValueListList) (or None in case of failure)'''
        self.logger.debug('enter ARGetMultipleEntries...')
        existList = cars.ARBooleanList()
        fieldList = cars.ARFieldValueListList()
        assert isinstance(schema, str)
        assert isinstance(entryIdList, cars.AREntryIdListList)
        assert isinstance(idList, cars.ARInternalIdList) or idList is None
        self.errnr = self.arapi.ARGetMultipleEntries(byref(self.context),
                                                     schema,
                                                     my_byref(entryIdList),
                                                     my_byref(idList),
                                                     byref(existList),
                                                     byref(fieldList),
                                                     byref(self.arsl))
        if self.errnr < 2:
            return (existList, fieldList)
        else:
            self.logger.error( "ARGetMultipleEntries: failed")
            return None
        
    def ARGetMultipleExtFieldCandidates(self, schema):
        '''ARGetMultipleExtFieldCandidates Retrieves a list of all available 
external data source fields (field candidates).

Users choose the data from one of these field candidates to populate the
vendor form.
Input:  schema (ARCompoundSchema)
  :returns: a tuple of (fieldMapping, limit, dataType) (or None in case of failure)'''
        self.logger.debug('enter ARGetMultipleExtFieldCandidates...')
        fieldMapping = cars.ARFieldMappingList()
        limit = cars.ARFieldLimitList()
        dataType = cars.ARUnsignedIntList()
        self.errnr = self.arapi.ARGetMultipleExtFieldCandidates(byref(self.context),
                                                            byref(schema),
                                                            byref(fieldMapping),
                                                            byref(limit),
                                                            byref(dataType),
                                                            byref(self.arsl))
        if self.errnr < 2:
            return (fieldMapping, limit, dataType)
        else:
            self.logger.error( "ARGetMultipleExtFieldCandidates: failed")
            return None

    def ARGetMultipleFields (self, schemaString, 
                             idList=None,
                             fieldId2=None,
                             fieldName=None,
                             fieldMap=None,
                             dataType=None,
                             option=None,
                             createMode=None,
                             defaultVal=None,
                             permissions=None,
                             limit=None,
                             dInstanceList=None,
                             helpText=None,
                             timestamp=None,
                             owner=None,
                             lastChanged=None,
                             changeDiary=None):
        '''ARGetMultipleFields returns a list of the fields and their attributes.
       
ARGetMultipleFields returns list of field definitions for a specified form.
In contrast to the C APi this function constructs an ARFieldInfoList
for the form and returns all information this way.
Input: schemaString
      (optional) idList (ARInternalIdList; default: None) we currently
              expect a real ARInternalIdList, because then it's very
              easy to simply hand over the result of a GetListField
              call
      (optional) fieldId2: although it is declared optional (to be consistent
           with the AR API), this needs to be set (if not, this function will create
           an ARInternalIdList) (see the output for an explanation)
         fieldName=None (ARNameList)
         fieldMap=None (ARFieldMappingList)
         dataType=None (ARUnsignedIntList)
         option=None (ARUnsignedIntList)
         createMode=None (ARUnsignedIntList)
         defaultVal=None (ARValueList)
         permissions=None (ARPermissionListList)
         limit=None (ARFieldLimitList)
         dInstanceList=None (ARDisplayInstanceListList)
         helpText=None (ARTextStringList)
         timestamp=None (ARTimestampList)
         owner=None (ARAccessNameList)
         lastChanged=None (ARAccessNameList)
         changeDiary=None (ARTextStringList)
  :returns: ARFieldInfoList; contains entries for all ids that you handed over;
        if a field could not be retrieved, the according fieldid will be None; that's
        the only way to decide if the list could be retrieved or not!
        (all input lists should contain the return values from the server, but we
         will also create an ARFieldInfoList) or None in case of failure'''
        self.logger.debug('enter ARGetMultipleFields...')
        existList = cars.ARBooleanList()
        # fieldId2 needs to be created -- this will be the identifier for the caller, 
        # if a field could be retrieved or not!
        if fieldId2 is None:
            fieldId2 = cars.ARInternalIdList()
        self.errnr = self.arapi.ARGetMultipleFields(byref(self.context),
                                                  schemaString,
                                                  my_byref(idList),
                                                  byref(existList),
                                                  byref(fieldId2),
                                                  my_byref(fieldName),
                                                  my_byref(fieldMap),
                                                  my_byref(dataType),
                                                  my_byref(option),
                                                  my_byref(createMode),
                                                  my_byref(defaultVal),
                                                  my_byref(permissions),
                                                  my_byref(limit),
                                                  my_byref(dInstanceList),
                                                  my_byref(helpText),
                                                  my_byref(timestamp),
                                                  my_byref(owner),
                                                  my_byref(lastChanged),
                                                  my_byref(changeDiary),
                                                  byref(self.arsl))
        if idList and idList.numItems != existList.numItems:
            self.logger.error('ARGetMultipleFields returned another number of fields for form %s than expected!' % (schemaString))
#        self.logger.debug('ARGetMultipleFields returned %s' % self.errnr)
        if self.errnr < 2:
            # from what the API returns, create an ARFieldInfoList
            tempList = (cars.ARFieldInfoStruct * existList.numItems)()
            for i in range(existList.numItems):
                if existList.booleanList[i]:
                    if fieldId2:
                        tempList[i].fieldId = fieldId2.internalIdList[i]
                    if fieldName:
                        tempList[i].fieldName = fieldName.nameList[i].value
                    if timestamp:
                        tempList[i].timestamp = timestamp.timestampList[i]
                    if fieldMap:
                        tempList[i].fieldMap = fieldMap.mappingList[i]
                    if dataType:
                        tempList[i].dataType = dataType.intList[i]
                    if option:
                        tempList[i].option = option.intList[i]
                    if createMode:
                        tempList[i].createMode = createMode.intList[i]
                    if defaultVal:
                        tempList[i].defaultVal = defaultVal.valueList[i]
                    # if the user does not have admin rights, permissions will be a list of 0 items!
                    if permissions and permissions.numItems > i:
                        tempList[i].permList = permissions.permissionList[i]
                    if limit:
                        tempList[i].limit = limit.fieldLimitList[i]
                    if dInstanceList:
                        tempList[i].dInstanceList = dInstanceList.dInstanceList[i]
                    if owner:
                        tempList[i].owner = owner.nameList[i].value
                    if lastChanged:
                        tempList[i].lastChanged = lastChanged.nameList[i].value
                    if helpText:
                        tempList[i].helpText = helpText.stringList[i]
                    if changeDiary:
                        tempList[i].changeDiary = changeDiary.stringList[i]
                else:
                    self.logger.error( "ARGetMultipleFields: failed to retrieve field# %d from %s" % (
                                i, schemaString))
                    tempList[i].fieldId = None
                    tempList[i].fieldName = None
            return cars.ARFieldInfoList(existList.numItems, tempList)
        else:
            self.logger.error( "ARGetMultipleFields: failed for %s" % (
                                                schemaString))
            return None

    def ARGetMultipleLocalizedValues(self, localizedRequestList):
        '''ARGetMultipleLocalizedValues Retrieves multiple localized text 
strings from the Remedy Message Catalog.

The messages that the server retrieves depend on the user locale in the control
structure. This function performs the same action as ARGetLocalizedValues
but is easier to use and more efficient than retrieving multiple values one by
one.
Input:  (ARLocalizedRequestList) localizedRequestList 
  :returns: tuple of (localizedValueList, timestampList) 
        or None in case of failure'''
        self.logger.debug('enter ARGetMultipleLocalizedValues...')
        localizedValueList = cars.ARValueList()
        timestampList = cars.ARTimestampList()
        self.errnr = self.arapi.ARGetMultipleLocalizedValues (byref(self.context),
                                                    byref(localizedRequestList),
                                                    byref(localizedValueList),
                                                    byref(timestampList),
                                                    byref(self.arsl))
        if self.errnr < 2:
            return (localizedValueList, timestampList)
        else:
            self.logger.error( "ARGetMultipleLocalizedValues: failed")
            return None

    def ARGetMultipleSchemas(self, changedSince=0, 
                            schemaTypeList=None,
                            nameList=None, 
                            fieldIdList=None,
                            schemaList = None,
                            groupListList = None,
                            admingrpListList = None,
                            getListFieldsList = None,
                            sortListList = None,
                            indexListList = None,
                            defaultVuiList = None,
                            helpTextList = None,
                            timestampList = None,
                            ownerList = None,
                            lastChangedList = None,
                            changeDiaryList = None,
                            objPropListList = None):
        '''ARGetMultipleSchemas retrieves information about several schemas
from the server at once. Please be aware, that this function
has not been tested on V5.1!!!

This information does not include the form field definitions (see 'ARGetField'). This
function performs the same action as ARGetSchema but is easier to use and
more efficient than retrieving multiple forms one by one.
Information is returned in lists for each item, with one item in the list for
each form returned. For example, if the second item in the list for existList is
TRUE, the name of the second form is returned in the second item in the list
for schemaNameList.
Input:  (optional) changedSince (default =0), 
        (optional) schemaTypeList(default =None)
        (optional) nameList(default =None) 
        (optional) fieldIdList(default =None)
        (optional) schemaList (default = None)
        (optional) schemaInheritanceListList (default = None, # reserved for future use)
        (optional) groupListList (default = None)
        (optional) admingrpListList (default = None)
        (optional) getListFieldsList (default = None)
        (optional) sortListList (default = None)
        (optional) indexListList (default = None)
        (optional) defaultVuiList (default = None)
        (optional) helpTextList (default = None)
        (optional) timestampList (default = None)
        (optional) ownerList (default = None)
        (optional) lastChangedList (default = None)
        (optional) changeDiaryList (default = None)
        (optional) objPropListList (default = None)
  :returns: ARSchemaList (or None in case of failure)'''
        self.logger.debug('enter ARGetMultipleSchemas...')
        existList = cars.ARBooleanList()
        schemaNameList = cars.ARNameList()
        self.errnr = self.arapi.ARGetMultipleSchemas(byref(self.context),
                                                     changedSince, 
                                                     my_byref(schemaTypeList),
                                                     my_byref(nameList), 
                                                     my_byref(fieldIdList),
                                                     my_byref(existList),
                                                     my_byref(schemaNameList),
                                                     my_byref(schemaList),
                                                     my_byref(groupListList),
                                                     my_byref(admingrpListList),
                                                     my_byref(getListFieldsList),
                                                     my_byref(sortListList),
                                                     my_byref(indexListList),
                                                     my_byref(defaultVuiList),
                                                     my_byref(helpTextList),
                                                     my_byref(timestampList),
                                                     my_byref(ownerList),
                                                     my_byref(lastChangedList),
                                                     my_byref(changeDiaryList),
                                                     my_byref(objPropListList),
                                                     byref(self.arsl))
        if self.errnr > 1:
            self.logger.error('ARGetMultipleSchemas: failed')
            return None
        else:
            tempArray = (ARSchema * existList.numItems)()
            for i in range(existList.numItems):
                if existList.booleanList[i]:
                    tempArray[i].name = schemaNameList.nameList[i].value
                    if schemaList: tempArray[i].schema = schemaList.compoundSchema[i]
                    if groupListList: tempArray[i].groupList = groupListList.permissionList[i]
                    if admingrpListList: tempArray[i].admingrpList = admingrpListList.internalIdListList[i]
                    if getListFieldsList: tempArray[i].getListFields = getListFieldsList.listFieldList[i]
                    if indexListList: tempArray[i].sortList = sortListList.sortListList[i]
                    if indexListList: tempArray[i].indexList = indexListList.indexListList[i]
                    if defaultVuiList: tempArray[i].defaultVui = defaultVuiList.nameList[i].value
                    if helpTextList: tempArray[i].helpText = helpTextList.stringList[i]
                    if timestampList: tempArray[i].timestamp = timestampList.timestampList[i]
                    if ownerList: tempArray[i].owner = ownerList.nameList[i].value
                    if lastChangedList: tempArray[i].lastChanged = lastChangedList.nameList[i].value
                    if changeDiaryList: tempArray[i].changeDiary = changeDiaryList.stringList[i]
                    if objPropListList: tempArray[i].objPropList = objPropListList.propsList[i]
                else:
                    self.logger.error('ARGetMultipleSchemas: "%s" does not exist!' % nameList.nameList[i].value)
            return ARSchemaList(existList.numItems, tempArray)

    def ARGetSchema (self, name):
        '''ARGetSchema returns all information about a schema.
        
This information does not include the form's field
definitions (see 'ARGetField').
Input: string (schema)
  :returns: ARSchema (containing: schema, groupList, admingrpList,
                getListFields, sortList, indexList,
                defaultVui, helpText, timestamp, owner,
                lastChanged, changeDiary, objPropList) or None in case of failure'''
        self.logger.debug('enter ARGetSchema...')
        if name.strip() == '':
            self.logger.error('ARGetSchema: no schema name given')
            self.errnr = 2
            return None
        schema = cars.ARCompoundSchema()
        groupList = cars.ARPermissionList()
        admingrpList = cars.ARInternalIdList()
        getListFields = cars.AREntryListFieldList()
        sortList = cars.ARSortList()
        indexList = cars.ARIndexList()
        defaultVui = cars.ARNameType()
        helpText = c_char_p()
        timestamp = cars.ARTimestamp()
        owner = cars.ARAccessNameType()
        lastChanged = cars.ARAccessNameType()
        changeDiary = c_char_p()
        objPropList = cars.ARPropList()
        self.errnr = self.arapi.ARGetSchema (byref(self.context),
                                             name,
                                             byref(schema),
                                             byref(groupList),
                                             byref(admingrpList),
                                             byref(getListFields),
                                             byref(sortList),
                                             byref(indexList),
                                             defaultVui,
                                             byref(helpText),
                                             byref(timestamp),
                                             owner,
                                             lastChanged,
                                             byref(changeDiary),
                                             byref(objPropList),
                                             byref(self.arsl))
        if self.errnr < 2:
            return ARSchema(name,
                            schema,
                            groupList,
                            admingrpList,
                            getListFields,
                            sortList,
                            indexList,
                            defaultVui.value,
                            helpText,
                            timestamp,
                            owner.value,
                            lastChanged.value,
                            changeDiary,
                            objPropList)
        else:
            self.logger.error( "ARGetSchema: failed for schema %s" % name)
            return None
        
    def ARGetServerInfo(self, requestList):
        '''ARGetServerInfo retrieves the requested configuration information.
        
Input:  ARServerInfoRequestList
  :returns: ARServerInfoList (or None in case of failure)'''
        self.logger.debug('enter ARGetServerInfo...')
        serverInfo = cars.ARServerInfoList()
        self.errnr = self.arapi.ARGetServerInfo(byref(self.context),
                                                byref(requestList),
                                                byref(serverInfo),
                                                byref(self.arsl))
        if self.errnr < 2:
            return serverInfo
        else:
            self.logger.error( "ARGetServerInfo: failed")
            return None

    def ARGetSessionConfiguration(self, variableId):
        '''ARGetSessionConfiguration retrieves a public API session variable.
        
Input:  variableId
  :returns: ARValueStruct (or None in case of failure)'''
        self.logger.debug('enter ARGetSessionConfiguration...')
        variableValue = cars.ARValueStruct()
        self.errnr = self.arapi.ARGetSessionConfiguration(byref(self.context),
                                                          variableId,
                                                          byref(variableValue),
                                                          byref(self.arsl))
        if self.errnr < 2:
            return variableValue
        else:
            self.logger.error( "ARGetSessionConfiguration: failed")
            return None

    def ARGetServerStatistics (self, requestList):
        '''ARGetServerStatistics returns the requested statistics.

The counts returned
generally represent the number of occurrences since starting the server. If a
statistic reaches the maximum value for a long integer, the system resets the
counter and begins incrementing again.
Input: ARServerInfoRequestList
  :returns: ARServerInfoList (or None in case of failure)'''
        self.logger.debug('enter ARGetServerStatistics...')
        serverInfo = cars.ARServerInfoList()
        self.errnr = self.arapi.ARGetServerStatistics(byref(self.context),
                                                      byref(requestList),
                                                      byref(serverInfo),
                                                      byref(self.arsl))
        
        if self.errnr < 2:
            return serverInfo
        else:
            self.logger.error( "ARGetServerStatistics: failed")
            return None

    def ARGetSupportFile(self, fileType, 
                         name, 
                         id2, 
                         fileId, 
                         filePtr):
        '''ARGetSupportFile retrieves a file supporting external reports.
        
Input:  fileType, 
         name, 
         id2, 
         fileId, 
         filePtr
  :returns: timestamp (or None in case of failure)'''
        self.logger.debug('enter ARGetSupportFile...')
        self.errnr = 0
        raise pyARSNotImplemented

    def ARGetTextForErrorMessage(self, msgId):
        '''ARGetTextForErrorMessage Retrieves the message text for the 
specified error from the local catalog

The length of the text is limited by AR_MAX_MESSAGE_SIZE
(255 bytes).
Input:  msgId
  :returns: String with the (localized) error message (or None in case 
        of failure)'''
        self.logger.debug('enter ARGetTextForErrorMessage...')
        self.errnr = 0
        pointer = self.arapi.ARGetTextForErrorMessage (msgId)
        if self.errnr < 2:
            return c_char_p(pointer).value
#            text = c_char_p(pointer)
#            return text.value
        else:
            self.logger.error('ARGetTextForErrorMessage failed')
            return None

    def ARGetVUI(self, schema, vuiId):
        '''ARGetVUI retrieves information about the form view (VUI) with the indicated ID
        
Input:  schema: name of schema
        vuiId: internalId
  :returns: ARVuiInfoStruct (or None in case of failure)'''
        self.logger.debug('enter ARGetVUI...')
        vuiName = cars.ARNameType()
        locale = cars.ARLocaleType()
        vuiType = c_uint()
        dPropList = cars.ARPropList()
        helpText = c_char_p()
        timestamp = cars.ARTimestamp()
        owner = cars.ARAccessNameType()
        lastChanged = cars.ARAccessNameType()
        changeDiary = c_char_p()
        self.errnr = self.arapi.ARGetVUI (byref(self.context),
                                          schema,
                                          vuiId,
                                          vuiName,
                                          locale,
                                          byref(vuiType),
                                          byref(dPropList),
                                          byref(helpText),
                                          byref(timestamp),
                                          owner,
                                          lastChanged,
                                          byref(changeDiary),
                                          byref(self.arsl))
        if self.errnr < 2:
            return cars.ARVuiInfoStruct(vuiId,
                                        vuiName.value,
                                        timestamp,
                                        dPropList,
                                        owner.value,
                                        locale.value,
                                        vuiType,
                                        lastChanged.value,
                                        helpText.value,
                                        changeDiary.value)
        else:
            self.logger.error( "ARGetVUI: failed")
            return None

    def ARImport(self,  structItems, 
                 importBuf, 
                 importOption=cars.AR_IMPORT_OPT_CREATE):
        '''ARImport imports the indicated structure definitions to the specified server.

Use this function to copy structure definitions from one AR System server to another.
Input:  structItems
        importBuf
        optional: importOption (Default=cars.AR_IMPORT_OPT_CREATE)
  :returns: errnr'''
        self.logger.debug('enter ARImport...')
        self.errnr = self.arapi.ARImport(byref(self.context),
                                         byref(structItems),
                                         importBuf,
                                         importOption,
                                         byref(self.arsl))
        return self.errnr

    def ARInitialization(self):
        '''ARInitialization performs server- and network-specific
initialization operations for each Action Request
System session.

Input:  
  :returns: errnr'''
        self.logger.debug('enter ARInitialization...')
        self.errnr =  self.arapi.ARInitialization(byref(self.context),
                                                  byref(self.arsl))
        if self.errnr > 1:
            self.logger.error( "ARInitialization: failed")
        return self.errnr

    def ARJulianDateToDate(self, jd):
        '''ARJulianDateToDate converts a Julian date to a year, month, and day value.

The Julian date is the
number of days since noon, Universal Time, on January 1, 4713 BCE (on the
Julian calendar). The changeover from the Julian calendar to the Gregorian
calendar occurred in October, 1582. The Julian calendar is used for dates on
or before October 4, 1582. The Gregorian calendar is used for dates on or
after October 15, 1582.
Input:  integer
  :returns: ARDateStruct (or None in case of failure)'''
        self.logger.debug('enter ARJulianDateToDate...')
        date = cars.ARDateStruct()
        self.errnr = self.arapi.ARJulianDateToDate(byref(self.context),
                                                   jd,
                                                   byref(date),
                                                   byref(self.arsl))
        if self.errnr < 2:
            return date
        else:
            self.logger.error( "ARJulianDateToDate: failed")
            return None

    def ARLoadARQualifierStruct(self, schema, 
                                qualString, 
                                displayTag=None):
        '''ARLoadARQualifierStruct loads the specified qualification string.

Loads the specified qualification string ARQualifierStruct structure. This function
qualifications in the required format.
Input:  schema
        qualString: containing the qualification to load (following the syntax
                        rules for entering qualifications in the AR System Windows 
                        User Tool query bar).
        displayTag: name of the form view (VUI) to use for resolving field names.
  :returns: ARQualifierStruct (or None in case of failure)'''
        self.logger.debug('enter ARLoadARQualifierStruct...')
        qualifier = cars.ARQualifierStruct()
        self.errnr = self.arapi.ARLoadARQualifierStruct(byref(self.context),
                                                        schema,
                                                        displayTag,
                                                        qualString,
                                                        byref(qualifier),
                                                        byref(self.arsl))  
        if self.errnr < 2:
            return qualifier
        else:
            self.logger.error( "ARLoadARQualifierStruct: failed")
            return None

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
        '''Login returns a context that has already been validated.

Input: server (can be specified as hostname:tcpport)
       username
       password
       (optional) language (default: '')
       (optional) authString (default: '')
       (optional) tcpport (default: 0)
       (optional) rpcnumber (default: 0)
       (optional) cacheId (default: 0)
       (optional) operationTime (default: 0)
       (optional) sessionId (default: 0)
  :returns: control record (or None in case of failure)'''
        self.logger.debug('enter Login...')
        self.errnr = 0
        # look for a ':' in the hostname; if you find it, split off the
        # port number
        originalServer = server
        if server.find(':') > -1:
            server,tcpport = server.split(':')
            tcpport = int(tcpport)

        if language.lower() == 'utf-8':
            (self.oldCharset, self.oldErrorhandling) = set_conversion_mode('utf-8', 
                                                                           'strict')
        # setup the context
        self.context = cars.ARControlStruct(cacheId,
                                            operationTime,
                                            username,
                                            password,
                                            language,
                                            sessionId,
                                            authString,
                                            server)
        # self.arsl = cars.ARStatusList()
        # initialize the API
        self.errnr = self.arapi.ARInitialization (byref(self.context),
                                                  byref(self.arsl))
        if self.errnr > 1:
            self.logger.error('Login: error during Initialization')
            return None
        if server == '':
            serverList = self.ARGetListServer()
            if serverList is None or serverList.numItems == 0:
                self.logger.error('no server name given, serverList is empty')
                return None
            server = serverList.nameList[0].value
            self.logger.error('no server name given, selected %s as server' % (
                server))
            self.ARFree(serverList)

        self.logger.debug('calling ARSetServerPort with %s:%d' % (server, tcpport))
        self.errnr = self.ARSetServerPort(server, tcpport, rpcnumber)
        if self.errnr > 1:
            self.logger.error('ARSetServerPort failed, still trying to login!') 
            pass
        adminFlag = cars.ARBoolean()
        subAdminFlag = cars.ARBoolean()
        customFlag = cars.ARBoolean()
        self.errnr = self.arapi.ARVerifyUser (byref(self.context),
                                              byref(adminFlag),
                                              byref(subAdminFlag),
                                              byref(customFlag),
                                              byref(self.arsl))
        if self.errnr < 2:
            return self.context
        else:
            self.logger.error('error logging in to: %s as %s' % (
                                originalServer, 
                                username))
            return None
        
    def Logoff (self):
        '''Logoff ends the session with the Remedy server.

Input: 
  :returns: errnr'''
        self.logger.debug('enter Logoff...')
        if self.context:
            self.errnr = self.arapi.ARTermination(byref(self.context),
                                                  byref(self.arsl))
            if self.errnr > 1:
                self.logger.error( "Logoff: failed")
        return self.errnr

    def ARMergeEntry(self, 
                     schema,
                     fieldList,
                     mergeType = cars.AR_MERGE_ENTRY_DUP_ERROR):
        '''ARMergeEntry merges an existing database entry into the indicated form.

You can merge entries into base forms only. To add entries to join
forms, merge them into one of the underlying base forms.
Input:  (ARNameType) schema,
        (ARFieldValueList) fieldList
        (c_uint) mergeType (optional, default: AR_MERGE_ENTRY_DUP_ERROR)
  :returns: entryId (or None in case of failure)'''
        self.logger.debug('enter ARMergeEntry...')
        entryId = cars.AREntryIdType()
        self.errnr = self.arapi.ARMergeEntry(byref(self.context),
                                             schema,
                                             my_byref(fieldList),
                                             mergeType,
                                             entryId,
                                             byref(self.arsl))
        if self.errnr > 1:
            self.logger.error( "ARMergeEntry: failed for schema %s" % schema)
            return None
        else:
            return entryId.value

    def ARRegisterForAlerts(self, clientPort, 
                            registrationFlags=0):
        '''ARRegisterForAlerts registers the specified user with the AR System 
server to receive alerts.
        
Input:  (c_int) clientPort 
        (c_uint) registrationFlags (optional; reserved for future use and should be set to zero.)
  :returns: errnr'''
        self.logger.debug('enter ARRegisterForAlerts...')
        self.errnr = self.arapi.ARRegisterForAlerts(byref(self.context),
                                                    clientPort,
                                                    registrationFlags,
                                                    byref(self.arsl))
        if self.errnr > 1:
            self.logger.error( "ARRegisterForAlerts: failed for port %s" % clientPort)
        return self.errnr

    def ARSetActiveLink(self, name, 
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
        '''ARSetActiveLink updates the active link.

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
  :returns: errnr'''
        self.logger.debug('enter ARSetActiveLink...')
        if order is not None and not isinstance(order, c_uint):
            order = c_uint(order)
        if executeMask is not None and not isinstance(executeMask, c_uint):
            executeMask = c_uint(executeMask)
        if controlField is not None and not isinstance(controlField, c_uint):
            controlField = cars.ARInternalId(controlField)
        if focusField is not None and not isinstance(focusField, c_uint):
            focusField = cars.ARInternalId(focusField)
        if enable is not None and not isinstance(enable, c_uint):
            enable = c_uint(enable)
        self.errnr = self.arapi.ARSetActiveLink(byref(self.context),
                                                name, 
                                                newName, 
                                                my_byref(order), 
                                                my_byref(workflowConnect),
                                                my_byref(groupList),
                                                my_byref(executeMask),
                                                my_byref(controlField),
                                                my_byref(focusField),
                                                my_byref(enable),
                                                my_byref(query),
                                                my_byref(actionList),
                                                my_byref(elseList),
                                                helpText,
                                                owner,
                                                changeDiary,
                                                my_byref(objPropList),
                                                byref(self.arsl))
        if self.errnr > 1:
            self.logger.error('ARSetActiveLink: failed for %s' % name)
        return self.errnr

    def ARSetCharMenu(self, 
                      name, 
                      newName = None, 
                      refreshCode = None, 
                      menuDefn = None, 
                      helpText = None, 
                      owner = None,
                      changeDiary = None, 
                      objPropList = None):
        '''ARSetCharMenu updates the character menu.

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
  :returns: errnr'''
        self.logger.debug('enter ARSetCharMenu...')
        if refreshCode is not None and not isinstance(refreshCode, c_uint):
            refreshCode = c_uint(refreshCode)
        self.errnr = self.arapi.ARSetCharMenu(byref(self.context),
                                              name,
                                              newName, 
                                              my_byref(refreshCode), 
                                              my_byref(menuDefn), 
                                              helpText, 
                                              owner,
                                              changeDiary, 
                                              my_byref(objPropList),
                                              byref(self.arsl))
        if self.errnr > 1:
            self.logger.error('ARSetCharMenu failed for old: %s/new: %s' % (name,
                              newName))
        return self.errnr 

    def ARSetContainer(self, name,
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
                       objPropList = None):
        '''ARSetContainer updates the definition for the container.
        
Input:  name
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
  :returns: errnr'''
        self.logger.debug('enter ARSetContainer...')
        if type_ is not None and not isinstance(type_, c_uint):
            type_ = c_uint(type_)
        self.errnr = self.arapi.ARSetContainer(byref(self.context),
                                               name,
                                               newName,
                                               my_byref(groupList),
                                               my_byref(admingrpList),
                                               my_byref(ownerObjList),
                                               my_byref(label),
                                               my_byref(description),
                                               my_byref(type_),
                                               my_byref(references),
                                               removeFlag,
                                               helpText,
                                               owner,
                                               changeDiary,
                                               my_byref(objPropList),
                                               byref(self.arsl))
        if self.errnr > 1:
            self.logger.error("ARSetContainer: failed for %s" % name)
        return self.errnr

    def ARSetEntry(self, schema, 
                   entryIdList, 
                   fieldList, 
                   getTime = 0, 
                   option = None):
        '''ARSetEntry updates the form entry with the indicated ID on the 
specified server.

Input:  schema
        entryId: AREntryIdList
        fieldList: ARFieldValueList
        (optional) getTime (the server compares this value with the 
                    value in the Modified Date core field to
                    determine whether the entry has been changed 
                    since the last retrieval.)
        (optional) option (for join forms only; can be AR_JOIN_SETOPTION_NONE
                    or AR_JOIN_SETOPTION_REF)
  :returns: errnr'''
        self.logger.debug('enter ARSetEntry...')
        self.errnr = self.arapi.ARSetEntry (byref (self.context),
                                            schema,
                                            byref(entryIdList),
                                            byref(fieldList),
                                            getTime,
                                            option,
                                            byref(self.arsl))
        if self.errnr > 1:
            self.logger.error("ARSetEntry: failed")
        return self.errnr

    def ARSetEscalation(self, name, 
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
        '''ARSetEscalation updates the escalation.

The changes are added to the server immediately and returned to users who
request information about escalations.
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
  :returns: errnr'''
        self.logger.debug('enter ARSetEscalation...')
        if enable is not None and not isinstance(enable, c_uint):
            enable = c_uint(enable)
        self.errnr = self.arapi.ARSetEscalation(byref(self.context),
                                                name, 
                                                newName,
                                                my_byref(escalationTm), 
                                                my_byref(schemaList), 
                                                my_byref(enable), 
                                                my_byref(query), 
                                                my_byref(actionList),
                                                my_byref(elseList), 
                                                helpText, 
                                                owner, 
                                                changeDiary, 
                                                my_byref(objPropList),
                                                byref(self.arsl))
        if self.errnr > 1:
            self.logger.error('ARSetEscalation failed for %s' % name)
        return self.errnr

    def ARSetField(self, schema, 
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
        '''ARSetField updates the definition for the form field.
        
Input: schema, 
       fieldId, 
       (optional) fieldName = None, 
       (optional) fieldMap = None, 
       (optional) option = None, 
       (optional) createMode = None, 
       (optional) defaultVal = None,
       (optional) permissions = None, 
       (optional) limit = None, 
       (optional) dInstanceList = None, 
       (optional) helpText = None, 
       (optional) owner = None, 
       (optional) changeDiary = None
  :returns: errnr'''
        self.logger.debug('enter ARSetField...')
        if option is not None and not isinstance(option, c_uint):
            option = c_uint(option)
        if createMode is not None and not isinstance(createMode, c_uint):
            createMode = c_uint(createMode)
        self.errnr = self.arapi.ARSetField(byref(self.context),
                                           schema, 
                                           fieldId,
                                           fieldName, 
                                           my_byref(fieldMap), 
                                           my_byref(option), 
                                           my_byref(createMode), 
                                           my_byref(defaultVal),
                                           my_byref(permissions), 
                                           my_byref(limit), 
                                           my_byref(dInstanceList), 
                                           helpText, 
                                           owner, 
                                           changeDiary,
                                           byref(self.arsl))
        if self.errnr > 1:
            self.logger.error('ARSetField: failed for %s:%d' % (schema,fieldId))
        return self.errnr

    def ARSetFilter(self, name, 
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
        '''ARSetFilter updates the filter.

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
  :returns: errnr'''
        self.logger.debug('enter ARSetFilter...')
        if order is not None and not isinstance(order, c_uint):
            order = c_uint(order)
        if opSet is not None and not isinstance(opSet, c_uint):
            opSet = c_uint(opSet)
        if enable is not None and not isinstance(enable, c_uint):
            enable = c_uint(enable)
        self.errnr = self.arapi.ARSetFilter(byref(self.context),
                                            name, 
                                            newName,
                                            my_byref(order),
                                            my_byref(workflowConnect),
                                            my_byref(opSet),
                                            my_byref(enable),
                                            my_byref(query),
                                            my_byref(actionList),
                                            my_byref(elseList),
                                            helpText,
                                            owner,
                                            changeDiary,
                                            my_byref(objPropList),
                                            byref(self.arsl))
        if self.errnr > 1:
            self.logger.error('ARSetFilter: failed for %s' % name)
        return self.errnr

    def ARSetFullTextInfo(self, fullTextInfo):
        '''ARSetFullTextInfo updates the indicated FTS information

Note: Full text search (FTS) is documented for backward compatibility only,
and is not supported in AR System 6.3.
Input:  fullTextInfo
  :returns: errnr'''
        self.logger.debug('enter ARSetFullTextInfo...')
        self.errnr = self.arapi.ARSetFullTextInfo(byref(self.context),
                                                  my_byref(fullTextInfo),
                                                  byref(self.arsl))
        if self.errnr > 1:
            self.logger.error('ARSetFullTextInfo: failed')
        return self.errnr

    def ARSetLogging(self, 
                   logTypeMask = cars.AR_DEBUG_SERVER_NONE, 
                   whereToWriteMask = cars.AR_WRITE_TO_STATUS_LIST, 
                   file_ = None):
        '''ARSetLogging activates and deactivates client-side logging of server activity.
        
Input:  (optional) logTypeMask:  what to log (default: nothing)
        (optional) whereToWriteMask: to log file or (default) status list
        (optional) file_: FileHandle (default: None)
  :returns: errnr'''
        self.logger.debug('enter ARSetLogging...')
#        logType = c_ulong(logTypeMask)
#        whereToWrite = c_ulong(whereToWriteMask)
        self.errnr = self.arapi.ARSetLogging (byref(self.context),
                                              logTypeMask,
                                              whereToWriteMask,
                                              my_byref(file_),
                                              byref(self.arsl))
        if self.errnr > 1:
            self.logger.error('ARSetLogging: failed')
        return self.errnr

    def ARSetSchema(self, name,
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
        '''ARSetSchema updates the definition for the form.

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
  :returns: errnr'''
        self.logger.debug('enter ARSetSchema...')
        self.errnr = self.arapi.ARSetSchema(byref(self.context),
                                            name,
                                            newName,
                                            my_byref(schema),
                                            my_byref(groupList),
                                            my_byref(admingrpList),
                                            my_byref(getListFields),
                                            my_byref(sortList),
                                            my_byref(indexList),
                                            defaultVui,
                                            helpText,
                                            owner,
                                            changeDiary,
                                            my_byref(objPropList),
                                            byref(self.arsl))
        if self.errnr > 1:
            self.logger.error('ARSetSchema failed for schema %s' % (name))
        return self.errnr 

    def ARSetServerInfo(self, serverInfo):
        '''ARSetServerInfo updates the indicated configuration information.
        
Input:  serverInfo (ARServerInfoList)
  :returns: errnr'''
        self.logger.debug('enter ARSetServerInfo...')
        self.errnr = self.arapi.ARSetServerInfo(byref(self.context),
                                                my_byref(serverInfo),
                                                byref(self.arsl))
        if self.errnr > 1:
            self.logger.error('ARSetServerInfo: failed')
        return self.errnr

    def ARSetServerPort(self, server, 
                        port = 0, 
                        rpcProgNum = 0):
        '''ARSetServerPort specifies the port.
        
ARSetServerPort specifies the port that your program will use to communicate with the
AR System server and whether to use a private server.
        
Input:  server
        (optional) port
        (optional) rpcProgNum
  :returns: errnr'''
        self.logger.debug('enter ARSetServerPort...')
        self.errnr = self.arapi.ARSetServerPort(byref(self.context),
                                                server,
                                                port,
                                                rpcProgNum,
                                                byref(self.arsl))
        if self.errnr > 1:
            self.logger.error('ARSetServerPort: failed')
        return self.errnr

    def ARSetSessionConfiguration(self,
                                  variableId,
                                  variableValue):
        '''ARSetSessionConfiguration sets an API session variable.
        
Input:  variableId (c_uint),
        variableValue (ARValueStruct)
  :returns: errnr'''
        self.logger.debug('enter ARSetSessionConfiguration...')
        self.errnr = self.arapi.ARSetSessionConfiguration(byref(self.context),
                                                          variableId,
                                                          my_byref(variableValue),
                                                          byref(self.arsl))
        if self.errnr > 1:
            self.logger.error('ARSetSessionConfiguration: failed')
        return self.errnr

    def ARSetSupportFile(self, 
                         fileType, 
                        name, 
                        id2, 
                        fileId, 
                        filePtr):
        '''ARSetSupportFile sets a support file in the AR System.
        
Input:  fileType, 
        name, 
        id2, 
        fileId, 
        filePtr
  :returns: errnr'''
        self.logger.debug('enter ARSetSupportFile...')
        self.errnr = self.arapi.ARSetSupportFile(byref(self.context),
                                                    fileType, 
                                                    name, 
                                                    id2, 
                                                    fileId, 
                                                    byref(filePtr), 
                                                    byref(self.arsl))
        if self.errnr > 1:
            self.logger.error('ARSetSupportFile failed ')
        return self.errnr


    def ARSetVUI(self, schema, 
                 vuiId, 
                 vuiName = None, 
                 locale = None, 
                 vuiType=None,
                 dPropList=None, 
                 helpText=None, 
                 owner=None, 
                 changeDiary=None):
        '''ARSetVUI updates the form view (VUI).
        
Input: schema, 
       vuiId, 
       (optional) vuiName = None, 
       (optional) locale = None, 
       (optional) vuiType=None,
       (optional) dPropList=None, 
       (optional) helpText=None, 
       (optional) owner=None, 
       (optional) changeDiary=None
  :returns: errnr'''
        self.logger.debug('enter ARSetVUI...')
        if vuiType is not None and not isinstance(vuiType, c_uint):
            vuiType = c_uint(vuiType)
        self.errnr = self.arapi.ARSetVUI(byref(self.context),
                                            schema,
                                            vuiId, 
                                            vuiName, 
                                            locale, 
                                            my_byref(vuiType),
                                            my_byref(dPropList), 
                                            helpText, 
                                            owner, 
                                            changeDiary,
                                            byref(self.arsl))
        if self.errnr > 1:
            self.logger.error('ARSetVUI: failed for schema: %s/vui %s' % (schema, vuiId))
        return self.errnr

    def ARSignal(self, signalList):
        '''ARSignal causes the server to reload information.
        
Input:  (ARSignalList) signalList 
  :returns: errnr'''
        self.logger.debug('enter ARSignal...')
        self.errnr = self.arapi.ARSignal(byref(self.context),
                                         my_byref(signalList),
                                         byref(self.arsl))
        
        if self.errnr > 1:
            self.logger.error('ARSignal: failed')
        return self.errnr

    def ARTermination(self):
        '''ARTermination disconnects from the server.

Performs environment-specific cleanup routines and disconnects from the
specified AR System session. All API programs that interact with the
AR System should call this function upon completing work in a given
session. Calling this function is especially important in environments that
use floating licenses. If you do not disconnect from the server, your license
token is unavailable for other users for the defined time-out interval.
Input:
  :returns: errnr'''
        self.logger.debug('enter ARTermination...')
        self.errnr = 0
        if self.context != None:
            self.errnr = self.arapi.ARTermination(byref(self.context),
                                                  byref(self.arsl))
        self.context = None
        return self.errnr
        
    def ARValidateFormCache(self, form, 
                            mostRecentActLink = 0, 
                            mostRecentMenu = 0, 
                            mostRecentGuide = 0):
        '''ARValidateFormCache retrieves key information from a cached definition.

Retrieves key information from a cached definition (such as form name,
form change time, active link change time, active link guide change time, and
menu change time) and returns information about any changes to the
definition given this information. This function call also returns information
about updates to the current user performing a test. This information causes
the cache to reload to insure accurate definitions.
This call is intended to allow Remedy User to gather all the data that is needed
to validate its local cache for a form in a single call.
Input:  form
        (ARTimestamp) mostRecentActLink (optional, default = 0)
        (ARTimestamp) mostRecentMenu (optional, default = 0)
        (ARTimestamp) mostRecentGuide (optional, default = 0)
  :returns: tuple of (formLastModified, numActLinkOnForm, numActLinkSince, menuSinceList
            groupsLastChanged, userLastChanged, guideSinceList)
            or None in case of failure'''
        self.logger.debug('enter ARValidateFormCache...')
        formLastModified = cars.ARTimestamp()
        numActLinkOnForm = c_int()
        numActLinkSince = c_int()
        menuSinceList = cars.ARNameList()
        groupsLastChanged = cars.ARTimestamp()
        userLastChanged = cars.ARTimestamp()
        guideSinceList = cars.ARNameList()
        self.errnr = self.arapi.ARValidateFormCache(byref(self.context),
                                        form,
                                        mostRecentActLink, 
                                        mostRecentMenu, 
                                        mostRecentGuide,
                                        byref(formLastModified),
                                        byref(numActLinkOnForm),
                                        byref(numActLinkSince),
                                        byref(menuSinceList),
                                        byref(groupsLastChanged),
                                        byref(userLastChanged),
                                        byref(guideSinceList),
                                        byref(self.arsl))
        if self.errnr < 2:
            return (formLastModified.value, 
                    numActLinkOnForm.value, 
                    numActLinkSince.value, 
                    menuSinceList,
                    groupsLastChanged.value, 
                    userLastChanged.value, 
                    guideSinceList)
        else:
            self.logger.error('ARValidateFormCache: failed')
            return None

    def ARValidateLicense(self, licenseType):
        '''ARValidateLicense confirms whether the current server holds a 
valid license of the specified type.
        
Input:  (ARLicenseNameType) licenseType 
  :returns: ARLicenseValidStruct (or None in case of failure)'''
        self.logger.debug('enter ARValidateLicense...')
        licenseValid = cars.ARLicenseValidStruct()
        self.errnr = self.arapi.ARValidateLicense(byref(self.context),
                                    licenseType,
                                    byref(licenseValid),
                                    byref(self.arsl))
        if self.errnr < 2:
            return licenseValid
        else:
            self.logger.error('ARValidateLicense: failed')
            return None

    def ARValidateMultipleLicenses(self, licenseTypeList):
        '''ARValidateMultipleLicenses checks whether the current server holds a license for several specified license
types. This function performs the same action as ARValidateLicense, but it is easier
to use and more efficient than validating licenses one by one.

Input:  (ARLicenseNameList) licenseTypeList 
  :returns: ARLicenseValidList or None in case of failure'''
        self.logger.debug('enter ARValidateMultipleLicenses...')
        licenseValidList = cars.ARLicenseValidList()
        self.errnr = self.arapi.ARValidateMultipleLicense(byref(self.context),
                                    byref(licenseTypeList),
                                    byref(licenseValidList),
                                    byref(self.arsl))
        if self.errnr < 2:
            return licenseValidList
        else:
            self.logger.error('ARValidateMultipleLicense: failed')
            return None

    def ARVerifyUser(self):
        '''ARVerifyUser checks the cache on the specified server
to determine whether the specified user is registered
with the current server. 
        
Input:  
  :returns: tuple of (adminFlag, subAdminFlag, customFlag) 
        or None in case of failure'''
        self.logger.debug('enter ARVerifyUser...')
        adminFlag = cars.ARBoolean()
        subAdminFlag = cars.ARBoolean()
        customFlag = cars.ARBoolean()
        self.errnr = self.arapi.ARVerifyUser(byref(self.context),
                                  byref(adminFlag),
                                  byref(subAdminFlag),
                                  byref(customFlag),
                                  byref(self.arsl))
        if self.errnr < 2:
            return (adminFlag.value and True or False, 
                    subAdminFlag and True or False, 
                    customFlag and True or False)
        else:
            self.logger.error('ARVerifyUser: failed')
            return None
###########################################################################
#
#
# XML support functions
#
#

    def ARGetActiveLinkFromXML(self, parsedStream, 
                               activeLinkName):
        '''ARGetActiveLinkFromXML retrieves an active link from an XML document.

Input: parsedStream
       activeLinkName
  :returns: (ARActiveLinkStruct, supportFileList, arDocVersion) or None
        in case of failure'''
        self.logger.debug('enter ARGetActiveLinkFromXML...')
        self.errnr = 0
        order = c_uint()
        schemaList = cars.ARWorkflowConnectStruct()
        groupList = cars.ARInternalIdList()
        executeMask = c_uint()
        controlField = cars.ARInternalId()
        focusField = cars.ARInternalId()
        enable = c_uint()
        query = cars.ARQualifierStruct()
        actionList = cars.ARActiveLinkActionList()
        elseList = cars.ARActiveLinkActionList()
        supportFileList = cars.ARSupportFileInfoList()
        helpText = c_char_p()
        modifiedDate = cars.ARTimestamp()
        owner = cars.ARAccessNameType()
        lastChanged = cars.ARAccessNameType()
        changeDiary = c_char_p()
        objPropList = cars.ARPropList()
        arDocVersion = c_uint()
        self.errnr = self.arapi.ARGetActiveLinkFromXML(byref(self.context),
                                                        my_byref(parsedStream),
                                                          activeLinkName,
                                                          byref(order),
                                                          byref(schemaList),
                                                          byref(groupList),
                                                          byref(executeMask),
                                                          byref(controlField),
                                                          byref(focusField),
                                                          byref(enable),
                                                          byref(query),
                                                          byref(actionList),
                                                          byref(elseList),
                                                          byref(supportFileList),
                                                          owner,
                                                          lastChanged,
                                                          byref(modifiedDate),
                                                          byref(helpText),
                                                          byref(changeDiary),
                                                          byref(objPropList),
                                                          byref(arDocVersion),
                                                          byref(self.arsl))
        if self.errnr < 2:
            return (ARActiveLinkStruct(activeLinkName,
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
                                    modifiedDate,
                                    owner.value,
                                    lastChanged.value,
                                    changeDiary,
                                    objPropList), supportFileList, arDocVersion)
        else:
            self.logger.error('ARGetActiveLinkFromXML: failed for %s' % activeLinkName)
            return None

    def ARGetContainerFromXML(self, parsedStream, containerName):
        '''ARGetContainerFromXML retrieves containers from an XML document.

Input: parsedStream, 
    containerName
  :returns: (ARContainerStruct, arDocVersion) or None in case of failure'''
        self.logger.debug('enter ARGetContainerFromXML...')
        self.errnr = 0
        groupList = cars.ARPermissionList()
        admingrpList = cars.ARInternalIdList()
        ownerObjList = cars.ARContainerOwnerObjList()
        label = c_char_p()
        description = c_char_p()
        type_ = c_uint()
        references = cars.ARReferenceList()
        helpText = c_char_p()
        owner = cars.ARAccessNameType()
        timestamp = cars.ARTimestamp()
        lastChanged = cars.ARAccessNameType()
        changeDiary = c_char_p()
        objPropList = cars.ARPropList()
        arDocVersion = c_uint()
        self.errnr = self.arapi.ARGetContainerFromXML(byref(self.context),
                                                      byref(parsedStream),
                                                       containerName,
                                                       byref(groupList),
                                                       byref(admingrpList),
                                                       byref(ownerObjList),
                                                       byref(label),
                                                       byref(description),
                                                       byref(type_),
                                                       byref(references),
                                                       owner,
                                                       lastChanged,
                                                       byref(timestamp),
                                                       byref(helpText),
                                                       byref(changeDiary),
                                                       byref(objPropList),
                                                       byref(arDocVersion),
                                                       byref(self.arsl))
        if self.errnr < 2:
            return (ARContainerStruct(containerName,
                                       groupList,
                                       admingrpList,
                                       ownerObjList,
                                       label,
                                       description,
                                       type_,
                                       references,
                                       helpText,
                                       owner.value,
                                       timestamp,
                                       lastChanged.value,
                                       changeDiary.value,
                                       objPropList), arDocVersion)
        else:
            self.logger.error('ARGetContainerFromXML: failed for %s' % containerName)
            return None

    def ARGetDSOMappingFromXML(self, parsedStream, 
                               mappingName):
        '''ARGetDSOMappingFromXML retrieves DSO mapping information from an 
XML document. For more information on DSO mapping, refer to the Distributed 
Server Option Administrator's Guide.

Input: parsedStream
     mappingName
  :returns: (fromSchema,
        fromServer,
        toSchema,
        toServer,
        enabled,
        updateCode,
        transferMode,
        mapType,
        rtnMapType,
        defaultMap,
        duplicateAction,
        patternMatch,
        requiredFields,
        retryTime,
        mapping,
        rtnMapping,
        matchQual,
        owner,
        lastModifiedBy,
        modifiedDate,
        helpText,
        changeHistory, arDocVersion) or None in case of failure'''
        self.logger.debug('enter ARGetDSOMappingFromXML...')
        self.errnr = 0

        fromSchema = cars.ARNameType()
        fromServer = cars.ARServerNameType()
        toSchema = cars.ARNameType()
        toServer = cars.ARServerNameType()
        enabled = c_uint()
        updateCode = c_uint()
        transferMode = c_uint()
        mapType = c_uint()
        rtnMapType = c_uint()
        defaultMap = c_uint()
        duplicateAction = c_uint()
        patternMatch = c_uint()
        requiredFields = c_uint()
        retryTime = c_long()
        mapping = c_char_p()
        rtnMapping = c_char_p()
        matchQual = c_char_p()
        owner = cars.ARServerNameType()
        lastModifiedBy = cars.ARServerNameType()
        modifiedDate = cars.ARServerNameType()
        helpText = c_char_p()
        changeHistory = c_char_p()
        objPropList = cars.ARPropList()
        arDocVersion = c_uint()
        self.errnr = self.arapi.ARGetDSOMappingFromXML(byref(self.context),
                                                        my_byref(parsedStream),
                                                        mappingName,
                                                        fromSchema,
                                                        fromServer,
                                                        toSchema,
                                                        toServer,
                                                        byref(enabled),
                                                        byref(updateCode),
                                                        byref(transferMode),
                                                        byref(mapType),
                                                        byref(rtnMapType),
                                                        byref(defaultMap),
                                                        byref(duplicateAction),
                                                        byref(patternMatch),
                                                        byref(requiredFields),
                                                        byref(retryTime),
                                                        byref(mapping),
                                                        byref(rtnMapping),
                                                        byref(matchQual),
                                                        owner,
                                                        lastModifiedBy,
                                                        byref(modifiedDate),
                                                        byref(helpText),
                                                        byref(changeHistory),
                                                        byref(objPropList),
                                                        byref(arDocVersion),
                                                        byref(self.arsl))         
        if self.errnr < 2:
            return (fromSchema,
                    fromServer,
                    toSchema,
                    toServer,
                    enabled,
                    updateCode,
                    transferMode,
                    mapType,
                    rtnMapType,
                    defaultMap,
                    duplicateAction,
                    patternMatch,
                    requiredFields,
                    retryTime,
                    mapping,
                    rtnMapping,
                    matchQual,
                    owner,
                    lastModifiedBy,
                    modifiedDate,
                    helpText,
                    changeHistory, arDocVersion)
        else:
            self.logger.error('ARGetDSOMappingFromXML: failed for %s' % mappingName)
            return None        
        
    def ARGetDSOPoolFromXML(self, parsedStream, poolName):
        self.logger.debug('enter ARGetDSOPoolFromXML...')
        self.errnr = 0
        raise pyARSNotImplemented

    def ARGetEscalationFromXML(self, parsedStream, escalationName):
        '''ARGetEscalationFromXML retrieves escalations from an XML document.

Input: parsedStream, escalationName
  :returns: (AREscalationStruct, arDocVersion) or None in case of failure'''
        self.logger.debug('enter ARGetEscalationFromXML...')
        self.errnr = 0
        escalationTm = cars.AREscalationTmStruct()
        schemaList = cars.ARWorkflowConnectStruct()
        enable = c_uint()
        query = cars.ARQualifierStruct()
        actionList = cars.ARFilterActionList()
        elseList = cars.ARFilterActionList()
        helpText = c_char_p()
        timestamp = cars.ARTimestamp()
        owner = cars.ARAccessNameType()
        lastChanged = cars.ARAccessNameType()
        changeDiary = c_char_p()
        objPropList = cars.ARPropList()
        arDocVersion = c_uint()
        self.errnr = self.arapi.ARGetEscalationFromXML(byref(self.context),
                                                        my_byref(parsedStream),
                                                        escalationName,
                                                        byref(escalationTm),
                                                        byref(schemaList),
                                                        byref(enable),
                                                        byref(query),
                                                        byref(actionList),
                                                        byref(elseList),
                                                        owner,
                                                        lastChanged,
                                                        byref(timestamp),
                                                        byref(helpText),
                                                        byref(changeDiary),
                                                        byref(objPropList),
                                                        byref(arDocVersion),
                                                        byref(self.arsl))
        if self.errnr < 2:
            return (AREscalationStruct(escalationName,
                        escalationTm,
                        schemaList,
                        enable,
                        query,
                        actionList,
                        elseList,
                        helpText,
                        timestamp,
                        owner.value,
                        lastChanged.value,
                        changeDiary,
                        objPropList), arDocVersion)
        else:
            self.logger.error('ARGetEscalationFromXML: failed')
            return None

    def ARGetFieldFromXML(self, parsedStream, fieldName):
        '''ARGetFieldFromXML retrieves a filter from an XML document.

Input: parsedStream
       menuName
  :returns: (ARFieldInfoStruct, arDocVersion)
        or None in case of failure'''
        self.logger.debug('enter ARGetFieldFromXML...')
        self.errnr = 0
        fieldName = cars.ARNameType()
        fieldId = cars.ARInternalId()
        fieldMap = cars.ARFieldMappingStruct()
        dataType = c_uint()
        option = c_uint()
        createMode = c_uint()
        defaultVal = cars.ARValueStruct()
        # if we ask for permissions we need admin rights...
        permissions = cars.ARPermissionList()
        limit = cars.ARFieldLimitStruct()
        dInstanceList = cars.ARDisplayInstanceList()
        helpText = c_char_p()
        timestamp = cars.ARTimestamp()
        owner = cars.ARAccessNameType()
        lastChanged = cars.ARAccessNameType()
        changeDiary = c_char_p()
        arDocVersion = c_uint()
        self.errnr = self.arapi.ARGetFieldFromXML(byref(self.context),
                                                  my_byref(parsedStream),
                                                  fieldName,
                                                  byref(fieldId),
                                                  byref(fieldMap),
                                                  byref(dataType),
                                                  byref(option),
                                                  byref(createMode),
                                                  byref(defaultVal),
                                                  byref(permissions),
                                                  byref(limit),
                                                  byref(dInstanceList),
                                                  byref(helpText),
                                                  byref(timestamp),
                                                  owner,
                                                  lastChanged,
                                                  byref(changeDiary),
                                                  byref(arDocVersion),
                                                  byref(self.arsl))
        if self.errnr < 2:
            return (cars.ARFieldInfoStruct(fieldId,
                                           fieldName,
                                           timestamp,
                                           fieldMap,
                                           dataType,
                                           option,
                                           createMode,
                                           defaultVal,
                                           permissions,
                                           limit,
                                           dInstanceList,
                                           owner.value,
                                           lastChanged.value,
                                           helpText.value,
                                           changeDiary.value),
                   arDocVersion)
        else:
            self.logger.error('ARGetField: failed for fieldName %s' % (
                    fieldName))
            return None

    def ARGetFilterFromXML(self, parsedStream, filterName):
        '''ARGetFilterFromXML retrieves a filter from an XML document.

Input: parsedStream
       menuName
  :returns: (ARFilterStruct, arDocVersion)
        or None in case of failure'''
        self.logger.debug('enter ARGetFilterFromXML...')
        self.errnr = 0
        order = c_uint()
        schemaList = cars.ARWorkflowConnectStruct()
        opSet = c_uint()
        enable = c_uint()
        query = cars.ARQualifierStruct()
        actionList = cars.ARFilterActionList()
        elseList = cars.ARFilterActionList()
        helpText = c_char_p()
        timestamp = cars.ARTimestamp()
        owner = cars.ARAccessNameType()
        lastChanged = cars.ARAccessNameType()
        changeDiary = c_char_p()
        objPropList = cars.ARPropList()
        arDocVersion = c_uint()
        
        self.errnr = self.arapi.ARGetFilterFromXML(byref(self.context),
                                                   my_byref(parsedStream),
                                                   filterName,
                                                   byref(order),
                                                   byref(schemaList),
                                                   byref(opSet),
                                                   byref(enable),
                                                   byref(query),
                                                   byref(actionList),
                                                   byref(elseList),
                                                   owner,
                                                   lastChanged,
                                                   byref(timestamp),
                                                   byref(helpText),
                                                   byref(changeDiary),
                                                   byref(objPropList),
                                                   byref(arDocVersion),
                                                   byref(self.arsl))
        if self.errnr < 2:
            return (ARFilterStruct(filterName,
                                   order,
                                   schemaList,
                                   opSet,
                                   enable,
                                   query,
                                   actionList,
                                   elseList,
                                   helpText,
                                   timestamp,
                                   owner.value,
                                   lastChanged.value,
                                   changeDiary,
                                   objPropList), 
                   arDocVersion)
        else:
            self.logger.error('ARGetFilterFromXML: failed for %s' % filterName)
            return None

    def ARGetListXMLObjects(self, xmlInputDoc):
        '''ARGetListXMLObjects retrieves object names and types from an XML document.

Input: xmlInputDoc (ARXMLInputDoc)
  :returns: (objectTypeList (ARUnsignedIntList), objectNameList (ARNameList), 
        subTypeList (ARUnsignedIntList), appBlockNameList (ARNameList))
or None in case of failure'''
        self.logger.debug('enter ARGetListXMLObjects...')
        self.errnr = 0
        objectTypeList = cars.ARUnsignedIntList()
        objectNameList = cars.ARNameList()
        subTypeList = cars.ARUnsignedIntList()
        appBlockNameList = cars.ARNameList()
        self.errnr = self.arapi.ARGetListXMLObjects(byref(self.context),
                                                    my_byref(xmlInputDoc),
                                                    byref(objectTypeList),
                                                    byref(objectNameList),
                                                    byref(subTypeList),
                                                    byref(appBlockNameList),
                                                    byref(self.arsl))
        if self.errnr < 2:
            return (objectTypeList, objectNameList, subTypeList, appBlockNameList)
        else:
            self.logger.error('ARGetListXMLObjects failed')
            return None

    def ARGetMenuFromXML(self, parsedStream, menuName):
        '''ARGetMenuFromXML retrieves menus from an XML document.

Input: parsedStream
       menuName
  :returns: (ARMenuStruct, arDocVersion)
        or None in case of failure'''
        self.logger.debug('enter ARGetMenuFromXML...')
        self.errnr = 0
        refreshCode = c_uint()
        menuDefn = cars.ARCharMenuStruct()
        helpText = c_char_p()
        timestamp = cars.ARTimestamp()
        owner = cars.ARAccessNameType()
        lastChanged = cars.ARAccessNameType()
        changeDiary = c_char_p()
        objPropList = cars.ARPropList()
        arDocVersion = c_uint()
        self.errnr = self.arapi.ARGetMenuFromXML(byref(self.context),
                                                 my_byref(parsedStream),
                                                 menuName,
                                                 byref(refreshCode),
                                                 byref(menuDefn),
                                                 owner,
                                                 lastChanged,
                                                 byref(timestamp),
                                                 byref(helpText),
                                                 byref(changeDiary),
                                                 byref(objPropList),
                                                 byref(arDocVersion),
                                                 byref(self.arsl))
        if self.errnr < 2:
            return (ARMenuStruct(menuName,
                                refreshCode,
                                menuDefn,
                                helpText,
                                timestamp,
                                owner.value,
                                lastChanged.value,
                                changeDiary,
                                objPropList), arDocVersion)
        else:
            self.logger.error('ARGetMenuFromXML: failed for %s' % menuName)
            return None

    def ARGetSchemaFromXML(self, parsedStream, schemaName):
        '''ARGetSchemaFromXML retrieves schemas from an XML document.

Input: parsedStream
       schemaName
  :returns: (ARSchema, 
        nextFieldID, 
        coreVersion, 
        upgradeVersion,
        fieldInfoList,
        vuiInfoList, 
        arDocVersion)
        or None in case of failure'''
        self.logger.debug('enter ARGetSchemaFromXML...')
        self.errnr = 0
        # first define all ARSchema fields
        schema = cars.ARCompoundSchema()
        groupList = cars.ARPermissionList()
        admingrpList = cars.ARInternalIdList()
        getListFields = cars.AREntryListFieldList()
        sortList = cars.ARSortList()
        indexList = cars.ARIndexList()
        defaultVui = cars.ARNameType()
        helpText = c_char_p()
        timestamp = cars.ARTimestamp()
        owner = cars.ARAccessNameType()
        lastChanged = cars.ARAccessNameType()
        changeDiary = c_char_p()
        objPropList = cars.ARPropList()
        
        # now define the extensions that this API call offers
        nextFieldID = cars.ARInternalId()
        coreVersion = c_ulong()
        upgradeVersion = c_int()
        fieldInfoList = cars.ARFieldInfoList()
        vuiInfoList = cars.ARVuiInfoList()
        arDocVersion = c_uint()
        self.errnr = self.arapi.ARGetSchemaFromXML (byref(self.context),
                                                    my_byref(parsedStream),
                                                    schemaName,
                                                    byref(schema),
                                                    byref(groupList),
                                                    byref(admingrpList),
                                                    byref(getListFields),
                                                    byref(sortList),
                                                    byref(indexList),
                                                    defaultVui,
                                                    byref(nextFieldID),
                                                    byref(coreVersion),
                                                    byref(upgradeVersion),
                                                    byref(fieldInfoList),
                                                    byref(vuiInfoList),
                                                    owner,
                                                    lastChanged,
                                                    byref(timestamp),
                                                    byref(helpText),
                                                    byref(changeDiary),
                                                    byref(objPropList),
                                                    byref(arDocVersion),
                                                    byref(self.arsl))
        if self.errnr < 2:
            return (ARSchema(schemaName,
                            schema,
                            groupList,
                            admingrpList,
                            getListFields,
                            sortList,
                            indexList,
                            defaultVui,
                            helpText,
                            timestamp,
                            owner,
                            lastChanged,
                            changeDiary,
                            objPropList), 
                    nextFieldID, 
                    coreVersion, 
                    upgradeVersion,
                    fieldInfoList,
                    vuiInfoList, 
                    arDocVersion)
        else:
            self.logger.error( "ARGetSchemaFromXML: failed for schema %s" % schemaName)
            return None


    def ARGetVUIFromXML(self, parsedStream, schemaName):
        '''ARGetVUIFromXML retrieves views from an XML document.

Input: parsedStream
        schemaName
  :returns: (vuiInfoList, fieldInfoList, modifiedDate, arDocVersion)
        or None in case of failure'''
        self.logger.debug('enter ARGetVUIFromXML...')
        vuiInfoList = cars.ARVuiInfoList()
        fieldInfoList = cars.ARFieldInfoList()
        modifiedDate = cars.ARTimestamp()
        arDocVersion = c_uint()
        self.errnr = self.arapi.ARGetVUIFromXML(byref(self.context),
                                                my_byref(parsedStream),
                                                schemaName,
                                                byref(vuiInfoList),
                                                byref(fieldInfoList),
                                                byref(modifiedDate),
                                                byref(arDocVersion),
                                                byref(self.arsl))
        if self.errnr < 2:
            return (vuiInfoList, fieldInfoList, modifiedDate, arDocVersion)
        else:
            self.logger.error('ARGetVUIFromXML failed')
            return None

    def ARParseXMLDocument(self, xmlInputDoc, objectsToParse = None):
        '''ARParseXMLDocument parses the contents of an XML document.

Input: xmlInputDoc (ARXMLInputDoc; contains either the xml string or a reference
                to a file or a url)
  :returns: tuple of: (parsedStream (ARXMLParsedStream)
        parsedObjects (ARStructItemList))
        or None in case of failure'''
        self.logger.debug('enter ARParseXMLDocument...')
        parsedStream = cars.ARXMLParsedStream()
        parsedObjects = cars.ARStructItemList()
        self.errnr = self.arapi.ARParseXMLDocument(byref(self.context),
                                                   byref(xmlInputDoc),
                                                   my_byref(objectsToParse),
                                                   byref(parsedStream),
                                                   byref(parsedObjects),
                                                   byref(self.arsl))
        if self.errnr < 2:
            return (parsedStream, parsedObjects)
        else:
            self.logger.error('ARParseXMLDocument failed')
            return None

    def ARSetActiveLinkToXML(self, activeLinkName,
                             xmlDocHdrFtrFlag = False, 
                             executionOrder = 0,
                             workflowConnect = None,
                             accessList = None,
                             executeOn = 0,
                             controlFieldID = 0,
                             focusFieldID = 0,
                             enabled = 0,
                             query = None,
                             ifActionList = None,
                             elseActionList = None,
                             supportFileList = None,
                             owner = '',
                             lastModifiedBy = '',
                             modifiedDate = 0,
                             helpText = None,
                             changeHistory = None,
                             objPropList = None,
                             arDocVersion = c_uint(0)):
        '''ARSetActiveLinkToXML converts active links to XML.

Input: 
  :returns: string containing the XML
        or None in case of failure'''
        self.logger.debug('enter ARSetActiveLinkToXML...')
        self.errnr = 0
        if not isinstance(executionOrder, c_uint):
            executionOrder = c_uint(executionOrder)
        if not isinstance(executeOn, c_uint):
            executeOn = c_uint(executeOn)
        if not isinstance(controlFieldID, c_uint):
            controlFieldID = c_uint(controlFieldID)
        if not isinstance(focusFieldID, c_uint):
            focusFieldID = c_uint(focusFieldID)
        if not isinstance(enabled, c_uint):
            enabled = c_uint(enabled)
        if not isinstance(modifiedDate, cars.ARTimestamp):
            modifiedDate = cars.ARTimestamp(modifiedDate)
        if not isinstance(arDocVersion, c_uint):
            arDocVersion = c_uint(arDocVersion)

        assert isinstance(xmlDocHdrFtrFlag, int) or xmlDocHdrFtrFlag is None
        assert isinstance(activeLinkName, str) or activeLinkName is None
        assert isinstance(executionOrder, c_uint) or executionOrder is None
        assert isinstance(workflowConnect, cars.ARWorkflowConnectStruct) or workflowConnect is None
        assert isinstance(accessList, cars.ARInternalIdList) or accessList is None
        assert isinstance(executeOn, c_uint) or executeOn is None
        assert isinstance(controlFieldID, cars.ARInternalId) or controlFieldID is None
        assert isinstance(focusFieldID, cars.ARInternalId) or focusFieldID is None
        assert isinstance(enabled, c_uint) or enabled is None
        assert isinstance(query, cars.ARQualifierStruct) or query is None
        assert isinstance(ifActionList, cars.ARActiveLinkActionList) or ifActionList is None
        assert isinstance(elseActionList, cars.ARActiveLinkActionList) or elseActionList is None
        assert isinstance(supportFileList, cars.ARSupportFileInfoList) or supportFileList is None
        assert isinstance(owner, str)
        assert isinstance(lastModifiedBy, str)
        assert isinstance(modifiedDate, cars.ARTimestamp)
        assert isinstance(helpText, str) or helpText is None
        assert isinstance(changeHistory, str) or changeHistory is None
        assert isinstance(objPropList, cars.ARPropList) or objPropList is None
        assert isinstance(arDocVersion, c_uint)
        xml = cars.ARXMLOutputDoc(cars.AR_XML_DOC_CHAR_STR) 
        self.errnr = self.arapi.ARSetActiveLinkToXML(byref(self.context),
                                                     my_byref(xml), 
                                                     xmlDocHdrFtrFlag, 
                                                     activeLinkName,
                                                     my_byref(executionOrder),
                                                     my_byref(workflowConnect),
                                                     my_byref(accessList),
                                                     my_byref(executeOn),
                                                     my_byref(controlFieldID),
                                                     my_byref(focusFieldID),
                                                     my_byref(enabled),
                                                     my_byref(query),
                                                     my_byref(ifActionList),
                                                     my_byref(elseActionList),
                                                     my_byref(supportFileList),
                                                     owner,
                                                     lastModifiedBy,
                                                     my_byref(modifiedDate),
                                                     helpText,
                                                     changeHistory,
                                                     my_byref(objPropList),
                                                     my_byref(arDocVersion),
                                                     byref(self.arsl))
        if self.errnr < 2:
            return xml.u.charBuffer
        else:
            self.logger.error('ARSetActiveLinkToXML failed')
            return None

    def ARSetContainerToXML(self, containerName, 
                            xmlDocHdrFtrFlag = False,
                            permissionList = None,
                            subAdminGrpList = None,
                            ownerObjectList = None,
                            label = '',
                            description = '',
                            containerType = 1,
                            referenceList = None,
                            owner = '',
                            lastModifiedBy = '',
                            modifiedDate = 0,
                            helpText = None,
                            changeHistory = None,
                            objPropList = None,
                            arDocVersion = c_uint(0)):
        '''ARSetContainerToXML converts containers to XML.

Input: 
  :returns: string containing the XML
        or None in case of failure'''
        self.logger.debug('enter ARSetContainerToXML...')
        self.errnr = 0
        if not isinstance(containerType, c_uint):
            containerType = c_uint(containerType)
        if not isinstance(modifiedDate, cars.ARTimestamp):
            modifiedDate = cars.ARTimestamp(modifiedDate)
        if not isinstance(arDocVersion, c_uint):
            arDocVersion = c_uint(arDocVersion)
            
        xml = cars.ARXMLOutputDoc(cars.AR_XML_DOC_CHAR_STR)
        self.errnr = self.arapi.ARSetContainerToXML(byref(self.context),
                                                 byref(xml),
                                                 xmlDocHdrFtrFlag,
                                                 containerName,
                                                 my_byref(permissionList),
                                                 my_byref(subAdminGrpList),
                                                 my_byref(ownerObjectList),
                                                 label,
                                                 description,
                                                 my_byref(containerType),
                                                 my_byref(referenceList),
                                                 owner,
                                                 lastModifiedBy,
                                                 my_byref(modifiedDate),
                                                 helpText,
                                                 changeHistory,
                                                 my_byref(objPropList),
                                                 my_byref(arDocVersion),
                                                 byref(self.arsl))
        if self.errnr < 2:
            return xml.u.charBuffer
        else:
            self.logger.error("ARSetContainerToXML returned an error")
            return None

    def ARSetDSOMappingToXML(self, mappingName, xmlDocHdrFtrFlag,) :
        '''ARSetDSOMappingToXML retrieves information about the DSO mapping.

Input: 
  :returns: string containing the XML
        or None in case of failure'''
        self.logger.debug('enter ARSetDSOMappingToXML...')
        self.errnr = 0
        raise pyARSNotImplemented

    def ARSetDSOPoolToXML(self, poolName, 
                          xmlDocHdrFtrFlag = False,
                          enabled = 0,
                        defaultPool = True,
                        threadCount = 0,
                        connection = None,
                        owner = None,
                        lastModifiedBy = None,
                        modifiedDate = 0,
                        helpText = None,
                        changeHistory = None,
                        objPropList = None,
                        arDocVersion = c_uint(0)):
        '''ARSetDSOPoolToXML retrieves information about the DSO pool.

Input: 
  :returns: string containing the XML
        or None in case of failure'''
        self.logger.debug('enter ARSetDSOPoolToXML...')
        self.errnr = 0
        if not isinstance(enabled, c_uint):
            enabled = c_uint(enabled)
        if not isinstance(defaultPool, c_uint):
            defaultPool = c_uint(defaultPool)
        if not isinstance(threadCount, c_long):
            threadCount = c_long(threadCount)
        if not isinstance(modifiedDate, cars.ARTimestamp):
            modifiedDate = cars.ARTimestamp(modifiedDate)
        if not isinstance(arDocVersion, c_uint):
            arDocVersion = c_uint(arDocVersion)
            
        xml = cars.ARXMLOutputDoc(cars.AR_XML_DOC_CHAR_STR)
        # poolName = cars.ARNameType()
#        enabled = c_uint()
#        defaultPool = c_uint()
#        threadCount = c_long()
#        connection = c_char_p()
#        owner = cars.ARAccessNameType()
#        lastModifiedBy = cars.ARAccessNameType()
#        modifiedDate = cars.ARTimestamp()
#        helpText = c_char_p()
#        changeHistory = c_char_p()
#        objPropList = cars.ARPropList()
#        arDocVersion = c_uint(0)
        self.errnr = self.arapi.ARSetDSOPoolToXML(byref(self.context),
                                                 byref(xml),
                                                 xmlDocHdrFtrFlag,
                                                 poolName,
                                                 my_byref(enabled),
                                                 my_byref(defaultPool),
                                                 my_byref(threadCount),
                                                 my_byref(connection),
                                                 owner,
                                                 lastModifiedBy,
                                                 my_byref(modifiedDate),
                                                 helpText,
                                                 changeHistory,
                                                 my_byref(objPropList),
                                                 my_byref(arDocVersion),
                                                 byref(self.arsl))
        if self.errnr < 2:
            return xml.u.charBuffer
        else:
            self.logger.error("ARSetDSOPoolToXML returned an error")
            return None

    def ARSetEscalationToXML(self, escalationName, 
                             xmlDocHdrFtrFlag = 0,
                             escalationTime = None,
                             workflowConnect = None,
                             enabled = 0,
                             query = None,
                             ifActionList = None,
                             elseActionList = None,
                             owner = '',
                             lastModifiedBy = '',
                             modifiedDate = 0,
                             helpText = None,
                             changeHistory = None,
                             objPropList = None,
                             arDocVersion = c_uint(0)):
        '''ARSetEscalationToXML converts escalations to XML.

Input: 
  :returns: string containing the XML
        or None in case of failure'''
        self.logger.debug('enter ARSetEscalationToXML...')
        if not isinstance(enabled, c_uint):
            enabled = c_uint(enabled)
        if not isinstance(modifiedDate, cars.ARTimestamp):
            modifiedDate = cars.ARTimestamp(modifiedDate)
        if not isinstance(arDocVersion, c_uint):
            arDocVersion = c_uint(arDocVersion)
            
        xml = cars.ARXMLOutputDoc(cars.AR_XML_DOC_CHAR_STR)
        self.errnr = self.arapi.ARSetEscalationToXML(byref(self.context),
                                                byref(xml),
                                                 xmlDocHdrFtrFlag,
                                                 escalationName,
                                                 my_byref(escalationTime),
                                                 my_byref(workflowConnect),
                                                 my_byref(enabled),
                                                 my_byref(query),
                                                 my_byref(ifActionList),
                                                 my_byref(elseActionList),
                                                 owner,
                                                 lastModifiedBy,
                                                 my_byref(modifiedDate),
                                                 helpText,
                                                 changeHistory,
                                                 my_byref(objPropList),
                                                 my_byref(arDocVersion),
                                                 byref(self.arsl))
        if self.errnr < 2:
            return xml.u.charBuffer
        else:
            self.logger.error("ARSetEscalationToXML returned an error")
            return None

    def ARSetFieldToXML(self, fieldName, 
                        xmlDocHdrFtrFlag = 0,
                        fieldID = 0,
                        fieldMapping = None,
                        dataType = 0,
                        entryMode = 0,
                        createMode = 0,
                        defaultValue = None,
                        permissionList = None,
                        fieldLimit = None,
                        dInstanceList = None,
                        owner = '',
                        lastModifiedBy = '',
                        modifiedDate = 0,
                        helpText = None,
                        changeHistory = None,
                        arDocVersion = c_uint(0)):
        '''ARSetFieldToXML converts a field to XML.

Input: fieldName, 
        xmlDocHdrFtrFlag = 0,
        fieldID = 0,
        fieldMapping = None,
        dataType = 0,
        entryMode = 0,
        createMode = 0,
        defaultValue = None,
        permissionList = None,
        fieldLimit = None,
        dInstanceList = None,
        owner = '',
        lastModifiedBy = '',
        modifiedDate = 0,
        helpText = None,
        changeHistory = None,
        arDocVersion = c_uint(0)
  :returns: string containing the XML
        or None in case of failure'''
        self.logger.debug('enter ARSetFieldToXML...')
        self.errnr = 0
        if not isinstance(fieldID, c_uint):
            fieldID = c_uint(fieldID)
        if not isinstance(dataType, c_uint):
            dataType = c_uint(dataType)
        if not isinstance(entryMode, c_uint):
            entryMode = c_uint(entryMode)
        if not isinstance(createMode, c_uint):
            createMode = c_uint(createMode)
        if not isinstance(modifiedDate, cars.ARTimestamp):
            modifiedDate = cars.ARTimestamp(modifiedDate)
        if not isinstance(arDocVersion, c_uint):
            arDocVersion = c_uint(arDocVersion)
        xml = cars.ARXMLOutputDoc(cars.AR_XML_DOC_CHAR_STR)
        self.errnr = self.arapi.ARSetFieldToXML(byref(self.context),
                                                byref(xml),
                                                xmlDocHdrFtrFlag,
                                                fieldName,
                                                my_byref(fieldID),
                                                my_byref(fieldMapping),
                                                my_byref(dataType),
                                                my_byref(entryMode),
                                                my_byref(createMode),
                                                my_byref(defaultValue),
                                                my_byref(permissionList),
                                                my_byref(fieldLimit),
                                                my_byref(dInstanceList),
                                                owner,
                                                lastModifiedBy,
                                                my_byref(modifiedDate),
                                                helpText,
                                                changeHistory,
                                                my_byref(arDocVersion),
                                                byref(self.arsl))
        if self.errnr < 2:
            return xml.u.charBuffer
        else:
            self.logger.error("ARSetFieldToXML returned an error")
            return None

    def ARSetFilterToXML(self, filterName, xmlDocHdrFtrFlag = 0, 
                         executionOrder = None,
                         workflowConnect = None,
                         executeOn = None,
                         enabled = None,
                         query = None,
                         ifActionList = None,
                         elseActionList = None,
                         owner = '',
                         lastModifiedBy = '',
                         modifiedDate = 0,
                         helpText = None,
                         changeHistory = None,
                         objPropList = None,
                         arDocVersion = c_uint(0)):
        '''ARSetEscalationToXML converts a filter to XML.

Input: 
  :returns: string containing the XML
        or None in case of failure'''
        self.logger.debug('enter ARSetFilterToXML...')
        if not isinstance(executionOrder, c_uint):
            executionOrder = c_uint(executionOrder)
        if not isinstance(executeOn, c_uint):
            executeOn = c_uint(executeOn)
        if not isinstance(enabled, c_uint):
            enabled = c_uint(enabled)
        if not isinstance(modifiedDate, cars.ARTimestamp):
            modifiedDate = cars.ARTimestamp(modifiedDate)
        if not isinstance(arDocVersion, c_uint):
            arDocVersion = c_uint(arDocVersion)
            
        xml = cars.ARXMLOutputDoc(cars.AR_XML_DOC_CHAR_STR)
        self.errnr = self.arapi.ARSetFilterToXML(byref(self.context),
                                                 byref(xml),
                                                 xmlDocHdrFtrFlag,
                                                 filterName,
                                                 my_byref(executionOrder),
                                                 my_byref(workflowConnect),
                                                 my_byref(executeOn),
                                                 my_byref(enabled),
                                                 my_byref(query),
                                                 my_byref(ifActionList),
                                                 my_byref(elseActionList),
                                                 owner,
                                                 lastModifiedBy,
                                                 my_byref(modifiedDate),
                                                 helpText,
                                                 changeHistory,
                                                 my_byref(objPropList),
                                                 my_byref(arDocVersion),
                                                 byref(self.arsl))
        if self.errnr < 2:
            return xml.u.charBuffer
        else:
            self.logger.error("ARSetFilterToXML returned an error")
            return None

    def ARSetMenuToXML(self, menuName,
                       xmlDocHdrFtrFlag = 0, 
                       refreshCode = 0,
                       menuDefn = None,
                       owner = '',
                       lastModifiedBy = '',
                       modifiedDate = 0,
                       helpText = None,
                       changeHistory = None,
                       objPropList = None,
                       arDocVersion = c_uint(0)):
        '''ARSetMenuToXML converts menus to XML.

Input: 
  :returns: string containing the XML
        or None in case of failure'''
        self.logger.debug('enter ARSetMenuToXML...')
        self.errnr = 0
        if not isinstance(refreshCode, c_uint):
            refreshCode = c_uint(refreshCode)
        if not isinstance(modifiedDate, cars.ARTimestamp) and modifiedDate is not None:
            modifiedDate = cars.ARTimestamp(modifiedDate)
        if not isinstance(arDocVersion, c_uint):
            arDocVersion = c_uint(arDocVersion)
        xml = cars.ARXMLOutputDoc(cars.AR_XML_DOC_CHAR_STR)
        self.errnr = self.arapi.ARSetMenuToXML(byref(self.context),
                                                byref(xml),
                                                xmlDocHdrFtrFlag,
                                                menuName,
                                                my_byref(refreshCode),
                                                my_byref(menuDefn),
                                                owner,
                                                lastModifiedBy,
                                                my_byref(modifiedDate),
                                                helpText,
                                                changeHistory,
                                                my_byref(objPropList),
                                                my_byref(arDocVersion),
                                                byref(self.arsl))
        if self.errnr < 2:
            return xml.u.charBuffer
        else:
            self.logger.error("ARSetMenuToXML returned an error")
            return None

    def ARSetSchemaToXML (self, schemaName, xmlDocHdrFtrFlag=False,
                        compoundSchema=None,
                        permissionList=None,
                        subAdminGrpList=None,
                        getListFields=None,
                        sortList=None,
                        indexList=None,
                        defaultVui='',
                        nextFieldID = 0,
                        coreVersion = 0,
                        upgradeVersion=0,
                        fieldInfoList=None,
                        vuiInfoList=None,
                        owner='',
                        lastModifiedBy='',
                        modifiedDate=0,
                        helpText='',
                        changeHistory='',
                        objPropList=None,
                        arDocVersion = 0):
        '''ARSetSchemaToXML dump Schema to XML according...

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
       (optional) owner (default: '')
       (optional) lastModifiedBy (default: '')
       (optional) modifiedDate (default: 0)
       (optional) helpText (default: '')
       (optional) changeHistory (default: '')
       (optional) objPropList (default: None)
       (optional) arDocVersion (default: 0)
  :returns: string containing the XML (or None in case of failure)'''
        self.logger.debug('enter ARSetSchemaToXML...')
        # initialize to return the XML as a string (not as a file)
        xml = cars.ARXMLOutputDoc(cars.AR_XML_DOC_CHAR_STR)
        if not isinstance(modifiedDate, cars.ARTimestamp):
                modifiedDate = cars.ARTimestamp(modifiedDate)
        if not isinstance(coreVersion, c_ulong):
                coreVersion = c_ulong(coreVersion)
        if not isinstance(upgradeVersion, c_int):
                upgradeVersion = c_int(upgradeVersion)
        if not isinstance(arDocVersion, c_uint):
                arDocVersion = c_uint(arDocVersion)
        assert isinstance(xmlDocHdrFtrFlag, int)
        assert isinstance(schemaName, str)
        assert isinstance(compoundSchema, cars.ARCompoundSchema) or compoundSchema is None
        assert isinstance(permissionList, cars.ARPermissionList) or permissionList is None
        assert isinstance(subAdminGrpList, cars.ARInternalIdList) or subAdminGrpList is None
        assert isinstance(getListFields, cars.AREntryListFieldList) or getListFields is None
        assert isinstance(sortList, cars.ARSortList) or sortList is None
        assert isinstance(indexList, cars.ARIndexList) or indexList is None
        assert isinstance(defaultVui, str)
        assert isinstance(nextFieldID, cars.ARInternalId) or nextFieldID is None
        assert isinstance(coreVersion, c_ulong)
        assert isinstance(upgradeVersion, c_int)
        assert isinstance(fieldInfoList, cars.ARFieldInfoList) or fieldInfoList is None
        assert isinstance(vuiInfoList, cars.ARVuiInfoList) or vuiInfoList is None
        assert isinstance(owner, str)
        assert isinstance(lastModifiedBy, str)
        assert isinstance(modifiedDate, cars.ARTimestamp)
        assert isinstance(helpText, str) or subAdminGrpList is None
        assert isinstance(changeHistory, str) or subAdminGrpList is None
        assert isinstance(objPropList, cars.ARPropList) or objPropList is None
        assert isinstance(arDocVersion, c_uint)
        self.errnr = self.arapi.ARSetSchemaToXML(byref(self.context),
                                                 byref(xml),
                                                 xmlDocHdrFtrFlag,
                                                 schemaName,
                                                 my_byref(compoundSchema),
                                                 my_byref(permissionList),
                                                 my_byref(subAdminGrpList),
                                                 my_byref(getListFields),
                                                 my_byref(sortList),
                                                 my_byref(indexList),
                                                 defaultVui,
                                                 my_byref(nextFieldID),
                                                 my_byref(coreVersion),
                                                 my_byref(upgradeVersion),
                                                 my_byref(fieldInfoList),
                                                 my_byref(vuiInfoList),
                                                 owner,
                                                 lastModifiedBy,
                                                 my_byref(modifiedDate),
                                                 helpText,
                                                 changeHistory,
                                                 my_byref(objPropList),
                                                 my_byref(arDocVersion),
                                                 byref(self.arsl))
        if self.errnr < 2:
            return xml.u.charBuffer
        else:
            self.logger.error("ARSetSchemaToXML returned an error")
            return None

    def ARSetVUIToXML(self, schemaName,
                      xmlDocHdrFtrFlag=False, 
                      vuiInfoList = None,
                      fieldInfoList = None,
                      modifiedDate = 0,
                      arDocVersion = 0):
        '''ARSetVUIToXML converts a view to an XML document.
Input: schemaName
      (optional) xmlDocHdrFtrFlag (ARBoolean, default: False)
      (optional) schemaName (ARNameType, default: None),
      (optional) vuiInfoList (ARVuiInfoList, default: None),
      (optional) fieldInfoList (ARFieldInfoList, default: None),
      (optional) modifiedDate (ARTimestamp, default: 0),
      (optional) arDocVersion (unsigned int, default: 0)
  :returns: string containing the XML (or None in case of failure)'''
        self.logger.debug('enter ARSetVUIToXML...')
        xml = cars.ARXMLOutputDoc(cars.AR_XML_DOC_CHAR_STR)
        if not isinstance(modifiedDate, cars.ARTimestamp):
            modifiedDate = cars.ARTimestamp(modifiedDate)
        if not isinstance(arDocVersion, c_uint):
            arDocVersion = c_uint(arDocVersion)
        assert isinstance(vuiInfoList, cars.ARVuiInfoList) or vuiInfoList is None
        assert isinstance(fieldInfoList, cars.ARFieldInfoList) or fieldInfoList is None
        self.errnr = self.arapi.ARSetVUIToXML(byref(self.context),
                                              byref(xml),
                                              xmlDocHdrFtrFlag, 
                                              schemaName,
                                              my_byref(vuiInfoList),
                                              my_byref(fieldInfoList),
                                              my_byref(modifiedDate),
                                              my_byref(arDocVersion),
                                              byref(self.arsl))
        if self.errnr < 2:
            return xml.u.charBuffer
        else:
            self.logger.error('ARSetVUIToXML failed')
            return None

    def ARSetDocFooterToXML(self):
        '''ARSetDocFooterToXML converts document headers to XML.
        
Input: 
  :returns: string containing the XML (or None in case of failure)'''
        self.logger.debug('enter ARSetDocFooterToXML...')
        xml = cars.ARXMLOutputDoc(cars.AR_XML_DOC_CHAR_STR)
        self.errnr = self.arapi.ARSetDocFooterToXML(byref(self.context),
                                                    byref(xml),
                                                    byref(self.arsl))
        if self.errnr < 2:
            return xml.u.charBuffer
        else:
            self.logger.error('ARSetDocFooterToXML failed')
            return None

    def ARSetDocHeaderToXML(self):
        '''ARSetDocHeaderToXML converts document headers to XML.
        
Input: 
  :returns: string containing the XML (or None in case of failure)'''
        self.logger.debug('enter ARSetDocHeaderToXML...')
        xml = cars.ARXMLOutputDoc(cars.AR_XML_DOC_CHAR_STR)
        self.errnr = self.arapi.ARSetDocHeaderToXML(byref(self.context),
                                                    byref(xml),
                                                    byref(self.arsl))
        if self.errnr < 2:
            return xml.u.charBuffer
        else:
            self.logger.error('ARSetDocHeaderToXML failed')
            return None


###########################################################################
#
#
# ARFree functions (created dynamically)
#
#
    def FreeARActiveLinkStruct(self, obj):
        '''FreeARActiveLinkStruct frees all substructures of ARActiveLinkStruct.'''
        self.ARFree(obj.schemaList)
        self.ARFree(obj.groupList)
        self.ARFree(obj.query)
        self.ARFree(obj.actionList)
        self.ARFree(obj.elseList)
        self.ARFree(obj.objPropList)

    def FreeARActiveLinkList(self, obj):
        '''FreeARActiveLinkStruct frees all elements of ARActiveLinkList.'''
        for i in range(obj.numItems):
            self.FreeARActiveLinkStruct(obj.activeLinkList[i])

    def FreeARContainerList(self, obj):
        for i in range(obj.numItems):
            self.FreeARContainerStruct(obj.containerList[i])
                
    def FreeARContainerStruct(self, obj):
        self.ARFree(obj.groupList)
        self.ARFree(obj.admingrpList)
        self.ARFree(obj.ownerObjList)
        self.ARFree(obj.references)
        self.ARFree(obj.objPropList)

    def FreeAREscalationList(self, obj):
        '''FreeAREscalationList frees all elements of AREscalationList.'''
        for i in range(obj.numItems):
            self.FreeAREscalationStruct(obj.escalationList[i])

    def FreeAREscalationStruct(self, obj):
        '''FreeAREscalationStruct frees all substructures of AREscalationStruct.'''
        # self.ARFree(obj.escalationTm)
        self.ARFree(obj.schemaList)
        self.ARFree(obj.query)
        self.ARFree(obj.actionList)
        self.ARFree(obj.elseList)
        self.ARFree(obj.objPropList)

    def FreeARFilterList(self, obj):
        '''FreeARFilterList frees all elements of ARFilterList.'''
        for i in range(obj.numItems):
            self.FreeARFilterStruct(obj.filterList[i])
    
    def FreeARFilterStruct(self, obj):
        '''FreeARFilterStruct frees all substructures of ARFilterStruct.'''
        self.ARFree(obj.schemaList)
        self.ARFree(obj.query)
        self.ARFree(obj.actionList)
        self.ARFree(obj.elseList)
        self.ARFree(obj.objPropList)

    def FreeARMenuList(self, obj):
        '''FreeARMenuList frees all elements of ARMenuList.'''
        for i in range(obj.numItems):
            self.ARFree(obj.menuList[i])

    def FreeARMenuStruct(self, obj):
        '''FreeARMenuStruct frees all substructures of ARMenuStruct.'''
        self.ARFree(obj.menuDefn)
        self.ARFree(obj.objPropList)

    def FreeARSchema(self, obj):
        '''FreeARSchema frees all substructures of ARSchema.'''
        self.ARFree(obj.schema)
        self.ARFree(obj.groupList)
        self.ARFree(obj.getListFields)
        self.ARFree(obj.sortList)
        self.ARFree(obj.indexList)
        self.ARFree(obj.objPropList)

    def FreeARSchemaList(self, obj):
        '''FreeARSchemaList frees all elements of ARSchemaList.'''
        for i in range(obj.numItems):
            self.FreeARSchema(obj.schemaList[i])

    def ARFree(self, obj, freeStruct=False):
        '''ARFree frees all substructures of the handed structure.'''
        # self.logger.debug('pyARS: ARFree called for %s' % (obj))
        if obj is None:
            return
        try:
            
            if obj.__class__.__name__ in ('ARActiveLinkList', 'ARActiveLinkStruct',
                                          'ARContainerList', 'ARContainerStruct',
                                          'AREscalationList', 'AREscalationStruct',
                                          'ARFilterList', 'ARFilterStruct', 
                                          'ARMenuList', 'ARMenuStruct',
                                          'ARSchema', 'ARSchemaList'):
                return eval('self.Free%s(obj)' % obj.__class__.__name__)
            elif isinstance(obj, (cars.AREscalationTmStruct, cars.AREscalationTmList)):
                # cannot find any free routine for those...
                pass
            else:
                return eval('self.arapi.Free%s(byref(obj), freeStruct)' % (
                       obj.__class__.__name__))

        except KeyError:
            self.logger.error("ARFree failed for class: %s" % (str(obj.__class__.__name__)))
            return None

class ARS(ARS51):
    pass
    
if cars.version >= 60:
    class ARSchema(Structure):
        _fields_ = [("name", cars.ARNameType),
                    ("schema", cars.ARCompoundSchema),
                    ("schemaInheritanceList", cars.ARSchemaInheritanceList),
                    ("groupList", cars.ARPermissionList),
                    ("admingrpList", cars.ARInternalIdList),
                    ("getListFields",  cars.AREntryListFieldList),
                    ("sortList", cars.ARSortList),
                    ("indexList", cars.ARIndexList),
                    ("archiveInfo", cars.ARArchiveInfoStruct),
                    ("defaultVui", cars.ARNameType),
                    ("helpText", c_char_p),
                    ("timestamp", cars.ARTimestamp),
                    ("owner", cars.ARAccessNameType),
                    ("lastChanged", cars.ARAccessNameType),
                    ("changeDiary", c_char_p),
                    ("objPropList", cars.ARPropList)]

    class ARSchemaList(Structure):
        _fields_ = [('numItems', c_uint),
                    ('schemaList',POINTER(ARSchema))]  
        
    class ARS60(ARS51):
        '''pythonic wrapper Class for Remedy C API, V6.0
    
Create an instance of ars and call its methods...
similar to ARSPerl and ARSJython.'''

        def ARCreateSchema(self, name, 
                           schema, 
                           schemaInheritanceList, 
                           groupList, 
                           admingrpList, 
                           getListFields,
                           sortList, 
                           indexList, 
                           archiveInfo,
                           defaultVui,
                           helpText='', 
                           owner='', 
                           changeDiary='', 
                           objPropList=None):
            '''ARCreateSchema creates a new form.

ARCreateSchema creates a new form with the indicated name on the specified 
server. The nine required core fields are automatically associated with the 
new form.
Input: name of schema
       schema, 
       schemaInheritanceList (will be set to None, as it is reserved for future use), 
       groupList, 
       admingrpList, 
       getListFields,
       sortList, 
       indexList, 
       archiveInfo,
       defaultVui,
       optional: helpText (default = None)
       optional: owner (default = None)
       optional: changeDiary (default = None)
       optional: objPropList (default = None)   
  :returns: errnr'''
            self.logger.debug('enter ARCreateSchema...')
            # schemaInheritanceList = None # reserved for future use...
            self.errnr = self.arapi.ARCreateSchema(byref(self.context),
                                                   name, 
                                                   my_byref(schema), 
                                                   None, # byref(schemaInheritanceList), 
                                                   my_byref(groupList), 
                                                   my_byref(admingrpList), 
                                                   my_byref(getListFields),
                                                   my_byref(sortList), 
                                                   my_byref(indexList), 
                                                   my_byref(archiveInfo),
                                                   defaultVui,
                                                   helpText, 
                                                   owner, 
                                                   changeDiary, 
                                                   my_byref(objPropList),
                                                   byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARCreateSchema failed for schema %s.' % name)
            return self.errnr

        def ARDeleteActiveLink(self, name, 
                               deleteOption = cars.AR_DEFAULT_DELETE_OPTION):
            '''ARDeleteActiveLink deletes the active link.
        
ARDeleteActiveLink deletes the active link with the indicated name from the
specified server and deletes any container references to the active link.
Input: name
       (optional) deleteOption (default = cars.AR_DEFAULT_DELETE_OPTION)
  :returns: errnr'''
            self.logger.debug('enter ARDeleteActiveLink: %s...' % (name))
            self.errnr = self.arapi.ARDeleteActiveLink(byref(self.context),
                                                       name,
                                                       deleteOption,
                                                       byref(self.arsl))
            return self.errnr

        def ARDeleteCharMenu(self, name, 
                             deleteOption = cars.AR_DEFAULT_DELETE_OPTION):
            '''ARDeleteCharMenu deletes the character menu with the indicated name from
the specified server.

Input: name
       (optional) deleteOption (default = cars.AR_DEFAULT_DELETE_OPTION)
  :returns: errnr'''
            self.logger.debug('enter ARDeleteCharMenu...')
            self.errnr = self.arapi.ARDeleteCharMenu(byref(self.context),
                                                   name,
                                                   deleteOption,
                                                   byref(self.arsl))
            return self.errnr

        def ARDeleteContainer(self, name, 
                              deleteOption = cars.AR_DEFAULT_DELETE_OPTION):
            '''ARDeleteContainer deletes the container .
        
ARDeleteContainer deletes the container with the indicated name from
the specified server and deletes any references to the container from other containers.
Input: name
       (optional) deleteOption (default = cars.AR_DEFAULT_DELETE_OPTION)
  :returns: errnr'''
            self.logger.debug('enter ARDeleteContainer...')
            self.errnr = self.arapi.ARDeleteContainer(byref(self.context),
                                                   name,
                                                   deleteOption,
                                                   byref(self.arsl))
            return self.errnr

        def ARDeleteEscalation(self, name, deleteOption = cars.AR_DEFAULT_DELETE_OPTION):
            '''ARDeleteEscalation deletes the escalation.
        
ARDeleteEscalation deletes the escalation with the indicated name from the
specified server and deletes any container references to the escalation.
Input:  name
       (optional) deleteOption (default = cars.AR_DEFAULT_DELETE_OPTION)
  :returns: errnr'''
            self.logger.debug('enter ARDeleteEscalation...')
            self.errnr = self.arapi.ARDeleteEscalation(byref(self.context),
                                                       name,
                                                       deleteOption,
                                                       byref(self.arsl))
            return self.errnr

        def ARDeleteFilter(self, name, deleteOption = cars.AR_DEFAULT_DELETE_OPTION):
            '''ARDeleteFilter deletes the filter.
        
ARDeleteFilter deletes the filter with the indicated name from the
specified server and deletes any container references to the filter.
Input:  name
       (optional) deleteOption (default = cars.AR_DEFAULT_DELETE_OPTION)
  :returns: errnr'''
            self.logger.debug('enter ARDeleteFilter...')
            self.errnr = self.arapi.ARDeleteFilter(byref(self.context),
                                                   name,
                                                   deleteOption,
                                                   byref(self.arsl))
            return self.errnr

        def ARExport(self, 
                     structItems, 
                     displayTag = None, 
                     vuiType = cars.AR_VUI_TYPE_WINDOWS, 
                     lockinfo = None):
            '''ARExport exports the indicated structure definitions.

Use this function to copy structure definitions from one AR System server to another.
Note: Form exports do not work the same way with ARExport as they do in
Remedy Administrator. Other than views, you cannot automatically
export related items along with a form. You must explicitly specify the
workflow items you want to export. Also, ARExport cannot export a form
without embedding the server name in the export file (something you can
do with the "Server-Independent" option in Remedy Administrator).
Input: (ARStructItemList) structItems
       (ARNameType) displayTag (optional, default = None)
       (c_uint) vuiType (optional, default = cars.AR_VUI_TYPE_WINDOWS)
       (ARWorkflowLockStruct) lockinfo  (optional, default = None)
  :returns: string (or None in case of failure)'''
            self.logger.debug('enter ARExport...')
            exportBuf = c_char_p()
            self.errnr = self.arapi.ARExport(byref(self.context),
                                             byref(structItems),
                                             displayTag,
                                             vuiType,
                                             my_byref(lockinfo),
                                             byref(exportBuf),
                                             byref(self.arsl))
            if self.errnr < 2:
                return exportBuf.value
            else:
                self.logger.error('ARExport failed with %d' % (self.errnr))
                return None

        def ARExportLicense(self):
            '''ARExportLicense exports license.
            
ARExportLicense specifies a pointer that is set to malloced 
space and contains the full contents of the license file currently 
on the server. This buffer can be written to a file to produce 
an exact replication of the license file, including all checksums
and encryption.
Input: 
  :returns: exportBuf (or None in case of failure)'''
            self.logger.debug('enter ARExportLicense...')
            exportBuf = c_char_p()
            self.errnr = self.arapi.ARExportLicense(byref(self.context),
                                                    byref(exportBuf),
                                                    byref(self.arsl))
            if self.errnr < 2:
                return exportBuf.value
            else:
                self.logger.error('ARExportLicense failed')
                return None
 
        def ARGetApplicationState(self, applicationName):
            '''ARGetApplicationState: retrieves the application state: 
maintenance (admin only), test, or production.
Input: applicationName
  :returns: currentStateName (ARNameType) or None in case of failure'''
            self.logger.debug('enter ARGetApplicationState...')
            currentStateName = cars.ARNameType()
            self.errnr = self.arapi.ARGetApplicationState(byref(self.context),
                                                          applicationName,
                                                          currentStateName,
                                                          byref(self.arsl))
            if self.errnr < 2:
                return currentStateName.value
            else:
                self.logger.error('ARGetApplicationState: failed for %s' % applicationName)
                return None
            
        def ARGetListActiveLink (self, schema=None, 
                                 changedSince=0, 
                                 objPropList = None):
            '''ARGetListActiveLink retrieves a list of active links for a schema/server.

You can retrieve all
(accessible) active links or limit the list to active links associated with a
particular form or modified after a specified time.
Input: (optional) schema (default: None)
       (optional) changeSince (default: 0)
       (optional) objPropList (default: None)
  :returns: ARNameList or None in case of failure'''
            self.logger.debug('enter ARGetListActiveLink...')
            nameList = cars.ARNameList()
            self.errnr = self.arapi.ARGetListActiveLink (byref(self.context),
                                                    schema,
                                                    changedSince,
                                                    my_byref(objPropList),
                                                    byref(nameList),
                                                    byref(self.arsl))
            if self.errnr < 2:
                return nameList
            else:
                self.logger.error('ARGetListActiveLink failed for schema %s' % schema)
                return None
    
        def ARGetListApplicationState(self):
            '''ARGetListApplicationState retrieves the list of application states 
(maintenance, test, or production) that an application on this server 
can assume. This list is server-dependent.
Input: 
  :returns: ARNameList or None in case of failure'''
            self.logger.debug('enter ARGetListApplicationState...')
            stateNameList = cars.ARNameList()
            self.errnr =self.arapi.ARGetListApplicationState(byref(self.context),
                                                    byref(stateNameList),
                                                    byref(self.arsl))
            if self.errnr < 2:
                return stateNameList
            else:
                self.logger.error('ARGetListApplicationState: failed')
                return None
    
        def ARGetListCharMenu(self, changedSince=0, 
                              formList = None,
                              actLinkList = None, 
                              objPropList = None):
            '''ARGetListCharMenu retrieves a list of character menus.

Input: (ARTimestamp) changedSince (optional, default = 0)
       (ARNameList) formList (optional, default = None)
       (ARNameList) actLinkList (optional, default = None)
       (ARPropList) objPropList (optional, default = None)
  :returns: ARNameList or None in case of failure'''
            self.logger.debug('enter ARGetListCharMenu...')
            nameList = cars.ARNameList()
            self.errnr =self.arapi.ARGetListCharMenu(byref(self.context),
                                                    changedSince,
                                                    my_byref(formList),
                                                    my_byref(actLinkList),
                                                    my_byref(objPropList),
                                                    byref(nameList),
                                                    byref(self.arsl))
            if self.errnr < 2:
                return nameList
            else:
                self.logger.error('ARGetListCharMenu: failed')
                return None
    
        def ARGetListContainer (self, changedSince=0,
                              containerTypes = None,
                              attributes=cars.ARCON_ALL | cars.AR_HIDDEN_INCREMENT,
                              ownerObjList=None, 
                              objPropList = None):
            '''ARGetListContainer retrieves a list of containers.

You can retrieve all
(accessible) containers or limit the list to containers of a particular type,
containers owned by a specified form, or containers modified after a
specified time.
Input: (optional) changedSince (default: 0)
       (optional) containerTypes: ARContainerTypeList
       (optional) attributes (default: )
       (optional) ownerObjList (default: None)
       (optional) objPropList (Default: None)
  :returns: ARContainerInfoList or None in case of failure
Please note: I'm not sure about the parameter configuration;
I've implemented according to the C API documentation, but
the exact usage of attributes & containerTypes is still
a secret to me... Beware... has not been tested well!'''
            self.logger.debug('enter ARGetListContainer...')
            conList = cars.ARContainerInfoList()
            self.errnr = self.arapi.ARGetListContainer (byref(self.context),
                                                   changedSince,
                                                   my_byref(containerTypes),
                                                   attributes,
                                                   my_byref(ownerObjList),
                                                   my_byref(objPropList),
                                                   byref(conList),
                                                   byref(self.arsl))
            if self.errnr < 2:
                return conList
            else:
                self.logger.error('ARGetListContainer: failed')
                return None
    
        def ARGetListEntry (self, schema, 
                            query=None,
                            getListFields=None, 
                            sortList=None,
                            firstRetrieve=cars.AR_START_WITH_FIRST_ENTRY,
                            maxRetrieve=cars.AR_NO_MAX_LIST_RETRIEVE,
                            useLocale = False):
            '''ARGetListEntry retrieves a list of entries for a schema.

The AR System Server
returns data from each entry as a string containing the concatenated values
of selected fields. You can limit the list to entries that match particular
conditions by specifying the qualifier parameter. ARGetListEntryWithFields
also returns a qualified list of entries, but as field/value pairs.
Input: schema/form name
       (optional) query (ARQualifierStruct)
       (optional) getListFields (default: None)
       (optional) sortList (default: None)
       (optional) firstRetrieve (default: AR_START_WITH_FIRST_ENTRY)
       (optional) maxRetrieve (default: AR_NO_MAX_LIST_RETRIEVE)
       (optional) useLocale (default: False)
  :returns: (AREntryListList, numMatches) or None in case of failure'''
            self.logger.debug('enter ARGetListEntry...')
            entryList = cars.AREntryListList()
            numMatches = c_uint()
            self.errnr = self.arapi.ARGetListEntry(byref(self.context),
                                          schema,
                                          my_byref(query),
                                          my_byref(getListFields),
                                          my_byref(sortList),
                                          firstRetrieve,
                                          maxRetrieve,
                                          useLocale, 
                                          byref(entryList),
                                          byref(numMatches),
                                          byref(self.arsl))
            if self.errnr < 2:
                return (entryList, numMatches.value)                                     
            else:
                self.logger.error("ARGetListEntry failed: schema: %s/query: %s" % (schema, query))
                return None

        def ARGetListEntryWithFields (self, schema, 
                                      query = None,
                                      getListFields=None, 
                                      sortList=None,
                                      firstRetrieve=cars.AR_START_WITH_FIRST_ENTRY,
                                      maxRetrieve=cars.AR_NO_MAX_LIST_RETRIEVE,
                                      useLocale = False):
            '''ARGetListEntryWithFields retrieve a list of entries for a schema.

Data from each entry
is returned as field/value pairs for all fields. You can limit the list to entries
that match particular conditions by specifying the qualifier parameter.
ARGetListEntry also returns a qualified list of entries, but as a string for each
entry containing the concatenated values of selected fields.
Note: It is important that the query looks something like this:
'field' = "value" (please note the quotation marks).
Input: schema/form name
       (optional) query string (default: None)
       (optional) getListFields (default: None)
       (optional) sortList (default: None)
       (optional) firstRetrieve (default: AR_START_WITH_FIRST_ENTRY)
       (optional) maxRetrieve (default: AR_NO_MAX_LIST_RETRIEVE)
       (optional) useLocale (default: False)
  :returns: (AREntryListFieldValueList, numMatches) or None in case of failure'''
            self.logger.debug('enter ARGetListEntryWithFields...')
            entryList = cars.AREntryListFieldValueList()
            numMatches = c_uint()
            self.errnr = self.arapi.ARGetListEntryWithFields(byref(self.context),
                                          schema,
                                          my_byref(query),
                                          my_byref(getListFields),
                                          my_byref(sortList),
                                          firstRetrieve,
                                          maxRetrieve,
                                          useLocale,
                                          byref(entryList),
                                          byref(numMatches),
                                          byref(self.arsl))
            if self.errnr < 2:
                return (entryList, numMatches.value)
            else:
                self.logger.error ("ARGetListEntryWithFields: failed!")
                return None
                
        def ARGetListEscalation (self, schema=None,
                               changedSince = 0,
                               objPropList = None):
            '''ARGetListEscalation retrieves a list of all escalations.

You can retrieve all
escalations or limit the list to escalations associated with a particular form.
The call returns all escalations modified on or after the timestamp.
Input: (optional) schema (default: None)
       (optional) changedSince (default: 0)
       (optional) objPropList (default: None)
  :returns: ARAccessNameList or None in case of failure'''
            self.logger.debug('enter ARGetListEscalation...')
            nameList = cars.ARNameList()
            self.errnr = self.arapi.ARGetListEscalation (byref(self.context),
                                                    schema,
                                                    changedSince,
                                                    my_byref(objPropList),
                                                    byref(nameList),
                                                    byref(self.arsl))
            if self.errnr < 2:
                return nameList
            else:
                self.logger.error ("ARGetListEscalation: failed!")
                return None
    
        def ARGetListFilter(self, schema=None, 
                            changedSince=0, 
                            objPropList = None):
            '''ARGetListFilter return a list of all available filter for a schema.

You can retrieve all filters or
limit the list to filters associated with a particular form or modified after a
specified time.
Input: (optional) schema (default: None -- retrieve all filter names)
       (optional) changedSince (default: 0)
       (optional) objPropList (default: None)
  :returns: ARNameList or None in case of failure'''
            self.logger.debug('enter ARGetListFilter...')
            nameList = cars.ARNameList()
            self.errnr = self.arapi.ARGetListFilter(byref(self.context),
                                                   schema, 
                                                   changedSince,
                                                   my_byref(objPropList),
                                                   byref(nameList),
                                                   byref(self.arsl))
            if self.errnr < 2:
                return nameList
            else:
                self.logger.error ("ARGetListFilter: failed!")
                return None

        def ARGetListRole (self, applicationName, 
                           userName = None, 
                           password = None):
            '''ARGetListRole retrieves a list of roles for a deployable application 
or returns a list of roles for a user for a deployable application.

Input: applicationName, 
       (optional) userName (default = None)
       (optional) password (default = None)
  :returns: roleList (ARRoleInfoList) or None in case of failure'''
            self.logger.debug('enter ARGetListRole...')
            roleList = cars.ARRoleInfoList()
            self.errnr = self.arapi.ARGetListRole(byref(self.context),
                                                  applicationName,
                                                  userName,
                                                  password,
                                                  byref(roleList),
                                                  byref(self.arsl))
            if self.errnr < 2:
                return roleList
            else:
                self.logger.error ("ARGetListRole: failed!")
                return None
                    
        def ARGetListSchema(self, changedSince=0, 
                            schemaType=cars.AR_HIDDEN_INCREMENT,
                            name='', 
                            fieldIdList=None, 
                            objPropList=None):
            '''ARGetListSchema return a list of all available schemas.

You can retrieve all (accessible) forms or limit the list to forms of a 
particular type or forms modified after a specified time.
Input: (optional) changedSince (ARTimestamp, default: 0)
       (optional) schemaType (c_uint, default: AR_LIST_SCHEMA_ALL | AR_HIDDEN_INCREMENT)
       (optional) name (ARNameType, default "", only necessary if schemaType is
       AR_LIST_SCHEMA_UPLINK
       (optional) fieldIdList (ARInternalIdList, default: None) ARS then only returns the
       forms that contain all the fields in this list.
       (optional) objPropList (default: None)
  :returns: ARNameList or None in case of failure'''
            self.logger.debug('enter ARGetListSchema...')
            nameList = cars.ARNameList()
            if not isinstance(changedSince, cars.ARTimestamp):
                changedSince = cars.ARTimestamp(changedSince)
            if objPropList is None:
                objPropList = cars.ARPropList(0)
            assert isinstance(changedSince, cars.ARTimestamp)
            assert isinstance(schemaType, int)
            assert isinstance(name, str)
            assert isinstance(fieldIdList, cars.ARInternalIdList) or fieldIdList is None
            assert isinstance(objPropList, cars.ARPropList) or objPropList is None
            assert isinstance(nameList, cars.ARNameList)
            self.errnr = self.arapi.ARGetListSchema(byref(self.context),
                                                   changedSince,
                                                   schemaType,
                                                   name,
                                                   my_byref(fieldIdList),
                                                   my_byref(objPropList),
                                                   byref(nameList),
                                                   byref(self.arsl))
            if self.errnr < 2:
                return nameList
            else:
                self.logger.error ("ARGetListSchema: failed!")
                return None

        def ARGetListSchemaWithAlias(self, changedSince=0, 
                                     schemaType=cars.AR_HIDDEN_INCREMENT, 
                                     name='', 
                                     fieldIdList=None, 
                                     vuiLabel=None, 
                                     objPropList=None):
            '''ARGetListSchemaWithAlias retrieves a list of form definitions 
and their corresponding aliases.

You can retrieve all (accessible) forms or limit the list to
forms of a particular type or forms modified after a specified time.
Input: (optional) changedSince (ARTimestamp, default: 0)
       (optional) schemaType (c_uint, default: AR_LIST_SCHEMA_ALL | AR_HIDDEN_INCREMENT)
       (optional) name (ARNameType, default "", only necessary if schemaType is
       AR_LIST_SCHEMA_UPLINK
       (optional) fieldIdList (ARInternalIdList, default: None) ARS then only returns the
       forms that contain all the fields in this list.
       (optional) vuiLabel (default: None)
       (optional) objPropList (default: None)
  :returns: (nameList [ARNameList], aliasList[ARNameList]) or None in case of failure'''
            self.logger.debug('enter ARGetListSchemaWithAlias...')
            nameList = cars.ARNameList()
            aliasList = cars.ARNameList()
            self.errnr = self.arapi.ARGetListSchemaWithAlias(byref(self.context),
                                                       changedSince,
                                                       schemaType,
                                                       name,
                                                       my_byref(fieldIdList),
                                                       vuiLabel,
                                                       my_byref(objPropList),
                                                       byref(nameList),
                                                       byref(aliasList),
                                                       byref(self.arsl))
            if self.errnr < 2:
                return (nameList, aliasList)
            else:
                self.logger.error ("ARGetListSchemaWithAlias: failed!")
                return None
    
        def ARGetMultipleContainers(self, 
                                    changedSince = 0, 
                                    nameList = None,
                                    containerTypes = None,
                                    attributes = cars.AR_HIDDEN_INCREMENT,
                                    ownerObjList = None,
                                    refTypes = None,
                                    # here start the result parameters
                                    containerNameList = None,
                                    groupListList = None,
                                    admingrpListList = None,
                                    ownerObjListList = None,
                                    labelList = None,
                                    descriptionList = None,
                                    typeList = None,
                                    referenceList = None,
                                    helpTextList = None,
                                    ownerList = None,
                                    timestampList = None,
                                    lastChangedList = None,
                                    changeDiaryList = None,
                                    objPropListList = None):
            '''ARGetMultipleContainers retrieves multiple container objects.

While the server returns the information in lists for each item, pyars
converts this to a struct of its own.
Input: (optional) changedSince = 0, 
       (optional) nameList = None,
       (optional) containerTypes = None,
       (optional) attributes = cars.AR_HIDDEN_INCREMENT,
       (optional) ownerObjList = None,
       (optional) refTypes = None,
       With the following parameters you define which information is returned
       containerNameList = None,
       (optional) groupListList = None,
       (optional) admingrpListList = None,
       (optional) ownerObjListList = None,
       (optional) labelList = None,
       (optional) descriptionList = None,
       (optional) typeList = None,
       (optional) referenceList = None,
       (optional) helpTextList = None,
       (optional) ownerList = None,
       (optional) timestampList = None,
       (optional) lastChangedList = None,
       (optional) changeDiaryList = None,
       (optional) objPropListList = None
  :returns: ARContainerList or None in case of failure'''
            self.logger.debug('enter ARGetMultipleContainers...')
            existList = cars.ARBooleanList()
            if containerNameList is None:
                containerNameList = cars.ARNameList()
            self.errnr = self.arapi.ARGetMultipleContainers(byref(self.context),
                                                            changedSince, 
                                                            my_byref(nameList),
                                                            my_byref(containerTypes),
                                                            attributes,
                                                            my_byref(ownerObjList),
                                                            my_byref(refTypes),
                                                            # result parameters
                                                            byref(existList),
                                                            my_byref(containerNameList),
                                                            my_byref(groupListList),
                                                            my_byref(admingrpListList),
                                                            my_byref(ownerObjListList),
                                                            my_byref(labelList),
                                                            my_byref(descriptionList),
                                                            my_byref(typeList),
                                                            my_byref(referenceList),
                                                            my_byref(helpTextList),
                                                            my_byref(ownerList),
                                                            my_byref(timestampList),
                                                            my_byref(lastChangedList),
                                                            my_byref(changeDiaryList),
                                                            my_byref(objPropListList),
                                                            byref(self.arsl))
            
            if self.errnr > 1:
                self.logger.error('ARGetMultipleContainers: failed')
                return None
            else:
                tempArray = (ARContainerStruct * existList.numItems)()
                for i in range(existList.numItems):
                    if existList.booleanList[i]:
                        tempArray[i].name = containerNameList.nameList[i].value
                        if groupListList: tempArray[i].groupList = groupListList.permissionList[i]
                        if admingrpListList: tempArray[i].admingrpList = admingrpListList.internalIdListList[i]
                        if ownerObjListList: tempArray[i].ownerObjList = ownerObjListList.ownerObjListList[i]
                        if descriptionList: tempArray[i].label = labelList.stringList[i]
                        if descriptionList: tempArray[i].description = descriptionList.stringList[i]
                        if typeList: tempArray[i].type = typeList.intList[i]
                        if referenceList: tempArray[i].references = referenceList.referenceListList[i]
                        if helpTextList: tempArray[i].helpText = helpTextList.stringList[i]
                        if ownerList: tempArray[i].owner = ownerList.nameList[i].value
                        if timestampList: tempArray[i].timestamp = timestampList.timestampList[i]
                        if lastChangedList: tempArray[i].lastChanged = lastChangedList.nameList[i].value
                        if changeDiaryList: tempArray[i].changeDiary = changeDiaryList.stringList[i]
                        if objPropListList: tempArray[i].objPropList = objPropListList.propsList[i]
                    else:
                        self.logger.error('ARGetMultipleContainers: "%s" does not exist!' % nameList.nameList[i].value)
                return ARContainerList(existList.numItems, tempArray)

      
        def ARGetMultipleEntryPoints(self, changedSince,
                                     appNameList,
                                     refTypeList,
                                     displayTag = None,
                                     vuiType = cars.AR_VUI_TYPE_NONE,
                                     entryPointNameList = None,
                                     entryPointTypeList = None,
                                     entryPointDLabelList = None,
                                     ownerAppNameList = None,
                                     ownerAppDLabelList = None,
                                     groupListList = None,
                                     ownerObjListList = None,
                                     descriptionList = None,
                                     referencesList = None,
                                     helpTextList = None,
                                     timestampList = None,
                                     objPropListList = None):
            '''ARGetMultipleEntryPoints retrieves the entry points of multiple 
applications. 

It returns the entry points that are accessible by 
the user, taking into account user permissions, licenses,
and application states.
Input: (ARTimeStamp) changedSince,
       (ARNameList) appNameList,
       (ARReferenceTypeList) refTypeList,
       (ARNameType) displayTag (optional, default = None)
       (c_uint) vuiType (optional, default = cars.AR_VUI_TYPE_NONE,
       (ARNameList) entryPointNameList (optional, default = None)
       (ARUnsignedIntList) entryPointTypeList (optional, default = None)
       (ARTextStringList) entryPointDLabelList (optional, default = None)
       (ARNameList) ownerAppNameList (optional, default = None)
       (ARTextStringList) ownerAppDLabelList (optional, default = None)
       (ARPermissionListList) groupListList (optional, default = None)
       (ARContainerOwnerObjListList) ownerObjListList (optional, default = None)
       (ARTextStringList) descriptionList (optional, default = None)
       (ARReferenceListList) referencesList (optional, default = None)
       (ARTextStringList) helpTextList (optional, default = None)
       (ARTimestampList) timestampList (optional, default = None)
       (ARPropListList) objPropListList (optional, default = None)
  :returns: a list of entryPointNameList, entryPointTypeList, entryPointDLabelList,
            ownerAppNameList,ownerAppDLabelList, groupListList,
             ownerObjListList, descriptionList, referencesList, 
             helpTextList, timestampList, objPropListList
         or None in case of failure'''
            self.logger.debug('enter ARGetMultipleEntryPoints...')
            if not isinstance(vuiType, c_uint):
                vuiType = c_uint(vuiType)
            self.errnr = self.arapi.ARGetMultipleEntryPoints(byref(self.context),
                                                 changedSince,
                                                 my_byref(appNameList),
                                                 my_byref(refTypeList),
                                                 my_byref(displayTag),
                                                 my_byref(vuiType),
                                                 my_byref(entryPointNameList),
                                                 my_byref(entryPointTypeList),
                                                 my_byref(entryPointDLabelList),
                                                 my_byref(ownerAppNameList),
                                                 my_byref(ownerAppDLabelList),
                                                 my_byref(groupListList),
                                                 my_byref(ownerObjListList),
                                                 my_byref(descriptionList),
                                                 my_byref(referencesList),
                                                 my_byref(helpTextList),
                                                 my_byref(timestampList),
                                                 my_byref(objPropListList),
                                                 byref(self.arsl))
            if self.errnr < 2:
                return (entryPointNameList, 
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
            else:
                self.logger.error('ARGetMultipleEntryPoints: failed')
                return None
    
        def ARGetMultipleSchemas(self, changedSince=0, 
                                schemaTypeList = None,
                                nameList=None, 
                                fieldIdList=None,
                                schemaList = None,
                                schemaInheritanceListList = None, # reserved for future use
                                groupListList = None,
                                admingrpListList = None,
                                getListFieldsList = None,
                                sortListList = None,
                                indexListList = None,
                                archiveInfoList = None,
                                defaultVuiList = None,
                                helpTextList = None,
                                timestampList = None,
                                ownerList = None,
                                lastChangedList = None,
                                changeDiaryList = None,
                                objPropListList = None):
            '''ARGetMultipleSchemas retrieves information about several schemas
from the server at once.

This information does not include the form field definitions (see ARGetField). This
function performs the same action as ARGetSchema but is easier to use and
more efficient than retrieving multiple forms one by one.
Information is returned in lists for each item, with one item in the list for
each form returned. For example, if the second item in the list for existList is
TRUE, the name of the second form is returned in the second item in the list
for schemaNameList.
Input:  changedSince=0, 
        (optional) schemaTypeList (default = None),
        (optional) nameList (default = None), 
        (optional) fieldIdList (default =None),
        (optional) schemaList (default = None),
        (optional) schemaInheritanceListList (default  = None), # reserved for future use
        (optional) groupListList (default  = None),
        (optional) admingrpListList (default  = None),
        (optional) getListFieldsList (default  = None),
        (optional) sortListList (default  = None),
        (optional) indexListList (default  = None),
        (optional) archiveInfoList (default  = None),
        (optional) defaultVuiList (default  = None),
        (optional) helpTextList (default  = None),
        (optional) timestampList (default  = None),
        (optional) ownerList (default  = None),
        (optional) lastChangedList (default  = None),
        (optional) changeDiaryList (default  = None),
        (optional) objPropListList (default = None)
  :returns: ARSchemaList or None in case of failure'''
            self.logger.debug('enter ARGetMultipleSchemas...')
            existList = cars.ARBooleanList()
            schemaNameList = cars.ARNameList()
            # make sure, objPropListList is not None. Otherwise
            # we will crash the ARSystem server!
            if objPropListList is None:
                internalObjPropListList = cars.ARPropListList()
            else:
                internalObjPropListList = objPropListList
            self.errnr = self.arapi.ARGetMultipleSchemas(byref(self.context),
                                           changedSince, 
                                           my_byref(schemaTypeList),
                                           my_byref(nameList), 
                                           my_byref(fieldIdList),
                                           my_byref(existList),
                                           my_byref(schemaNameList),
                                           my_byref(schemaList),
                                           None, # my_byref(schemaInheritanceListList),
                                           my_byref(groupListList),
                                           my_byref(admingrpListList),
                                           my_byref(getListFieldsList),
                                           my_byref(sortListList),
                                           my_byref(indexListList),
                                           my_byref(archiveInfoList),
                                           my_byref(defaultVuiList),
                                           my_byref(helpTextList),
                                           my_byref(timestampList),
                                           my_byref(ownerList),
                                           my_byref(lastChangedList),
                                           my_byref(changeDiaryList),
                                           byref(internalObjPropListList),
                                           byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARGetMultipleSchemas: failed')
                return None
            else:
                tempArray = (ARSchema * existList.numItems)()
                for i in range(existList.numItems):
                    if existList.booleanList[i]:
                        tempArray[i].name = schemaNameList.nameList[i].value
                        if schemaList: tempArray[i].schema = schemaList.compoundSchema[i]
                        if groupListList: tempArray[i].groupList = groupListList.permissionList[i]
                        if admingrpListList: tempArray[i].admingrpList = admingrpListList.internalIdListList[i]
                        if getListFieldsList: tempArray[i].getListFields = getListFieldsList.listFieldList[i]
                        if indexListList: tempArray[i].sortList = sortListList.sortListList[i]
                        if indexListList: tempArray[i].indexList = indexListList.indexListList[i]
                        if archiveInfoList: tempArray[i].archiveInfo = archiveInfoList.archiveInfoList[i]
                        if defaultVuiList: tempArray[i].defaultVui = defaultVuiList.nameList[i].value
                        if helpTextList: tempArray[i].helpText = helpTextList.stringList[i]
                        if timestampList: tempArray[i].timestamp = timestampList.timestampList[i]
                        if ownerList: tempArray[i].owner = ownerList.nameList[i].value
                        if lastChangedList: tempArray[i].lastChanged = lastChangedList.nameList[i].value
                        if changeDiaryList: tempArray[i].changeDiary = changeDiaryList.stringList[i]
                        if objPropListList: tempArray[i].objPropList = internalObjPropListList.propsList[i]
                    else:
                        self.logger.error('ARGetMultipleSchemas: "%s" does not exist!' % nameList.nameList[i].value)
                return ARSchemaList(existList.numItems, tempArray)
    
        def ARGetSchema (self, name):
            '''ARGetSchema returns all information about a schema.
        
This information does not include the form's field
definitions (see ARGetField).
Input: string (schema)
  :returns: ARSchema (schema, groupList, admingrpList,
                getListFields, sortList, indexList,
                defaultVui, helpText, timestamp, owner,
                lastChanged, changeDiary, objPropList)
            or None in case of failure'''
            self.logger.debug('enter ARGetSchema...')
            schema = cars.ARCompoundSchema()
            schemaInheritanceList = cars.ARSchemaInheritanceList()
            groupList = cars.ARPermissionList()
            admingrpList = cars.ARInternalIdList()
            getListFields = cars.AREntryListFieldList()
            sortList = cars.ARSortList()
            indexList = cars.ARIndexList()
            archiveInfo = cars.ARArchiveInfoStruct()
            defaultVui = cars.ARNameType()
            helpText = c_char_p()
            timestamp = cars.ARTimestamp()
            owner = cars.ARAccessNameType()
            lastChanged = cars.ARAccessNameType()
            changeDiary = c_char_p()
            objPropList = cars.ARPropList()
            self.errnr = self.arapi.ARGetSchema (byref(self.context),
                                            name,
                                            byref(schema),
                                            byref(schemaInheritanceList),
                                            byref(groupList),
                                            byref(admingrpList),
                                            byref(getListFields),
                                            byref(sortList),
                                            byref(indexList),
                                            byref(archiveInfo),
                                            defaultVui,
                                            byref(helpText),
                                            byref(timestamp),
                                            owner,
                                            lastChanged,
                                            byref(changeDiary),
                                            byref(objPropList),
                                            byref(self.arsl))

            if self.errnr < 2:
                return ARSchema(name, 
                                schema,
                                schemaInheritanceList,
                                groupList,
                                admingrpList,
                                getListFields,
                                sortList,
                                indexList,
                                archiveInfo,
                                defaultVui.value,
                                helpText,
                                timestamp,
                                owner.value,
                                lastChanged.value,
                                changeDiary,
                                objPropList)
            else:
                self.logger.error( "ARGetSchema: failed for schema %s" % name)
                return None

        def ARImportLicense(self, importBuf, 
                            importOption = cars.AR_LICENSE_IMPORT_APPEND):
            '''ARImportLicense imports a license.

It imports a buffer, which is the contents of a license file, including checksums
and encryption and an option, which tells whether to overwrite the existing
license file or append to it.
When called, the server validates that the buffer is a valid license file and
either appends the licenses in the file to the existing license file or replaces the
existing license file with the new file.
Input:  importBuf, 
        (optional) importOption (default = cars.AR_LICENSE_IMPORT_APPEND)
  :returns: errnr'''
            self.logger.debug('enter ARImportLicense...')
            self.errnr = self.arapi.ARImportLicense (byref(self.context),
                                                     importBuf,
                                                     importOption,
                                                     byref(self.arsl))
            if self.errnr > 1:
                self.logger.error( "ARImportLicense: failed!")
            return self.errnr
    
        def ARSetApplicationState(self, applicationName, stateName):
            '''ARSetApplicationState sets the application state (maintenance, test, or production) 
in the AR System Application State form.
            
Input:  applicationName, 
        stateName
  :returns: errnr'''
            self.logger.debug('enter ARSetApplicationState...')
            self.errnr = self.arapi.ARSetApplicationState(byref(self.context),
                                                          applicationName,
                                                          stateName,
                                                          byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARSetApplicationState failed for %s' % applicationName)
            return self.errnr
    
        def ARSetSchema(self, name,
                        newName = None,
                        schema = None,
                        schemaInheritanceList = None,
                        groupList = None,
                        admingrpList = None,
                        getListFields = None,
                        sortList = None,
                        indexList = None,
                        archiveInfo = None,
                        defaultVui = None,
                        helpText = None,
                        owner = None,
                        changeDiary = None,
                        objPropList = None,
                        setOption = None):
            '''ARSetSchema updates the definition for the form.

If the schema is locked, only the indexList and the defaultVui can be
set.
Input:  name,
        (optional) newName = None,
        (optional) schema = None,
        (optional) schemaInheritanceList = None,
        (optional) groupList = None,
        (optional) admingrpList = None,
        (optional) getListFields = None,
        (optional) sortList = None,
        (optional) indexList = None,
        (optional) archiveInfo = None,
        (optional) defaultVui = None,
        (optional) helpText = None,
        (optional) owner = None,
        (optional) changeDiary = None,
        (optional) objPropList = None,
        (optional) setOption = None
  :returns: errnr'''
            self.logger.debug('enter ARSetSchema...')
            self.errnr = self.arapi.ARSetSchema(byref(self.context),
                                                name,
                                                newName,
                                                my_byref(schema),
                                                None, # my_byref(schemaInheritanceList),
                                                my_byref(groupList),
                                                my_byref(admingrpList),
                                                my_byref(getListFields),
                                                my_byref(sortList),
                                                my_byref(indexList),
                                                my_byref(archiveInfo),
                                                defaultVui,
                                                helpText,
                                                owner,
                                                changeDiary,
                                                my_byref(objPropList),
                                                byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARSetSchema failed for schema %s' % (name))
            return self.errnr 

    ###########################################################################
    #
    #
    # XML support functions
    #
    #

        def ARGetActiveLinkFromXML(self, parsedStream, 
                                   activeLinkName,
                                   appBlockName = None):
            '''ARGetActiveLinkFromXML retrieves an active link from an XML document.

Input: parsedStream
       activeLinkName
       appBlockName
  :returns: (ARActiveLinkStruct, supportFileList, arDocVersion) or 
    None in case of failure'''
            self.logger.debug('enter ARGetActiveLinkFromXML...')
            order = c_uint()
            schemaList = cars.ARWorkflowConnectStruct()
            groupList = cars.ARInternalIdList()
            executeMask = c_uint()
            controlField = cars.ARInternalId()
            focusField = cars.ARInternalId()
            enable = c_uint()
            query = cars.ARQualifierStruct()
            actionList = cars.ARActiveLinkActionList()
            elseList = cars.ARActiveLinkActionList()
            supportFileList = cars.ARSupportFileInfoList()
            helpText = c_char_p()
            modifiedDate = cars.ARTimestamp()
            owner = cars.ARAccessNameType()
            lastChanged = cars.ARAccessNameType()
            changeDiary = c_char_p()
            objPropList = cars.ARPropList()
            arDocVersion = c_uint()
            self.errnr = self.arapi.ARGetActiveLinkFromXML(byref(self.context),
                                                           my_byref(parsedStream),
                                                              activeLinkName,
                                                              appBlockName,
                                                              byref(order),
                                                              byref(schemaList),
                                                              byref(groupList),
                                                              byref(executeMask),
                                                              byref(controlField),
                                                              byref(focusField),
                                                              byref(enable),
                                                              byref(query),
                                                              byref(actionList),
                                                              byref(elseList),
                                                              byref(supportFileList),
                                                              owner,
                                                              lastChanged,
                                                              byref(modifiedDate),
                                                              byref(helpText),
                                                              byref(changeDiary),
                                                              byref(objPropList),
                                                              byref(arDocVersion),
                                                              byref(self.arsl))
            if self.errnr < 2:
                return (ARActiveLinkStruct(activeLinkName,
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
                                            modifiedDate,
                                            owner.value,
                                            lastChanged.value,
                                            changeDiary,
                                            objPropList), supportFileList, arDocVersion)
            else:
                self.logger.error('ARGetActiveLinkFromXML: failed for %s' % activeLinkName)
                return None

        def ARGetSchemaFromXML(self, parsedStream, schemaName):
            '''ARGetSchemaFromXML retrieves schemas from an XML document.
    
Input: parsedStream
       schemaName
  :returns: (ARSchema, 
        nextFieldID, 
        coreVersion, 
        upgradeVersion,
        fieldInfoList,
        vuiInfoList, 
        arDocVersion)
        or None in case of failure'''
            self.logger.debug('enter ARGetSchemaFromXML...')
            # first define all ARSchema fields
            schema = cars.ARCompoundSchema()
            groupList = cars.ARPermissionList()
            admingrpList = cars.ARInternalIdList()
            getListFields = cars.AREntryListFieldList()
            sortList = cars.ARSortList()
            indexList = cars.ARIndexList()
            archiveInfo = cars.ARArchiveInfoStruct()
            defaultVui = cars.ARNameType()
            helpText = c_char_p()
            timestamp = cars.ARTimestamp()
            owner = cars.ARAccessNameType()
            lastChanged = cars.ARAccessNameType()
            changeDiary = c_char_p()
            objPropList = cars.ARPropList()
            
            # now define the extensions that this API call offers
            nextFieldID = cars.ARInternalId()
            coreVersion = c_ulong()
            upgradeVersion = c_int()
            fieldInfoList = cars.ARFieldInfoList()
            vuiInfoList = cars.ARVuiInfoList()
            arDocVersion = c_uint()
            self.errnr = self.arapi.ARGetSchemaFromXML (byref(self.context),
                                                        my_byref(parsedStream),
                                                        schemaName,
                                                        byref(schema),
                                                        byref(groupList),
                                                        byref(admingrpList),
                                                        byref(getListFields),
                                                        byref(sortList),

                                                        byref(indexList),
                                                        byref(archiveInfo),
                                                        defaultVui,
                                                        byref(nextFieldID),
                                                        byref(coreVersion),
                                                        byref(upgradeVersion),
                                                        byref(fieldInfoList),
                                                        byref(vuiInfoList),
                                                        owner,
                                                        lastChanged,
                                                        byref(timestamp),
                                                        byref(helpText),
                                                        byref(changeDiary),
                                                        byref(objPropList),
                                                        byref(arDocVersion),
                                                        byref(self.arsl))
            if self.errnr < 2:
                return (ARSchema(schemaName,
                                schema,
                                groupList,
                                admingrpList,
                                getListFields,
                                sortList,
                                indexList,
                                archiveInfo,
                                defaultVui,
                                helpText,
                                timestamp,
                                owner,
                                lastChanged,
                                changeDiary,
                                objPropList), 
                        nextFieldID, 
                        coreVersion, 
                        upgradeVersion,
                        fieldInfoList,
                        vuiInfoList, 
                        arDocVersion)
            else:
                self.logger.error( "ARGetSchemaFromXML: failed for schema %s" % schemaName)
                return None

        def ARParseXMLDocument(self, xmlnputDoc, objectsToParse = None):
            self.logger.debug('enter ARParseXMLDocument...')
            parsedStream = cars.ARXMLParsedStream()
            parsedObjects = cars.ARStructItemList()
            appBlockNameList = cars.ARNameList()
            self.errnr = self.arapi.ARParseXMLDocument(byref(self.context),
                                                       byref(xmlnputDoc),
                                                       my_byref(objectsToParse),
                                                       byref(parsedStream),
                                                       byref(parsedObjects),
                                                       byref(appBlockNameList),
                                                       byref(self.arsl))
            if self.errnr < 2:
                return (parsedStream, parsedObjects, appBlockNameList)
            else:
                self.logger.error('ARParseXMLDocument failed')
                return None

        def ARSetSchemaToXML (self, schemaName, 
                              xmlDocHdrFtrFlag=False,
                              compoundSchema=None,
                            permissionList=None,
                            subAdminGrpList=None,
                            getListFields=None,
                            sortList=None,
                            indexList=None,
                            archiveInfo=None,
                            defaultVui='',
                            nextFieldID=0,
                            coreVersion = 0,
                            upgradeVersion=0,
                            fieldInfoList=None,
                            vuiInfoList=None,
                            owner='',
                            lastModifiedBy='',
                            modifiedDate=0,
                            helpText='',
                            changeHistory='',
                            objPropList=None,
                            arDocVersion = 0):
            '''ARSetSchemaToXML Dump Schema to XML according...
    
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
       (optional) xmlDocHdrFtrFlag (default: False)
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
       (optional) owner (default: '')
       (optional) lastModifiedBy (default: '')
       (optional) modifiedDate (default: 0)
       (optional) helpText (default: '')
       (optional) changeHistory (default: '')
       (optional) objPropList (default: None)
       (optional) arDocVersion (default: 0)
  :returns: string containing the XML or None in case of failure'''
            self.logger.debug('enter ARSetSchemaToXML...')
            # initialize to return the XML as a string (not as a file)
            xml = cars.ARXMLOutputDoc(cars.AR_XML_DOC_CHAR_STR)
            if not isinstance(modifiedDate, cars.ARTimestamp):
                modifiedDate = cars.ARTimestamp(modifiedDate)
            if not isinstance(coreVersion, c_ulong):
                coreVersion = c_ulong(coreVersion)
            if not isinstance(upgradeVersion, c_int):
                upgradeVersion = c_int(upgradeVersion)
            if not isinstance(arDocVersion, c_uint):
                arDocVersion = c_uint(arDocVersion)
            assert isinstance(xmlDocHdrFtrFlag, int)
            assert isinstance(schemaName, str)
            assert isinstance(compoundSchema, cars.ARCompoundSchema) or compoundSchema is None
            assert isinstance(permissionList, cars.ARPermissionList) or permissionList is None
            assert isinstance(subAdminGrpList, cars.ARInternalIdList) or subAdminGrpList is None
            assert isinstance(getListFields, cars.AREntryListFieldList) or getListFields is None
            assert isinstance(sortList, cars.ARSortList) or sortList is None
            assert isinstance(indexList, cars.ARIndexList) or indexList is None
            assert isinstance(archiveInfo, cars.ARArchiveInfoStruct) or archiveInfo is None
            assert isinstance(defaultVui, str)
            assert isinstance(nextFieldID, cars.ARInternalId) or nextFieldID is None
            assert isinstance(coreVersion, c_ulong)
            assert isinstance(upgradeVersion, c_int)
            assert isinstance(fieldInfoList, cars.ARFieldInfoList) or fieldInfoList is None
            assert isinstance(vuiInfoList, cars.ARVuiInfoList) or vuiInfoList is None
            assert isinstance(owner, str)
            assert isinstance(lastModifiedBy, str)
            assert isinstance(modifiedDate, cars.ARTimestamp)
            assert isinstance(helpText, str)
            assert isinstance(changeHistory, str)
            assert isinstance(objPropList, cars.ARPropList) or objPropList is None
            assert isinstance(arDocVersion, c_uint) or arDocVersion is None

            self.errnr = self.arapi.ARSetSchemaToXML(byref(self.context),
                                                     byref(xml),
                                                     xmlDocHdrFtrFlag,
                                                     schemaName,
                                                     my_byref(compoundSchema),
                                                     my_byref(permissionList),
                                                     my_byref(subAdminGrpList),
                                                     my_byref(getListFields),
                                                     my_byref(sortList),
                                                     my_byref(indexList),
                                                     my_byref(archiveInfo),
                                                     defaultVui,
                                                     my_byref(nextFieldID),
                                                     my_byref(coreVersion),
                                                     my_byref(upgradeVersion),
                                                     my_byref(fieldInfoList),
                                                     my_byref(vuiInfoList),
                                                     owner,
                                                     lastModifiedBy,
                                                     my_byref(modifiedDate),
                                                     helpText, 
                                                     changeHistory, 
                                                     my_byref(objPropList),
                                                     my_byref(arDocVersion),
                                                     byref(self.arsl))
            if self.errnr > 1:
                self.logger.error("ARSetSchemaToXML returned an error")
                return None
            return xml.u.charBuffer

    class ARS(ARS60):
        pass
    
if cars.version >= 63:
    class ARS63(ARS60):
        '''pythonic wrapper Class for Remedy C API, V6.3

Create an instance of ars and call its methods...
similar to ARSPerl and ARSJython'''
        
        def ARBeginBulkEntryTransaction (self):
            '''ARBeginBulkEntryTransaction marks the beginning of a series of 
entry API function calls.

Those function calls will be grouped together and sent 
to the AR System server as part of one transaction. All calls 
related to create, set, delete, and merge operations made between 
this API call and a trailing AREndBulkEntryTransaction call will 
not be sent to the server until the trailing call is made.
Input:
  :returns: errnr'''
            self.logger.debug('enter ARBeginBulkEntryTransaction: ')
            self.errnr = self.arapi.ARBeginBulkEntryTransaction(byref(self.context),
                                                       byref(self.arsl))
            return self.errnr
    
        def AREndBulkEntryTransaction(self, 
                                      actionType = cars.AR_BULK_ENTRY_ACTION_SEND):
            '''AREndBulkEntryTransaction marks the ending of a series of entry API function calls.

Those function calls
are grouped together and sent to the AR System server as part 
of one transaction. All calls related to create, set, delete, 
and merge operations made before this API call and after the 
preceding ARBeginBulkEntryTransaction call will be sent to the
server when this call is issued and executed within a single 
database transaction.
Input: (optional) actionType (default = cars.AR_BULK_ENTRY_ACTION_SEND)
  :returns: bulkEntryReturnList'''
            self.logger.debug('enter AREndBulkEntryTransaction...')
            bulkEntryReturnList = cars.ARBulkEntryReturnList()
            self.errnr = self.arapi.AREndBulkEntryTransaction(byref(self.context),
                                               actionType,
                                               byref(bulkEntryReturnList),
                                               byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('AREndBulkEntryTransaction failed')
            # we need to return the bulkEntryReturnList anyway, as it may contain
            # status information about the error!
            return bulkEntryReturnList
    
        def ARGetControlStructFields (self):
            '''ARGetControlStructFields returns the single pieces of the control record.
    
ARGetControlStructFields returns the single pieces of the control
record. This method actually is not necessary in python, as we have
direct access to the members of the struct; however to be
compatible with arsjython and ARSPerl, we implement this method.
Input: 
  :returns: (cacheId, errnr, operationTime, user, password, localeInfo, ,
         sessionId, authString, server)'''
            self.logger.debug('enter ARGetControlStructFields...')
            self.errnr = 0
            return (self.context.cacheId, self.errnr, 
                    self.context.operationTime, self.context.user,
                    self.context.password, self.context.localeInfo, 
                    self.context.sessionId,
                    self.context.authString, self.context.server)
                  
        def ARGetEntryBlock(self, entryBlockList, 
                            blockNumber = 0):
            '''ARGetEntryBlock retrieves a list of entries contained in a block of entries 
retrieved using ARGetListEntryBlocks.

Input: entryBlockList
       (optional) blockNumber (default = 0)
  :returns: AREntryListFieldValueList or None in case of failure'''
            self.logger.debug('enter ARGetEntryBlock')
            entryList = cars.AREntryListFieldValueList()
            self.errnr = self.arapi.ARGetEntryBlock(my_byref(entryBlockList),
                                                    blockNumber,
                                                    byref(entryList),
                                                    byref(self.arsl))
            if self.errnr < 2:
                return entryList
            else:
                self.logger.error('ARGetEntryBlock: failed')
                return None
    
        def ARGetListEntryBlocks(self, schema, 
                                 qualifier = None, 
                                 getListFields = None,
                                 sortList = None,
                                 numRowsPerBlock = 50,
                                 firstRetrieve = cars.AR_START_WITH_FIRST_ENTRY,
                                 maxRetrieve = cars.AR_NO_MAX_LIST_RETRIEVE,
                                 useLocale = False):
            '''ARGetListEntryBlocks retrieves a list of blocks of entries.
            
Data is returned as a data structure, 
AREntryListBlock. Entries are encapsulated in the AREntryListBlock 
data structure and divided into blocks of entries. You call
ARGetEntryBlock with a block number to return a list of entries for 
that block.
Input:
  :returns: (entryBlockList (AREntryBlockList), 
         numReturnedRows, 
         numMatches) or None in case of failure'''
            self.logger.debug('enter ARGetListEntryBlocks...')
            entryBlockList = cars.AREntryBlockList()
            numReturnedRows = c_uint()
            numMatches = c_uint()
            self.errnr = self.arapi.ARGetListEntryBlocks(byref(self.context),
                                          schema,
                                          my_byref(qualifier),
                                          my_byref(getListFields),
                                          my_byref(sortList),
                                          numRowsPerBlock,
                                          firstRetrieve,
                                          maxRetrieve,
                                          useLocale,
                                          byref(entryBlockList),
                                          byref(numReturnedRows),
                                          byref(numMatches),
                                          byref(self.arsl))
            if self.errnr < 2:
                return (entryBlockList, 
                        numReturnedRows.value, 
                        numMatches.value)
            else:
                self.logger.error('ARGetListEntryBlocks failed!')
                return None

        def ARGetMultipleCharMenus(self, changedSince = 0, 
                                   nameList = None,
                                   refreshCodeList = None,
                                   menuDefnList = None,
                                   helpTextList = None,
                                   timestampList = None,
                                   ownerList = None,
                                   lastChangedList = None,
                                   changeDiaryList = None,
                                   objPropListList = None):
            '''ARGetMultipleCharMenus retrieves information about a group of 
character menus.

This function
performs the same action as ARGetCharMenu but is easier to use and more
efficient than retrieving multiple entries one by one.
While the server returns information in lists for each item, pyars converts
this into a struct of its own.
Input: changedSince = 0, 
       (optional) nameList = None,
       (optional) refreshCodeList = None,
       (optional) menuDefnList = None,
       (optional) helpTextList = None,
       (optional) timestampList = None,
       (optional) ownerList = None,
       (optional) lastChangedList = None,
       (optional) changeDiaryList = None,
       (optional) objPropListList = None
  :returns: ARMenuList or None in case of failure'''
            self.logger.debug('enter ARGetMultipleCharMenus...')
            existList = cars.ARBooleanList()
            charMenuNameList = cars.ARNameList()
            self.errnr = self.arapi.ARGetMultipleCharMenus(byref(self.context),
                                                           changedSince,
                                                           my_byref(nameList),
                                                           byref(existList),
                                                           byref(charMenuNameList),
                                                           my_byref(refreshCodeList),
                                                           my_byref(menuDefnList),
                                                           my_byref(helpTextList),
                                                           my_byref(timestampList),
                                                           my_byref(ownerList),
                                                           my_byref(lastChangedList),
                                                           my_byref(changeDiaryList),
                                                           my_byref(objPropListList),
                                                           byref(self.arsl))
            if self.errnr < 2:
                tempArray = (ARMenuStruct * existList.numItems)()
                for i in range(existList.numItems):
                    if existList.booleanList[i]:
                        tempArray[i].name = charMenuNameList.nameList[i].value
                        if refreshCodeList: tempArray[i].refreshCode = refreshCodeList.intList[i]
                        if menuDefnList: tempArray[i].menuDefn = menuDefnList.list[i]
                        if helpTextList: tempArray[i].helpText = helpTextList.stringList[i]
                        if timestampList: tempArray[i].timestamp = timestampList.timestampList[i]
                        if ownerList: tempArray[i].owner = ownerList.nameList[i].value
                        if lastChangedList: tempArray[i].lastChanged = lastChangedList.nameList[i].value
                        if changeDiaryList: tempArray[i].changeDiary = changeDiaryList.stringList[i]
                        if objPropListList: tempArray[i].objPropList = objPropListList.propsList[i]
                    else:
                        self.logger.error('ARGetMultipleCharMenus: "%s" does not exist!' % nameList.nameList[i].value)
                return ARMenuList(existList.numItems, tempArray)
            else:
                self.logger.error('ARGetMultipleCharMenus: failed')
                return None

        def ARGetMultipleEscalations (self, changedSince = 0, 
                                      nameList = None,
                                      esclTmList = None,
                                      workflowConnectList = None,
                                      enableList = None,
                                      queryList = None,
                                      actionListList = None,
                                      elseListList = None,
                                      helpTextList = None,
                                      timestampList = None,
                                      ownerList = None,
                                      lastChangedList = None,
                                      changeDiaryList = None,
                                      objPropListList = None):
            '''ARGetMultipleEscalations retrieves information about a group 
of escalations.

This function performs
the same action as ARGetEscalation but is easier to use and more efficient than
retrieving multiple entries one by one.
While the server returns information in lists for each item, pyars converts
this into a struct of its own.
Input: changedSince = 0, 
      nameList = None,
      esclTmList = None,
      workflowConnectList = None,
      enableList = None,
      queryList = None,
      actionListList = None,
      elseListList = None,
      helpTextList = None,
      timestampList = None,
      ownerList = None,
      lastChangedList = None,
      changeDiaryList = None,
      objPropListList = None
  :returns: AREscalationList or None in case of failure'''
            self.logger.debug('enter ARGetMultipleEscalations...')
            existList = cars.ARBooleanList()
            esclNameList = cars.ARNameList()
            self.errnr = self.arapi.ARGetMultipleEscalations(byref(self.context),
                                                           changedSince,
                                                           my_byref(nameList),
                                                           byref(existList),
                                                           byref(esclNameList),
                                                           my_byref(esclTmList),
                                                           my_byref(workflowConnectList),
                                                           my_byref(enableList),
                                                           my_byref(queryList),
                                                           my_byref(actionListList),
                                                           my_byref(elseListList),
                                                           my_byref(helpTextList),
                                                           my_byref(timestampList),
                                                           my_byref(ownerList),
                                                           my_byref(lastChangedList),
                                                           my_byref(changeDiaryList),
                                                           my_byref(objPropListList),
                                                           byref(self.arsl))
            if self.errnr < 2:
                tempArray = (AREscalationStruct * existList.numItems)()
                for i in range(existList.numItems):
                    if existList.booleanList[i]:
                        tempArray[i].name = esclNameList.nameList[i].value
                        if esclTmList: tempArray[i].escalationTm = esclTmList.escalationTmList[i]
                        if workflowConnectList: tempArray[i].schemaList = workflowConnectList.workflowConnectList[i]
                        if enableList: tempArray[i].enable = enableList.intList[i]
                        if queryList: tempArray[i].query = queryList.qualifierList[i]
                        if actionListList: tempArray[i].actionList = actionListList.actionListList[i]
                        if elseListList: tempArray[i].elseList = elseListList.actionListList[i]
                        if helpTextList: tempArray[i].helpText = helpTextList.stringList[i]
                        if timestampList: tempArray[i].timestamp = timestampList.timestampList[i]
                        if ownerList: tempArray[i].owner = ownerList.nameList[i].value
                        if lastChangedList: tempArray[i].lastChanged = lastChangedList.nameList[i].value
                        if changeDiaryList: tempArray[i].changeDiary = changeDiaryList.stringList[i]
                        if objPropListList: tempArray[i].objPropList = objPropListList.propsList[i]
                    else:
                        self.logger.error('ARGetMultipleEscalations: "%s" does not exist!' % nameList.nameList[i].value)
                return AREscalationList(existList.numItems, tempArray)
            else:
                self.logger.error('ARGetMultipleEscalations: failed')
                return None
    
        def ARGetMultipleFilters(self, changedSince = 0, 
                                 nameList = None,
                                 orderList = None,
                                 workflowConnectList = None,
                                 opSetList = None,
                                 enableList = None,
                                 queryList = None,
                                 actionListList = None,
                                 elseListList = None,
                                 helpTextList = None,
                                 timestampList = None,
                                 ownerList = None,
                                 lastChangedList = None,
                                 changeDiaryList = None,
                                 objPropListList = None):
            '''ARGetMultipleFilters retrieves information about a group of filters.

This function performs the same
action as ARGetFilter but is easier to use and more efficient than retrieving
multiple entries one by one.
While the server returns information in lists for each item, pyars converts
this into a struct of its own.
Input:   (ARTimestamp) changedSince (optional, default = 0)
         (ARNameList) nameList (optional, default = None)
         (ARUnsignedIntList)orderList (optional, default = None)
         (ARWorkflowConnectList) workflowConnectList (optional, default = None)
         (ARUnsignedIntList) opSetList (optional, default = None)
         (ARUnsignedIntList) enableList (optional, default = None)
         (ARQualifierList) queryList (optional, default = None)
         (ARFilterActionListList) actionListList (optional, default = None)
         (ARFilterActionListList) elseListList (optional, default = None)
         (ARTextStringList) helpTextList (optional, default = None)
         (ARTimestampList) timestampList (optional, default = None)
         (ARAccessNameList) ownerList (optional, default = None)
         (ARAccessNameList) lastChangedList (optional, default = None)
         (ARTextStringList) changeDiaryList (optional, default = None)
         (ARPropListList) objPropListList (optional, default = None)
  :returns: ARFilterList or None in case of failure'''
            self.logger.debug('enter ARGetMultipleFilters...')
            existList = cars.ARBooleanList()
            filterNameList = cars.ARNameList()
            self.errnr = self.arapi.ARGetMultipleFilters(byref(self.context),
                                                         changedSince,
                                                         my_byref(nameList),
                                                         byref(existList),
                                                         byref(filterNameList),
                                                         my_byref(orderList),
                                                         my_byref(workflowConnectList),
                                                         my_byref(opSetList),
                                                         my_byref(enableList),
                                                         my_byref(queryList),
                                                         my_byref(actionListList),
                                                         my_byref(elseListList),
                                                         my_byref(helpTextList),
                                                         my_byref(timestampList),
                                                         my_byref(ownerList),
                                                         my_byref(lastChangedList),
                                                         my_byref(changeDiaryList),
                                                         my_byref(objPropListList),
                                                         byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARGetMultipleFilters: failed')
                return None
            else:
                tempArray = (ARFilterStruct * existList.numItems)()
                for i in range(existList.numItems):
                    if existList.booleanList[i]:
                        tempArray[i].name = filterNameList.nameList[i].value
                        if orderList: tempArray[i].order = orderList.intList[i]
                        if workflowConnectList: tempArray[i].schemaList = workflowConnectList.workflowConnectList[i]
                        if opSetList: tempArray[i].opSet = opSetList.intList[i]
                        if enableList: tempArray[i].enable = enableList.intList[i]
                        if queryList: tempArray[i].query = queryList.qualifierList[i]
                        if actionListList: tempArray[i].actionList = actionListList.actionListList[i]
                        if elseListList: tempArray[i].elseList = elseListList.actionListList[i]
                        if helpTextList: tempArray[i].helpText = helpTextList.stringList[i]
                        if timestampList: tempArray[i].timestamp = timestampList.timestampList[i]
                        if ownerList: tempArray[i].owner = ownerList.nameList[i].value
                        if lastChangedList: tempArray[i].lastChanged = lastChangedList.nameList[i].value
                        if changeDiaryList: tempArray[i].changeDiary = changeDiaryList.stringList[i]
                        if objPropListList: tempArray[i].objPropList = objPropListList.propsList[i]
                    else:
                        filter_ = self.ARGetFilter(nameList.nameList[i].value)
                        if self.errnr > 1:
                            self.logger.error('even second trial failed for %d) "%s"' % (
                                               i, nameList.nameList[i].value))
                        else:
                            tempArray[i] = filter_
#                            self.logger.error('second trial worked for %d) "%s"' % (
#                                              i, nameList.nameList[i].value))
                        # self.logger.error('ARGetMultipleFilters: "%s" does not exist!' % nameList.nameList[i].value)
                return ARFilterList(existList.numItems, tempArray)

        def ARGetMultipleVUIs(self, schema, 
                              wantList = None, 
                              changedSince = 0,
                              dPropListList = None, 
                              helpTextList = None,
                              timeStampList = None,
                              ownerList = None,
                              lastChangedList = None,
                              changeDiaryList = None):
            '''ARGetMultipleVUIs retrieves information about a group of form views
(VUIs).

PLEASE NOTE: This function seems to have a bug in the Remedy DLLs. The symptoms
are a mangeld localeList!!! Use with caution!

This function
performs the same action as ARGetVUI but is easier to use and more efficient
than retrieving multiple entries one by one.
While the server returns information in lists for each item, pyars converts
this into a struct of its own.
Input:  schema
       optional: wantList (ARInternalIdList, default = None),
       optional: changedSince (default = 0)
       optional: dPropListList
       optional: helpTextList
       optional: timeStampList
       optional: ownerList
       optional: lastChangedList
       optional: changeDiaryList
  :returns: ARVuiInfoList or None in case of failure'''
            self.logger.debug('enter ARGetMultipleVUIs...')
            existList = cars.ARBooleanList()
            gotList = cars.ARInternalIdList()
            nameList = cars.ARNameList()
            localeList = cars.ARLocaleList()
            vuiTypeList = cars.ARUnsignedIntList()
            self.errnr = self.arapi.ARGetMultipleVUIs(byref(self.context),
                                                     schema,
                                                     my_byref(wantList),
                                                     changedSince,
                                                     byref(existList),
                                                     byref(gotList),
                                                     byref(nameList),
                                                     byref(localeList),
                                                     byref(vuiTypeList),
                                                     my_byref(dPropListList),
                                                     my_byref(helpTextList),
                                                     my_byref(timeStampList),
                                                     my_byref(ownerList),
                                                     my_byref(lastChangedList),
                                                     my_byref(changeDiaryList),
                                                     byref(self.arsl))
            if self.errnr < 2:
                tempArray = (cars.ARVuiInfoStruct * existList.numItems)()
                for i in range(existList.numItems):
                    if existList.booleanList[i]:
                        tempArray[i].vuiId = gotList.internalIdList[i]
                        tempArray[i].vuiName = nameList.nameList[i].value
                        if timeStampList: tempArray[i].timestamp = timeStampList.timestampList[i]
                        if dPropListList: tempArray[i].props = dPropListList.propsList[i]
                        if ownerList: tempArray[i].owner = ownerList.nameList[i].value
#                       self.logger.debug('   ARGetMultipleVUIs: id: %s, struct %s, orig locale: %s' % (
#                           tempArray[i].vuiId, 
#                           localeList.localeList[i],
#                           localeList.localeList[i].value))
#                       tempArray[i].locale = localeList.localeList[i].value
                        tempArray[i].locale = '' # bug in AR DLL!!!
#                       self.logger.debug('   ARGetMultipleVUIs: copy == orig? %s' % (
#                                   tempArray[i].locale == localeList.localeList[i].value))
                        tempArray[i].vuiType = vuiTypeList.intList[i]
                        if lastChangedList: tempArray[i].lastChanged = lastChangedList.nameList[i].value
                        if helpTextList: tempArray[i].helpText = helpTextList.stringList[i]
                        if changeDiaryList: tempArray[i].changeDiary = changeDiaryList.stringList[i]
                    else:
                        self.logger.error('ARGetMultipleVUIs: "%d" does not exist!' % wantList.internalIdList[i])
                return cars.ARVuiInfoList(existList.numItems, tempArray)
            else:
                self.logger.error( "ARGetMultipleVUIs: failed for schema %s" %schema)
                return None 

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
            '''Login returns a context that has already been validated.
    
Input: server (can be specified as hostname:tcpport)
       username
       password
       (optional) language (default: '')
       (optional) authString (default: '')
       (optional) tcpport (default: 0)
       (optional) rpcnumber (default: 0)
       (optional) charSet (default: '')
       (optional) timeZone (default: '')
       (optional) customDateFormat (default: '')
       (optional) customTimeFormat (default: '')
       (optional) separators (default: '')
       (optional) cacheId (default: 0)
       (optional) operationTime (default: 0)
       (optional) sessionId (default: 0)
  :returns: control record (or None in case of failure)'''
            self.logger.debug('enter Login...')
            self.errnr = 0
            # look for a ':' in the hostname; if you find it, split off the
            # port number
            originalServer = server
            if server.find(':') > -1:
                server,tcpport = server.split(':')
                tcpport = int(tcpport)
                
            # setup the context
            if charSet.lower() == 'utf-8':
                (self.oldCharset, self.oldErrorhandling) = set_conversion_mode('utf-8', 
                                                                               'strict')
            self.context = cars.ARControlStruct(cacheId,
                                                operationTime,
                                                username,
                                                password,
                                                cars.ARLocalizationInfo(language, 
                                                                        charSet, 
                                                                        timeZone, 
                                                                        customDateFormat, 
                                                                        customTimeFormat, 
                                                                        separators), 
                                                sessionId,
                                                authString,
                                                server)
            # self.arsl = cars.ARStatusList()
            # initialize the API
            self.errnr = self.arapi.ARInitialization (byref(self.context),
                                                      byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('Login: error during Initialization')
                return None
            if server == '':
                serverList = self.ARGetListServer()
                if serverList is None or serverList.numItems == 0:
                    self.logger.error('no server name given, serverList is empty')
                    return None
                server = serverList.nameList[0].value
                self.logger.error('no server name given, selected %s as server' % (
                    server))
                self.ARFree(serverList)
    
            self.logger.debug('calling ARSetServerPort with %s:%d' % (server, tcpport))
            self.errnr = self.ARSetServerPort(server, tcpport, rpcnumber)
            if self.errnr > 1:
                self.logger.error('ARSetServerPort failed, still trying to login!') 
                pass
            adminFlag = cars.ARBoolean()
            subAdminFlag = cars.ARBoolean()
            customFlag = cars.ARBoolean()
            self.errnr = self.arapi.ARVerifyUser (byref(self.context),
                                                  byref(adminFlag),
                                                  byref(subAdminFlag),
                                                  byref(customFlag),
                                                  byref(self.arsl))
            if self.errnr < 2:
                return self.context
            else:
                self.logger.error('error logging in to: %s as %s' % (
                                    originalServer, 
                                    username))
                return None

        def Logoff (self):
            '''Logoff ends the session with the Remedy server. 
    
Input: 
  :returns: errnr (or no output if no session was active)'''
            self.logger.debug('enter Logoff...')
            self.errnr = 0
            if self.context:
                self.errnr = self.arapi.ARTermination(byref(self.context),
                                                      byref(self.arsl))
                if self.errnr > 1:
                    self.logger.error( "Logoff: failed")
                # restore the ctypes conversion mode to the one it was before
                # Login
                if self.oldCharset is not None:
                    set_conversion_mode(self.oldCharset, self.oldErrorhandling)
            return self.errnr

        def ARParseXMLDocument(self, xmlInputDoc, objectsToParse = None):
            '''ARParseXMLDocument parses the contents of an XML document.

Input: xmlInputDoc (ARXMLInputDoc; contains either the xml string or a reference
                to a file or a url)
  :returns: tuple of: (parsedStream (ARXMLParsedStream)
        parsedObjects (ARStructItemList)
        appBlockList (ARNameList))
        or None in case of failure'''
            self.logger.debug('enter ARParseXMLDocument...')
            self.errnr = 0
            parsedStream = cars.ARXMLParsedStream()
            parsedObjects = cars.ARStructItemList()
            appBlockList = cars.ARNameList()
            self.errnr = self.arapi.ARParseXMLDocument(byref(self.context),
                                                        byref(xmlInputDoc),
                                                        my_byref(objectsToParse),
                                                        byref(parsedStream),
                                                        byref(parsedObjects),
                                                        byref(appBlockList),
                                                        byref(self.arsl))
            if self.errnr < 2:
                return (parsedStream, parsedObjects, appBlockList)
            else:
                self.logger.error('ARParseXMLDocument failed')
                return None

    class ARS(ARS63):
        pass         

if cars.version >= 70:
    class ARSchema(Structure):
        _fields_ = [("name", cars.ARNameType),
                    ("schema", cars.ARCompoundSchema),
                    ("schemaInheritanceList", cars.ARSchemaInheritanceList),
                    ("groupList", cars.ARPermissionList),
                    ("admingrpList", cars.ARInternalIdList),
                    ("getListFields",  cars.AREntryListFieldList),
                    ("sortList", cars.ARSortList),
                    ("indexList", cars.ARIndexList),
                    ("archiveInfo", cars.ARArchiveInfoStruct),
                    ("auditInfo", cars.ARAuditInfoStruct),
                    ("defaultVui", cars.ARNameType),
                    ("helpText", c_char_p),
                    ("timestamp", cars.ARTimestamp),
                    ("owner", cars.ARAccessNameType),
                    ("lastChanged", cars.ARAccessNameType),
                    ("changeDiary", c_char_p),
                    ("objPropList", cars.ARPropList)]

    class ARSchemaList(Structure):
        _fields_ = [('numItems', c_uint),
                    ('schemaList',POINTER(ARSchema))]  
        
    class ARS70(ARS63):
        '''pythonic wrapper Class for Remedy C API, V7.0

Create an instance of ars and call its methods...
similar to ARSPerl and ARSJython'''
                
        def ARCreateField(self, schema, 
                          fieldId, 
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
            '''ARCreateField creates a new field.

ARCreateField creates a new field with the indicated name on the specified server. Forms
can contain data and nondata fields. Nondata fields serve several purposes.
Trim fields enhance the appearance and usability of the form (for example,
lines, boxes, or static text). Control fields provide mechanisms for executing
active links (for example, menus, buttons, or toolbar buttons). Other
nondata fields organize data for viewing (for example, pages and page
holders) or show data from another form (for example, tables and columns).
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
  :returns: fieldId (or None in case of failure)'''
            self.logger.debug('enter ARCreateField...')
            self.errnr = 0
            self.errnr = self.arapi.ARCreateField(byref(self.context),
                                                  schema, 
                                                  byref(fieldId), 
                                                  reservedIdOK,
                                                  fieldName, 
                                                  my_byref(fieldMap), 
                                                  dataType, 
                                                  option, 
                                                  createMode, 
                                                  fieldOption,
                                                  my_byref(defaultVal), 
                                                  my_byref(permissions),
                                                  my_byref(limit), 
                                                  my_byref(dInstanceList),
                                                  helpText, 
                                                  owner, 
                                                  changeDiary,
                                                  byref(self.arsl))
            if self.errnr < 2:
                return fieldId
            else:
                self.logger.error('ARCreateField: failed for %s on %s' % (fieldName, schema))
                return None

        def ARCreateSchema(self, name, 
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
            '''ARCreateSchema creates a new form.

ARCreateSchema creates a new form with the indicated name on the specified 
server. The nine required core fields are automatically associated with the 
new form.
Input: (ARNameType) name of schema
       (ARCompoundSchema) schema, 
       (ARSchemaInheritanceList) schemaInheritanceList (will be set to None, as it is reserved for future use), 
       (ARPermissionList) groupList, 
       (ARInternalIdList) admingrpList, 
       (AREntryListFieldList) getListFields,
       (ARSortList) sortList, 
       (ARIndexList) indexList, 
       (ARArchiveInfoStruct) archiveInfo,
       (ARAuditInfoStruct) auditInfo, 
       (ARNameType) defaultVui,
       (c_char_p) helpText (optional, default =None)
       (ARAccessNameType) owner (optional, default =None)
       (c_char_p) changeDiary (optional, default =None)
       (ARPropList) objPropList (optional, default =None)   
  :returns: errnr'''
            self.logger.debug('enter ARCreateSchema...')
            self.errnr = 0
            schemaInheritanceList = None # reserved for future use...
            self.errnr = self.arapi.ARCreateSchema(byref(self.context),
                                                   name, 
                                                   my_byref(schema), 
                                                   my_byref(schemaInheritanceList), 
                                                   my_byref(groupList), 
                                                   my_byref(admingrpList), 
                                                   my_byref(getListFields),
                                                   my_byref(sortList), 
                                                   my_byref(indexList), 
                                                   my_byref(archiveInfo),
                                                   my_byref(auditInfo), 
                                                   defaultVui,
                                                   helpText, 
                                                   owner, 
                                                   changeDiary, 
                                                   my_byref(objPropList),
                                                   byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARCreateSchema failed for schema %s.' % name)
            return self.errnr        

        def ARGetClientCharSet(self):
            '''ARGetClientCharSet retrieves a string that represents the name of the character set the client is
using. The API assumes that all character data the client passes it is encoded
in this character set, and returns all character data encoded in this character
set.
Use the ARControlStruct localeInfo.charSet field to set the client
character set as described under ARInitialization().

Input: 
  :returns: string or None in case of failure'''
            self.logger.debug('enter ARGetClientCharSet...')
            self.errnr = 0
            string = c_char_p()
            self.errnr = self.arapi.ARGetClientCharSet(byref(self.context),
                                               string,
                                               byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARGetClientCharSet: failed')
                return None
            else:
                return string.value

        def ARGetField (self, schema, fieldId):
            '''ARGetField retrieves the information for one field on a form.

ARGetField returns a ARFieldInfoStruct filled for a given fieldid.
Input: (ARNameType) schema
       (ARInternalId) fieldId
  :returns: ARFieldInfoStruct (or None in case of failure)'''
            self.logger.debug('enter ARGetField...')
            if schema.strip() == '' or schema == cars.AR_CURRENT_TRAN_TAG or \
                schema == cars.AR_CURRENT_SCHEMA_TAG:
                self.logger.error('ARGetField: no useful schema given')
                self.errnr = 2
                return None
            try:
                if not isinstance(fieldId,int):
                    fieldId=int(fieldId)
            except:
                self.logger.error('ARGetField: no valid fieldid given')
                self.errnr = 2
                return None
            fieldName = cars.ARNameType()
            fieldMap = cars.ARFieldMappingStruct()
            dataType = c_uint()
            option = c_uint()
            createMode = c_uint()
            fieldOption = c_uint()
            defaultVal = cars.ARValueStruct()
            # if we ask for permissions we need admin rights...
            permissions = cars.ARPermissionList()
            limit = cars.ARFieldLimitStruct()
            dInstanceList = cars.ARDisplayInstanceList()
            helpText = c_char_p()
            timestamp = cars.ARTimestamp()
            owner = cars.ARAccessNameType()
            lastChanged = cars.ARAccessNameType()
            changeDiary = c_char_p()
            self.errnr = self.arapi.ARGetField(byref(self.context),
                                              schema,
                                              fieldId,
                                              fieldName,
                                              byref(fieldMap),
                                              byref(dataType),
                                              byref(option),
                                              byref(createMode),
                                              byref(fieldOption),
                                              byref(defaultVal),
                                              byref(permissions),
                                              byref(limit),
                                              byref(dInstanceList),
                                              byref(helpText),
                                              byref(timestamp),
                                              owner,
                                              lastChanged,
                                              byref(changeDiary),
                                              byref(self.arsl))
            if self.errnr < 2:
                return cars.ARFieldInfoStruct(fieldId,
                                           fieldName.value,
                                           timestamp,
                                           fieldMap,
                                           dataType,
                                           option,
                                           createMode,
                                           fieldOption,
                                           defaultVal,
                                           permissions,
                                           limit,
                                           dInstanceList,
                                           owner.value,
                                           lastChanged.value,
                                           helpText.value,
                                           changeDiary.value)
            else:
                self.logger.error('ARGetField: failed for schema %s and fieldid %d' % (
                        schema, fieldId))
                return None

        def ARGetMultipleFields (self, schemaString, 
                                 idList=None,
                                 fieldId2=None,
                                 fieldName=None,
                                 fieldMap=None,
                                 dataType=None,
                                 option=None,
                                 createMode=None,
                                 fieldOption=None,
                                 defaultVal=None,
                                 permissions=None,
                                 limit=None,
                                 dInstanceList=None,
                                 helpText=None,
                                 timestamp=None,
                                 owner=None,
                                 lastChanged=None,
                                 changeDiary=None):
            '''ARGetMultipleFields returns a list of the fields and their attributes.
       
ARGetMultipleFields returns list of field definitions for a specified form.
In contrast to the C APi this function constructs an ARFieldInfoList
for the form and returns all information this way.
Input: schemaString
      (ARInternalIdList) idList (optional; default: None) we currently
              expect a real ARInternalIdList, because then it's very
              easy to simply hand over the result of a GetListField
              call
      (ARInternalIdList) fieldId2: although it is declared optional (to be consistent
           with the AR API), this needs to be set (if not, this function will create
           an ARInternalIdList) (see the output for an explanation)
      (ARNameList) fieldName 
      (ARFieldMappingList) fieldMap 
      (ARUnsignedIntList) dataType 
      (ARUnsignedIntList) option 
      (ARUnsignedIntList) createMode 
      (ARUnsignedIntList) fieldOption 
      (ARValueList) defaultVal 
      (ARPermissionListList) permissions 
      (ARFieldLimitList) limit 
      (ARDisplayInstanceListList) dInstanceList 
      (ARTextStringList) helpText 
      (ARTimestampList) timestamp 
      (ARAccessNameList) owner 
      (ARAccessNameList) lastChanged 
      (ARTextStringList) changeDiary either hand over None (as is
              default) or supply according ARxxxxList for the 
              API call. 
  :returns: ARFieldInfoList; contains entries for all ids that you handed over;
       if a field could not be retrieved, the according fieldid will be None; that's
       the only way to decide if the list could be retrieved or not!
       (all input lists should contain the return values from the server, but we
        will also create an ARFieldInfoList) or None in case of failure'''
            self.logger.debug('enter ARGetMultipleFields...')
            # we assume that we have been handed over a string
    #       if self.schemaExists(schemaString) == 0:
    #           self.logger.error('Schema %s does not exist on server.' % (schemaString))
    #           return None
            existList = cars.ARBooleanList()
            # fieldId2 needs to be created -- this will be the identifier for the caller, 
            # if a field could be retrieved or not!
            if fieldId2 is None:
                fieldId2 = cars.ARInternalIdList()
            assert isinstance(schemaString, str)
            assert isinstance(idList, cars.ARInternalIdList) or idList is None
            assert isinstance(fieldId2, cars.ARInternalIdList)
            assert isinstance(fieldName, cars.ARNameList) or fieldName is None
            assert isinstance(fieldMap, cars.ARFieldMappingList) or fieldMap is None
            assert isinstance(dataType, cars.ARUnsignedIntList) or dataType is None
            assert isinstance(option, cars.ARUnsignedIntList) or option is None
            assert isinstance(createMode, cars.ARUnsignedIntList) or createMode is None
            assert isinstance(fieldOption, cars.ARUnsignedIntList) or fieldOption is None
            assert isinstance(defaultVal, cars.ARValueList) or defaultVal is None
            assert isinstance(permissions, cars.ARPermissionListList) or permissions is None
            assert isinstance(limit, cars.ARFieldLimitList) or limit is None
            assert isinstance(dInstanceList, cars.ARDisplayInstanceListList) or dInstanceList is None
            assert isinstance(helpText, cars.ARTextStringList) or helpText is None
            assert isinstance(timestamp, cars.ARTimestampList) or timestamp is None
            assert isinstance(owner, cars.ARAccessNameList) or owner is None
            assert isinstance(lastChanged, cars.ARAccessNameList) or lastChanged is None
            assert isinstance(changeDiary, cars.ARTextStringList) or changeDiary is None
           
            self.errnr = self.arapi.ARGetMultipleFields(byref(self.context),
                                                  schemaString,
                                                  my_byref(idList),
                                                  byref(existList),
                                                  byref(fieldId2),
                                                  my_byref(fieldName),
                                                  my_byref(fieldMap),
                                                  my_byref(dataType),
                                                  my_byref(option),
                                                  my_byref(createMode),
                                                  my_byref(fieldOption),
                                                  my_byref(defaultVal),
                                                  my_byref(permissions),
                                                  my_byref(limit),
                                                  my_byref(dInstanceList),
                                                  my_byref(helpText),
                                                  my_byref(timestamp),
                                                  my_byref(owner),
                                                  my_byref(lastChanged),
                                                  my_byref(changeDiary),
                                                  byref(self.arsl))
    #       self.logger.debug('GetMultipleFields: after API call')
            if idList and idList.numItems != existList.numItems:
                self.logger.error('ARGetMultipleFields returned another number of fields for form %s than expected!' % (schemaString))
            if self.errnr < 2:
                # from what the API returns, create an ARFieldInfoList
                tempList = (cars.ARFieldInfoStruct * existList.numItems)()
                for i in range(existList.numItems):
                    if existList.booleanList[i]:
                        if fieldId2:
                            tempList[i].fieldId = fieldId2.internalIdList[i]
                        if fieldName:
                            tempList[i].fieldName = fieldName.nameList[i].value
                        if timestamp:
                            tempList[i].timestamp = timestamp.timestampList[i]
                        if fieldMap:
                            tempList[i].fieldMap = fieldMap.mappingList[i]
                        if dataType:
                            tempList[i].dataType = dataType.intList[i]
                        if option:
                            tempList[i].option = option.intList[i]
                        if createMode:
                            tempList[i].createMode = createMode.intList[i]
                        if fieldOption:
                            tempList[i].fieldOption = fieldOption.intList[i]
                        if defaultVal:
                            tempList[i].defaultVal = defaultVal.valueList[i]
                        # if the user does not have admin rights, permissions will be a list of 0 items!
                        if permissions and permissions.numItems > i:
                            tempList[i].permList = permissions.permissionList[i]
                        if limit:
                            tempList[i].limit = limit.fieldLimitList[i]
                        if dInstanceList:
                            tempList[i].dInstanceList = dInstanceList.dInstanceList[i]
                        if owner:
                            tempList[i].owner = owner.nameList[i].value
                        if lastChanged:
                            tempList[i].lastChanged = lastChanged.nameList[i].value
                        if helpText:
                            tempList[i].helpText = helpText.stringList[i]
                        if changeDiary:
                            tempList[i].changeDiary = changeDiary.stringList[i]
                    else:
                        self.logger.error( "ARGetMultipleFields: failed to retrieve field# %d from %s" % (
                                    i, schemaString))
                        tempList[i].fieldId = None
                        tempList[i].fieldName = None
#                tempRes = cars.ARFieldInfoList(existList.numItems, tempList)
                return cars.ARFieldInfoList(existList.numItems, tempList)
            else:
                self.logger.error( "ARGetMultipleFields: failed for %s" % (
                           schemaString))
                return None

        def ARGetMultipleSchemas(self, changedSince=0, 
                                schemaTypeList = None,
                                nameList=None, 
                                fieldIdList=None,
                                schemaList = None,
                                schemaInheritanceListList = None, # reserved for future use
                                groupListList = None,
                                admingrpListList = None,
                                getListFieldsList = None,
                                sortListList = None,
                                indexListList = None,
                                archiveInfoList = None,
                                auditInfoList = None,
                                defaultVuiList = None,
                                helpTextList = None,
                                timestampList = None,
                                ownerList = None,
                                lastChangedList = None,
                                changeDiaryList = None,
                                objPropListList = None):
            '''ARGetMultipleSchemas retrieves information about several schemas
from the server at once.

This information does not include the form field definitions (see ARGetField). This
function performs the same action as ARGetSchema but is easier to use and
more efficient than retrieving multiple forms one by one.
Information is returned in lists for each item, with one item in the list for
each form returned. For example, if the second item in the list for existList is
TRUE, the name of the second form is returned in the second item in the list
for schemaNameList.
Input:  (ARTimestamp) changedSince=0, 
        (ARUnsignedIntList) schemaTypeList (optional, default = None),
        (ARNameList) nameList (optional, default = None), 
        (ARInternalIdList) fieldIdList (optional, default =None),
        (ARCompoundSchemaList) schemaList (optional, default = None),
        (ARSchemaInheritanceListList) schemaInheritanceListList (optional, default  = None), # reserved for future use
        (ARPermissionListList) groupListList (optional, default  = None),
        (ARInternalIdListList) admingrpListList (optional, default  = None),
        (AREntryListFieldListList) getListFieldsList (optional, default  = None),
        (ARSortListList) sortListList (optional, default  = None),
        (ARSortListList) indexListList (optional, default  = None),
        (ARSortListList) archiveInfoList (optional, default  = None),
        (ARAuditInfoList) auditInfoList (optional, default  = None),
        (ARNameList) defaultVuiList (optional, default  = None),
        (ARTextStringList) helpTextList (optional, default  = None),
        (ARTimestampList) timestampList (optional, default  = None),
        (ARAccessNameList) ownerList (optional, default  = None),
        (ARAccessNameList) lastChangedList (optional, default  = None),
        (ARTextStringList) changeDiaryList (optional, default  = None),
        (ARPropListList) objPropListList (optional, default = None)
  :returns: ARSchemaList or None in case of failure'''
            self.logger.debug('enter ARGetMultipleSchemas...')
            self.errnr = 0
            existList = cars.ARBooleanList()
            schemaNameList = cars.ARNameList()
            schemaInheritanceListList = None
            self.errnr = self.arapi.ARGetMultipleSchemas(byref(self.context),
                                                         changedSince, 
                                           my_byref(schemaTypeList),
                                           my_byref(nameList), 
                                           my_byref(fieldIdList),
                                           my_byref(existList),
                                           my_byref(schemaNameList),
                                           my_byref(schemaList),
                                           my_byref(schemaInheritanceListList),
                                           my_byref(groupListList),
                                           my_byref(admingrpListList),
                                           my_byref(getListFieldsList),
                                           my_byref(sortListList),
                                           my_byref(indexListList),
                                           my_byref(archiveInfoList),
                                           my_byref(auditInfoList),
                                           my_byref(defaultVuiList),
                                           my_byref(helpTextList),
                                           my_byref(timestampList),
                                           my_byref(ownerList),
                                           my_byref(lastChangedList),
                                           my_byref(changeDiaryList),
                                           my_byref(objPropListList),
                                           byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARGetMultipleSchemas: failed')
                return None
            else:
                # self.logger.debug('ARGetMultipleSchemas: after API call')
                tempArray = (ARSchema * existList.numItems)()
                for i in range(existList.numItems):
                    tempArray[i].name = schemaNameList.nameList[i].value
                    if existList.booleanList[i]:
                        if schemaList: tempArray[i].schema = schemaList.compoundSchema[i]
                        if groupListList: tempArray[i].groupList = groupListList.permissionList[i]
                        if admingrpListList: tempArray[i].admingrpList = admingrpListList.internalIdListList[i]
                        if getListFieldsList: tempArray[i].getListFields = getListFieldsList.listFieldList[i]
                        if indexListList: tempArray[i].sortList = sortListList.sortListList[i]
                        if indexListList: tempArray[i].indexList = indexListList.indexListList[i]
                        if archiveInfoList: tempArray[i].archiveInfo = archiveInfoList.archiveInfoList[i]
                        if auditInfoList: tempArray[i].auditInfo = auditInfoList.auditInfoList[i]
                        if defaultVuiList: tempArray[i].defaultVui = defaultVuiList.nameList[i].value
                        if helpTextList: tempArray[i].helpText = helpTextList.stringList[i]
                        if timestampList: tempArray[i].timestamp = timestampList.timestampList[i]
                        if ownerList: tempArray[i].owner = ownerList.nameList[i].value
                        if lastChangedList: tempArray[i].lastChanged = lastChangedList.nameList[i].value
                        if changeDiaryList: tempArray[i].changeDiary = changeDiaryList.stringList[i]
                        if objPropListList: tempArray[i].objPropList = objPropListList.propsList[i]
                    else:
                        self.logger.error('ARGetMultipleSchemas: "%s" does not exist!' % nameList.nameList[i].value)
                return ARSchemaList(existList.numItems, tempArray)

        def ARGetSchema (self, name):
            '''ARGetSchema returns all information about a schema.
        
This information does not include the form's field
definitions (see ARGetField).
Input: (ARNameType) name
  :returns: ARSchema or None in case of failure'''
            self.logger.debug('enter ARGetSchema...')
            self.errnr = 0
            schema = cars.ARCompoundSchema()
            schemaInheritanceList = cars.ARSchemaInheritanceList()
            groupList = cars.ARPermissionList()
            admingrpList = cars.ARInternalIdList()
            getListFields = cars.AREntryListFieldList()
            sortList = cars.ARSortList()
            indexList = cars.ARIndexList()
            archiveInfo = cars.ARArchiveInfoStruct()
            auditInfo = cars.ARAuditInfoStruct()
            defaultVui = cars.ARNameType()
            helpText = c_char_p()
            timestamp = cars.ARTimestamp()
            owner = cars.ARAccessNameType()
            lastChanged = cars.ARAccessNameType()
            changeDiary = c_char_p()
            objPropList = cars.ARPropList()
            self.errnr = self.arapi.ARGetSchema (byref(self.context),
                                            name,
                                            byref(schema),
                                            byref(schemaInheritanceList),
                                            byref(groupList),
                                            byref(admingrpList),
                                            byref(getListFields),
                                            byref(sortList),
                                            byref(indexList),
                                            byref(archiveInfo),
                                            byref(auditInfo),
                                            defaultVui,
                                            byref(helpText),
                                            byref(timestamp),
                                            owner,
                                            lastChanged,
                                            byref(changeDiary),
                                            byref(objPropList),
                                            byref(self.arsl))
            if self.errnr < 2:
                return ARSchema(name, 
                                schema,
                                schemaInheritanceList,
                                groupList,
                                admingrpList,
                                getListFields,
                                sortList,
                                indexList,
                                archiveInfo,
                                auditInfo,
                                defaultVui.value,
                                helpText,
                                timestamp,
                                owner.value,
                                lastChanged.value,
                                changeDiary,
                                objPropList)
            else:
                self.logger.error( "ARGetSchema: failed for schema %s" % name)
                return None

        def ARGetServerCharSet(self):
            '''ARGetServerCharSet retrieves a string that represents the name of the character set the API library
uses to communicate with the server. If this differs from the client charset,
the API will convert the data to the right character set.

Input:
  :returns: string or None in case of failure'''
            self.logger.debug('enter ARGetServerCharSet...')
            self.errnr = 0
            string = c_char_p()
            self.errnr = self.arapi.ARGetServerCharSet(byref(self.context),
                                               string,
                                               byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARGetServerCharSet: failed')
                return None
            else:
                return string.value

        def ARServiceEntry(self, formName,
                           entryIdList = None,
                           fieldValueList = None,
                           internalIdList = None):
            '''ARServiceEntry takes an entry ID with a list of input field values, 
executes filter workflow, and returns a list of output fields without
writing the specified entry to the database. Thus, it eliminates the ARSetEntry 
call, ARGetEntry call, the ARDeleteEntry call, and several filters.
This call can work with an AR System web service to obtain external services, or
with a Set Fields filter action to consume an internal AR System service.

Input: (ARNameType) formName
        (AREntryIdList) entryIdList (optional, default = None)
        (ARFieldValueList) fieldValueList (optional, default = None)
        (ARInternalIdList) internalIdList (optional, default = None)
  :returns: ARFieldValueList or None in case of failure'''
            self.logger.debug('enter ARServiceEntry...')
            self.errnr = 0
            outputFieldList = cars.ARFieldValueList()
            self.errnr = self.arapi.ARServiceEntry(byref(self.context),
                                                   formName,
                                                   my_byref(entryIdList),
                                                   my_byref(fieldValueList),
                                                   my_byref(internalIdList),
                                                   byref(outputFieldList),
                                                   byref(self.arsl))
            if self.errnr < 2:
                return outputFieldList
            else:
                self.logger.error('ARServiceEntry has failed.')
                return None
                                               
        def ARSetField(self, schema, 
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
                       setFieldOptions = 0):
            '''ARSetField updates the definition for the form field.
            
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
  :returns: errnr'''
            self.logger.debug('enter ARSetField...')
            self.errnr = 0
            if option is not None and not isinstance(option, c_uint):
                option = c_uint(option)
            if createMode is not None and not isinstance(createMode, c_uint):
                createMode = c_uint(createMode)
            if fieldOption is not None and not isinstance(fieldOption, c_uint):
                fieldOption = c_uint(fieldOption)
            self.errnr = self.arapi.ARSetField(byref(self.context),
                                               schema, 
                                               fieldId,
                                               fieldName, 
                                               my_byref(fieldMap), 
                                               my_byref(option), 
                                               my_byref(createMode),
                                               my_byref(fieldOption),
                                               my_byref(defaultVal),
                                               my_byref(permissions), 
                                               my_byref(limit), 
                                               my_byref(dInstanceList), 
                                               helpText, 
                                               owner, 
                                               changeDiary,
                                               setFieldOptions,
                                               byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARSetField: failed for %s:%d' % (schema,fieldId))
            return self.errnr

        def ARSetImpersonatedUser(self, name):
            '''ARSetImpersonatedUser sets a user profile.

Enables plug-ins, the mid tier, and other programs (such as the Email
Engine) to run as an administrator but to perform operations as a specific
user (with the user's permissions and licensing in effect).
Input: name (ARNameType)
  :returns: errnr'''
            self.logger.debug('enter ARSetImpersonatedUser...')
            self.errnr = 0
            self.errnr = self.arapi.ARSetImpersonatedUser(byref(self.context),
                                                          name,
                                                          byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARSetImpersonatedUser: failed for %s' % (name))
            return self.errnr
        
        def ARSetSchema(self, name,
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
            '''ARSetSchema updates the definition for the form.

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
        (optional) setOption (optional, default = None)
  :returns: errnr'''
            self.logger.debug('enter ARSetSchema...')
            self.errnr = 0
            schemaInheritanceList = None
            self.errnr = self.arapi.ARSetSchema(byref(self.context),
                                                name,
                                                newName,
                                                my_byref(schema),
                                                my_byref(schemaInheritanceList),
                                                my_byref(groupList),
                                                my_byref(admingrpList),
                                                my_byref(getListFields),
                                                my_byref(sortList),
                                                my_byref(indexList),
                                                my_byref(archiveInfo),
                                                my_byref(auditInfo),
                                                defaultVui,
                                                helpText,
                                                owner,
                                                changeDiary,
                                                my_byref(objPropList),
                                                byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARSetSchema failed for schema %s' % (name))
            return self.errnr 

        def ARGetFieldFromXML(self, parsedStream, fieldName):
            '''ARGetFieldFromXML retrieves a filter from an XML document.

Input: (ARXMLParsedStream) parsedStream
       (ARNameType) menuName
  :returns: (ARFieldInfoStruct, arDocVersion)
            or None in case of failure'''
            self.logger.debug('enter ARGetFieldFromXML...')
            self.errnr = 0
            fieldName = cars.ARNameType()
            fieldId = cars.ARInternalId()
            fieldMap = cars.ARFieldMappingStruct()
            dataType = c_uint()
            option = c_uint()
            createMode = c_uint()
            fieldOption = c_uint()
            defaultVal = cars.ARValueStruct()
            # if we ask for permissions we need admin rights...
            permissions = cars.ARPermissionList()
            limit = cars.ARFieldLimitStruct()
            dInstanceList = cars.ARDisplayInstanceList()
            helpText = c_char_p()
            timestamp = cars.ARTimestamp()
            owner = cars.ARAccessNameType()
            lastChanged = cars.ARAccessNameType()
            changeDiary = c_char_p()
            arDocVersion = c_uint()
            self.errnr = self.arapi.ARGetFieldFromXML(byref(self.context),
                                                      my_byref(parsedStream),
                                                      fieldName,
                                                      byref(fieldId),
                                                      byref(fieldMap),
                                                      byref(dataType),
                                                      byref(option),
                                                      byref(createMode),
                                                      byref(fieldOption),
                                                      byref(defaultVal),
                                                      byref(permissions),
                                                      byref(limit),
                                                      byref(dInstanceList),
                                                      byref(helpText),
                                                      byref(timestamp),
                                                      owner,
                                                      lastChanged,
                                                      byref(changeDiary),
                                                      byref(arDocVersion),
                                                      byref(self.arsl))
            if self.errnr < 2:
                return (cars.ARFieldInfoStruct(fieldId,
                                               fieldName,
                                               timestamp,
                                               fieldMap,
                                               dataType,
                                               option,
                                               createMode,
                                               fieldOption,
                                               defaultVal,
                                               permissions,
                                               limit,
                                               dInstanceList,
                                               owner.value,
                                               lastChanged.value,
                                               helpText.value,
                                               changeDiary.value),
                       arDocVersion)
            else:
                self.logger.error('ARGetFieldFromXML: failed for fieldName %s' % (
                        fieldName))
                return None


        def ARGetSchemaFromXML(self, parsedStream, schemaName):
            '''ARGetSchemaFromXML retrieves schemas from an XML document.
    
Input: (ARXMLParsedStream) parsedStream
       (ARNameType) schemaName
  :returns: (ARSchema, 
        nextFieldID, 
        coreVersion, 
        upgradeVersion,
        fieldInfoList,
        vuiInfoList, 
        arDocVersion)
        or None in case of failure'''
            self.logger.debug('enter ARGetSchemaFromXML...')
            self.errnr = 0
            # first define all ARSchema fields
            schema = cars.ARCompoundSchema()
            groupList = cars.ARPermissionList()
            admingrpList = cars.ARInternalIdList()
            getListFields = cars.AREntryListFieldList()
            sortList = cars.ARSortList()
            indexList = cars.ARIndexList()
            archiveInfo = cars.ARArchiveInfoStruct()
            auditInfo = cars.ARAuditInfoStruct()
            defaultVui = cars.ARNameType()
            helpText = c_char_p()
            timestamp = cars.ARTimestamp()
            owner = cars.ARAccessNameType()
            lastChanged = cars.ARAccessNameType()
            changeDiary = c_char_p()
            objPropList = cars.ARPropList()
            
            # now define the extensions that this API call offers
            nextFieldID = cars.ARInternalId()
            coreVersion = c_ulong()
            upgradeVersion = c_int()
            fieldInfoList = cars.ARFieldInfoList()
            vuiInfoList = cars.ARVuiInfoList()
            arDocVersion = c_uint()
            self.errnr = self.arapi.ARGetSchemaFromXML (byref(self.context),
                                                        my_byref(parsedStream),
                                                        schemaName,
                                                        byref(schema),
                                                        byref(groupList),
                                                        byref(admingrpList),
                                                        byref(getListFields),
                                                        byref(sortList),
                                                        byref(indexList),
                                                        byref(archiveInfo),
                                                        byref(auditInfo),
                                                        defaultVui,
                                                        byref(nextFieldID),
                                                        byref(coreVersion),
                                                        byref(upgradeVersion),
                                                        byref(fieldInfoList),
                                                        byref(vuiInfoList),
                                                        owner,
                                                        lastChanged,
                                                        byref(timestamp),
                                                        byref(helpText),
                                                        byref(changeDiary),
                                                        byref(objPropList),
                                                        byref(arDocVersion),
                                                        byref(self.arsl))
            if self.errnr < 2:
                return (ARSchema(schemaName,
                                schema,
                                groupList,
                                admingrpList,
                                getListFields,
                                sortList,
                                indexList,
                                archiveInfo,
                                auditInfo,
                                defaultVui,
                                helpText,
                                timestamp,
                                owner,
                                lastChanged,
                                changeDiary,
                                objPropList), 
                        nextFieldID, 
                        coreVersion, 
                        upgradeVersion,
                        fieldInfoList,
                        vuiInfoList, 
                        arDocVersion)
            else:
                self.logger.error( "ARGetSchemaFromXML: failed for schema %s" % schemaName)
                return None

        def ARSetFieldToXML(self, fieldName, 
                            xmlDocHdrFtrFlag = False,
                            fieldID = 0,
                            fieldMapping = None,
                            dataType = 0,
                            entryMode = 0,
                            createMode = 0,
                            fieldOption = 0,
                            defaultValue = None,
                            permissionList = None,
                            fieldLimit = None,
                            dInstanceList = None,
                            owner = '',
                            lastModifiedBy = '',
                            modifiedDate = 0,
                            helpText = None,
                            changeHistory = None,
                            arDocVersion = c_uint(0)):
            '''ARSetFieldToXML converts a field to XML.

Input: 
  :returns: string containing the XML
        or None in case of failure'''
            self.logger.debug('enter ARSetFieldToXML...')
            self.errnr = 0
            if not isinstance(fieldID, c_uint):
                fieldID = c_uint(fieldID)
            if not isinstance(dataType, c_uint):
                dataType = c_uint(dataType)
            if not isinstance(entryMode, c_uint):
                entryMode = c_uint(entryMode)
            if not isinstance(createMode, c_uint):
                createMode = c_uint(createMode)
            if not isinstance(fieldOption, c_uint):
                fieldOption = c_uint(fieldOption)
            if not isinstance(modifiedDate, cars.ARTimestamp):
                modifiedDate = cars.ARTimestamp(modifiedDate)
            if not isinstance(arDocVersion, c_uint):
                arDocVersion = c_uint(arDocVersion)
            xml = cars.ARXMLOutputDoc(cars.AR_XML_DOC_CHAR_STR)
            self.errnr = self.arapi.ARSetFieldToXML(byref(self.context),
                                                    byref(xml),
                                                    xmlDocHdrFtrFlag,
                                                    fieldName,
                                                    my_byref(fieldID),
                                                    my_byref(fieldMapping),
                                                    my_byref(dataType),
                                                    my_byref(entryMode),
                                                    my_byref(createMode),
                                                    my_byref(fieldOption),
                                                    my_byref(defaultValue),
                                                    my_byref(permissionList),
                                                    my_byref(fieldLimit),
                                                    my_byref(dInstanceList),
                                                    owner,
                                                    lastModifiedBy,
                                                    my_byref(modifiedDate),
                                                    helpText,
                                                    changeHistory,
                                                    my_byref(arDocVersion),
                                                    byref(self.arsl))
            if self.errnr < 2:
                return xml.u.charBuffer
            else:
                self.logger.error("ARSetFieldToXML returned an error")
                return None

        def ARSetSchemaToXML (self, schemaName, xmlDocHdrFtrFlag=False,
                            compoundSchema=None,
                            permissionList=None,
                            subAdminGrpList=None,
                            getListFields=None,
                            sortList=None,
                            indexList=None,
                            archiveInfo = None,
                            auditInfo = None,
                            defaultVui = '',
                            nextFieldID = 0,
                            coreVersion = 0,
                            upgradeVersion=0,
                            fieldInfoList=None,
                            vuiInfoList=None,
                            owner='',
                            lastModifiedBy='',
                            modifiedDate=0,
                            helpText='',
                            changeHistory='',
                            objPropList=None,
                            arDocVersion = 0):
            '''ARSetSchemaToXML dump Schema to XML according...

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
       (optional) archiveInfo (default: None),
       (optional) auditInfo (default: None),
       (optional) defaultVui (default: None)
       (optional) nextFieldID (default: None)
       (optional) coreVersion (default: 0)
       (optional) upgradeVersion (default: 0)
       (optional) fieldInfoList (default: None)
       (optional) vuiInfoList (default: None)
       (optional) owner (default: '')
       (optional) lastModifiedBy (default: '')
       (optional) modifiedDate (default: 0)
       (optional) helpText (default: '')
       (optional) changeHistory (default: '')
       (optional) objPropList (default: None)
       (optional) arDocVersion (default: 0)
  :returns: string containing the XML (or None in case of failure)'''
            self.logger.debug('enter ARSetSchemaToXML...')
            self.errnr = 0
            # initialize to return the XML as a string (not as a file)
            xml = cars.ARXMLOutputDoc(cars.AR_XML_DOC_CHAR_STR)
            if not isinstance(modifiedDate, cars.ARTimestamp):
                modifiedDate = cars.ARTimestamp(modifiedDate)
            if not isinstance(nextFieldID, cars.ARInternalId):
                nextFieldID = cars.ARInternalId(nextFieldID)
            if not isinstance(coreVersion, c_ulong):
                coreVersion = c_ulong(coreVersion)
            if not isinstance(upgradeVersion, c_int):
                upgradeVersion = c_int(upgradeVersion)
            if not isinstance(arDocVersion, c_uint):
                arDocVersion = c_uint(arDocVersion)
            
            assert isinstance(xmlDocHdrFtrFlag, int)
            assert isinstance(schemaName, str)
            assert isinstance(compoundSchema, cars.ARCompoundSchema) or compoundSchema is None
            assert isinstance(permissionList, cars.ARPermissionList) or permissionList is None
            assert isinstance(subAdminGrpList, cars.ARInternalIdList) or subAdminGrpList is None
            assert isinstance(getListFields, cars.AREntryListFieldList) or getListFields is None
            assert isinstance(sortList, cars.ARSortList) or sortList is None
            assert isinstance(indexList, cars.ARIndexList) or indexList is None
            assert isinstance(archiveInfo, cars.ARArchiveInfoStruct) or archiveInfo is None
            assert isinstance(auditInfo, cars.ARAuditInfoStruct) or auditInfo is None
            assert isinstance(defaultVui, str)
            assert isinstance(nextFieldID, cars.ARInternalId)
            assert isinstance(coreVersion, c_ulong)
            assert isinstance(upgradeVersion, c_int)
            assert isinstance(fieldInfoList, cars.ARFieldInfoList) or fieldInfoList is None
            assert isinstance(vuiInfoList, cars.ARVuiInfoList) or vuiInfoList is None
            assert isinstance(owner, str)
            assert isinstance(lastModifiedBy, str)
            assert isinstance(modifiedDate, cars.ARTimestamp)
            assert isinstance(helpText, str)
            assert isinstance(changeHistory, str)
            assert isinstance(objPropList, cars.ARPropList) or objPropList is None
            assert isinstance(arDocVersion, c_uint) or arDocVersion is None
            
            self.errnr = self.arapi.ARSetSchemaToXML(byref(self.context),
                                                     byref(xml),
                                                     xmlDocHdrFtrFlag,
                                                     schemaName,
                                                     my_byref(compoundSchema),
                                                     my_byref(permissionList),
                                                     my_byref(subAdminGrpList),
                                                     my_byref(getListFields),
                                                     my_byref(sortList),
                                                     my_byref(indexList),
                                                     my_byref(archiveInfo),
                                                     my_byref(auditInfo),
                                                     defaultVui,
                                                     my_byref(nextFieldID),
                                                     my_byref(coreVersion),
                                                     my_byref(upgradeVersion),
                                                     my_byref(fieldInfoList),
                                                     my_byref(vuiInfoList),
                                                     owner,
                                                     lastModifiedBy,
                                                     my_byref(modifiedDate),
                                                     helpText,
                                                     changeHistory,
                                                     my_byref(objPropList),
                                                     my_byref(arDocVersion),
                                                     byref(self.arsl))
            if self.errnr < 2:
                return xml.u.charBuffer
            else:
                self.logger.error("ARSetSchemaToXML returned an error")
                return None

    class ARS(ARS70):
        pass

if cars.version >= 71:
    class ARFilterStruct(Structure):
        _fields_ = [("name", cars.ARNameType),
                    ("order", c_uint),
                    ("schemaList", cars.ARWorkflowConnectStruct),
                    ("opSet", c_uint),
                    ("enable", c_uint),
                    ("query", cars.ARQualifierStruct),
                    ("actionList", cars.ARFilterActionList),
                    ("elseList", cars.ARFilterActionList),
                    ("helpText", c_char_p),
                    ("timestamp", cars.ARTimestamp),
                    ("owner", cars.ARAccessNameType),
                    ("lastChanged", cars.ARAccessNameType),
                    ("changeDiary", c_char_p),
                    ("objPropList", cars.ARPropList),
                    ("errorFilterOptions", c_uint),
                    ("errorFilterName", cars.ARNameType)]
    
    class ARFilterList(Structure):
        _fields_ = [('numItems', c_uint),
                    ('filterList',POINTER(ARFilterStruct))]

    class ARS71(ARS70):
        '''pythonic wrapper Class for Remedy C API, V7.1

Create an instance of ars and call its methods...
similar to ARSPerl and ARSJython'''
    
        def ARCreateFilter(self, 
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
            '''ARCreateFilter creates a new filter.

ARCreateFilter creates a new filter with the indicated name on the specified 
server. The filter takes effect immediately and remains in effect until changed 
or deleted.
Input: name, 
       (unsigned int) order,
       (ARWorkflowConnectStruct) schemaList,
       (unsigned int) opSet,
       (unsigned int) enable,
       (ARQualifierStruct) query,
       (ARFilterActionList) actionList,
       (ARFilterActionList) elseList,
       (char) helpText,
       (ARAccessNameType) owner,
       (char) changeDiary,
       (ARPropList) objPropList,
       (unsigned int) errorFilterOptions
       (ARNameType) errorFilterName
  :returns: errnr'''
            self.logger.debug('enter ARCreateFilter...')
            self.errnr = 0
            self.errnr = self.arapi.ARCreateFilter(byref(self.context),
                                                   name, 
                                                   order, 
                                                   my_byref(schemaList),
                                                   opSet, 
                                                   enable, 
                                                   my_byref(query),
                                                   my_byref(actionList),
                                                   my_byref(elseList),
                                                   helpText,
                                                   owner, 
                                                   changeDiary,
                                                   my_byref(objPropList),
                                                   errorFilterOptions,
                                                   errorFilterName,
                                                   byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARCreateFilter failed for %s' % name)
            return self.errnr

        def ARCreateMultipleFields (self, 
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
            '''ARCreateMultipleFields creates multiple fields in a form. 

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
  :returns: errnr'''
            self.logger.debug('enter ARCreateMultipleFields...')
            self.errnr = 0
            self.errnr = self.arapi.ARCreateMultipleFields(byref(self.context),
                                                           schema,
                                                    my_byref(fieldIdList),
                                                    my_byref(reservedIdOKList),
                                                    my_byref(fieldNameList),
                                                    my_byref(fieldMapList),
                                                    my_byref(dataTypeList),
                                                    my_byref(optionList),
                                                    my_byref(createModeList),
                                                    my_byref(fieldOptionList),
                                                    my_byref(defaultValList),
                                                    my_byref(permissionListList),
                                                    my_byref(limitList),
                                                    my_byref(dInstanceListList),
                                                    my_byref(helpTextList),
                                                    my_byref(ownerList),
                                                    my_byref(changeDiaryList),
                                                           byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARCreateMultipleFields: failed')
            return self.errnr

        def ARExportToFile(self, structItems,
                           displayTag = None,
                           vuiType = cars.AR_VUI_TYPE_WINDOWS,
                           lockinfo = None,
                           filePtr = None):
            '''ARExportToFile exports the indicated structure definitions 
from the specified server to a file. Use this function to copy structure 
definitions from one AR System server to another.
Input: (ARStructItemList) structItems
       (ARNameType)displayTag (optional, default = None)
       (c_uint) vuiType  (optional, default = AR_VUI_TYPE_WINDOWS)
       (ARWorkflowLockStruct) lockinfo  (optional, default = None)
       (FILE) filePtr  (optional, default = None, resulting in an error)
  :returns: errnr'''
            self.logger.debug('enter ARExportToFile...')
            self.errnr = 0
            self.errnr = self.arapi.ARExportToFile(byref(self.context),
                                                   my_byref(structItems),
                                                   displayTag,
                                                   vuiType,
                                                   my_byref(lockinfo),
                                                   my_byref(filePtr),
                                                   byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARExportToFile: failed ')
            return self.errnr

        def ARGetFilter (self, filter_):
            '''ARGetFilter retrieves a filter with a given name.

Input: filter name
  :returns: ARFilterStruct (order, schemaList, opSet, enable, query, actionList,
           elseList, helpText, timestamp, owner, lastChanged,
           changeDiary, objPropList, errorFilterOptions, errorFilterName) or 
None in case of failure'''
            self.logger.debug('enter ARGetFilter...')
            order = c_uint()
            schemaList = cars.ARWorkflowConnectStruct()
            opSet = c_uint()
            enable = c_uint()
            query = cars.ARQualifierStruct()
            actionList = cars.ARFilterActionList()
            elseList = cars.ARFilterActionList()
            helpText = c_char_p()
            timestamp = cars.ARTimestamp()
            owner = cars.ARAccessNameType()
            lastChanged = cars.ARAccessNameType()
            changeDiary = c_char_p()
            objPropList = cars.ARPropList()
            errorFilterOptions = c_uint()
            errorFilterName = cars.ARNameType()
            self.errnr = self.arapi.ARGetFilter(byref(self.context),
                                           filter_,
                                           byref(order),
                                           byref(schemaList),
                                           byref(opSet),
                                           byref(enable),
                                           byref(query),
                                           byref(actionList),
                                           byref(elseList),
                                           byref(helpText),
                                           byref(timestamp),
                                           owner,
                                           lastChanged,
                                           byref(changeDiary),
                                           byref(objPropList),
                                           byref(errorFilterOptions),
                                           errorFilterName,
                                           byref(self.arsl))
            if self.errnr < 2:
                return ARFilterStruct(filter_,
                                      order,
                                      schemaList,
                                      opSet,
                                      enable,
                                      query,
                                      actionList,
                                      elseList,
                                      helpText,
                                      timestamp,
                                      owner.value,
                                      lastChanged.value,
                                      changeDiary,
                                      objPropList,
                                      errorFilterOptions,
                                      errorFilterName.value)
            else:
                self.logger.error('ARGetFilter: failed for "%s"' % filter_)
                return None

        def ARGetMultipleFilters(self, changedSince = 0, 
                                 nameList = None,
                                 orderList = None,
                                 workflowConnectList = None,
                                 opSetList = None,
                                 enableList = None,
                                 queryList = None,
                                 actionListList = None,
                                 elseListList = None,
                                 helpTextList = None,
                                 timestampList = None,
                                 ownerList = None,
                                 lastChangedList = None,
                                 changeDiaryList = None,
                                 objPropListList = None,
                                 errorFilterOptionsList = None,
                                 errorFilterNameList = None):
            '''ARGetMultipleFilters retrieves information about a group of filters.

This function performs the same
action as ARGetFilter but is easier to use and more efficient than retrieving
multiple entries one by one.
While the server returns information in lists for each item, pyars converts
this into a struct of its own.
Input: changedSince (optional, default = 0), 
         nameList (optional, default = None) (ARNameList)
         orderList (optional, default = None) (ARUnsignedIntList)
         workflowConnectList (optional, default = None) (ARWorkflowConnectList)
         opSetList (optional, default = None) (ARUnsignedIntList)
         enableList (optional, default = None) (ARUnsignedIntList)
         queryList (optional, default = None) (ARQualifierList)
         actionListList (optional, default = None) (ARFilterActionListList)
         elseListList (optional, default = None) (ARFilterActionListList)
         helpTextList (optional, default = None) (ARTextStringList)
         timestampList (optional, default = None) (ARTimestampList)
         ownerList (optional, default = None) (ARAccessNameList)
         lastChangedList (optional, default = None) (ARAccessNameList)
         changeDiaryList (optional, default = None) (ARTextStringList)
         objPropListList (optional, default = None) (ARPropListList)
         errorFilterOptionsList (optional, default = None) (ARUnsignedIntList)
         errorFilterNameList (optional, default = None) (ARNameList)
  :returns: ARFilterList or None in case of failure'''
            self.logger.debug('enter ARGetMultipleFilters...')
            self.errnr = 0
            existList = cars.ARBooleanList()
            filterNameList = cars.ARNameList()
            self.errnr = self.arapi.ARGetMultipleFilters(byref(self.context),
                                                         changedSince,
                                                         my_byref(nameList),
                                                         byref(existList),
                                                         byref(filterNameList),
                                                         my_byref(orderList),
                                                         my_byref(workflowConnectList),
                                                         my_byref(opSetList),
                                                         my_byref(enableList),
                                                         my_byref(queryList),
                                                         my_byref(actionListList),
                                                         my_byref(elseListList),
                                                         my_byref(helpTextList),
                                                         my_byref(timestampList),
                                                         my_byref(ownerList),
                                                         my_byref(lastChangedList),
                                                         my_byref(changeDiaryList),
                                                         my_byref(objPropListList),
                                                         my_byref(errorFilterOptionsList),
                                                         my_byref(errorFilterNameList),
                                                         byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARGetMultipleFilters: failed')
                return None
            else:
                tempArray = (ARFilterStruct * existList.numItems)()
                for i in range(existList.numItems):
                    if existList.booleanList[i]:
                        tempArray[i].name = filterNameList.nameList[i].value
                        if orderList: tempArray[i].order = orderList.intList[i]
                        if workflowConnectList: tempArray[i].schemaList = workflowConnectList.workflowConnectList[i]
                        if opSetList: tempArray[i].opSet = opSetList.intList[i]
                        if enableList: tempArray[i].enable = enableList.intList[i]
                        if queryList: tempArray[i].query = queryList.qualifierList[i]
                        if actionListList: tempArray[i].actionList = actionListList.actionListList[i]
                        if elseListList: tempArray[i].elseList = elseListList.actionListList[i]
                        if helpTextList: tempArray[i].helpText = helpTextList.stringList[i]
                        if timestampList: tempArray[i].timestamp = timestampList.timestampList[i]
                        if ownerList: tempArray[i].owner = ownerList.nameList[i].value
                        if lastChangedList: tempArray[i].lastChanged = lastChangedList.nameList[i].value
                        if changeDiaryList: tempArray[i].changeDiary = changeDiaryList.stringList[i]
                        if objPropListList: tempArray[i].objPropList = objPropListList.propsList[i]
                        if errorFilterOptionsList: tempArray[i].errorFilterOptions = errorFilterOptionsList.intList[i]
                        if errorFilterNameList: tempArray[i].errorFilterName = errorFilterNameList.nameList[i].value
                    else:
                        filter_ = self.ARGetFilter(nameList.nameList[i].value)
                        if self.errnr > 1:
                            self.logger.error('even second trial failed for %d) "%s"' % (
                                               i, nameList.nameList[i].value))
                        else:
                            tempArray[i] = filter_
#                            self.logger.error('second trial worked for %d) "%s"' % (
#                                              i, nameList.nameList[i].value))
                        # self.logger.error('ARGetMultipleFilters: "%s" does not exist!' % nameList.nameList[i].value)
                return ARFilterList(existList.numItems, tempArray)

        def ARSetFilter(self, name, 
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
            '''ARSetFilter updates the filter.

The changes are added to the server immediately and returned to users who
request information about filters.
Input:  name, 
        (ARNameType) newName,
        (c_uint) order (optional, default = None),
        (ARWorkflowConnectStruct) workflowConnect (optional, default = None),
        (c_uint) opSet (optional, default = None),
        (c_uint) enable (optional, default = None),
        (ARQualifierStruct) query (optional, default = None),
        (ARFilterActionList) actionList (optional, default = None),
        (ARFilterActionList) elseList (optional, default = None),
        (c_char) helpText (optional, default = None),
        (ARAccessNameType) owner (optional, default = None),
        (c_char) changeDiary (optional, default = None),
        (ARPropList) objPropList (optional, default = None),
        (c_uint) errorFilterOptions  (optional, default = None),
        (ARNameType) errorFilterName  (optional, default = None)
  :returns: errnr'''
            self.logger.debug('enter ARSetFilter...')
            self.errnr = 0
            if order is not None and not isinstance(order, c_uint):
                order = c_uint(order)
            if opSet is not None and not isinstance(opSet, c_uint):
                opSet = c_uint(opSet)
            if enable is not None and not isinstance(enable, c_uint):
                enable = c_uint(enable)
            if errorFilterOptions is not None and not isinstance(errorFilterOptions, c_uint):
                errorFilterOptions = c_uint(errorFilterOptions)
            self.errnr = self.arapi.ARSetFilter(byref(self.context),
                                                name, 
                                                newName,
                                                my_byref(order),
                                                my_byref(workflowConnect),
                                                my_byref(opSet),
                                                my_byref(enable),
                                                my_byref(query),
                                                my_byref(actionList),
                                                my_byref(elseList),
                                                helpText,
                                                owner,
                                                changeDiary,
                                                my_byref(objPropList),
                                                my_byref(errorFilterOptions),
                                                errorFilterName,
                                                byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARSetFilter: failed for %s' % name)
            return self.errnr

        def ARSetMultipleFields (self, schema,
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
            '''ARSetMultipleFields updates the definition for a list of fields 
with the specified IDs on the specified form on the specified server. 

This call produces the same result as a sequence of
ARSetField calls to update the individual fields, but it can be more efficient
because it requires only one call from the client to the AR System server and
because the server can perform multiple database operations in a single
transaction and avoid repeating operations such as those performed at the end of
each individual call.
Input:  (ARNameType) schema (optional, default = None),
        (ARInternalIdList) fieldIdList (optional, default = None),
        (ARNamePtrList) fieldNameList (optional, default = None),
        (ARFieldMappingPtrList) fieldMapList (optional, default = None),
        (ARUnsignedIntList) optionList (optional, default = None),
        (ARUnsignedIntList) createModeList (optional, default = None),
        (ARUnsignedIntList) fieldOptionList (optional, default = None),
        (ARValuePtrList) defaultValList (optional, default = None),
        (ARPermissionListPtrList) permissionListList (optional, default = None),
        (ARFieldLimitPtrList) limitList (optional, default = None),
        (ARDisplayInstanceListPtrList) dInstanceListList (optional, default = None),
        (ARTextStringList) helpTextList (optional, default = None),
        (ARAccessNamePtrList) ownerList (optional, default = None),
        (ARTextStringList) changeDiaryList (optional, default = None),
        (ARUnsignedIntList) setFieldOptionList (optional, default = None),
        (ARStatusListList) setFieldStatusList (optional, default = None)
  :returns: errnr'''
            self.logger.debug('enter ARSetMultipleFields...')
            self.errnr = 0
            self.errnr = self.arapi.ARSetMultipleFields(byref(self.context),
                                                schema,
                                                my_byref(fieldIdList),
                                                my_byref(fieldNameList),
                                                my_byref(fieldMapList),
                                                my_byref(optionList),
                                                my_byref(createModeList),
                                                my_byref(fieldOptionList),
                                                my_byref(defaultValList),
                                                my_byref(permissionListList),
                                                my_byref(limitList),
                                                my_byref(dInstanceListList),
                                                my_byref(helpTextList),
                                                my_byref(ownerList),
                                                my_byref(changeDiaryList),
                                                my_byref(setFieldOptionList),
                                                my_byref(setFieldStatusList),
                                                byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARSetMultipleFields: failed')
            return self.errnr

        def ARGetFilterFromXML(self, parsedStream, filterName):
            '''ARGetFilterFromXML retrieves a filter from an XML document.

Input: (ARXMLParsedStream) parsedStream
       (ARNameType) filterName
  :returns: (ARFilterStruct, arDocVersion)
        or None in case of failure'''
            self.logger.debug('enter ARGetFilterFromXML...')
            self.errnr = 0
            order = c_uint()
            schemaList = cars.ARWorkflowConnectStruct()
            opSet = c_uint()
            enable = c_uint()
            query = cars.ARQualifierStruct()
            actionList = cars.ARFilterActionList()
            elseList = cars.ARFilterActionList()
            helpText = c_char_p()
            timestamp = cars.ARTimestamp()
            owner = cars.ARAccessNameType()
            lastChanged = cars.ARAccessNameType()
            changeDiary = c_char_p()
            objPropList = cars.ARPropList()
            errorFilterOptions = c_uint()
            errorFilterName = cars.ARNameType()

            arDocVersion = c_uint()
            
            self.errnr = self.arapi.ARGetFilterFromXML(byref(self.context),
                                                       my_byref(parsedStream),
                                                       filterName,
                                                       byref(order),
                                                       byref(schemaList),
                                                       byref(opSet),
                                                       byref(enable),
                                                       byref(query),
                                                       byref(actionList),
                                                       byref(elseList),
                                                       owner,
                                                       lastChanged,
                                                       byref(timestamp),
                                                       byref(helpText),
                                                       byref(changeDiary),
                                                       byref(objPropList),
                                                       byref(errorFilterOptions),
                                                       errorFilterName,
                                                       byref(arDocVersion),
                                                       byref(self.arsl))
            if self.errnr < 2:
                return (ARFilterStruct(filterName,
                                       order,
                                       schemaList,
                                       opSet,
                                       enable,
                                       query,
                                       actionList,
                                       elseList,
                                       helpText,
                                       timestamp,
                                       owner.value,
                                       lastChanged.value,
                                       changeDiary,
                                       objPropList,
                                       errorFilterOptions,
                                       errorFilterName.value), 
                       arDocVersion)
            else:
                self.logger.error('ARGetFilterFromXML: failed for %s' % filterName)
                return None

    class ARS(ARS71):
        pass

if cars.version >= 75:
    
    class ARActiveLinkStruct(Structure):
        _fields_ = [("name", cars.ARNameType),
                    ("order", c_uint),
                    ("schemaList", cars.ARWorkflowConnectStruct),
                    ("groupList", cars.ARInternalIdList),
                    ("executeMask", c_uint),
                    ("controlField", cars.ARInternalId),
                    ("focusField",  cars.ARInternalId),
                    ("enable", c_uint),
                    ("query", cars.ARQualifierStruct),
                    ("actionList", cars.ARActiveLinkActionList),
                    ("elseList", cars.ARActiveLinkActionList),
                    ("helpText", c_char_p),
                    ("timestamp", cars.ARTimestamp),
                    ("owner", cars.ARAccessNameType),
                    ("lastChanged", cars.ARAccessNameType),
                    ("changeDiary", c_char_p),
                    ("objPropList", cars.ARPropList),
                    ("errorActlinkOptions", c_uint),
                    ("errorActlinkName", cars.ARNameType)]

    class ARActiveLinkList(Structure):
        _fields_ = [('numItems', c_uint),
                    ('activeLinkList',POINTER(ARActiveLinkStruct))]


    class ARS75(ARS71):
        '''pythonic wrapper Class for Remedy C API, V7.5

Create an instance of ars and call its methods...
similar to ARSPerl and ARSJython'''

        def ARCreateActiveLink (self, name, 
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
       (optional) errorActlinkOptions (Reserved for future use. Set to NULL.)
       (optional) errorActlinkName (Reserved for future use. Set to NULL.)
  :returns: errnr'''
            self.logger.debug('enter ARCreateActiveLink...')
            self.errnr = 0
            self.errnr = self.arapi.ARCreateActiveLink(byref(self.context),
                                                       name, 
                                                       order, 
                                                       my_byref(schemaList), 
                                                       my_byref(groupList),
                                                       executeMask,
                                                       my_byref(controlField),
                                                       my_byref(focusField),
                                                       enable, 
                                                       my_byref(query),
                                                       my_byref(actionList),
                                                       my_byref(elseList),
                                                       helpText,
                                                       owner,
                                                       changeDiary,
                                                       my_byref(objPropList),
                                                       errorActlinkOptions,
                                                       errorActlinkName,
                                                       byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARCreateActiveLink failed for %s' % name)
            return self.errnr

        def ARCreateImage(self, name,
                          imageBuf,
                          imageType,
                          description = None,
                          helpText = None,
                          owner = None,
                          changeDiary = None,
                          objPropList = None):
            '''ARCreateImage creates a new image with the indicated name on the specified server
Input: name (ARNameType)
       imageBuf (ARImageDataStruct)
       imageType (c_char_p, Valid values are: BMP, GIF, JPEG or JPG, and PNG.)
       (optional) description (c_char_p, default: None)
       (optional) helpText (c_char_p, default: None)
       (optional) owner (ARAccessNameType, default: None)
       (optional) changeDiary (c_char_p, default: None)
       (optional) objPropList (ARPropList, default: None)
  :returns: errnr'''
            self.logger.debug('enter ARCreateImage...')
            self.errnr = self.arapi.ARCreateImage(byref(self.context),
                                                  name,
                                                  my_byref(imageBuf),
                                                  imageType,
                                                  description,
                                                  helpText,
                                                  owner,
                                                  changeDiary,
                                                  my_byref(objPropList),
                                                  byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARCreateImage failed for %s' % name)
            return self.errnr            

        def ARDeleteImage(self, name,
                          updateRef):
            '''ARDeleteImage deletes the image with the indicated name from the specified server.
Input: name (ARNameType)
       updateRef (ARBoolean, specify TRUE to remove all references to the image)
  :returns: errnr'''
            self.logger.debug('enter ARDeleteImage...')
            self.errnr = self.arapi.ARDeleteImage(byref(self.context),
                                                  name,
                                                  updateRef,
                                                  byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARDeleteImage failed for %s' % name)
            return self.errnr  

        def ARGetActiveLink (self, name):
            '''ARGetActiveLink retrieves the active link with the indicated name.

ARGetActiveLink retrieves the active link with the indicated name on
the specified server.
Input: name (ARNameType)
  :returns: ARActiveLinkStruct (containing: order, schemaList,
           groupList, executeMask, controlField,
           focusField, enable, query, actionList,
           elseList, helpText, timestamp, owner, lastChanged,
           changeDiary, objPropList, errorActlinkOptions, errorActlinkName) 
    or None in case of failure'''
            self.logger.debug('enter ARGetActiveLink...')
            order = c_uint()
            schemaList = cars.ARWorkflowConnectStruct()
            groupList = cars.ARInternalIdList()
            executeMask = c_uint()
            controlField = cars.ARInternalId()
            focusField = cars.ARInternalId()
            enable = c_uint()
            query = cars.ARQualifierStruct()
            actionList = cars.ARActiveLinkActionList()
            elseList = cars.ARActiveLinkActionList()
            helpText = c_char_p()
            timestamp = cars.ARTimestamp()
            owner = cars.ARAccessNameType()
            lastChanged = cars.ARAccessNameType()
            changeDiary = c_char_p()
            objPropList = cars.ARPropList()
            errorActlinkOptions = c_uint()
            errorActlinkName = cars.ARNameType()
            
            self.errnr = self.arapi.ARGetActiveLink(byref(self.context),
                                      name,
                                      byref(order),
                                      byref(schemaList),
                                      byref(groupList),
                                      byref(executeMask),
                                      byref(controlField),
                                      byref(focusField),
                                      byref(enable),
                                      byref(query),
                                      byref(actionList),
                                      byref(elseList),
                                      byref(helpText),
                                      byref(timestamp),
                                      owner,
                                      lastChanged,
                                      byref(changeDiary),
                                      byref(objPropList),
                                      byref(errorActlinkOptions),
                                      byref(errorActlinkName),
                                      byref(self.arsl))
            if self.errnr < 2:
                result = ARActiveLinkStruct(name,
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
                                            timestamp,
                                            owner.value,
                                            lastChanged.value,
                                            changeDiary,
                                            objPropList,
                                            errorActlinkOptions,
                                            errorActlinkName.value)
                return result
            else:
                self.logger.error('ARGetActiveLink: failed for %s' % name)
                return None

        def ARGetCacheEvent(self, eventIdList, 
                            returnOption = cars.AR_GCE_OPTION_NONE):
            '''ARGetCacheEvent retrieves the list of events that occurred in the 
AR System server cache and the number of server caches, and indicates when 
administrative operations become public. You can direct this API call to either 
return the results immediately or when the next event occurs. This call is useful 
for detecting cache events in production cache mode.
In developer cache mode, the call always returns immediately regardless of the
value of the return option. In developer cache mode, there can only ever be one
copy of the cache and it is always public.
Input: eventIdList (ARInternalIdList)
       (optional) returnOption (c_uint, default = 0, call returns the information immediately)
  :returns: (eventIdOccuredList (ARInternalIdList), cacheCount (c_uint)) or 
        (None, errnr) in case of failure'''
            self.logger.debug('enter ARGetCacheEvent...')
            eventIdOccuredList = cars.ARInternalIdList()
            cacheCount = c_uint()
            self.errnr = self.arapi.ARGetCacheEvent(byref(self.context),
                                                    my_byref(eventIdList),
                                                    returnOption,
                                                    byref(eventIdOccuredList),
                                                    byref(cacheCount),
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARGetCacheEvent: failed')
                return (None, self.errnr)
            else:
                return (eventIdOccuredList, cacheCount)      

        def ARGetImage(self, name):
            '''ARGetImage retrieves information about the specified image from 
the specified server.
Input: name (ARNameType)
  :returns: (content (ARImageDataStruct),
    imageType (c_char_p),
    timestamp (ARTimeStamp),
    checkSum (c_char_p),
    description (c_char_p),
    helpText (c_char_p),
    owner (ARAccessNameType),
    changeDiary (c_char_p),
    objPropList (ARPropList)) or None in case of failure'''
            self.logger.debug('enter ARGetImage...')
            content = cars.ARImageDataStruct()
            imageType = c_char_p()
            timestamp = cars.ARTimestamp()
            checkSum = c_char_p()
            description = c_char_p()
            helpText = c_char_p()
            owner = cars.ARAccessNameType()
            lastChanged = cars.ARAccessNameType()
            changeDiary = c_char_p()
            objPropList = cars.ARPropList()
            self.errnr = self.arapi.ARGetImage(byref(self.context),
                                               name,
                                               byref(content),
                                               byref(imageType), # docs say without byref, but header file with
                                               byref(timestamp),
                                               byref(checkSum),
                                               byref(description),
                                               byref(helpText),
                                               owner,
                                               lastChanged,
                                               byref(changeDiary),
                                               byref(objPropList),
                                               byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARGetImage: failed')
                return None
            else:
                return (content, imageType.value, 
                        timestamp.value, 
                        checkSum.value, 
                        description.value,
                        helpText.value, 
                        owner.value, 
                        changeDiary.value, 
                        objPropList)

        def ARGetListEntryWithMultiSchemaFields (self, queryFromList, 
                                      getListFields=None, 
                                      qualifier = None,
                                      sortList=None,
                                      firstRetrieve=cars.AR_START_WITH_FIRST_ENTRY,
                                      maxRetrieve=cars.AR_NO_MAX_LIST_RETRIEVE,
                                      useLocale = False):
            '''ARGetListEntryWithMultiSchemaFields performs dynamic joins by querying across multiple forms—including view and
vendor forms—at run time.
Input: queryFromList (ARMultiSchemaQueryFromList)
       (optional) getListFields (ARMultiSchemaFieldIdList, deafult = None), 
       (optional) qualifier (ARMultiSchemaQualifierStruct, default = None),
       (optional) sortList (ARMultiSchemaSortList, default = None),
       (optional) firstRetrieve (c_uint, default=cars.AR_START_WITH_FIRST_ENTRY),
       (optional) maxRetrieve (c_uint, default=cars.AR_NO_MAX_LIST_RETRIEVE),
       (optional) useLocale (ARBoolean, default = False)
  :returns: (ARMultiSchemaFieldValueListList, numMatches (c_uint))'''
            self.logger.debug('enter ARGetListEntryWithMultiSchemaFields...')
            entryList = cars.ARMultiSchemaFieldValueListList()
            numMatches = c_uint()
            self.errnr = self.arapi.ARGetListEntryWithMultiSchemaFields(byref(self.context),
                                                                        my_byref(queryFromList),
                                                                        my_byref(getListFields),
                                                                        my_byref(qualifier),
                                                                        my_byref(sortList),
                                                                        firstRetrieve,
                                                                        maxRetrieve,
                                                                        useLocale,
                                                                        byref(entryList),
                                                                        byref(numMatches),
                                                                        byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARGetListEntryWithMultiSchemaFields: failed')
                return None
            else:
                return (entryList, numMatches)

        def ARGetListImage(self, schemaList = None, 
                           changedSince = 0,
                           imageType = None):
            '''ARGetListImage retrieves a list of image names from the specified 
server. You can retrieve all images or limit the list to those images associated 
with particular schemas, those modified after a specified time, and those of a 
specific type.
Input: (optional) schemaList (ARNameList, default = None),
       (optional) changedSince (ARTimestamp, default = 0),
       (optional) imageType (c_char_p, default = None)
  :returns: imageList (ARNameList) or None in case of failure'''
            self.logger.debug('enter ARGetListImage...')
            imageList = cars.ARNameList()
            self.errnr = self.arapi.ARGetListImage(byref(self.context),
                                                   my_byref(schemaList),
                                                   changedSince,
                                                   imageType,
                                                   byref(imageList),
                                                   byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARGetListImage: failed')
                return None
            else:
                return imageList

        def ARGetMultipleActiveLinks(self, changedSince=0, 
                                     nameList = None,
                                     orderList = None,
                                     schemaList = None,
                                     groupListList = None,
                                     executeMaskList = None,
                                     controlFieldList = None,
                                     focusFieldList = None,
                                     enableList = None,
                                     queryList = None,
                                     actionListList = None,
                                     elseListList = None,
                                     helpTextList = None,
                                     timestampList = None,
                                     ownersList = None,
                                     lastChangedList = None,
                                     changeDiaryList = None,
                                     objPropListList = None,
                                     errorActlinkOptionsList = None,
                                     errorActlinkNameList = None):
            '''ARGetMultipleActiveLinks retrieves multiple active link definitions.

This function performs the same
action as ARGetActiveLink but is easier to use and more efficient than
retrieving multiple entries one by one.
Please note: While the ARSystem returns the information in lists for each item, 
pyars will convert this into an ARActiveLinkList of its own.
Input: changedSince 
         nameList (ARNameList)
         orderList (ARUnsignedIntList)
         schemaList (ARWorkflowConnectList)
         groupListList (ARInternalIdListList)
         executeMaskList (ARUnsignedIntList)
         controlFieldList (ARInternalIdList)
         focusFieldList (ARInternalIdList)
         enableList (ARUnsignedIntList)
         queryList (ARQualifierList)
         actionListList (ARActiveLinkActionListList)
         elseListList (ARActiveLinkActionListList)
         helpTextList (ARTextStringList)
         timestampList (ARTimestampList)
         ownersList (ARAccessNameList)
         lastChangedList (ARAccessNameList)
         changeDiaryList (ARTextStringList)
         objPropListList (ARPropListList)
         errorActlinkOptionsList (ARUnsignedIntList)
         errorActlinkNameList (ARNameList)
  :returns: ARActiveLinkList (or None in case of failure)'''
            self.logger.debug('enter ARGetMultipleActiveLinks...')
            self.errnr = 0
            existList = cars.ARBooleanList()
            actLinkNameList = cars.ARNameList()
            self.errnr = self.arapi.ARGetMultipleActiveLinks(byref(self.context),
                                                        changedSince,
                                                        my_byref(nameList),
                                                        byref(existList),
                                                        byref(actLinkNameList),
                                                        my_byref(orderList),
                                                        my_byref(schemaList),
                                                        my_byref(groupListList),
                                                        my_byref(executeMaskList),
                                                        my_byref(controlFieldList),
                                                        my_byref(focusFieldList),
                                                        my_byref(enableList),
                                                        my_byref(queryList),
                                                        my_byref(actionListList),
                                                        my_byref(elseListList),
                                                        my_byref(helpTextList),
                                                        my_byref(timestampList),
                                                        my_byref(ownersList),
                                                        my_byref(lastChangedList),
                                                        my_byref(changeDiaryList),
                                                        my_byref(objPropListList),
                                                        my_byref(errorActlinkOptionsList),
                                                        my_byref(errorActlinkNameList),
                                                        byref(self.arsl))
            if self.errnr < 2:
                tempArray = (ARActiveLinkStruct * existList.numItems)()
    #            self.logger.debug(' num of entries: existList: %d, nameList: %d, order: %d' % (
    #                              existList.numItems, actLinkNameList.numItems, orderList.numItems))
                for i in range(existList.numItems):
                    if existList.booleanList[i]:
                        tempArray[i].name=actLinkNameList.nameList[i].value
                        if orderList: tempArray[i].order = orderList.intList[i]
                        if schemaList: tempArray[i].schemaList = schemaList.workflowConnectList[i]
                        if groupListList: tempArray[i].groupList = groupListList.internalIdListList[i]
                        if executeMaskList: tempArray[i].executeMask = executeMaskList.intList[i]
                        if controlFieldList: tempArray[i].controlField = controlFieldList.internalIdList[i]
                        if focusFieldList: tempArray[i].focusField = focusFieldList.internalIdList[i]
                        if enableList: tempArray[i].enable = enableList.intList[i]
                        if queryList: tempArray[i].query = queryList.qualifierList[i]
                        if actionListList: tempArray[i].actionList = actionListList.actionListList[i]
                        if elseListList: tempArray[i].elseList = elseListList.actionListList[i]
                        if helpTextList: 
                            tempArray[i].helpText = helpTextList.stringList[i]
                            if not tempArray[i].helpText == helpTextList.stringList[i]:
                                self.logger.error('''   1) %s is buggy: %s 
                                original helptext: %s''' % (tempArray[i].name,
                                          tempArray[i].helpText, helpTextList.stringList[i]))
                        if timestampList: tempArray[i].timestamp = timestampList.timestampList[i]
                        if ownersList: tempArray[i].owner = ownersList.nameList[i].value
                        if lastChangedList: tempArray[i].lastChanged = lastChangedList.nameList[i].value
                        if changeDiaryList: tempArray[i].changeDiary = changeDiaryList.stringList[i]
                        if objPropListList: tempArray[i].objPropList = objPropListList.propsList[i]
                        if errorActlinkOptionsList: tempArray[i].errorActlinkOptions = errorActlinkOptionsList.intList[i]
                        if errorActlinkNameList: tempArray[i].errorActlinkName = errorActlinkNameList.nameList[i].value
                    else:
                        self.logger.error('ARGetMultipleActiveLinks: "%s" does not exist! %s' % (nameList.nameList[i].value,
                                                                                                 self.statusText()))
    
                if not helpTextList is None:
                    for j in range(existList.numItems):
                        if tempArray[j].helpText != helpTextList.stringList[j]:
                            self.logger.error('''   2) %d(%s) is buggy: %s
                             original helptext: %s''' % (j, tempArray[j].name,
                                              tempArray[j].helpText, helpTextList.stringList[j]))
                return ARActiveLinkList(existList.numItems, tempArray)
            else:
                self.logger.error( "ARGetMultipleActiveLinks: failed")
                return None

        def ARGetMultipleImages(self, changedSince = 0,
                                nameList = None,
                                imageTypeList = None,
                                timestampList = None,
                                descriptionList = cars.ARTextStringList(),
                                helpTextList = None,
                                ownerList = None,
                                lastChangedList = None,
                                changeDiaryList = None,
                                objPropListList = None,
                                checkSumList = None,
                                imageDataList = None):
            '''ARGetMultipleImages retrieves information from the specified server 
about the images whose names are specified in the nameList parameter. This function 
performs the same action as ARGetImage, but it is more efficient than retrieving 
information about multiple images one by one.
Input: (optional) changedSince (ARTimestamp, default = 0),
       (optional) nameList (ARNameList, default = None)
       (optional) imageTypeList (ARTextStringList, default = None)
       (optional) timestampList (ARTimestampList, default = None)
       (optional) descriptionList (ARTextStringList, default = None)
       (optional) helpTextList (ARTextStringList, default = None)
       (optional) ownerList (ARAccessNameList, default = None)
       (optional) lastChangedList (ARAccessNameList, default = None)
       (optional) changeDiaryList (ARTextStringList, default = None)
       (optional) objPropListList (ARPropListList, default = None)
       (optional) checkSumList (ARTextStringList, default = None)
       (optional) imageDataList (ARImageDataList, default = None)
  :returns: (existList, imageNameList, imageTypeList,  timestampList, descriptionList,
    helpTextList, ownerList, lastChangedList, changeDiaryList, objPropListList,
    checkSumList, imageDataList)'''
            self.logger.debug('enter ARGetMultipleImages...')
            existList = cars.ARBooleanList()
            imageNameList = cars.ARNameList()
            self.errnr = self.arapi.ARGetMultipleImages(byref(self.context),
                                                        changedSince,
                                                        my_byref(nameList),
                                                        byref(existList),
                                                        byref(imageNameList),
                                                        my_byref(imageTypeList),
                                                        my_byref(timestampList),
                                                        my_byref(descriptionList),
                                                        my_byref(helpTextList),
                                                        my_byref(ownerList),
                                                        my_byref(lastChangedList),
                                                        my_byref(changeDiaryList),
                                                        my_byref(objPropListList),
                                                        my_byref(checkSumList),
                                                        my_byref(imageDataList),
                                                        byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARGetMultipleImages: failed')
                return None
            else:
                return (existList, 
                        imageNameList, 
                        imageTypeList,  
                        timestampList, 
                        descriptionList,
                        helpTextList, 
                        ownerList, 
                        lastChangedList, 
                        changeDiaryList, 
                        objPropListList,
                        checkSumList, 
                        imageDataList)
                                                        
        def ARGetObjectChangeTimes(self):
            '''ARGetObjectChangeTimes retrieves timestamps for the last create, 
modify, and delete operations for each type of server object.
Input:
  :returns: ARObjectChangeTimestampList or None in case of failure'''
            self.logger.debug('enter ARGetObjectChangeTimes...')
            objectChanges = cars.ARObjectChangeTimestampList()
            self.errnr = self.arapi.ARGetObjectChangeTimes(byref(self.context),
                                                           byref(objectChanges),
                                                           byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARGetObjectChangeTimes: failed')
                return None
            else:
                return objectChanges
                        
        def ARGetOneEntryWithFields(self, schema,
                                    qualifier = None,
                                    getListFields = None,
                                    sortList = None,
                                    useLocale = False):
            '''ARGetOneEntryWithFields retrieves one entry from AR System matching a given qualification. Similar to
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
  :returns: (entryList (AREntryListFieldValueList), numMatches (c_uint))'''
            self.logger.debug('enter ARGetOneEntryWithFields...')
            entryList = cars.AREntryListFieldValueList()
            numMatches = c_uint()
            self.errnr = self.arapi.ARGetOneEntryWithFields(byref(self.context),
                                                            schema,
                                                            my_byref(qualifier),
                                                            my_byref(getListFields),
                                                            my_byref(sortList),
                                                            useLocale,
                                                            byref(entryList),
                                                            byref(numMatches),
                                                            byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARGetOneEntryWithFields: failed for %s' % schema)
                return None
            else:
                return (entryList, numMatches)

        def ARRunEscalation(self, escalationName):
            '''ARRunEscalation runs the specified escalation immediately
Input: escalationName (ARNameType)
  :returns: errnr'''
            self.logger.debug('enter ARRunEscalation...')
            self.errnr = self.arapi.ARRunEscalation(byref(self.context),
                                                    escalationName,
                                                    byref(self.arsl))
            return self.errnr
        
        def ARSetActiveLink(self, name, 
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
            '''ARSetActiveLink updates the active link.

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
  :returns: errnr'''
            self.logger.debug('enter ARSetActiveLink...')
            if order is not None and not isinstance(order, c_uint):
                order = c_uint(order)
            if executeMask is not None and not isinstance(executeMask, c_uint):
                executeMask = c_uint(executeMask)
            if controlField is not None and not isinstance(controlField, c_uint):
                controlField = cars.ARInternalId(controlField)
            if focusField is not None and not isinstance(focusField, c_uint):
                focusField = cars.ARInternalId(focusField)
            if enable is not None and not isinstance(enable, c_uint):
                enable = c_uint(enable)
            self.errnr = self.arapi.ARSetActiveLink(byref(self.context),
                                                    name, 
                                                    newName, 
                                                    my_byref(order), 
                                                    my_byref(workflowConnect),
                                                    my_byref(groupList),
                                                    my_byref(executeMask),
                                                    my_byref(controlField),
                                                    my_byref(focusField),
                                                    my_byref(enable),
                                                    my_byref(query),
                                                    my_byref(actionList),
                                                    my_byref(elseList),
                                                    helpText,
                                                    owner,
                                                    changeDiary,
                                                    my_byref(objPropList),
                                                    my_byref(errorActlinkOptions),
                                                    errorActlinkName,
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARSetActiveLink: failed for %s' % name)
            return self.errnr

        def ARSetImage(self, name,
                        newName = None,
                        imageBuf = None,
                        imageType = None,
                        description = None,
                        helpText = None,
                        owner = None,
                        changeDiary = None,
                        objPropList = None):
            '''ARSetImage updates the image with the indicated name on the specified server. After the
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
  :returns: errnr'''
            self.logger.debug('enter ARSetImage...')
            self.errnr = self.arapi.ARSetImage(byref(self.context),
                                                    name, 
                                                    newName, 
                                                    my_byref(imageBuf), 
                                                    imageType,
                                                    description,
                                                    helpText,
                                                    owner,
                                                    changeDiary,
                                                    my_byref(objPropList),
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARSetImage: failed for %s' % name)
            return self.errnr          

        def ARWfdClearAllBreakpoints(self):
            '''ARWfdClearAllBreakpoints removes all breakpoints from the server..

Input: 
  :returns: errnr'''
            self.logger.debug('enter ARWfdClearAllBreakpoints...')
            self.errnr = self.arapi.ARWfdClearAllBreakpoints(byref(self.context),
                                               byref(self.arsl))
            return self.errnr

        def ARWfdClearBreakpoint(self, bpId):
            '''ARWfdClearBreakpoint removes the specified breakpoint from the server.

Input: bpId (c_uint)
  :returns: errnr'''
            self.logger.debug('enter ARWfdClearBreakpoint...')
            self.errnr = self.arapi.ARWfdClearBreakpoint(byref(self.context),
                                                         bpId,
                                                         byref(self.arsl))
            return self.errnr
        
        def ARWfdExecute(self, mode = cars.WFD_EXECUTE_STEP):
            '''Instructs the debug server to begin execution.
Input: (optional) mode  (c_uint, default: single step)
  :returns: (result, extraInfo1, extraInfo2) or None in case of failure'''
            self.logger.debug('enter ARWfdExecute...')
            result = c_uint()
            extraInfo1 = c_uint()
            extraInfo2 = c_uint()
            self.errnr = self.arapi.ARWfdClearBreakpoint(byref(self.context),
                                                         byref(result),
                                                         byref(extraInfo1),
                                                         byref(extraInfo2),
                                                         byref(self.arsl))
            if self.errnr > 1:
                return None
            return (result, extraInfo1, extraInfo2)

        def ARWfdGetCurrentLocation(self, howFarBack = 0):
            '''ARWfdGetCurrentLocation description Requests the current location 
of the worker thread during debugging.
Input: (optional) howFarBack (c_uint, default = 0)
  :returns: location'''
            self.logger.debug('enter ARWfdGetCurrentLocation...')
            location = cars.ARWfdCurrentLocation()
            self.errnr = self.arapi.ARWfdClearBreakpoint(byref(self.context),
                                                         howFarBack,
                                                         byref(location),
                                                         byref(self.arsl))
            if self.errnr > 1:
                return None
            return location
            
        
        def ARWfdGetDebugMode(self):
            '''ARWfdGetDebugMode returns the current debug mode.
Input:
  :returns: integer (current debug mode)'''
            self.logger.debug('enter ARWfdGetDebugMode...')
            mode = c_uint()
            self.errnr = self.arapi.ARWfdGetDebugMode(byref(self.context),
                                                         byref(mode),
                                                         byref(self.arsl))
            if self.errnr > 1:
                return None
            return mode

        def ARWfdGetFieldValues(self, howFarBack = 0):
            '''ARWfdGetFieldValues requests the field-value list associated with 
the current schema at the current location.
Input: (optional) howFarBack (c_uint, default = 0)
  :returns: (ARFieldValueList, ARFieldValueList) or None in case of failure'''
            self.logger.debug('enter ARWfdGetFieldValues...')
            trFieldList = cars.ARFieldValueList()
            dbFieldList = cars.ARFieldValueList()
            self.errnr = self.arapi.ARWfdGetFieldValues(byref(self.context),
                                                        howFarBack,
                                                        byref(trFieldList),
                                                        byref(dbFieldList),
                                                        byref(self.arsl))
            if self.errnr > 1:
                return None
            return (trFieldList, dbFieldList)
        
        def ARWfdGetFilterQual(self):
            '''ARWfdGetFilterQual requests the field-value list associated with 
the current schema at the current location.
Input:
  :returns: filterQual (ARQualifierStruct)'''
            self.logger.debug('enter ARWfdGetFilterQual...')
            filterQual = cars.ARQualifierStruct()
            self.errnr = self.arapi.ARWfdGetFilterQual(byref(self.context),
                                                       byref(filterQual),
                                                       byref(self.arsl))
            if self.errnr > 1:
                return None
            return filterQual
            
        def ARWfdGetKeywordValue(self, keywordId):
            '''ARWfdGetKeywordValue retrieves the value of a keyword, if possible.
Input: keywordId (c_uint)
  :returns: ARValueStruct'''
            self.logger.debug('enter ARWfdGetKeywordValue...')
            value = cars.ARValueStruct()
            self.errnr = self.arapi.ARWfdGetKeywordValue(byref(self.context),
                                                         keywordId,
                                                         byref(value),
                                                         byref(self.arsl))
            if self.errnr > 1:
                return None
            return value

        def ARWfdGetUserContext(self, mask = 0):
            '''ARWfdGetUserContext retrieves information associated with the workflow user.
Input: mask (c_uint)
  :returns: ARWfdUserContext'''
            self.logger.debug('enter ARWfdGetUserContext...')
            userInfo = cars.ARWfdUserContext()
            self.errnr = self.arapi.ARWfdGetUserContext(byref(self.context),
                                                         mask,
                                                         byref(userInfo),
                                                         byref(self.arsl))
            if self.errnr > 1:
                return None
            return userInfo

        def ARWfdListBreakpoints(self):
            '''ARWfdListBreakpoints returns a list of server breakpoints.
Input:
  :returns: ARWfdRmtBreakpointList (or None in case of failure)'''
            self.logger.debug('enter ARWfdListBreakpoints...')
            bpList = cars.ARWfdRmtBreakpointList()
            self.errnr = self.arapi.ARWfdGetUserContext(byref(self.context),
                                                         byref(bpList),
                                                         byref(self.arsl))
            if self.errnr > 1:
                return None
            return bpList
                    
        def ARWfdSetBreakpoint(self, inBp):
            '''ARWfdSetBreakpoint sets a breakpoint on the server, and overwrites 
if needed.
Input: inBp (ARWfdRmtBreakpoint)
  :returns: errnr'''
            self.logger.debug('enter ARWfdSetBreakpoint...')
            self.errnr = self.arapi.ARWfdSetBreakpoint(byref(self.context),
                                                       my_byref(inBp),
                                                       byref(self.arsl))
            return self.errnr
        
        def ARWfdSetDebugMode(self, mode = cars.WFD_EXECUTE_STEP):
            '''ARWfdSetDebugMode sets a new debug mode.
Input: (optional) mode (c_uint, default: WFD_EXECUTE_STEP)
  :returns: errnr'''
            self.logger.debug('enter ARWfdSetDebugMode...')
            self.errnr = self.arapi.ARWfdSetDebugMode(byref(self.context),
                                                      mode,
                                                      byref(self.arsl))
            return self.errnr

        def ARWfdSetFieldValues(self, trFieldList, dbFieldList):
            '''ARWfdSetFieldValues overwrites the field-value list associated 
with the current schema at the current location.
Input: trFieldList (ARFieldValueList)
       dbFieldList (ARFieldValueList)
  :returns: errnr'''
            self.logger.debug('enter ARWfdSetFieldValues...')
            self.errnr = self.arapi.ARWfdSetFieldValues(byref(self.context),
                                                      my_byref(trFieldList),
                                                      my_byref(dbFieldList),
                                                      byref(self.arsl))
            return self.errnr

        def ARWfdSetQualifierResult(self, result):
            '''ARWfdSetQualifierResult forces the qualifier result to the specified 
Boolean value.
Input: result (ARBoolean)
  :returns: errnr'''
            self.logger.debug('enter ARWfdSetQualifierResult...')
            self.errnr = self.arapi.ARWfdSetQualifierResult(byref(self.context),
                                                            result,
                                                            byref(self.arsl))
            return self.errnr
        
        def ARWfdTerminateAPI(self, errorCode):
            '''ARWfdTerminateAPI causes workflow to return with an optionally 
specified error at the next opportunity. If an error is not specified, a generic 
TERMINATED_BY_DEBUGGER error will be returned
Input: errorCode (c_uint)
  :returns: errnr'''
            self.logger.debug('enter ARWfdTerminateAPI...')
            self.errnr = self.arapi.ARWfdTerminateAPI(byref(self.context),
                                                      errorCode,
                                                      byref(self.arsl))
            return self.errnr

        def ARGetActiveLinkFromXML(self, parsedStream, 
                                   activeLinkName,
                                   appBlockName = None):
            '''ARGetActiveLinkFromXML retrieves an active link from an XML document.

Input: parsedStream
       activeLinkName
       appBlockName
  :returns: (ARActiveLinkStruct, supportFileList, arDocVersion) or 
    None in case of failure'''
            self.logger.debug('enter ARGetActiveLinkFromXML...')
            self.errnr = 0
            
            order = c_uint()
            schemaList = cars.ARWorkflowConnectStruct()
            groupList = cars.ARInternalIdList()
            executeMask = c_uint()
            controlField = cars.ARInternalId()
            focusField = cars.ARInternalId()
            enable = c_uint()
            query = cars.ARQualifierStruct()
            actionList = cars.ARActiveLinkActionList()
            elseList = cars.ARActiveLinkActionList()
            supportFileList = cars.ARSupportFileInfoList()
            helpText = c_char_p()
            modifiedDate = cars.ARTimestamp()
            owner = cars.ARAccessNameType()
            lastChanged = cars.ARAccessNameType()
            changeDiary = c_char_p()
            objPropList = cars.ARPropList()
            arDocVersion = c_uint()
            errorActlinkOptions = c_uint()
            errorActlinkName = cars.ARNameType()
            self.errnr = self.arapi.ARGetActiveLinkFromXML(byref(self.context),
                                                           my_byref(parsedStream),
                                                           activeLinkName,
                                                           appBlockName,
                                                              byref(order),
                                                              byref(schemaList),
                                                              byref(groupList),
                                                              byref(executeMask),
                                                              byref(controlField),
                                                              byref(focusField),
                                                              byref(enable),
                                                              byref(query),
                                                              byref(actionList),
                                                              byref(elseList),
                                                              byref(supportFileList),
                                                              owner,
                                                              lastChanged,
                                                              byref(modifiedDate),
                                                              byref(helpText),
                                                              byref(changeDiary),
                                                              byref(objPropList),
                                                              byref(arDocVersion),
                                                              byref(errorActlinkOptions),
                                                              errorActlinkName,
                                                              byref(self.arsl))
            if self.errnr < 2:
                return (ARActiveLinkStruct(activeLinkName,
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
                                            modifiedDate,
                                            owner.value,
                                            lastChanged.value,
                                            changeDiary,
                                            objPropList,
                                            errorActlinkOptions,
                                            errorActlinkName), supportFileList, arDocVersion)
            else:
                self.logger.error('ARGetActiveLinkFromXML: failed for %s' % activeLinkName)
                return None

        def ARGetDSOPoolFromXML(self, parsedStream, poolName, appBlockName):
            '''ARGetDSOPoolFromXML retrieves information about a DSO pool from a 
definition in an XML document.
Input: parsedStream (ARXMLParsedStream)
       poolName (ARNameType)
       appBlockName (ARNameType)
  :returns: (enabled (c_uint),
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
            self.logger.debug('enter ARGetDSOPoolFromXML...')
            self.errnr = 0
            raise pyARSNotImplemented
        
        def ARGetImageFromXML(self, parsedStream, imageName, appBlockName):
            '''ARGetImageFromXML retrieves information about an image from an XML 
document.
Input: parsedStream (ARXMLParsedStream)
       imageName (ARNameType)
       appBlockName (ARNameType)
  :returns: (imageType (c_char_p),
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
            imageType = c_char_p()
            contentLength = c_uint()
            checksum = c_char_p()
            timestamp = cars.ARTimestamp()
            description = c_char_p()
            owner = cars.ARAccessNameType()
            lastModifiedBy = cars.ARAccessNameType()
            helpText = c_char_p()
            changeHistory = c_char_p()
            objPropList = cars.ARPropList()
            imageCon = c_char_p()
            self.errnr = self.arapi.ARGetImageFromXML(byref(self.context),
                                                      my_byref(parsedStream),
                                                      imageName,
                                                      appBlockName,
                                                      byref(imageType),
                                                      byref(contentLength),
                                                      byref(checksum),
                                                      byref(timestamp),
                                                      byref(description),
                                                      owner,
                                                      lastModifiedBy,
                                                      byref(helpText),
                                                      byref(changeHistory),
                                                      byref(objPropList),
                                                      byref(imageCon),
                                                      byref(self.arsl))

        def ARSetActiveLinkToXML(self, activeLinkName,
                                 xmlDocHdrFtrFlag = False, 
                                 executionOrder = 0,
                                 workflowConnect = None,
                                 accessList = None,
                                 executeOn = 0,
                                 controlFieldID = 0,
                                 focusFieldID = 0,
                                 enabled = 0,
                                 query = None,
                                 ifActionList = None,
                                 elseActionList = None,
                                 supportFileList = None,
                                 owner = '',
                                 lastModifiedBy = '',
                                 modifiedDate = 0,
                                 helpText = None,
                                 changeHistory = None,
                                 objPropList = None,
                                 arDocVersion = c_uint(0),
                                 errorActlinkOptions = c_uint(0),
                                 errorActlinkName = None):
            '''ARSetActiveLinkToXML converts active links to XML.
    
Input: activeLinkName (ARNameType),
       (optional) xmlDocHdrFtrFlag (ARBoolean, default = False), 
       (optional) executionOrder (c_uint, default = 0)
       (optional) workflowConnect (ARWorkflowConnectStruct, default = None),
       (optional) accessList (ARInternalIdList, default = None)
       (optional) executeOn (c_uint, default = 0)
       (optional) controlFieldID (ARInternalId, default = 0)
       (optional) focusFieldID (ARInternalId, default = 0)
       (optional) enabled (c_uint, default = 0)
       (optional) query (ARQualifierStruct, default = None)
       (optional) ifActionList (ARActiveLinkActionList, default = None)
       (optional) elseActionList (ARActiveLinkActionList, default = None)
       (optional) supportFileList (ARSupportFileInfoList, default = None)
       (optional) owner (ARAccessNameType, default = '')
       (optional) lastModifiedBy (ARAccessNameType, default = '')
       (optional) modifiedDate (ARTimestamp, default = 0)
       (optional) helpText (c_char_p, default = None)
       (optional) changeHistory (c_char_p, default = None)
       (optional) objPropList (ARPropList, default = None)
       (optional) arDocVersion (default = c_uint(0))
       (optional) errorActlinkOptions (c_uint, default = 0),
       (optional) errorActlinkName (ARNameType, default = None)
  :returns: string containing the XML
        or None in case of failure'''
            self.logger.debug('enter ARSetActiveLinkToXML...')
            if not isinstance(executionOrder, c_uint):
                executionOrder = c_uint(executionOrder)
            if not isinstance(executeOn, c_uint):
                executeOn = c_uint(executeOn)
            if not isinstance(controlFieldID, c_uint):
                controlFieldID = c_uint(controlFieldID)
            if not isinstance(focusFieldID, c_uint):
                focusFieldID = c_uint(focusFieldID)
            if not isinstance(enabled, c_uint):
                enabled = c_uint(enabled)
            if not isinstance(modifiedDate, cars.ARTimestamp):
                modifiedDate = cars.ARTimestamp(modifiedDate)
            if not isinstance(arDocVersion, c_uint):
                arDocVersion = c_uint(arDocVersion)
    
            assert isinstance(xmlDocHdrFtrFlag, int) or xmlDocHdrFtrFlag is None
            assert isinstance(activeLinkName, str) or activeLinkName is None
            assert isinstance(executionOrder, c_uint) or executionOrder is None
            assert isinstance(workflowConnect, cars.ARWorkflowConnectStruct) or workflowConnect is None
            assert isinstance(accessList, cars.ARInternalIdList) or accessList is None
            assert isinstance(executeOn, c_uint) or executeOn is None
            assert isinstance(controlFieldID, cars.ARInternalId) or controlFieldID is None
            assert isinstance(focusFieldID, cars.ARInternalId) or focusFieldID is None
            assert isinstance(enabled, c_uint) or enabled is None
            assert isinstance(query, cars.ARQualifierStruct) or query is None
            assert isinstance(ifActionList, cars.ARActiveLinkActionList) or ifActionList is None
            assert isinstance(elseActionList, cars.ARActiveLinkActionList) or elseActionList is None
            assert isinstance(supportFileList, cars.ARSupportFileInfoList) or supportFileList is None
            assert isinstance(owner, str)
            assert isinstance(lastModifiedBy, str)
            assert isinstance(modifiedDate, cars.ARTimestamp)
            assert isinstance(helpText, str) or helpText is None
            assert isinstance(changeHistory, str) or changeHistory is None
            assert isinstance(objPropList, cars.ARPropList) or objPropList is None
            assert isinstance(arDocVersion, c_uint)
            xml = cars.ARXMLOutputDoc(cars.AR_XML_DOC_CHAR_STR) 
            self.errnr = self.arapi.ARSetActiveLinkToXML(byref(self.context),
                                                         my_byref(xml), 
                                                         xmlDocHdrFtrFlag, 
                                                         activeLinkName,
                                                         my_byref(executionOrder),
                                                         my_byref(workflowConnect),
                                                         my_byref(accessList),
                                                         my_byref(executeOn),
                                                         my_byref(controlFieldID),
                                                         my_byref(focusFieldID),
                                                         my_byref(enabled),
                                                         my_byref(query),
                                                         my_byref(ifActionList),
                                                         my_byref(elseActionList),
                                                         my_byref(supportFileList),
                                                         owner,
                                                         lastModifiedBy,
                                                         my_byref(modifiedDate),
                                                         helpText,
                                                         changeHistory,
                                                         my_byref(objPropList),
                                                         my_byref(arDocVersion),
                                                         my_byref(errorActlinkOptions),
                                                         errorActlinkName,
                                                         byref(self.arsl))
            if self.errnr < 2:
                return xml.u.charBuffer
            else:
                self.logger.error('ARSetActiveLinkToXML failed')
                return None

        def ARSetDSOPoolToXML(self, poolName, 
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
            '''ARSetDSOPoolToXML retrieves information about the DSO pool.

Input: 
  :returns: string containing the XML
        or None in case of failure'''
            self.logger.debug('enter ARSetDSOPoolToXML...')
            self.errnr = 0
            if not isinstance(enabled, c_uint):
                enabled = c_uint(enabled)
            if not isinstance(defaultPool, c_uint):
                defaultPool = c_uint(defaultPool)
            if not isinstance(threadCount, c_long):
                threadCount = c_long(threadCount)
            if not isinstance(polling, c_uint):
                polling = c_uint(polling)
            if not isinstance(pollingInterval, c_uint):
                pollingInterval = c_uint(pollingInterval)
            if not isinstance(modifiedDate, cars.ARTimestamp):
                modifiedDate = cars.ARTimestamp(modifiedDate)
            if not isinstance(arDocVersion, c_uint):
                arDocVersion = c_uint(arDocVersion)
                
            xml = cars.ARXMLOutputDoc(cars.AR_XML_DOC_CHAR_STR)
            self.errnr = self.arapi.ARSetDSOPoolToXML(byref(self.context),
                                                     byref(xml),
                                                     xmlDocHdrFtrFlag,
                                                     poolName,
                                                     my_byref(enabled),
                                                     my_byref(defaultPool),
                                                     my_byref(threadCount),
                                                     my_byref(connection),
                                                     my_byref(polling),
                                                     my_byref(pollingInterval),
                                                     owner,
                                                     lastModifiedBy,
                                                     my_byref(modifiedDate),
                                                     helpText,
                                                     changeHistory,
                                                     my_byref(objPropList),
                                                     my_byref(arDocVersion),
                                                     byref(self.arsl))
            if self.errnr < 2:
                return xml.u.charBuffer
            else:
                self.logger.error("ARSetDSOPoolToXML returned an error")
                return None

        def ARSetImageToXML(self, imageName,
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
            '''ARSetImageToXML saves information about an image to an XML document.
Input: imageName (ARNameType)
       xmlDocHdrFtrFlag (ARBoolean)
       imageType (c_char_p)
       description (c_char_p)
       owner (ARAccessNameType)
       lastModifiedBy (ARAccessNameType)
       helpText (c_char_p)
       hangeHistory (c_char_p)
       objPropList (ARPropList)
       checksum (c_char)
       modifiedDate (ARTimestamp)
       imageContent (ARImageDataStruct)
  :returns: errnr'''
            self.logger.debug('enter ARSetImageToXML...')
            xml = cars.ARXMLOutputDoc(cars.AR_XML_DOC_CHAR_STR)
            self.errnr = self.arapi.ARSetImageToXML(byref(self.context),
                                                     byref(xml),
                                                     xmlDocHdrFtrFlag,
                                                     imageName,
                                                     imageType,
                                                     description,
                                                     owner,
                                                     lastModifiedBy,
                                                     helpText,
                                                     changeHistory,
                                                     objPropList,
                                                     checksum,
                                                     my_byref(modifiedDate),
                                                     imageContent,
                                                     byref(self.arsl))
            if self.errnr < 2:
                return xml.u.charBuffer
            else:
                self.logger.error("ARSetImageToXML returned an error")
                return None            

    class ARS(ARS75):
        pass

if cars.version >= 76.03:
    class ARActiveLinkStruct(Structure):
        _fields_ = [("name", cars.ARNameType),
                    ("order", c_uint),
                    ("schemaList", cars.ARWorkflowConnectStruct),
                    ("assignedGroupList", cars.ARInternalIdList),
                    ("groupList", cars.ARInternalIdList),
                    ("executeMask", c_uint),
                    ("controlField", cars.ARInternalId),
                    ("focusField",  cars.ARInternalId),
                    ("enable", c_uint),
                    ("query", cars.ARQualifierStruct),
                    ("actionList", cars.ARActiveLinkActionList),
                    ("elseList", cars.ARActiveLinkActionList),
                    ("helpText", c_char_p),
                    ("timestamp", cars.ARTimestamp),
                    ("owner", cars.ARAccessNameType),
                    ("lastChanged", cars.ARAccessNameType),
                    ("changeDiary", c_char_p),
                    ("objPropList", cars.ARPropList),
                    ("errorActlinkOptions", c_uint),
                    ("errorActlinkName", cars.ARNameType)]

    class ARActiveLinkList(Structure):
        _fields_ = [('numItems', c_uint),
                    ('activeLinkList',POINTER(ARActiveLinkStruct))]

    class ARContainerStruct(Structure):
        _fields_ = [("name", cars.ARNameType),
            ("assignedGroupList", cars.ARPermissionList),
            ("groupList", cars.ARPermissionList),
            ("admingrpList", cars.ARInternalIdList),
            ("ownerObjList", cars.ARContainerOwnerObjList),
            ("label", c_char_p),
            ("description", c_char_p),
            ("type", c_uint),
            ("references", cars.ARReferenceList),
            ("helpText", c_char_p),
            ("owner", cars.ARAccessNameType),
            ("timestamp", cars.ARTimestamp),
            ("lastChanged", cars.ARAccessNameType),
            ("changeDiary", c_char_p),
            ("objPropList", cars.ARPropList)]
    
    class ARContainerList(Structure):
        _fields_ = [('numItems', c_uint),
                    ('containerList',POINTER(ARContainerStruct))]
        
#    class ARFilterStruct(Structure):
#        _fields_ = [("name", cars.ARNameType),
#                    ("order", c_uint),
#                    ("schemaList", cars.ARWorkflowConnectStruct),
#                    ("opSet", c_uint),
#                    ("enable", c_uint),
#                    ("query", cars.ARQualifierStruct),
#                    ("actionList", cars.ARFilterActionList),
#                    ("elseList", cars.ARFilterActionList),
#                    ("helpText", c_char_p),
#                    ("timestamp", cars.ARTimestamp),
#                    ("owner", cars.ARAccessNameType),
#                    ("lastChanged", cars.ARAccessNameType),
#                    ("changeDiary", c_char_p),
#                    ("objPropList", cars.ARPropList),
#                    ("errorFilterOptions", c_uint),
#                    ("errorFilterName", cars.ARNameType)]
#    
#    class ARFilterList(Structure):
#        _fields_ = [('numItems', c_uint),
#                    ('filterList',POINTER(ARFilterStruct))]
    class ARSchema(Structure):
        _fields_ = [("name", cars.ARNameType),
                    ("schema", cars.ARCompoundSchema),
                    ("schemaInheritanceList", cars.ARSchemaInheritanceList),
                    ("assignedGroupList", cars.ARPermissionList),
                    ("groupList", cars.ARPermissionList),
                    ("admingrpList", cars.ARInternalIdList),
                    ("getListFields",  cars.AREntryListFieldList),
                    ("sortList", cars.ARSortList),
                    ("indexList", cars.ARIndexList),
                    ("archiveInfo", cars.ARArchiveInfoStruct),
                    ("auditInfo", cars.ARAuditInfoStruct),
                    ("defaultVui", cars.ARNameType),
                    ("helpText", c_char_p),
                    ("timestamp", cars.ARTimestamp),
                    ("owner", cars.ARAccessNameType),
                    ("lastChanged", cars.ARAccessNameType),
                    ("changeDiary", c_char_p),
                    ("objPropList", cars.ARPropList)]

    class ARSchemaList(Structure):
        _fields_ = [('numItems', c_uint),
                    ('schemaList',POINTER(ARSchema))]
        
    class ARS7603(ARS75):

        def ARCreateActiveLink (self, name, 
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
  :returns: errnr'''
            self.logger.debug('enter ARCreateActiveLink...')
            self.errnr = self.arapi.ARCreateActiveLink(byref(self.context),
                                                       name, 
                                                       order, 
                                                       my_byref(schemaList), 
                                                       my_byref(groupList),
                                                       executeMask,
                                                       my_byref(controlField),
                                                       my_byref(focusField),
                                                       enable, 
                                                       my_byref(query),
                                                       my_byref(actionList),
                                                       my_byref(elseList),
                                                       helpText,
                                                       owner,
                                                       changeDiary,
                                                       my_byref(objPropList),
                                                       errorActlinkOptions,
                                                       errorActlinkName,
                                                       objectModificationLogLabel,
                                                       byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARCreateActiveLink failed for %s' % name)
            return self.errnr

        def ARCreateCharMenu(self, 
                             name, 
                             refreshCode, 
                             menuDefn, 
                             helpText = None, 
                             owner = None,
                             changeDiary = None, 
                             objPropList = None,
                             objectModificationLogLabel = None):
            '''ARCreateCharMenu creates a new character menu.

ARCreateCharMenu creates a new character menu with the indicated name
Input: name (ARNameType)
       refreshCode (c_uint)
       menuDef (ARCharMenuStruct)
       (optional) helpText (c_char_p, default = None)
       (optional) owner (ARAccessNameType, default = None)
       (optional) changeDiary (c_char_p, default = None)
       (optional) objPropList (ARPropList, default = None)
       (optional) objectModificationLogLabel (c_char_p, default = None)
  :returns: errnr'''
            self.logger.debug('enter ARCreateCharMenu...')
            self.errnr = self.arapi.ARCreateCharMenu(byref(self.context),
                                                     name, 
                                                     refreshCode, 
                                                     my_byref(menuDefn), 
                                                     helpText, 
                                                     owner,
                                                     changeDiary, 
                                                     my_byref(objPropList),
                                                     objectModificationLogLabel,
                                                     byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARCreateCharMenu failed for %s' % name)
            return self.errnr 

        def ARCreateContainer(self, 
                              name, 
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
            '''ARCreateContainer creates a new container.

ARCreateContainer creates a new container with the indicated name. Use this 
function to create applications, active links, active link guides, filter 
guide, packing lists, guides, and AR System-defined container types. 
A container can also be a custom type that you define.
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
  :returns: errnr'''
            self.logger.debug('enter ARCreateContainer...')
            self.errnr = self.arapi.ARCreateContainer(byref(self.context),
                                                      name, 
                                                      my_byref(groupList), 
                                                      my_byref(admingrpList), 
                                                      my_byref(ownerObjList), 
                                                      my_byref(label), 
                                                      my_byref(description),
                                                      my_byref(type_),
                                                      my_byref(references),
                                                      removeFlag,
                                                      helpText,
                                                      owner,
                                                      changeDiary,
                                                      my_byref(objPropList),
                                                      my_byref(objectModificationLogLabel),
                                                      byref(self.arsl))
            if self.errnr < 2:
                self.logger.error('ARCreateContainer failed for %s' % name)
            return self.errnr

        def ARCreateEscalation(self, 
                               name, 
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
            '''ARCreateEscalation creates a new escalation.

ARCreateEscalation creates a new escalation with the indicated name. The escalation condition
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
  :returns: errnr'''
            self.logger.debug('enter ARCreateEscalation...')
            self.errnr = self.arapi.ARCreateEscalation(byref(self.context),
                                                       name, 
                                                       my_byref(escalationTm), 
                                                       my_byref(schemaList), 
                                                       enable, 
                                                       my_byref(query), 
                                                       my_byref(actionList),
                                                       my_byref(elseList), 
                                                       helpText, 
                                                       owner, 
                                                       changeDiary, 
                                                       my_byref(objPropList),
                                                       objectModificationLogLabel,
                                                       byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARCreateEscalation failed for %s' % name)
            return self.errnr

        def ARCreateField(self, schema, 
                          fieldId, 
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
            '''ARCreateField creates a new field.

ARCreateField creates a new field with the indicated name on the specified server. Forms
can contain data and nondata fields. Nondata fields serve several purposes.
Trim fields enhance the appearance and usability of the form (for example,
lines, boxes, or static text). Control fields provide mechanisms for executing
active links (for example, menus, buttons, or toolbar buttons). Other
nondata fields organize data for viewing (for example, pages and page
holders) or show data from another form (for example, tables and columns).
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
  :returns: fieldId (or None in case of failure)'''
            self.logger.debug('enter ARCreateField...')
            self.errnr = self.arapi.ARCreateField(byref(self.context),
                                                  schema, 
                                                  byref(fieldId), 
                                                  reservedIdOK,
                                                  fieldName, 
                                                  my_byref(fieldMap), 
                                                  dataType, 
                                                  option, 
                                                  createMode, 
                                                  fieldOption,
                                                  my_byref(defaultVal), 
                                                  my_byref(permissions),
                                                  my_byref(limit), 
                                                  my_byref(dInstanceList),
                                                  helpText, 
                                                  owner, 
                                                  changeDiary,
                                                  my_byref(objPropList),
                                                  byref(self.arsl))
            if self.errnr < 2:
                return fieldId
            else:
                self.logger.error('ARCreateField: failed for %s on %s' % (fieldName, schema))
                return None

        def ARCreateFilter(self, 
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
            '''ARCreateFilter creates a new filter.

ARCreateFilter creates a new filter with the indicated name on the specified 
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
  :returns: errnr'''
            self.logger.debug('enter ARCreateFilter...')
            self.errnr = 0
            self.errnr = self.arapi.ARCreateFilter(byref(self.context),
                                                   name, 
                                                   order, 
                                                   my_byref(schemaList),
                                                   opSet, 
                                                   enable, 
                                                   my_byref(query),
                                                   my_byref(actionList),
                                                   my_byref(elseList),
                                                   helpText,
                                                   owner, 
                                                   changeDiary,
                                                   my_byref(objPropList),
                                                   errorFilterOptions,
                                                   errorFilterName,
                                                   objectModificationLogLabel,
                                                   byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARCreateFilter failed for %s' % name)
            return self.errnr

        def ARCreateImage(self, name,
                          imageBuf,
                          imageType,
                          description = None,
                          helpText = None,
                          owner = None,
                          changeDiary = None,
                          objPropList = None,
                          objectModificationLogLabel = None):
            '''ARCreateImage creates a new image with the indicated name on the specified server
Input: name (ARNameType)
       imageBuf (ARImageDataStruct)
       imageType (c_char_p, Valid values are: BMP, GIF, JPEG or JPG, and PNG.)
       (optional) description (c_char_p, default: None)
       (optional) helpText (c_char_p, default: None)
       (optional) owner (ARAccessNameType, default: None)
       (optional) changeDiary (c_char_p, default: None)
       (optional) objPropList (ARPropList, default: None)
       (c_char) objectModificationLogLabel (optional, default = None)
  :returns: errnr'''
            self.logger.debug('enter ARCreateImage...')
            self.errnr = self.arapi.ARCreateImage(byref(self.context),
                                                  name,
                                                  my_byref(imageBuf),
                                                  imageType,
                                                  description,
                                                  helpText,
                                                  owner,
                                                  changeDiary,
                                                  my_byref(objPropList),
                                                  objectModificationLogLabel,
                                                  byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARCreateImage failed for %s' % name)
            return self.errnr
        
        def ARCreateMultipleFields (self, 
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
            '''ARCreateMultipleFields creates multiple fields in a form. 

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
  :returns: errnr'''
            self.logger.debug('enter ARCreateMultipleFields...')
            self.errnr = self.arapi.ARCreateMultipleFields(byref(self.context),
                                                           schema,
                                                    my_byref(fieldIdList),
                                                    my_byref(reservedIdOKList),
                                                    my_byref(fieldNameList),
                                                    my_byref(fieldMapList),
                                                    my_byref(dataTypeList),
                                                    my_byref(optionList),
                                                    my_byref(createModeList),
                                                    my_byref(fieldOptionList),
                                                    my_byref(defaultValList),
                                                    my_byref(permissionListList),
                                                    my_byref(limitList),
                                                    my_byref(dInstanceListList),
                                                    my_byref(helpTextList),
                                                    my_byref(ownerList),
                                                    my_byref(changeDiaryList),
                                                    my_byref(objPropListList),
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARCreateMultipleFields: failed')
            return self.errnr

        def ARCreateSchema(self, name, 
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
            '''ARCreateSchema creates a new form.

ARCreateSchema creates a new form with the indicated name on the specified 
server. The nine required core fields are automatically associated with the 
new form.
Input: (ARNameType) name of schema
       (ARCompoundSchema) schema, 
       (ARSchemaInheritanceList) schemaInheritanceList (will be set to None, as it is reserved for future use), 
       (ARPermissionList) groupList, 
       (ARInternalIdList) admingrpList, 
       (AREntryListFieldList) getListFields,
       (ARSortList) sortList, 
       (ARIndexList) indexList, 
       (ARArchiveInfoStruct) archiveInfo,
       (ARAuditInfoStruct) auditInfo, 
       (ARNameType) defaultVui,
       (c_char_p) helpText (optional, default =None)
       (ARAccessNameType) owner (optional, default =None)
       (c_char_p) changeDiary (optional, default =None)
       (ARPropList) objPropList (optional, default =None)
       (c_char_p) objectModificationLogLabel (optional, default = None)   
  :returns: errnr'''
            self.logger.debug('enter ARCreateSchema...')
            self.errnr = 0
            schemaInheritanceList = None # reserved for future use...
            self.errnr = self.arapi.ARCreateSchema(byref(self.context),
                                                   name, 
                                                   my_byref(schema), 
                                                   my_byref(schemaInheritanceList), 
                                                   my_byref(groupList), 
                                                   my_byref(admingrpList), 
                                                   my_byref(getListFields),
                                                   my_byref(sortList), 
                                                   my_byref(indexList), 
                                                   my_byref(archiveInfo),
                                                   my_byref(auditInfo), 
                                                   defaultVui,
                                                   helpText, 
                                                   owner, 
                                                   changeDiary, 
                                                   my_byref(objPropList),
                                                   objectModificationLogLabel,
                                                   byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARCreateSchema failed for schema %s.' % name)
            return self.errnr        

        def ARCreateVUI(self, schema, 
                        vuiId, vuiName, locale, 
                      vuiType=None,
                      dPropList=None, 
                      helpText=None, 
                      owner=None, 
                      changeDiary=None,
                      smObjProp=None):
            '''ARCreateVUI creates a new form view (VUI).

ARCreateVUI creates a new form view (VUI) with the indicated name on
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
  :returns: vuiId (or None in case of failure)'''
            self.logger.debug('enter ARCreateVUI with type %s and #dProps: %d' % (
                              vuiType, dPropList.numItems))
            tempVuiId = cars.ARInternalId(vuiId)
            self.errnr = self.arapi.ARCreateVUI(byref(self.context),
                                                schema,
                                                byref(tempVuiId), 
                                                vuiName, 
                                                locale, 
                                                vuiType,
                                                my_byref(dPropList), 
                                                helpText, 
                                                owner, 
                                                changeDiary,
                                                my_byref(smObjProp),
                                                byref(self.arsl))
            if self.errnr < 2:
                return tempVuiId.value
            else:
                self.logger.error('ARCreateVUI: failed for schema %s and vui %s' % (
                                  schema, vuiName))
                return None

        def ARDeleteActiveLink(self, name, 
                               deleteOption = cars.AR_DEFAULT_DELETE_OPTION,
                               objectModificationLogLabel = None):
            '''ARDeleteActiveLink deletes the active link.
        
ARDeleteActiveLink deletes the active link with the indicated name from the
specified server and deletes any container references to the active link.
Input: name
       (optional) deleteOption (default = cars.AR_DEFAULT_DELETE_OPTION)
       (optional) objectModificationLogLabel (c_char_p, default = None)
  :returns: errnr'''
            self.logger.debug('enter ARDeleteActiveLink: %s...' % (name))
            self.errnr = self.arapi.ARDeleteActiveLink(byref(self.context),
                                                       name,
                                                       deleteOption,
                                                       objectModificationLogLabel,
                                                       byref(self.arsl))
            return self.errnr

        def ARDeleteCharMenu(self, name, 
                             deleteOption = cars.AR_DEFAULT_DELETE_OPTION,
                             objectModificationLogLabel = None):
            '''ARDeleteCharMenu deletes the character menu with the indicated name from
the specified server.

Input: name
       (optional) deleteOption (default = cars.AR_DEFAULT_DELETE_OPTION)
       (optional) objectModificationLogLabel (c_char_p, default = None)
  :returns: errnr'''
            self.logger.debug('enter ARDeleteCharMenu...')
            self.errnr = self.arapi.ARDeleteCharMenu(byref(self.context),
                                                   name,
                                                   deleteOption,
                                                   objectModificationLogLabel,
                                                   byref(self.arsl))
            return self.errnr

        def ARDeleteContainer(self, name, 
                              deleteOption = cars.AR_DEFAULT_DELETE_OPTION,
                              objectModificationLogLabel = None):
            '''ARDeleteContainer deletes the container .
        
ARDeleteContainer deletes the container with the indicated name from
the specified server and deletes any references to the container from other containers.
Input: name
       (optional) deleteOption (default = cars.AR_DEFAULT_DELETE_OPTION)
       (optional) objectModificationLogLabel (default = None)
  :returns: errnr'''
            self.logger.debug('enter ARDeleteContainer...')
            self.errnr = self.arapi.ARDeleteContainer(byref(self.context),
                                                   name,
                                                   deleteOption,
                                                   objectModificationLogLabel,
                                                   byref(self.arsl))
            return self.errnr

        def ARDeleteEscalation(self, name, deleteOption = cars.AR_DEFAULT_DELETE_OPTION,
                               objectModificationLogLabel = None):
            '''ARDeleteEscalation deletes the escalation.
        
ARDeleteEscalation deletes the escalation with the indicated name from the
specified server and deletes any container references to the escalation.
Input:  name
       (optional) deleteOption (default = cars.AR_DEFAULT_DELETE_OPTION)
       (optional) objectModificationLogLabel (c_char_p, default = None)
  :returns: errnr'''
            self.logger.debug('enter ARDeleteEscalation...')
            self.errnr = self.arapi.ARDeleteEscalation(byref(self.context),
                                                       name,
                                                       deleteOption,
                                                       objectModificationLogLabel,
                                                       byref(self.arsl))
            return self.errnr

        def ARDeleteFilter(self, name, deleteOption = cars.AR_DEFAULT_DELETE_OPTION,
                           objectModificationLogLabel = None):
            '''ARDeleteFilter deletes the filter.
        
ARDeleteFilter deletes the filter with the indicated name from the
specified server and deletes any container references to the filter.
Input:  name
       (optional) deleteOption (default = cars.AR_DEFAULT_DELETE_OPTION)
       (c_char_p) objectModificationLogLabel (optional, default = None)   
  :returns: errnr'''
            self.logger.debug('enter ARDeleteFilter...')
            self.errnr = self.arapi.ARDeleteFilter(byref(self.context),
                                                   name,
                                                   deleteOption,
                                                   objectModificationLogLabel,
                                                   byref(self.arsl))
            return self.errnr

        def ARDeleteImage(self, name,
                          updateRef,
                          objectModificationLogLabel = None):
            '''ARDeleteImage deletes the image with the indicated name from the specified server.
Input: name (ARNameType)
       updateRef (ARBoolean, specify TRUE to remove all references to the image)
       (c_char_p) objectModificationLogLabel (optional, default = None)
  :returns: errnr'''
            self.logger.debug('enter ARDeleteImage...')
            self.errnr = self.arapi.ARDeleteImage(byref(self.context),
                                                  name,
                                                  updateRef,
                                                  objectModificationLogLabel,
                                                  byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARDeleteImage failed for %s' % name)
            return self.errnr

        def ARDeleteSchema(self, name, deleteOption = cars.AR_SCHEMA_CLEAN_DELETE,
                           objectModificationLogLabel = None):
            '''ARDeleteSchema deletes the form.
        
ARDeleteSchema deletes the form with the indicated name from the
specified server and deletes any container references to the form.
Input: name
       deleteOption
       (c_char_p) objectModificationLogLabel (optional, default = None)
  :returns: errnr'''
            self.logger.debug('enter ARDeleteSchema...')
            self.errnr = self.arapi.ARDeleteSchema(byref(self.context),
                                                   name,
                                                   deleteOption,
                                                   objectModificationLogLabel,
                                                   byref(self.arsl))
            return self.errnr

        def ARExport(self, 
                     structItems, 
                     displayTag = None, 
                     vuiType = cars.AR_VUI_TYPE_WINDOWS,
                     exportOption = cars.AR_EXPORT_DEFAULT,
                     lockinfo = None):
            '''ARExport exports the indicated structure definitions.

Use this function to copy structure definitions from one AR System server to another.
Note: Form exports do not work the same way with ARExport as they do in
Remedy Administrator. Other than views, you cannot automatically
export related items along with a form. You must explicitly specify the
workflow items you want to export. Also, ARExport cannot export a form
without embedding the server name in the export file (something you can
do with the "Server-Independent" option in Remedy Administrator).
Input: (ARStructItemList) structItems
       (ARNameType) displayTag (optional, default = None)
       (c_uint) vuiType (optional, default = cars.AR_VUI_TYPE_WINDOWS)
       (c_uint) exportOption (optional, default = cars.EXPORT_DEFAULT)
       (ARWorkflowLockStruct) lockinfo  (optional, default = None)
  :returns: string (or None in case of failure)'''
            self.logger.debug('enter ARExport...')
            exportBuf = c_char_p()
            self.errnr = self.arapi.ARExport(byref(self.context),
                                             byref(structItems),
                                             displayTag,
                                             vuiType,
                                             exportOption,
                                             my_byref(lockinfo),
                                             byref(exportBuf),
                                             byref(self.arsl))
            if self.errnr < 2:
                return exportBuf.value
            else:
                self.logger.error('ARExport failed with %d' % (self.errnr))
                return None

        def ARExportToFile(self, structItems,
                           displayTag = None,
                           vuiType = cars.AR_VUI_TYPE_WINDOWS,
                           exportOption = cars.AR_EXPORT_DEFAULT,
                           lockinfo = None,
                           filePtr = None):
            '''ARExportToFile exports the indicated structure definitions 
from the specified server to a file. Use this function to copy structure 
definitions from one AR System server to another.
Input: (ARStructItemList) structItems
       (ARNameType)displayTag (optional, default = None)
       (c_uint) vuiType  (optional, default = AR_VUI_TYPE_WINDOWS)
       (c_uint) exportOption (optional, default = cars.EXPORT_DEFAULT)
       (ARWorkflowLockStruct) lockinfo  (optional, default = None)
       (FILE) filePtr  (optional, default = None, resulting in an error)
  :returns: errnr'''
            self.logger.debug('enter ARExportToFile...')
            self.errnr = self.arapi.ARExportToFile(byref(self.context),
                                                   my_byref(structItems),
                                                   displayTag,
                                                   vuiType,
                                                   exportOption,
                                                   my_byref(lockinfo),
                                                   my_byref(filePtr),
                                                   byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARExportToFile: failed ')
            return self.errnr

        def ARGetActiveLink (self, name):
            '''ARGetActiveLink retrieves the active link with the indicated name.

ARGetActiveLink retrieves the active link with the indicated name on
the specified server.
Input: name (ARNameType)
  :returns: ARActiveLinkStruct (containing: order, schemaList,
           groupList, executeMask, controlField,
           focusField, enable, query, actionList,
           elseList, helpText, timestamp, owner, lastChanged,
           changeDiary, objPropList, errorActlinkOptions, errorActlinkName) 
    or None in case of failure'''
            self.logger.debug('enter ARGetActiveLink...')
            order = c_uint()
            schemaList = cars.ARWorkflowConnectStruct()
            assignedGroupList = cars.ARInternalIdList()
            groupList = cars.ARInternalIdList()
            executeMask = c_uint()
            controlField = cars.ARInternalId()
            focusField = cars.ARInternalId()
            enable = c_uint()
            query = cars.ARQualifierStruct()
            actionList = cars.ARActiveLinkActionList()
            elseList = cars.ARActiveLinkActionList()
            helpText = c_char_p()
            timestamp = cars.ARTimestamp()
            owner = cars.ARAccessNameType()
            lastChanged = cars.ARAccessNameType()
            changeDiary = c_char_p()
            objPropList = cars.ARPropList()
            errorActlinkOptions = c_uint()
            errorActlinkName = cars.ARNameType()
            self.errnr = self.arapi.ARGetActiveLink(byref(self.context),
                                      name,
                                      byref(order),
                                      byref(schemaList),
                                      byref(assignedGroupList),
                                      byref(groupList),
                                      byref(executeMask),
                                      byref(controlField),
                                      byref(focusField),
                                      byref(enable),
                                      byref(query),
                                      byref(actionList),
                                      byref(elseList),
                                      byref(helpText),
                                      byref(timestamp),
                                      owner,
                                      lastChanged,
                                      byref(changeDiary),
                                      byref(objPropList),
                                      byref(errorActlinkOptions),
                                      byref(errorActlinkName),
                                      byref(self.arsl))
            if self.errnr < 2:
                result = ARActiveLinkStruct(name,
                                            order,
                                            schemaList,
                                            assignedGroupList,
                                            groupList,
                                            executeMask,
                                            controlField,
                                            focusField,
                                            enable,
                                            query,
                                            actionList,
                                            elseList,
                                            helpText,
                                            timestamp,
                                            owner.value,
                                            lastChanged.value,
                                            changeDiary,
                                            objPropList,
                                            errorActlinkOptions,
                                            errorActlinkName.value)
                return result
            else:
                self.logger.error('ARGetActiveLink: failed for %s' % name)
                return None

        def ARGetContainer(self, name, refTypes = None):
            '''ARGetContainer retrieves the contents of the container.

It can return references of a single, specified type, of all types,
or of an exclude reference type. The system returns information for
accessible references and does nothing for references for which the user does
not have access.        
Input: name
       (optional) refTypes (None)
  :returns: ARContainerStruct (groupList, admingrpList, ownerObjList, label, description,
type,references,helpText,owner,timestamp,lastChanged,changeDiary,objPropList)
or None in case of failure'''
            self.logger.debug('enter ARGetContainer...')
            assignedGroupList = cars.ARPermissionList()
            groupList = cars.ARPermissionList()
            admingrpList = cars.ARInternalIdList()
            ownerObjList = cars.ARContainerOwnerObjList()
            label = c_char_p()
            description = c_char_p()
            type_ = c_uint()
            references = cars.ARReferenceList()
            helpText = c_char_p()
            owner = cars.ARAccessNameType()
            timestamp = cars.ARTimestamp()
            lastChanged = cars.ARAccessNameType()
            changeDiary = c_char_p()
            objPropList = cars.ARPropList()
            self.errnr = self.arapi.ARGetContainer(byref(self.context),
                                                   name,
                                                   my_byref(refTypes),
                                                   byref(assignedGroupList),
                                                   byref(groupList),
                                                   byref(admingrpList),
                                                   byref(ownerObjList),
                                                   byref(label),
                                                   byref(description),
                                                   byref(type_),
                                                   byref(references),
                                                   byref(helpText),
                                                   owner,
                                                   byref(timestamp),
                                                   lastChanged,
                                                   byref(changeDiary),
                                                   byref(objPropList),
                                                   byref(self.arsl))
            if self.errnr < 2:
                return ARContainerStruct(name,
                                           assignedGroupList,
                                           groupList,
                                           admingrpList,
                                           ownerObjList,
                                           label,
                                           description,
                                           type_,
                                           references,
                                           helpText,
                                           owner.value,
                                           timestamp,
                                           lastChanged.value,
                                           changeDiary.value,
                                           objPropList)
            else:
                self.logger.error('ARGetContainer: failed for %s' % name)
                return None

        def ARGetField (self, schema, fieldId):
            '''ARGetField retrieves the information for one field on a form.

ARGetField returns a ARFieldInfoStruct filled for a given fieldid.
Input: (ARNameType) schema
       (ARInternalId) fieldId
  :returns: ARFieldInfoStruct (or None in case of failure)'''
            self.logger.debug('enter ARGetField...')
            if schema.strip() == '' or schema == cars.AR_CURRENT_TRAN_TAG or \
                schema == cars.AR_CURRENT_SCHEMA_TAG:
                self.logger.error('ARGetField: no useful schema given')
                self.errnr = 2
                return None
            try:
                if not isinstance(fieldId,int):
                    fieldId=int(fieldId)
            except:
                self.logger.error('ARGetField: no valid fieldid given')
                self.errnr = 2
                return None
            fieldName = cars.ARNameType()
            fieldMap = cars.ARFieldMappingStruct()
            dataType = c_uint()
            option = c_uint()
            createMode = c_uint()
            fieldOption = c_uint()
            defaultVal = cars.ARValueStruct()
            # if we ask for permissions we need admin rights...
            assignedGroupList = cars.ARPermissionList()
            permissions = cars.ARPermissionList()
            limit = cars.ARFieldLimitStruct()
            dInstanceList = cars.ARDisplayInstanceList()
            helpText = c_char_p()
            timestamp = cars.ARTimestamp()
            owner = cars.ARAccessNameType()
            lastChanged = cars.ARAccessNameType()
            changeDiary = c_char_p()
            objPropList = cars.ARPropList()
            self.errnr = self.arapi.ARGetField(byref(self.context),
                                              schema,
                                              fieldId,
                                              fieldName,
                                              byref(fieldMap),
                                              byref(dataType),
                                              byref(option),
                                              byref(createMode),
                                              byref(fieldOption),
                                              byref(defaultVal),
                                              byref(assignedGroupList),
                                              byref(permissions),
                                              byref(limit),
                                              byref(dInstanceList),
                                              byref(helpText),
                                              byref(timestamp),
                                              owner,
                                              lastChanged,
                                              byref(changeDiary),
                                              byref(objPropList),
                                              byref(self.arsl))
            if self.errnr < 2:
                return cars.ARFieldInfoStruct(fieldId,
                                           fieldName.value,
                                           timestamp,
                                           fieldMap,
                                           dataType,
                                           option,
                                           createMode,
                                           fieldOption,
                                           defaultVal,
# TODO: fixme!?!?!? assignedGroupList is returned by the server
#   but ARFieldInfoStruct does not contain it!!!
#                                           assignedGroupList,
                                           permissions,
                                           limit,
                                           dInstanceList,
                                           owner.value,
                                           lastChanged.value,
                                           helpText.value,
                                           changeDiary.value,
                                           objPropList)
            else:
                self.logger.error('ARGetField: failed for schema %s and fieldid %d' % (
                        schema, fieldId))
                return None

        def ARGetListEntryWithMultiSchemaFields (self, queryFromList, 
                                      getListFields=None, 
                                      qualifier = None,
                                      sortList=None,
                                      firstRetrieve=cars.AR_START_WITH_FIRST_ENTRY,
                                      maxRetrieve=cars.AR_NO_MAX_LIST_RETRIEVE,
                                      useLocale = False,
                                      groupBy = None,
                                      having = None,
                                      entryList = None):
            '''ARGetListEntryWithMultiSchemaFields performs dynamic joins by querying across multiple forms—including view and
vendor forms—at run time.
Input: queryFromList (ARMultiSchemaFuncQueryFromList)
       (optional) getListFields (ARMultiSchemaFieldFuncList, default = None), 
       (optional) qualifier (ARMultiSchemaQualifierStruct, default = None),
       (optional) sortList (ARMultiSchemaSortList, default = None),
       (optional) firstRetrieve (c_uint, default=cars.AR_START_WITH_FIRST_ENTRY),
       (optional) maxRetrieve (c_uint, default=cars.AR_NO_MAX_LIST_RETRIEVE),
       (optional) useLocale (ARBoolean, default = False)
       (optional) groupBy (ARMultiSchemaFieldIdList, default = None)
       (optional) having (ARMultiSchemaFuncQualifierStruct, default = None)
       (optional) entryList (ARMultiSchemaFieldFuncValueListList, default = None)
  :returns: (ARMultiSchemaFieldValueListList, numMatches (c_uint))'''
            self.logger.debug('enter ARGetListEntryWithMultiSchemaFields...')
            entryList = cars.ARMultiSchemaFieldValueListList()
            numMatches = c_uint()
            self.errnr = self.arapi.ARGetListEntryWithMultiSchemaFields(byref(self.context),
                                                                        my_byref(queryFromList),
                                                                        my_byref(getListFields),
                                                                        my_byref(qualifier),
                                                                        my_byref(sortList),
                                                                        firstRetrieve,
                                                                        maxRetrieve,
                                                                        useLocale,
                                                                        my_byref(groupBy),
                                                                        my_byref(having),
                                                                        byref(entryList),
                                                                        byref(numMatches),
                                                                        byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARGetListEntryWithMultiSchemaFields: failed')
                return None
            else:
                return (entryList, numMatches)

        def ARGetListField(self, schema,
                         changedSince=0,
                         fieldType=cars.AR_FIELD_TYPE_DATA,
                         objPropList = None):
            '''ARGetListField returns a list of field ids for a schema.
        
You can retrieve all fields or limit the list to fields of a particular type or fields
modified after a specified time.
Input: string: schema
       (optional) timestamp: changedSince (default: 0)
       (optional) fieldType (default: AR_FIELD_TYPE_DATA)
       (optional) objPropList (this extension is not documented in the 7.6 C API guide)
  :returns: ARInternalIdList (or None in case of failure)'''
            self.logger.debug('enter ARGetListField...')
            idList = cars.ARInternalIdList()
            if not isinstance(schema,str):
                self.errnr=2
                self.logger.error ("ARGetListField: wrong argument!")
                return None
            self.errnr = self.arapi.ARGetListField(byref(self.context),
                                                   schema,
                                                   fieldType,
                                                   changedSince,
                                                   my_byref(objPropList),
                                                   byref(idList),
                                                   byref(self.arsl))
            if self.errnr < 2:
                return idList
            else:
                self.logger.error ("ARGetListField: failed for schema %s!" % (schema))
                return None

        def ARGetListVUI(self, schema, changedSince=0,
                         objPropList = None):
            '''ARGetListVUI retrieves a list of form views (VUI) for a particular form.

You can retrieve all views or limit the list to views modified after a
specified time.
Input: schema
       (optional) changedSince (ARTimestamp)
       (optional) objPropList (ARPropList)
  :returns: ARInternalIdList (or None in case of failure)'''
            self.logger.debug('enter ARGetListVUI...')
            idList = cars.ARInternalIdList()
            self.errnr = self.arapi.ARGetListVUI(byref(self.context),
                                                 schema,
                                                 changedSince,
                                                 my_byref(objPropList),
                                                 byref(idList),
                                                 byref(self.arsl))
            if self.errnr < 2:
                return idList
            else:
                self.logger.error( "ARGetListVUI: failed")
                return None

        def ARGetMultipleActiveLinks(self, changedSince=0, 
                                     nameList = None,
                                     orderList = None,
                                     schemaList = None,
                                     assignedGroupListList = None,
                                     groupListList = None,
                                     executeMaskList = None,
                                     controlFieldList = None,
                                     focusFieldList = None,
                                     enableList = None,
                                     queryList = None,
                                     actionListList = None,
                                     elseListList = None,
                                     helpTextList = None,
                                     timestampList = None,
                                     ownersList = None,
                                     lastChangedList = None,
                                     changeDiaryList = None,
                                     objPropListList = None,
                                     errorActlinkOptionsList = None,
                                     errorActlinkNameList = None):
            '''ARGetMultipleActiveLinks retrieves multiple active link definitions.

This function performs the same
action as ARGetActiveLink but is easier to use and more efficient than
retrieving multiple entries one by one.
Please note: While the ARSystem returns the information in lists for each item, 
pyars will convert this into an ARActiveLinkList of its own.
Input: changedSince 
         nameList (ARNameList)
         orderList (ARUnsignedIntList)
         schemaList (ARWorkflowConnectList)
         assignedGroupListList (ARInternalIdListList)
         groupListList (ARInternalIdListList)
         executeMaskList (ARUnsignedIntList)
         controlFieldList (ARInternalIdList)
         focusFieldList (ARInternalIdList)
         enableList (ARUnsignedIntList)
         queryList (ARQualifierList)
         actionListList (ARActiveLinkActionListList)
         elseListList (ARActiveLinkActionListList)
         helpTextList (ARTextStringList)
         timestampList (ARTimestampList)
         ownersList (ARAccessNameList)
         lastChangedList (ARAccessNameList)
         changeDiaryList (ARTextStringList)
         objPropListList (ARPropListList)
         errorActlinkOptionsList (ARUnsignedIntList)
         errorActlinkNameList (ARNameList)
  :returns: ARActiveLinkList (or None in case of failure)'''
            self.logger.debug('enter ARGetMultipleActiveLinks...')
            existList = cars.ARBooleanList()
            actLinkNameList = cars.ARNameList()
            self.errnr = self.arapi.ARGetMultipleActiveLinks(byref(self.context),
                                                        changedSince,
                                                        my_byref(nameList),
                                                        byref(existList),
                                                        byref(actLinkNameList),
                                                        my_byref(orderList),
                                                        my_byref(schemaList),
                                                        my_byref(assignedGroupListList),
                                                        my_byref(groupListList),
                                                        my_byref(executeMaskList),
                                                        my_byref(controlFieldList),
                                                        my_byref(focusFieldList),
                                                        my_byref(enableList),
                                                        my_byref(queryList),
                                                        my_byref(actionListList),
                                                        my_byref(elseListList),
                                                        my_byref(helpTextList),
                                                        my_byref(timestampList),
                                                        my_byref(ownersList),
                                                        my_byref(lastChangedList),
                                                        my_byref(changeDiaryList),
                                                        my_byref(objPropListList),
                                                        my_byref(errorActlinkOptionsList),
                                                        my_byref(errorActlinkNameList),
                                                        byref(self.arsl))
            if self.errnr < 2:
                tempArray = (ARActiveLinkStruct * existList.numItems)()
    #            self.logger.debug(' num of entries: existList: %d, nameList: %d, order: %d' % (
    #                              existList.numItems, actLinkNameList.numItems, orderList.numItems))
                for i in range(existList.numItems):
                    if existList.booleanList[i]:
                        tempArray[i].name=actLinkNameList.nameList[i].value
                        if orderList: tempArray[i].order = orderList.intList[i]
                        if schemaList: tempArray[i].schemaList = schemaList.workflowConnectList[i]
                        if assignedGroupListList: tempArray[i].assignedGroupList = assignedGroupListList.internalIdListList[i]
                        if groupListList: tempArray[i].groupList = groupListList.internalIdListList[i]
                        if executeMaskList: tempArray[i].executeMask = executeMaskList.intList[i]
                        if controlFieldList: tempArray[i].controlField = controlFieldList.internalIdList[i]
                        if focusFieldList: tempArray[i].focusField = focusFieldList.internalIdList[i]
                        if enableList: tempArray[i].enable = enableList.intList[i]
                        if queryList: tempArray[i].query = queryList.qualifierList[i]
                        if actionListList: tempArray[i].actionList = actionListList.actionListList[i]
                        if elseListList: tempArray[i].elseList = elseListList.actionListList[i]
                        if helpTextList: 
                            tempArray[i].helpText = helpTextList.stringList[i]
                            if not tempArray[i].helpText == helpTextList.stringList[i]:
                                self.logger.error('''   1) %s is buggy: %s 
                                original helptext: %s''' % (tempArray[i].name,
                                          tempArray[i].helpText, helpTextList.stringList[i]))
                        if timestampList: tempArray[i].timestamp = timestampList.timestampList[i]
                        if ownersList: tempArray[i].owner = ownersList.nameList[i].value
                        if lastChangedList: tempArray[i].lastChanged = lastChangedList.nameList[i].value
                        if changeDiaryList: tempArray[i].changeDiary = changeDiaryList.stringList[i]
                        if objPropListList: tempArray[i].objPropList = objPropListList.propsList[i]
                        if errorActlinkOptionsList: tempArray[i].errorActlinkOptions = errorActlinkOptionsList.intList[i]
                        if errorActlinkNameList: tempArray[i].errorActlinkName = errorActlinkNameList.nameList[i].value
                    else:
                        self.logger.error('ARGetMultipleActiveLinks: "%s" does not exist! %s' % (nameList.nameList[i].value,
                                                                                                 self.statusText()))
    
                if not helpTextList is None:
                    for j in range(existList.numItems):
                        if tempArray[j].helpText != helpTextList.stringList[j]:
                            self.logger.error('''   2) %d(%s) is buggy: %s
                             original helptext: %s''' % (j, tempArray[j].name,
                                              tempArray[j].helpText, helpTextList.stringList[j]))
                return ARActiveLinkList(existList.numItems, tempArray)
            else:
                self.logger.error( "ARGetMultipleActiveLinks: failed")
                return None

        def ARGetMultipleContainers(self, 
                                    changedSince = 0, 
                                    nameList = None,
                                    containerTypes = None,
                                    attributes = cars.AR_HIDDEN_INCREMENT,
                                    ownerObjList = None,
                                    refTypes = None,
                                    # here start the result parameters
                                    containerNameList = None,
                                    assignedGroupListList=None,
                                    groupListList = None,
                                    admingrpListList = None,
                                    ownerObjListList = None,
                                    labelList = None,
                                    descriptionList = None,
                                    typeList = None,
                                    referenceList = None,
                                    helpTextList = None,
                                    ownerList = None,
                                    timestampList = None,
                                    lastChangedList = None,
                                    changeDiaryList = None,
                                    objPropListList = None):
            '''ARGetMultipleContainers retrieves multiple container objects.

While the server returns the information in lists for each item, pyars
converts this to a struct of its own.
Input: (optional) changedSince = 0, 
       (optional) nameList = None,
       (optional) containerTypes = None,
       (optional) attributes = cars.AR_HIDDEN_INCREMENT,
       (optional) ownerObjList = None,
       (optional) refTypes = None,
       With the following parameters you define which information is returned
       (optional) containerNameList = None,
       (optional) assignedGroupListList = None
       (optional) groupListList = None,
       (optional) admingrpListList = None,
       (optional) ownerObjListList = None,
       (optional) labelList = None,
       (optional) descriptionList = None,
       (optional) typeList = None,
       (optional) referenceList = None,
       (optional) helpTextList = None,
       (optional) ownerList = None,
       (optional) timestampList = None,
       (optional) lastChangedList = None,
       (optional) changeDiaryList = None,
       (optional) objPropListList = None
  :returns: ARContainerList or None in case of failure'''
            self.logger.debug('enter ARGetMultipleContainers...')
            existList = cars.ARBooleanList()
            if containerNameList is None:
                containerNameList = cars.ARNameList()
            self.errnr = self.arapi.ARGetMultipleContainers(byref(self.context),
                                                            changedSince, 
                                                            my_byref(nameList),
                                                            my_byref(containerTypes),
                                                            attributes,
                                                            my_byref(ownerObjList),
                                                            my_byref(refTypes),
                                                            # result parameters
                                                            byref(existList),
                                                            my_byref(containerNameList),
                                                            my_byref(assignedGroupListList),
                                                            my_byref(groupListList),
                                                            my_byref(admingrpListList),
                                                            my_byref(ownerObjListList),
                                                            my_byref(labelList),
                                                            my_byref(descriptionList),
                                                            my_byref(typeList),
                                                            my_byref(referenceList),
                                                            my_byref(helpTextList),
                                                            my_byref(ownerList),
                                                            my_byref(timestampList),
                                                            my_byref(lastChangedList),
                                                            my_byref(changeDiaryList),
                                                            my_byref(objPropListList),
                                                            byref(self.arsl))
            
            if self.errnr > 1:
                self.logger.error('ARGetMultipleContainers: failed')
                return None
            else:
                tempArray = (ARContainerStruct * existList.numItems)()
                for i in range(existList.numItems):
                    if existList.booleanList[i]:
                        tempArray[i].name = containerNameList.nameList[i].value
                        if assignedGroupListList: tempArray[i].assignedGroupList = assignedGroupListList.assignedGroupList[i]
                        if groupListList: tempArray[i].groupList = groupListList.permissionList[i]
                        if admingrpListList: tempArray[i].admingrpList = admingrpListList.internalIdListList[i]
                        if ownerObjListList: tempArray[i].ownerObjList = ownerObjListList.ownerObjListList[i]
                        if descriptionList: tempArray[i].label = labelList.stringList[i]
                        if descriptionList: tempArray[i].description = descriptionList.stringList[i]
                        if typeList: tempArray[i].type = typeList.intList[i]
                        if referenceList: tempArray[i].references = referenceList.referenceListList[i]
                        if helpTextList: tempArray[i].helpText = helpTextList.stringList[i]
                        if ownerList: tempArray[i].owner = ownerList.nameList[i].value
                        if timestampList: tempArray[i].timestamp = timestampList.timestampList[i]
                        if lastChangedList: tempArray[i].lastChanged = lastChangedList.nameList[i].value
                        if changeDiaryList: tempArray[i].changeDiary = changeDiaryList.stringList[i]
                        if objPropListList: tempArray[i].objPropList = objPropListList.propsList[i]
                    else:
                        self.logger.error('ARGetMultipleContainers: "%s" does not exist!' % nameList.nameList[i].value)
                return ARContainerList(existList.numItems, tempArray)

        def ARGetMultipleFields (self, schemaString, 
                                 idList=None,
                                 fieldId2=None,
                                 fieldName=None,
                                 fieldMap=None,
                                 dataType=None,
                                 option=None,
                                 createMode=None,
                                 fieldOption=None,
                                 defaultVal=None,
                                 assignedGroupListList=None,
                                 permissions=None,
                                 limit=None,
                                 dInstanceList=None,
                                 helpText=None,
                                 timestamp=None,
                                 owner=None,
                                 lastChanged=None,
                                 changeDiary=None,
                                 objPropListList=None):
            '''ARGetMultipleFields returns a list of the fields and their attributes.
       
ARGetMultipleFields returns list of field definitions for a specified form.
In contrast to the C APi this function constructs an ARFieldInfoList
for the form and returns all information this way.
Input: schemaString
      (ARInternalIdList) idList (optional; default: None) we currently
              expect a real ARInternalIdList, because then it's very
              easy to simply hand over the result of a GetListField
              call
      (ARInternalIdList) fieldId2: although it is declared optional (to be consistent
           with the AR API), this needs to be set (if not, this function will create
           an ARInternalIdList) (see the output for an explanation)
      (ARNameList) fieldName 
      (ARFieldMappingList) fieldMap 
      (ARUnsignedIntList) dataType 
      (ARUnsignedIntList) option 
      (ARUnsignedIntList) createMode 
      (ARUnsignedIntList) fieldOption 
      (ARValueList) defaultVal
      (ARPermissionListList) assignedGroupListList
      (ARPermissionListList) permissions 
      (ARFieldLimitList) limit 
      (ARDisplayInstanceListList) dInstanceList 
      (ARTextStringList) helpText 
      (ARTimestampList) timestamp 
      (ARAccessNameList) owner 
      (ARAccessNameList) lastChanged 
      (ARTextStringList) changeDiary either hand over None (as is
              default) or supply according ARxxxxList for the 
              API call. 
      (ARPropListList) objPropListList
  :returns: ARFieldInfoList; contains entries for all ids that you handed over;
       if a field could not be retrieved, the according fieldid will be None; that's
       the only way to decide if the list could be retrieved or not!
       (all input lists should contain the return values from the server, but we
        will also create an ARFieldInfoList) or None in case of failure'''
            self.logger.debug('enter ARGetMultipleFields...')
            # we assume that we have been handed over a string
    #       if self.schemaExists(schemaString) == 0:
    #           self.logger.error('Schema %s does not exist on server.' % (schemaString))
    #           return None
            existList = cars.ARBooleanList()
            # fieldId2 needs to be created -- this will be the identifier for the caller, 
            # if a field could be retrieved or not!
            if fieldId2 is None:
                fieldId2 = cars.ARInternalIdList()
            assert isinstance(schemaString, str)
            assert isinstance(idList, cars.ARInternalIdList) or idList is None
            assert isinstance(fieldId2, cars.ARInternalIdList)
            assert isinstance(fieldName, cars.ARNameList) or fieldName is None
            assert isinstance(fieldMap, cars.ARFieldMappingList) or fieldMap is None
            assert isinstance(dataType, cars.ARUnsignedIntList) or dataType is None
            assert isinstance(option, cars.ARUnsignedIntList) or option is None
            assert isinstance(createMode, cars.ARUnsignedIntList) or createMode is None
            assert isinstance(fieldOption, cars.ARUnsignedIntList) or fieldOption is None
            assert isinstance(defaultVal, cars.ARValueList) or defaultVal is None
            assert isinstance(assignedGroupListList, cars.ARPermissionListList) or assignedGroupListList is None
            assert isinstance(permissions, cars.ARPermissionListList) or permissions is None
            assert isinstance(limit, cars.ARFieldLimitList) or limit is None
            assert isinstance(dInstanceList, cars.ARDisplayInstanceListList) or dInstanceList is None, "DInstanceList is %s" % dInstanceList
            assert isinstance(helpText, cars.ARTextStringList) or helpText is None, "helpText is %s" % helpText
            assert isinstance(timestamp, cars.ARTimestampList) or timestamp is None
            assert isinstance(owner, cars.ARAccessNameList) or owner is None
            assert isinstance(lastChanged, cars.ARAccessNameList) or lastChanged is None
            assert isinstance(changeDiary, cars.ARTextStringList) or changeDiary is None
            assert isinstance(objPropListList, cars.ARPropListList) or objPropListList is None
           
            self.errnr = self.arapi.ARGetMultipleFields(byref(self.context),
                                                  schemaString,
                                                  my_byref(idList),
                                                  byref(existList),
                                                  byref(fieldId2),
                                                  my_byref(fieldName),
                                                  my_byref(fieldMap),
                                                  my_byref(dataType),
                                                  my_byref(option),
                                                  my_byref(createMode),
                                                  my_byref(fieldOption),
                                                  my_byref(defaultVal),
                                                  my_byref(assignedGroupListList),
                                                  my_byref(permissions),
                                                  my_byref(limit),
                                                  my_byref(dInstanceList),
                                                  my_byref(helpText),
                                                  my_byref(timestamp),
                                                  my_byref(owner),
                                                  my_byref(lastChanged),
                                                  my_byref(changeDiary),
                                                  my_byref(objPropListList),
                                                  byref(self.arsl))
    #       self.logger.debug('GetMultipleFields: after API call')
            if idList and idList.numItems != existList.numItems:
                self.logger.error('ARGetMultipleFields returned another number of fields for form %s than expected!' % (schemaString))
            if self.errnr < 2:
                # from what the API returns, create an ARFieldInfoList
                tempList = (cars.ARFieldInfoStruct * existList.numItems)()
                for i in range(existList.numItems):
                    if existList.booleanList[i]:
                        if fieldId2:
                            tempList[i].fieldId = fieldId2.internalIdList[i]
                        if fieldName:
                            tempList[i].fieldName = fieldName.nameList[i].value
                        if timestamp:
                            tempList[i].timestamp = timestamp.timestampList[i]
                        if fieldMap:
                            tempList[i].fieldMap = fieldMap.mappingList[i]
                        if dataType:
                            tempList[i].dataType = dataType.intList[i]
                        if option:
                            tempList[i].option = option.intList[i]
                        if createMode:
                            tempList[i].createMode = createMode.intList[i]
                        if fieldOption:
                            tempList[i].fieldOption = fieldOption.intList[i]
                        if defaultVal:
                            tempList[i].defaultVal = defaultVal.valueList[i]
                        # if the user does not have admin rights, permissions will be a list of 0 items!
# TODO: how can we handle this??? see also ARGetField
#                        if assignedGroupListList and assignedGroupListList.numItems > i:
#                            tempList[i].assignedGroupList = assignedGroupListList.permissionList[i]
                        if permissions and permissions.numItems > i:
                            tempList[i].permList = permissions.permissionList[i]
                        if limit:
                            tempList[i].limit = limit.fieldLimitList[i]
                        if dInstanceList:
                            tempList[i].dInstanceList = dInstanceList.dInstanceList[i]
                        if owner:
                            tempList[i].owner = owner.nameList[i].value
                        if lastChanged:
                            tempList[i].lastChanged = lastChanged.nameList[i].value
                        if helpText:
                            tempList[i].helpText = helpText.stringList[i]
                        if changeDiary:
                            tempList[i].changeDiary = changeDiary.stringList[i]
                        if objPropListList:
                            tempList[i].objPropList = objPropListList.propList[i]
                    else:
                        self.logger.error( "ARGetMultipleFields: failed to retrieve field# %d from %s" % (
                                    i, schemaString))
                        tempList[i].fieldId = None
                        tempList[i].fieldName = None
#                tempRes = cars.ARFieldInfoList(existList.numItems, tempList)
                return cars.ARFieldInfoList(existList.numItems, tempList)
            else:
                self.logger.error( "ARGetMultipleFields: failed for %s" % (
                           schemaString))
                return None

        def ARGetMultipleSchemas(self, changedSince=0, 
                                schemaTypeList = None,
                                nameList=None, 
                                fieldIdList=None,
                                schemaList = None,
                                schemaInheritanceListList = None, # reserved for future use
                                assignedGroupListList = None,
                                groupListList = None,
                                admingrpListList = None,
                                getListFieldsList = None,
                                sortListList = None,
                                indexListList = None,
                                archiveInfoList = None,
                                auditInfoList = None,
                                defaultVuiList = None,
                                helpTextList = None,
                                timestampList = None,
                                ownerList = None,
                                lastChangedList = None,
                                changeDiaryList = None,
                                objPropListList = None):
            '''ARGetMultipleSchemas retrieves information about several schemas
from the server at once.

This information does not include the form field definitions (see ARGetField). This
function performs the same action as ARGetSchema but is easier to use and
more efficient than retrieving multiple forms one by one.
Information is returned in lists for each item, with one item in the list for
each form returned. For example, if the second item in the list for existList is
TRUE, the name of the second form is returned in the second item in the list
for schemaNameList.
Input:  (ARTimestamp) changedSince=0, 
        (ARUnsignedIntList) schemaTypeList (optional, default = None),
        (ARNameList) nameList (optional, default = None), 
        (ARInternalIdList) fieldIdList (optional, default =None),
        (ARCompoundSchemaList) schemaList (optional, default = None),
        (ARSchemaInheritanceListList) schemaInheritanceListList (optional, default  = None), # reserved for future use
        (ARPermissionListList) assignedGroupListList (optional, default  = None),
        (ARPermissionListList) groupListList (optional, default  = None),
        (ARInternalIdListList) admingrpListList (optional, default  = None),
        (AREntryListFieldListList) getListFieldsList (optional, default  = None),
        (ARSortListList) sortListList (optional, default  = None),
        (ARSortListList) indexListList (optional, default  = None),
        (ARSortListList) archiveInfoList (optional, default  = None),
        (ARAuditInfoList) auditInfoList (optional, default  = None),
        (ARNameList) defaultVuiList (optional, default  = None),
        (ARTextStringList) helpTextList (optional, default  = None),
        (ARTimestampList) timestampList (optional, default  = None),
        (ARAccessNameList) ownerList (optional, default  = None),
        (ARAccessNameList) lastChangedList (optional, default  = None),
        (ARTextStringList) changeDiaryList (optional, default  = None),
        (ARPropListList) objPropListList (optional, default = None)
  :returns: ARSchemaList or None in case of failure'''
            self.logger.debug('enter ARGetMultipleSchemas...')
            existList = cars.ARBooleanList()
            schemaNameList = cars.ARNameList()
            schemaInheritanceListList = None
            self.errnr = self.arapi.ARGetMultipleSchemas(byref(self.context),
                                                         changedSince, 
                                           my_byref(schemaTypeList),
                                           my_byref(nameList), 
                                           my_byref(fieldIdList),
                                           my_byref(existList),
                                           my_byref(schemaNameList),
                                           my_byref(schemaList),
                                           my_byref(schemaInheritanceListList),
                                           my_byref(assignedGroupListList),
                                           my_byref(groupListList),
                                           my_byref(admingrpListList),
                                           my_byref(getListFieldsList),
                                           my_byref(sortListList),
                                           my_byref(indexListList),
                                           my_byref(archiveInfoList),
                                           my_byref(auditInfoList),
                                           my_byref(defaultVuiList),
                                           my_byref(helpTextList),
                                           my_byref(timestampList),
                                           my_byref(ownerList),
                                           my_byref(lastChangedList),
                                           my_byref(changeDiaryList),
                                           my_byref(objPropListList),
                                           byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARGetMultipleSchemas: failed')
                return None
            else:
                # self.logger.debug('ARGetMultipleSchemas: after API call')
                tempArray = (ARSchema * existList.numItems)()
                for i in range(existList.numItems):
                    tempArray[i].name = schemaNameList.nameList[i].value
                    if existList.booleanList[i]:
                        if schemaList: tempArray[i].schema = schemaList.compoundSchema[i]
                        if assignedGroupListList: tempArray[i].assignedGroupList = assignedGroupListList.permissionList[i]
                        if groupListList: tempArray[i].groupList = groupListList.permissionList[i]
                        if admingrpListList: tempArray[i].admingrpList = admingrpListList.internalIdListList[i]
                        if getListFieldsList: tempArray[i].getListFields = getListFieldsList.listFieldList[i]
                        if indexListList: tempArray[i].sortList = sortListList.sortListList[i]
                        if indexListList: tempArray[i].indexList = indexListList.indexListList[i]
                        if archiveInfoList: tempArray[i].archiveInfo = archiveInfoList.archiveInfoList[i]
                        if auditInfoList: tempArray[i].auditInfo = auditInfoList.auditInfoList[i]
                        if defaultVuiList: tempArray[i].defaultVui = defaultVuiList.nameList[i].value
                        if helpTextList: tempArray[i].helpText = helpTextList.stringList[i]
                        if timestampList: tempArray[i].timestamp = timestampList.timestampList[i]
                        if ownerList: tempArray[i].owner = ownerList.nameList[i].value
                        if lastChangedList: tempArray[i].lastChanged = lastChangedList.nameList[i].value
                        if changeDiaryList: tempArray[i].changeDiary = changeDiaryList.stringList[i]
                        if objPropListList: tempArray[i].objPropList = objPropListList.propsList[i]
                    else:
                        self.logger.error('ARGetMultipleSchemas: "%s" does not exist!' % nameList.nameList[i].value)
                return ARSchemaList(existList.numItems, tempArray)

        def ARGetMultipleVUIs(self, schema, 
                              wantList = None, 
                              changedSince = 0,
                              dPropListList = None, 
                              helpTextList = None,
                              timeStampList = None,
                              ownerList = None,
                              lastChangedList = None,
                              changeDiaryList = None,
                              objPropListList = None):
            '''ARGetMultipleVUIs retrieves information about a group of form views
(VUIs).

PLEASE NOTE: This function seems to have a bug in the Remedy DLLs. The symptoms
are a mangeled localeList!!! Use with caution!

This function
performs the same action as ARGetVUI but is easier to use and more efficient
than retrieving multiple entries one by one.
While the server returns information in lists for each item, pyars converts
this into a struct of its own.
Input:  schema
       optional: wantList (ARInternalIdList, default = None),
       optional: changedSince (default = 0)
       optional: dPropListList
       optional: helpTextList
       optional: timeStampList
       optional: ownerList
       optional: lastChangedList
       optional: changeDiaryList
       optional: objPropListList (ARPropListList)
  :returns: ARVuiInfoList or None in case of failure'''
            self.logger.debug('enter ARGetMultipleVUIs...')
            existList = cars.ARBooleanList()
            gotList = cars.ARInternalIdList()
            nameList = cars.ARNameList()
            localeList = cars.ARLocaleList()
            vuiTypeList = cars.ARUnsignedIntList()
            self.errnr = self.arapi.ARGetMultipleVUIs(byref(self.context),
                                                     schema,
                                                     my_byref(wantList),
                                                     changedSince,
                                                     byref(existList),
                                                     byref(gotList),
                                                     byref(nameList),
                                                     byref(localeList),
                                                     byref(vuiTypeList),
                                                     my_byref(dPropListList),
                                                     my_byref(helpTextList),
                                                     my_byref(timeStampList),
                                                     my_byref(ownerList),
                                                     my_byref(lastChangedList),
                                                     my_byref(changeDiaryList),
                                                     my_byref(objPropListList),
                                                     byref(self.arsl))
            if self.errnr < 2:
                tempArray = (cars.ARVuiInfoStruct * existList.numItems)()
                for i in range(existList.numItems):
                    if existList.booleanList[i]:
                        tempArray[i].vuiId = gotList.internalIdList[i]
                        tempArray[i].vuiName = nameList.nameList[i].value
                        if timeStampList: tempArray[i].timestamp = timeStampList.timestampList[i]
                        if dPropListList: tempArray[i].props = dPropListList.propsList[i]
                        if ownerList: tempArray[i].owner = ownerList.nameList[i].value
#                       self.logger.debug('   ARGetMultipleVUIs: id: %s, struct %s, orig locale: %s' % (
#                           tempArray[i].vuiId, 
#                           localeList.localeList[i],
#                           localeList.localeList[i].value))
#                       tempArray[i].locale = localeList.localeList[i].value
                        tempArray[i].locale = '' # bug in AR DLL!!!
#                       self.logger.debug('   ARGetMultipleVUIs: copy == orig? %s' % (
#                                   tempArray[i].locale == localeList.localeList[i].value))
                        tempArray[i].vuiType = vuiTypeList.intList[i]
                        if lastChangedList: tempArray[i].lastChanged = lastChangedList.nameList[i].value
                        if helpTextList: tempArray[i].helpText = helpTextList.stringList[i]
                        if changeDiaryList: tempArray[i].changeDiary = changeDiaryList.stringList[i]
                    else:
                        self.logger.error('ARGetMultipleVUIs: "%d" does not exist!' % wantList.internalIdList[i])
                return cars.ARVuiInfoList(existList.numItems, tempArray)
            else:
                self.logger.error( "ARGetMultipleVUIs: failed for schema %s" %schema)
                return None 

        def ARGetSchema (self, name):
            '''ARGetSchema returns all information about a schema.
        
This information does not include the form's field
definitions (see ARGetField).
Input: (ARNameType) name
  :returns: ARSchema or None in case of failure'''
            self.logger.debug('enter ARGetSchema...')
            schema = cars.ARCompoundSchema()
            schemaInheritanceList = cars.ARSchemaInheritanceList()
            assignedGroupList= cars.ARPermissionList()
            groupList = cars.ARPermissionList()
            admingrpList = cars.ARInternalIdList()
            getListFields = cars.AREntryListFieldList()
            sortList = cars.ARSortList()
            indexList = cars.ARIndexList()
            archiveInfo = cars.ARArchiveInfoStruct()
            auditInfo = cars.ARAuditInfoStruct()
            defaultVui = cars.ARNameType()
            helpText = c_char_p()
            timestamp = cars.ARTimestamp()
            owner = cars.ARAccessNameType()
            lastChanged = cars.ARAccessNameType()
            changeDiary = c_char_p()
            objPropList = cars.ARPropList()
            self.errnr = self.arapi.ARGetSchema (byref(self.context),
                                            name,
                                            byref(schema),
                                            byref(schemaInheritanceList),
                                            byref(assignedGroupList),
                                            byref(groupList),
                                            byref(admingrpList),
                                            byref(getListFields),
                                            byref(sortList),
                                            byref(indexList),
                                            byref(archiveInfo),
                                            byref(auditInfo),
                                            defaultVui,
                                            byref(helpText),
                                            byref(timestamp),
                                            owner,
                                            lastChanged,
                                            byref(changeDiary),
                                            byref(objPropList),
                                            byref(self.arsl))
            if self.errnr < 2:
                return ARSchema(name, 
                                schema,
                                schemaInheritanceList,
                                assignedGroupList,
                                groupList,
                                admingrpList,
                                getListFields,
                                sortList,
                                indexList,
                                archiveInfo,
                                auditInfo,
                                defaultVui.value,
                                helpText,
                                timestamp,
                                owner.value,
                                lastChanged.value,
                                changeDiary,
                                objPropList)
            else:
                self.logger.error( "ARGetSchema: failed for schema %s" % name)
                return None

        def ARGetVUI(self, schema, vuiId):
            '''ARGetVUI retrieves information about the form view (VUI) with the indicated ID
        
Input:  schema: name of schema
        vuiId: internalId
  :returns: ARVuiInfoStruct (or None in case of failure)'''
            self.logger.debug('enter ARGetVUI...')
            vuiName = cars.ARNameType()
            locale = cars.ARLocaleType()
            vuiType = c_uint()
            dPropList = cars.ARPropList()
            helpText = c_char_p()
            timestamp = cars.ARTimestamp()
            owner = cars.ARAccessNameType()
            lastChanged = cars.ARAccessNameType()
            changeDiary = c_char_p()
            smObjProp = cars.ARPropList()
            self.errnr = self.arapi.ARGetVUI (byref(self.context),
                                              schema,
                                              vuiId,
                                              vuiName,
                                              locale,
                                              byref(vuiType),
                                              byref(dPropList),
                                              byref(helpText),
                                              byref(timestamp),
                                              owner,
                                              lastChanged,
                                              byref(changeDiary),
                                              byref(smObjProp),
                                              byref(self.arsl))
            if self.errnr < 2:
                return cars.ARVuiInfoStruct(vuiId,
                                            vuiName.value,
                                            timestamp,
                                            dPropList,
                                            owner.value,
                                            locale.value,
                                            vuiType,
                                            lastChanged.value,
                                            helpText.value,
                                            changeDiary.value,
                                            smObjProp)
            else:
                self.logger.error( "ARGetVUI: failed")
                return None

        def ARImport(self,  structItems, 
                     importBuf, 
                     importOption=cars.AR_IMPORT_OPT_CREATE,
                     objectModificationLogLabel = None):
            '''ARImport imports the indicated structure definitions to the specified server.

Use this function to copy structure definitions from one AR System server to another.
Input:  structItems
        importBuf
        (optional) importOption (Default=cars.AR_IMPORT_OPT_CREATE)
        (optional) objectModificationLogLabel (c_char_p, default = None)
  :returns: errnr'''
            self.logger.debug('enter ARImport...')
            self.errnr = self.arapi.ARImport(byref(self.context),
                                             byref(structItems),
                                             importBuf,
                                             importOption,
                                             objectModificationLogLabel,
                                             byref(self.arsl))
            return self.errnr

        def ARSetActiveLink(self, name, 
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
            '''ARSetActiveLink updates the active link.

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
  :returns: errnr'''
            self.logger.debug('enter ARSetActiveLink...')
            if order is not None and not isinstance(order, c_uint):
                order = c_uint(order)
            if executeMask is not None and not isinstance(executeMask, c_uint):
                executeMask = c_uint(executeMask)
            if controlField is not None and not isinstance(controlField, c_uint):
                controlField = cars.ARInternalId(controlField)
            if focusField is not None and not isinstance(focusField, c_uint):
                focusField = cars.ARInternalId(focusField)
            if enable is not None and not isinstance(enable, c_uint):
                enable = c_uint(enable)
            self.errnr = self.arapi.ARSetActiveLink(byref(self.context),
                                                    name, 
                                                    newName, 
                                                    my_byref(order), 
                                                    my_byref(workflowConnect),
                                                    my_byref(groupList),
                                                    my_byref(executeMask),
                                                    my_byref(controlField),
                                                    my_byref(focusField),
                                                    my_byref(enable),
                                                    my_byref(query),
                                                    my_byref(actionList),
                                                    my_byref(elseList),
                                                    helpText,
                                                    owner,
                                                    changeDiary,
                                                    my_byref(objPropList),
                                                    my_byref(errorActlinkOptions),
                                                    errorActlinkName,
                                                    objectModificationLogLabel,
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARSetActiveLink: failed for %s' % name)
            return self.errnr

        def ARSetCharMenu(self, 
                          name, 
                          newName = None, 
                          refreshCode = None, 
                          menuDefn = None, 
                          helpText = None, 
                          owner = None,
                          changeDiary = None, 
                          objPropList = None,
                          objectModificationLogLabel = None):
            '''ARSetCharMenu updates the character menu.

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
  :returns: errnr'''
            self.logger.debug('enter ARSetCharMenu...')
            if refreshCode is not None and not isinstance(refreshCode, c_uint):
                refreshCode = c_uint(refreshCode)
            self.errnr = self.arapi.ARSetCharMenu(byref(self.context),
                                                  name,
                                                  newName, 
                                                  my_byref(refreshCode), 
                                                  my_byref(menuDefn), 
                                                  helpText, 
                                                  owner,
                                                  changeDiary, 
                                                  my_byref(objPropList),
                                                  objectModificationLogLabel,
                                                  byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARSetCharMenu failed for old: %s/new: %s' % (name,
                                  newName))
            return self.errnr 

        def ARSetContainer(self, name,
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
            '''ARSetContainer updates the definition for the container.
        
Input:  name
       (optional) newName (default = None)
       (optional) groupList (default = None)
       (optional) admingrpList (default = None)
       (optional) ownerObjList (default = None)
       (optional) label (default = None)
       (optional) description (default = None)
       (optional) type (default = None)
       (optional) references (default = None)
       (optional) removeFlag (default = None)
       (optional) helpText (default = None)
       (optional) owner (default = None)
       (optional) changeDiary (default = None)
       (optional) objPropList (default = None)
       (optional) objectModificationLogLabel (default = None)
  :returns: errnr'''
            self.logger.debug('enter ARSetContainer...')
            if type_ is not None and not isinstance(type_, c_uint):
                type_ = c_uint(type_)
            self.errnr = self.arapi.ARSetContainer(byref(self.context),
                                                   name,
                                                   newName,
                                                   my_byref(groupList),
                                                   my_byref(admingrpList),
                                                   my_byref(ownerObjList),
                                                   my_byref(label),
                                                   my_byref(description),
                                                   my_byref(type_),
                                                   my_byref(references),
                                                   removeFlag,
                                                   helpText,
                                                   owner,
                                                   changeDiary,
                                                   my_byref(objPropList),
                                                   objectModificationLogLabel,
                                                   byref(self.arsl))
            if self.errnr > 1:
                self.logger.error("ARSetContainer: failed for %s" % name)
            return self.errnr

        def ARSetGetEntry(self, schema, 
                       entryIdList, 
                       fieldList, 
                       getTime = 0, 
                       option = None,
                       idList = None):
            '''ARSetGetEntry bundles the following API calls into one call:
ARSetEntry and ARGetEntry

Please note: self.arsl will be set to the geStatus list! 
Input:  schema
        entryId: AREntryIdList
        fieldList: ARFieldValueList
        (optional) getTime (the server compares this value with the 
                    value in the Modified Date core field to
                    determine whether the entry has been changed 
                    since the last retrieval.)
        (optional) option (for join forms only; can be AR_JOIN_SETOPTION_NONE
                    or AR_JOIN_SETOPTION_REF)
        (optional) idList (ARInternalIdList)
  :returns: (getFieldList, seStatus, geStatus) or None in case of Failure'''
            self.logger.debug('enter ARSetGetEntry...')
            getFieldList = cars.ARFieldValueList()
            seStatus = cars.ARStatusList()
            geStatus = cars.ARStatusList()
            self.errnr = self.arapi.ARSetGetEntry (byref (self.context),
                                                schema,
                                                byref(entryIdList),
                                                byref(fieldList),
                                                getTime,
                                                option,
                                                my_byref(idList),
                                                byref(getFieldList),
                                                byref(seStatus),
                                                byref(geStatus))
            if self.errnr > 1:
                self.logger.error("ARSetGetEntry: failed")
                return None
            self.arsl = geStatus
            return (getFieldList, seStatus, geStatus)

        def ARSetEscalation(self, name, 
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
            '''ARSetEscalation updates the escalation.

The changes are added to the server immediately and returned to users who
request information about escalations.
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
  :returns: errnr'''
            self.logger.debug('enter ARSetEscalation...')
            if enable is not None and not isinstance(enable, c_uint):
                enable = c_uint(enable)
            self.errnr = self.arapi.ARSetEscalation(byref(self.context),
                                                    name, 
                                                    newName,
                                                    my_byref(escalationTm), 
                                                    my_byref(schemaList), 
                                                    my_byref(enable), 
                                                    my_byref(query), 
                                                    my_byref(actionList),
                                                    my_byref(elseList), 
                                                    helpText, 
                                                    owner, 
                                                    changeDiary, 
                                                    my_byref(objPropList),
                                                    objectModificationLogLabel,
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARSetEscalation failed for %s' % name)
            return self.errnr

        def ARSetField(self, schema, 
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
                       setFieldOptions = 0,
                       objPropList = None):
            '''ARSetField updates the definition for the form field.
            
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
  :returns: errnr'''
            self.logger.debug('enter ARSetField...')
            if option is not None and not isinstance(option, c_uint):
                option = c_uint(option)
            if createMode is not None and not isinstance(createMode, c_uint):
                createMode = c_uint(createMode)
            if fieldOption is not None and not isinstance(fieldOption, c_uint):
                fieldOption = c_uint(fieldOption)
            self.errnr = self.arapi.ARSetField(byref(self.context),
                                               schema, 
                                               fieldId,
                                               fieldName, 
                                               my_byref(fieldMap), 
                                               my_byref(option), 
                                               my_byref(createMode),
                                               my_byref(fieldOption),
                                               my_byref(defaultVal),
                                               my_byref(permissions), 
                                               my_byref(limit), 
                                               my_byref(dInstanceList), 
                                               helpText, 
                                               owner, 
                                               changeDiary,
                                               setFieldOptions,
                                               my_byref(objPropList),
                                               byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARSetField: failed for %s:%d' % (schema,fieldId))
            return self.errnr

        def ARSetFilter(self, name, 
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
            '''ARSetFilter updates the filter.

The changes are added to the server immediately and returned to users who
request information about filters.
Input:  name, 
        (ARNameType) newName,
        (c_uint) order (optional, default = None),
        (ARWorkflowConnectStruct) workflowConnect (optional, default = None),
        (c_uint) opSet (optional, default = None),
        (c_uint) enable (optional, default = None),
        (ARQualifierStruct) query (optional, default = None),
        (ARFilterActionList) actionList (optional, default = None),
        (ARFilterActionList) elseList (optional, default = None),
        (c_char) helpText (optional, default = None),
        (ARAccessNameType) owner (optional, default = None),
        (c_char) changeDiary (optional, default = None),
        (ARPropList) objPropList (optional, default = None),
        (c_uint) errorFilterOptions  (optional, default = None),
        (ARNameType) errorFilterName  (optional, default = None)
        (c_char) objectModificationLogLabel (optional, default = None)
  :returns: errnr'''
            self.logger.debug('enter ARSetFilter...')
            if order is not None and not isinstance(order, c_uint):
                order = c_uint(order)
            if opSet is not None and not isinstance(opSet, c_uint):
                opSet = c_uint(opSet)
            if enable is not None and not isinstance(enable, c_uint):
                enable = c_uint(enable)
            if errorFilterOptions is not None and not isinstance(errorFilterOptions, c_uint):
                errorFilterOptions = c_uint(errorFilterOptions)
            self.errnr = self.arapi.ARSetFilter(byref(self.context),
                                                name, 
                                                newName,
                                                my_byref(order),
                                                my_byref(workflowConnect),
                                                my_byref(opSet),
                                                my_byref(enable),
                                                my_byref(query),
                                                my_byref(actionList),
                                                my_byref(elseList),
                                                helpText,
                                                owner,
                                                changeDiary,
                                                my_byref(objPropList),
                                                my_byref(errorFilterOptions),
                                                errorFilterName,
                                                objectModificationLogLabel,
                                                byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARSetFilter: failed for %s' % name)
            return self.errnr

        def ARSetImage(self, name,
                        newName = None,
                        imageBuf = None,
                        imageType = None,
                        description = None,
                        helpText = None,
                        owner = None,
                        changeDiary = None,
                        objPropList = None,
                        objectModificationLogLabel = None):
            '''ARSetImage updates the image with the indicated name on the specified server. After the
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
  :returns: errnr'''
            self.logger.debug('enter ARSetImage...')
            self.errnr = self.arapi.ARSetImage(byref(self.context),
                                                    name, 
                                                    newName, 
                                                    my_byref(imageBuf), 
                                                    imageType,
                                                    description,
                                                    helpText,
                                                    owner,
                                                    changeDiary,
                                                    my_byref(objPropList),
                                                    objectModificationLogLabel,
                                                    byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARSetImage: failed for %s' % name)
            return self.errnr
        
        def ARSetMultipleFields (self, schema,
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
            '''ARSetMultipleFields updates the definition for a list of fields 
with the specified IDs on the specified form on the specified server. 

This call produces the same result as a sequence of
ARSetField calls to update the individual fields, but it can be more efficient
because it requires only one call from the client to the AR System server and
because the server can perform multiple database operations in a single
transaction and avoid repeating operations such as those performed at the end of
each individual call.
Input:  (ARNameType) schema (optional, default = None),
        (ARInternalIdList) fieldIdList (optional, default = None),
        (ARNamePtrList) fieldNameList (optional, default = None),
        (ARFieldMappingPtrList) fieldMapList (optional, default = None),
        (ARUnsignedIntList) optionList (optional, default = None),
        (ARUnsignedIntList) createModeList (optional, default = None),
        (ARUnsignedIntList) fieldOptionList (optional, default = None),
        (ARValuePtrList) defaultValList (optional, default = None),
        (ARPermissionListPtrList) permissionListList (optional, default = None),
        (ARFieldLimitPtrList) limitList (optional, default = None),
        (ARDisplayInstanceListPtrList) dInstanceListList (optional, default = None),
        (ARTextStringList) helpTextList (optional, default = None),
        (ARAccessNamePtrList) ownerList (optional, default = None),
        (ARTextStringList) changeDiaryList (optional, default = None),
        (ARUnsignedIntList) setFieldOptionList (optional, default = None),
        (ARPropListList) objPropListList (optional, default = None)
        (ARStatusListList) setFieldStatusList (optional, default = None)
  :returns: errnr'''
            self.logger.debug('enter ARSetMultipleFields...')
            self.errnr = self.arapi.ARSetMultipleFields(byref(self.context),
                                                schema,
                                                my_byref(fieldIdList),
                                                my_byref(fieldNameList),
                                                my_byref(fieldMapList),
                                                my_byref(optionList),
                                                my_byref(createModeList),
                                                my_byref(fieldOptionList),
                                                my_byref(defaultValList),
                                                my_byref(permissionListList),
                                                my_byref(limitList),
                                                my_byref(dInstanceListList),
                                                my_byref(helpTextList),
                                                my_byref(ownerList),
                                                my_byref(changeDiaryList),
                                                my_byref(setFieldOptionList),
                                                my_byref(objPropListList),
                                                my_byref(setFieldStatusList),
                                                byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARSetMultipleFields: failed')
            return self.errnr

        def ARSetSchema(self, name,
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
            '''ARSetSchema updates the definition for the form.

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
  :returns: errnr'''
            self.logger.debug('enter ARSetSchema...')
            schemaInheritanceList = None
            self.errnr = self.arapi.ARSetSchema(byref(self.context),
                                                name,
                                                newName,
                                                my_byref(schema),
                                                my_byref(schemaInheritanceList),
                                                my_byref(groupList),
                                                my_byref(admingrpList),
                                                my_byref(getListFields),
                                                my_byref(sortList),
                                                my_byref(indexList),
                                                my_byref(archiveInfo),
                                                my_byref(auditInfo),
                                                defaultVui,
                                                helpText,
                                                owner,
                                                changeDiary,
                                                my_byref(objPropList),
                                                objectModificationLogLabel,
                                                byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARSetSchema failed for schema %s' % (name))
            return self.errnr 

        def ARSetVUI(self, schema, 
                     vuiId, 
                     vuiName = None, 
                     locale = None, 
                     vuiType=None,
                     dPropList=None, 
                     helpText=None, 
                     owner=None, 
                     changeDiary=None,
                     smObjProp=None):
            '''ARSetVUI updates the form view (VUI).
        
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
  :returns: errnr'''
            self.logger.debug('enter ARSetVUI...')
            if vuiType is not None and not isinstance(vuiType, c_uint):
                vuiType = c_uint(vuiType)
            self.errnr = self.arapi.ARSetVUI(byref(self.context),
                                                schema,
                                                vuiId, 
                                                vuiName, 
                                                locale, 
                                                my_byref(vuiType),
                                                my_byref(dPropList), 
                                                helpText, 
                                                owner, 
                                                changeDiary,
                                                my_byref(smObjProp),
                                                byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARSetVUI: failed for schema: %s/vui %s' % (schema, vuiId))
            return self.errnr

        def ARCreateTask(self, name, 
                         chars = None, 
                         objProperties = None, 
                         versionControlList = None):
            '''ARCreateTask: undocumented function

Input: (ARNameType) name
       (c_char)  chars
       (ARPropList) objProperties
       (ARVercntlObjectList) versionControlList
  :returns: errnr'''
            self.logger.debug('enter ARCreateTask...')
            self.errnr = self.arapi.ARCreateTask(byref(self.context),
                                                 name,
                                                 chars,
                                                 my_byref(objProperties),
                                                 my_byref(versionControlList),
                                                 byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARCreateTask: failed')
            return self.errnr

        def ARSetTask(self, name, newName, chars = None, owner = None, objProperties = None):
            '''ARSetTask: undocumented function

Input: (ARNameType) name
       (ARNameType) newName
       (c_char)  chars
       (ARAccessNameType) owner
       (ARPropList) objProperties
  :returns: errnr'''
            self.logger.debug('enter ARSetTask...')
            self.errnr = self.arapi.ARSetTask(byref(self.context),
                                                 name,
                                                 newName,
                                                 chars,
                                                 owner,
                                                 my_byref(objProperties),
                                                 byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARSetTask: failed')
            return self.errnr

        def ARDeleteTask(self, name):
            '''ARDeleteTask: undocumented function

Input: (ARNameType) name
  :returns: errnr'''
            self.logger.debug('enter ARDeleteTask...')
            self.errnr = self.arapi.ARDeleteTask(byref(self.context),
                                                 name,
                                                 byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARDeleteTask: failed')
            return self.errnr

        def ARCommitTask(self, name):
            '''ARCommitTask: undocumented function

  :param name: (ARNameType)
  :returns: errnr'''
            self.logger.debug('enter ARCommitTask...')
            self.errnr = self.arapi.ARCommitTask(byref(self.context),
                                                 name,
                                                 byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARCommitTask: failed')
            return self.errnr

        def ARRollbackTask(self, name):
            '''ARRollbackTask: undocumented function

  :param name: (ARNameType)
  :returns: errnr'''
            self.logger.debug('enter ARRollbackTask...')
            self.errnr = self.arapi.ARRollbackTask(byref(self.context),
                                                 name,
                                                 byref(self.arsl))
            if self.errnr > 1:
                self.logger.error('ARRollbackTask: failed')
            return self.errnr

#        def ARCreateCheckpoint(ARControlStruct *, ARNameType, ARNameType, char *, ARPropList *, ARStatusList *)): pass
#        def ARDeleteCheckpoint(ARControlStruct *, ARNameType, ARNameType, ARStatusList *)): pass
#        def ARRollbackToCheckpoint, (ARControlStruct *, ARNameType, ARNameType, char *, ARStatusList *)): pass
#        def ARAddObjects, (ARControlStruct *, ARNameType,  ARVercntlObjectList *,ARStatusList *)): pass
#        def ARRemoveObjects (ARControlStruct *, ARNameType, ARVercntlObjectList *, ARStatusList *)): pass
#        def ARGetTask (ARControlStruct *, ARNameType, int, ARTask *, ARStatusList *)): pass
#        def ARGetListTask (ARControlStruct *, ARAccessNameType, ARTimestamp, int, int, ARTaskInfoList *, ARStatusList *)): pass
#        def ARGetListCheckpoint (ARControlStruct *, ARNameType, ARTimestamp, int, ARTaskCheckpointList *, ARStatusList *)): pass
#        def ARCreateOverlay (ARControlStruct *, AROverlaidStruct *, char *objectModificationLogLabel, ARNameType, 
#                 ARInternalId *overlayId, ARStatusList *)): pass
#        def ARCreateOverlayFromObject (ARControlStruct *, AROverlaidStruct *, AROverlaidStruct *, char *objectModificationLogLabel, ARNameType, 
#                 ARInternalId *overlayId, ARStatusList *)): pass

    class ARS(ARS7603):
        pass

if cars.version >= 76.04:
    class ARS7604(ARS7603):
        pass

    class ARS(ARS7604):
        pass

if cars.version >= 80:
    class ARS80(ARS7604):
        pass

    class ARS(ARS80):
        pass

if cars.version >= 81:
    class ARS81(ARS80):
        pass

    class ARS(ARS81):
        pass

if __name__ == "__main__":
    print ('''pyARS.ars does not offer any functionality out of the box. It provides
you with an interface to Action Request System(R). 
    
internal information:
found the following api version: %s
python is running as %s
''' % (cars.version,
       cars.runningAs64bit and '64bit' or '32bit'))
    print ('''This is the path, where I'm looking for the ARSystem libraries:''')
    import os
    if  sys.platform =='cygwin':
        print ('\r\n'.join(os.environ['PATH'].split(':')))
    elif os.name == 'nt':
        print ('\r\n'.join(os.environ['PATH'].split(';')))
    else:
        print ('\r\n'.join(os.environ['LD_LIBRARY_PATH'].split(';')))
