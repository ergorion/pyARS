#######################################################################
#
# This is the low level implementation of the Remedy C API in Python.
# (C) 2004-2015 by Ergorion
#
#

from ctypes import CDLL, sizeof, c_long
import os
# import pdb
import sys
import struct

# a list of versions (major/minor version) of dll/.h files to check
# unfortunately, BMC used 4 digit version numbers in between, which
# make this look rather ugly...
versions = (81, 80, 76.04, 76.03, 75, 71, 70, 63, 60, 51)
versionDirectories = ('8.1', '8.0', '7.6', '7.5', '7.1', '7.0', '6.3', '6.0', '5.1')

libName = {'win32' : 'arapi',
           'cygwin' : 'arapi', # cygwin
           'cli' : 'arapi', # ironpython
           'linux2' : 'libarjni',
           'linux3' : 'libarjni',
           'sunos5' : 'libarjni'} 
# we need to differentiate the different python versions (as py3k does not
# know the data type long any more, and True/False cannot be defined any more)
if sys.version_info >= (3, 0):
    from ctypes import set_conversion_mode
    postfixP3k = '_py3k'
    set_conversion_mode('utf-8', 'strict') # python3k only knows unicode strings!
else:
    postfixP3k = ''
    
runningAs64bit = ( 8 * struct.calcsize("P")) == 64
if runningAs64bit:
    postfix64bit = {'win32' : '_win64',
                    'cygwin': '_win64',
                    'cli': '_win64',
                    'linux2' : '_lx64',
                    'linux3' : '_lx64',
                    'sunos5' : '_solsp64'}
    libName['sunos5'] = 'libari' # Starting with 7.6.4, Solaris only has libari for 64bit
    libName['linux2'] = 'libari' # Starting with 7.6.4, Linux2 only has libari for 64bit
    libName['linux3'] = 'libari' # Starting with 7.6.4, Linux3 only has libari for 64bit
else:
    postfix64bit = {'win32' : '',
                    'cygwin': '',
                    'cli': '',
                    'linux2' : '',
                    'linux3' : '',
                    'sunos5' : ''}

def extendPathWithWindowsRegistryInfo():
    '''Under Windows, we try to identify installation directories of
Remedy User or Admin tool, because more often than not, the PATH environment
variable is not sufficient to load the Remedy DLLs.
Input: 
Output: newPath
Sideeffect: This function extends the environment variable PATH
with the installation directories of aruser and aradmin.'''    
    oldPath = '' # here we store the original system PATH
    newPath = set() # here we collect all possible remedy directories
    pathconvert = None # if we are not running under cygwin, we don't need to convert paths
    try:
        if 'cygwin' == sys.platform:
            try:
                from cygwinreg import ConnectRegistry, OpenKey, QueryValueEx,CloseKey,EnumValue,\
                                  HKEY_LOCAL_MACHINE, HKEY_CURRENT_USER, KEY_READ
                import cygwinreg.WindowsError
            except ImportError:
                return (oldPath, '')
            import subprocess
            def pathconvert (path):
                try:
                    p = subprocess.Popen( [ 'cygpath', '-au', path ], stdout=subprocess.PIPE )
                except OSError:
                    return ''
                output, _ = p.communicate()
                if p.poll():
                    raise Exception( 'cygpath returns an error' )
                return output.strip()
            #end def pathconvert
        else:
            try: 
                from _winreg import ConnectRegistry, OpenKey, QueryValueEx,CloseKey,EnumValue,\
                                    HKEY_LOCAL_MACHINE, HKEY_CURRENT_USER, KEY_READ
            except ImportError: # python 3
                from winreg import ConnectRegistry, OpenKey, QueryValueEx,CloseKey,EnumValue,\
                                    HKEY_LOCAL_MACHINE, HKEY_CURRENT_USER, KEY_READ
        
        # prepare different directories that we know of in Registry Current User
        regDirectories = [('ARPATH0', r'Software\Remedy\AR System User\Users'), ]
        for version in versionDirectories:
            regDirectories.append(('InstallDir', r'Software\Remedy\AR System User\%s' % version))
            regDirectories.append(('InstallDir', r'Software\Remedy\AR System Administrator\%s' % version))
            
        pathList = {HKEY_LOCAL_MACHINE : (('Path', r'Software\Microsoft\Windows\CurrentVersion\App Paths\aruser.exe'),
                    ('Path', r'Software\Microsoft\Windows\CurrentVersion\App Paths\ARADMIN.EXE'),
                    ('', r'SOFTWARE\Classes\TypeLib\{3E92FB98-4B0A-11D1-A94C-00C04FC9BDF2}\1.0\HELPDIR')),
                    HKEY_CURRENT_USER : regDirectories}
        # store the current SYSTEM PATH settings for later reference
        try:
            oldPath = os.environ['PATH']
        except KeyError:
            oldPath = ''
        for key in pathList:
            reg = ConnectRegistry(None, key)
            directories = pathList[key]
            for queryKey, path in directories:
                try:
                    key = OpenKey(reg, path, 0, KEY_READ)
                    arDirectory, _ = QueryValueEx(key, queryKey)
                    newPath.add( arDirectory )
                    CloseKey(key)
                except WindowsError:
                    pass

        # now also check the registry shared_dlls
        reg = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
        key = OpenKey(reg, 'SOFTWARE\Microsoft\Windows\CurrentVersion\SharedDlls', 0, KEY_READ)
        i = 0
        while True:
            try:
                (entry, _value, _type) = EnumValue (key, i)
            except WindowsError:
                break
            if entry.rfind('arapi') > -1:
                # newPath = '%s;%s' % (newPath, entry[:entry.rfind('\\')])
                newPath.add( entry[:entry.rfind('\\')] )
            i = i+1
        
    except ValueError:
        # if we fail to read the path from the registry, we just continue, hoping
        # that the system path will work...
        pass
    adaptedPathSet = map( pathconvert, newPath )
    adaptedPathString = os.pathsep.join(adaptedPathSet)
    os.environ['PATH'] = '%s;%s' % (oldPath, adaptedPathString)
    return (oldPath, adaptedPathString)

def tryToLoadLib(sharedLibFileName = "arapi%s.dll"):
    foundDLL = False # have we found a DLL already?
    arapi = None
    for version in versions:
        try:
            if not foundDLL:
                # BMC used four digit version numbers for 7603 and 7604
                # afterwards it went back to 2 digit version numbers
                # in order to calculate right, I used floating point numbers
                # and here I have to correct this to a 4 digit number:
                dllVersion = version
                if dllVersion > 76 and dllVersion < 77:
                    dllVersion = int(100*dllVersion)
#                print "I'm trying to load %s Version %s " % (sharedLibFileName,
#                                                             dllVersion) 
                arapi = CDLL(sharedLibFileName % dllVersion)
                foundDLL = True
                break
        except OSError: # that's IronPython's and Linux way of telling something did not work
            pass
        except WindowsError: 
            # if this exception is raised, the loading of the API failed; we must
            # capture this exception and continue our loop in order to find the
            # correct API version...
            pass
                             
    return (foundDLL, arapi, version)

def tryListOfLibs(sharedLibraryList):
    '''
Input: list of names of shared libraries
Output: (foundDLL, arapi, version) or (False, None, None) if no library
        from this list could be loaded'''
    for sharedLib in sharedLibraryList:
        (foundDLL, arapi, version) = tryToLoadLib(sharedLib)
#        print "trying %s found a lib: %s" % (sharedLib, foundDLL)
        if foundDLL:
            return (foundDLL, arapi, version)
    return (False, None, None)

if os.name == 'nt' or sys.platform =='cygwin':
    oldPath = os.environ['PATH']
    (foundDLL, arapi, version) = tryListOfLibs(("%s%%s_build002%s.dll" % (libName[sys.platform],
                                                                         postfix64bit[sys.platform]), # 7.6.4 
                                                "%s%%s_build001%s.dll" % (libName[sys.platform],
                                                                         postfix64bit[sys.platform]), # 7.6.3
                                                "%s%%s%s.dll" % (libName[sys.platform],
                                                                postfix64bit[sys.platform])))
    if not foundDLL:
        (oldPath, newPath) = extendPathWithWindowsRegistryInfo()
        (foundDLL, arapi, version) = tryListOfLibs(("%s%%s_build002%s.dll" % (libName[sys.platform],
                                                                         postfix64bit[sys.platform]), # 7.6.4 
                                                "%s%%s_build001%s.dll" % (libName[sys.platform],
                                                                         postfix64bit[sys.platform]), # 7.6.3
                                                "%s%%s%s.dll" % (libName[sys.platform],
                                                                postfix64bit[sys.platform])))
    # The following cannot be moved into a function, as it needs to import
    # everything into this namespace
#    if foundDLL: 
#        try:
#            # we need to get the imported names into car's namespace
#            # so that the clients import cars do not need to know about the version!!!
#            try: 
#                exec('from _cars%s%s import *' % (version, postfixP3k))
##                print "I have successfully loaded _cars%s%s" % (version, postfixP3k)
#            except NameError: # for py3k
#                exec('from pyars._cars%s%s import *' % (version, postfixP3k))
#            foundInclude = True
#        except ImportError:
#            # originally I raised an error; but imagine that we find
#            # a later DLL (e.g. 9.5 and only 8.0 includes, that should
#            # still work)
#            pass
#            # raise NotImplementedError, "Could not load Ergorion import %s file" % (version)

elif os.name == 'posix':
    newPath = ''
    try:
        oldPath = os.environ['LD_LIBRARY_PATH']
    except KeyError:
        oldPath = ''

    (foundDLL, arapi, version) = tryListOfLibs(("%s%%s_build002%s.so" % (libName[sys.platform],
                                                                         postfix64bit[sys.platform]), # 7.6.4 
                                                "%s%%s_build001%s.so" % (libName[sys.platform],
                                                                         postfix64bit[sys.platform]), # 7.6.3
                                                "%s%%s%s.so" % (libName[sys.platform],
                                                                postfix64bit[sys.platform])))
    if foundDLL: 
        arapi = CDLL("libar%s.so" % postfix64bit[sys.platform])

foundInclude = False
if foundDLL: 
    try:
        try:
            dllVersion = version
            if dllVersion > 76 and dllVersion < 77:
                dllVersion = int(100*dllVersion)
            # we need to get the imported names into car's namespace
            # so that the clients import cars do not need to know about the version!!!
            exec('from _cars%s%s import *' % (dllVersion, postfixP3k))
        except NameError: # for py3k
            exec('from pyars._cars%s%s import *' % (dllVersion, postfixP3k))
        foundInclude = True
    except ImportError:
        # originally I raised an error; but imagine that we find
        # a later DLL (e.g. 9.5 and only 8.0 includes, that should
        # still work)
        pass
else:
    print ('FATAL ERROR: Could not load ARS shared libraries')
    print ('')
    print ('The current system path is set to the following directories:')
    if  sys.platform =='cygwin':
        print ('\r\n'.join(oldPath.split(':')))
    elif os.name == 'nt':
        print ('\r\n'.join(oldPath.split(';')))
    else:
        print ('\r\n'.join(oldPath.split(';')))
    print
    if newPath != '':
        print ('''I also looked in the Remedy install directories that I found \
in the registry:''')
        if  sys.platform =='cygwin':
            print ('\r\n'.join(newPath.split(':')))
        elif os.name == 'nt':
            print ('\r\n'.join(newPath.split(';')))
        else:
            print ('\r\n'.join(newPath.split(';')))
    else:
        print ('I could not find any Remedy install directory in the registry')
    if runningAs64bit:
        print ('This python version is running as 64bit.')
    else:
        print ('This python version is running as 32bit.')
    print ('''
Please double check your PATH settings and make sure you have:
on Windows and cygwin: arapi.dll, arrpc.dll, arutl.dll
on Solaris and Linux: libar.so and libari.so
in the appropriate version (e.g. arapi63.dll, libarjni63.so).
''')
    sys.exit(2)

if not foundInclude:
    print ('FATAL ERROR: Could not find any _carsnn%s.py include file' % postfixP3k)
    sys.exit(2)

#######################################################################
#
# This is a mapping dictionaries for easier access of
# unions depending on the types... (in order to get rid of
# endless if-elif-else cascades...)

ARValueStruct._mapping_so_ = { AR_DATA_TYPE_KEYWORD: 'u.keyNum',
                  AR_DATA_TYPE_INTEGER: 'u.intVal',
                  AR_DATA_TYPE_REAL: 'u.realVal',
                  AR_DATA_TYPE_CHAR: 'u.charVal',
                  AR_DATA_TYPE_DIARY: 'u.diaryVal',
                  AR_DATA_TYPE_ENUM: 'u.enumVal',
                  AR_DATA_TYPE_TIME: 'u.timeVal',
                  AR_DATA_TYPE_BITMASK: 'u.maskVal',
                  AR_DATA_TYPE_DECIMAL: 'u.decimalVal',
                  AR_DATA_TYPE_ULONG: 'u.ulongVal',
                  AR_DATA_TYPE_DATE: 'u.dateVal',
                  AR_DATA_TYPE_TIME_OF_DAY: 'u.timeOfDayVal' }
    # here comes the mapping for the complex types...
    # problem is, that the structs are defined as pointers in 
    # the C struct -- so we have to de-reference those first
    # via ctypes: .contents
ARValueStruct._mapping_co_ = {
            AR_DATA_TYPE_BYTES: 'obj.u.byteListVal.contents',
            AR_DATA_TYPE_ATTACH: '(obj.u.attachVal.contents.name, obj.u.attachVal.contents.origSize, obj.u.attachVal.contents.compSize)',
            AR_DATA_TYPE_CURRENCY: 'obj.u.currencyVal.contents',
            AR_DATA_TYPE_COORDS: '[(obj.u.coordListVal.contents.coords[i].x, obj.u.coordListVal.contents.coords[i].y) for i in range(obj.u.coordListVal.contents.numItems)]'
        }
ARActiveLinkActionStruct._mapping_ = { AR_ACTIVE_LINK_ACTION_MACRO: 'u.macro',
                  AR_ACTIVE_LINK_ACTION_FIELDS: 'u.setFields',
                  AR_ACTIVE_LINK_ACTION_MESSAGE: 'u.message',
                  AR_ACTIVE_LINK_ACTION_SET_CHAR: 'u.characteristics',
                  AR_ACTIVE_LINK_ACTION_DDE: 'u.dde',
                  AR_ACTIVE_LINK_ACTION_FIELDP: 'u.pushFields',
                  AR_ACTIVE_LINK_ACTION_SQL: 'u.sqlCommand',
                  AR_ACTIVE_LINK_ACTION_AUTO: 'u.automation',
                  AR_ACTIVE_LINK_ACTION_OPENDLG: 'u.openDlg',
                  AR_ACTIVE_LINK_ACTION_COMMITC: 'u.commitChanges',
                  AR_ACTIVE_LINK_ACTION_CLOSEWND: 'u.closeWnd',
                  AR_ACTIVE_LINK_ACTION_CALLGUIDE: 'u.callGuide',
                  AR_ACTIVE_LINK_ACTION_EXITGUIDE: 'u.exitGuide',
                  AR_ACTIVE_LINK_ACTION_GOTOGUIDELABEL: 'u.gotoGuide',
                  AR_ACTIVE_LINK_ACTION_WAIT: 'u.waitAction',
                  AR_ACTIVE_LINK_ACTION_GOTOACTION: 'u.gotoAction'
                  }

#######################################################################
#
# This is a mapping of all constants defined for ARS V5.1 to Strings
# for nicer output. As this is for cosmetic purposes only, we need
# to make sure that any error does not impact the import
# of this module, therefore I catch the expection of an unknown
# constant.

ars_const = {}

try:
    
    ars_const['AR_DATA_TYPE']= {
        AR_DATA_TYPE_NULL: 'NULL',
        AR_DATA_TYPE_KEYWORD: 'KEYWORD', 
        AR_DATA_TYPE_INTEGER: 'INTEGER', 
        AR_DATA_TYPE_REAL: 'REAL', 
        AR_DATA_TYPE_CHAR: 'CHAR', 
        AR_DATA_TYPE_DIARY: 'DIARY', 
        AR_DATA_TYPE_ENUM:'ENUM', 
        AR_DATA_TYPE_TIME: 'TIME', 
        AR_DATA_TYPE_BITMASK: 'BITMASK', 
        AR_DATA_TYPE_BYTES: 'BYTES', 
        AR_DATA_TYPE_DECIMAL: 'DECIMAL', 
        AR_DATA_TYPE_ATTACH: 'ATTACH', 
        AR_DATA_TYPE_CURRENCY: 'CURRENCY', 
        AR_DATA_TYPE_DATE: 'DATE',
        AR_DATA_TYPE_TIME_OF_DAY: 'TIME_OF_DAY',
        AR_DATA_TYPE_JOIN: 'JOIN', 
        AR_DATA_TYPE_TRIM: 'TRIM',
        AR_DATA_TYPE_CONTROL: 'CONTROL',
        AR_DATA_TYPE_TABLE: 'TABLE',
        AR_DATA_TYPE_COLUMN: 'COLUMN',
        AR_DATA_TYPE_PAGE: 'PAGE',
        AR_DATA_TYPE_PAGE_HOLDER: 'PAGE_HOLDER',
        AR_DATA_TYPE_ATTACH_POOL: 'ATTACH_POOL',
        AR_DATA_TYPE_ULONG: 'ULONG',
        AR_DATA_TYPE_COORDS: 'COORDS',
        AR_DATA_TYPE_VIEW: 'VIEW',
        AR_DATA_TYPE_DISPLAY: 'DISPLAY'
    }
    
    ars_const['AR_FIELD_OPTION'] = {
        0 : '*???ERROR???*',
        AR_FIELD_OPTION_REQUIRED: 'REQUIRED',
        AR_FIELD_OPTION_OPTIONAL: 'OPTIONAL',
        AR_FIELD_OPTION_SYSTEM: 'SYSTEM',
        AR_FIELD_OPTION_DISPLAY: 'DISPLAY',
        }
    ars_const['AR_FULLTEXT_OPTIONS'] = {
        AR_FULLTEXT_OPTIONS_NONE: 'NONE', 
        AR_FULLTEXT_OPTIONS_INDEXED: 'INDEXED'
    }
    ars_const['AR_ENUM_STYLE'] = {
        AR_ENUM_STYLE_REGULAR: 'REGULAR',
        AR_ENUM_STYLE_CUSTOM: 'CUSTOM',
        AR_ENUM_STYLE_QUERY: 'QUERY'
    }
    
    ars_const['AR_SERVER_INFO'] = {
            AR_SERVER_INFO_DB_TYPE: "DB_TYPE",
            AR_SERVER_INFO_SERVER_LICENSE: "SERVER_LICENSE",
            AR_SERVER_INFO_FIXED_LICENSE: "FIXED_LICENSE",
            AR_SERVER_INFO_VERSION: "VERSION",
            AR_SERVER_INFO_ALLOW_GUESTS: "ALLOW_GUESTS",
            AR_SERVER_INFO_USE_ETC_PASSWD: "USE_ETC_PASSWD",
            AR_SERVER_INFO_XREF_PASSWORDS: "XREF_PASSWORDS",
            AR_SERVER_INFO_DEBUG_MODE: "DEBUG_MODE",
            AR_SERVER_INFO_DB_NAME: "DB_NAME",
            AR_SERVER_INFO_DB_PASSWORD: "DB_PASSWORD",
            AR_SERVER_INFO_HARDWARE: "HARDWARE",
            AR_SERVER_INFO_OS: "OS",
            AR_SERVER_INFO_SERVER_DIR: "SERVER_DIR",
            AR_SERVER_INFO_DBHOME_DIR: "DBHOME_DIR",
            AR_SERVER_INFO_SET_PROC_TIME: "SET_PROC_TIME",
            AR_SERVER_INFO_EMAIL_FROM: "EMAIL_FROM",
            AR_SERVER_INFO_SQL_LOG_FILE: "SQL_LOG_FILE",
            AR_SERVER_INFO_FLOAT_LICENSE: "FLOAT_LICENSE",
            AR_SERVER_INFO_FLOAT_TIMEOUT: "FLOAT_TIMEOUT",
            AR_SERVER_INFO_UNQUAL_QUERIES: "UNQUAL_QUERIES",
            AR_SERVER_INFO_FILTER_LOG_FILE: "FILTER_LOG_FILE",
            AR_SERVER_INFO_USER_LOG_FILE: "USER_LOG_FILE",
            AR_SERVER_INFO_REM_SERV_ID: "REM_SERV_ID",
            AR_SERVER_INFO_MULTI_SERVER: "MULTI_SERVER",
            AR_SERVER_INFO_EMBEDDED_SQL: "EMBEDDED_SQL",
            AR_SERVER_INFO_MAX_SCHEMAS: "MAX_SCHEMAS",
            AR_SERVER_INFO_DB_VERSION: "DB_VERSION",
            AR_SERVER_INFO_MAX_ENTRIES: "MAX_ENTRIES",
            AR_SERVER_INFO_MAX_F_DAEMONS: "MAX_F_DAEMONS",
            AR_SERVER_INFO_MAX_L_DAEMONS: "MAX_L_DAEMONS",
            AR_SERVER_INFO_ESCALATION_LOG_FILE: "ESCALATION_LOG_FILE",
            AR_SERVER_INFO_ESCL_DAEMON: "ESCL_DAEMON",
            AR_SERVER_INFO_SUBMITTER_MODE: "SUBMITTER_MODE",
            AR_SERVER_INFO_API_LOG_FILE: "API_LOG_FILE",
            AR_SERVER_INFO_FTEXT_FIXED: "FTEXT_FIXED",
            AR_SERVER_INFO_FTEXT_FLOAT: "FTEXT_FLOAT",
            AR_SERVER_INFO_FTEXT_TIMEOUT: "FTEXT_TIMEOUT",
            AR_SERVER_INFO_RESERV1_A: "RESERV1_A",
            AR_SERVER_INFO_RESERV1_B: "RESERV1_B",
            AR_SERVER_INFO_RESERV1_C: "RESERV1_C",
            AR_SERVER_INFO_SERVER_IDENT: "SERVER_IDENT",
            AR_SERVER_INFO_DS_SVR_LICENSE: "DS_SVR_LICENSE",
            AR_SERVER_INFO_DS_MAPPING: "DS_MAPPING",
            AR_SERVER_INFO_DS_PENDING: "DS_PENDING",
            AR_SERVER_INFO_DS_RPC_SOCKET: "DS_RPC_SOCKET",
            AR_SERVER_INFO_DS_LOG_FILE: "DS_LOG_FILE",
            AR_SERVER_INFO_SUPPRESS_WARN: "SUPPRESS_WARN",
            AR_SERVER_INFO_HOSTNAME: "HOSTNAME",
            AR_SERVER_INFO_FULL_HOSTNAME: "FULL_HOSTNAME",
            AR_SERVER_INFO_SAVE_LOGIN: "SAVE_LOGIN",
            AR_SERVER_INFO_U_CACHE_CHANGE: "U_CACHE_CHANGE",
            AR_SERVER_INFO_G_CACHE_CHANGE: "G_CACHE_CHANGE",
            AR_SERVER_INFO_STRUCT_CHANGE: "STRUCT_CHANGE",
            AR_SERVER_INFO_CASE_SENSITIVE: "CASE_SENSITIVE",
            AR_SERVER_INFO_SERVER_LANG: "SERVER_LANG",
            AR_SERVER_INFO_ADMIN_ONLY: "ADMIN_ONLY",
            AR_SERVER_INFO_CACHE_LOG_FILE: "CACHE_LOG_FILE",
            AR_SERVER_INFO_FLASH_DAEMON: "FLASH_DAEMON",
            AR_SERVER_INFO_THREAD_LOG_FILE: "THREAD_LOG_FILE",
            AR_SERVER_INFO_ADMIN_TCP_PORT: "ADMIN_TCP_PORT",
            AR_SERVER_INFO_ESCL_TCP_PORT: "ESCL_TCP_PORT",
            AR_SERVER_INFO_FAST_TCP_PORT: "FAST_TCP_PORT",
            AR_SERVER_INFO_LIST_TCP_PORT: "LIST_TCP_PORT",
            AR_SERVER_INFO_FLASH_TCP_PORT: "FLASH_TCP_PORT",
            AR_SERVER_INFO_TCD_TCP_PORT: "TCD_TCP_PORT",
            AR_SERVER_INFO_DSO_DEST_PORT: "DSO_DEST_PORT",
            AR_SERVER_INFO_INFORMIX_DBN: "INFORMIX_DBN",
            AR_SERVER_INFO_INFORMIX_TBC: "INFORMIX_TBC",
            AR_SERVER_INFO_INGRES_VNODE: "INGRES_VNODE",
            AR_SERVER_INFO_ORACLE_SID: "ORACLE_SID",
            AR_SERVER_INFO_ORACLE_TWO_T: "ORACLE_TWO_T",
            AR_SERVER_INFO_SYBASE_CHARSET: "SYBASE_CHARSET",
            AR_SERVER_INFO_SYBASE_SERV: "SYBASE_SERV",
            AR_SERVER_INFO_SHARED_MEM: "SHARED_MEM",
            AR_SERVER_INFO_SHARED_CACHE: "SHARED_CACHE",
            AR_SERVER_INFO_CACHE_SEG_SIZE: "CACHE_SEG_SIZE",
            AR_SERVER_INFO_DB_USER: "DB_USER",
            AR_SERVER_INFO_NFY_TCP_PORT: "NFY_TCP_PORT",
            AR_SERVER_INFO_FILT_MAX_TOTAL: "FILT_MAX_TOTAL",
            AR_SERVER_INFO_FILT_MAX_STACK: "FILT_MAX_STACK",
            AR_SERVER_INFO_DEFAULT_ORDER_BY: "DEFAULT_ORDER_BY",
            AR_SERVER_INFO_DELAYED_CACHE: "DELAYED_CACHE",
            AR_SERVER_INFO_DSO_MERGE_STYLE: "DSO_MERGE_STYLE",
            AR_SERVER_INFO_EMAIL_LINE_LEN: "EMAIL_LINE_LEN",
            AR_SERVER_INFO_EMAIL_SYSTEM: "EMAIL_SYSTEM",
            AR_SERVER_INFO_INFORMIX_RELAY_MOD: "INFORMIX_RELAY_MOD",
            AR_SERVER_INFO_PS_RPC_SOCKET: "PS_RPC_SOCKET",
            AR_SERVER_INFO_REGISTER_PORTMAPPER: "REGISTER_PORTMAPPER",
            AR_SERVER_INFO_SERVER_NAME: "SERVER_NAME",
            AR_SERVER_INFO_DBCONF: "DBCONF",
            AR_SERVER_INFO_APPL_PENDING: "APPL_PENDING",
            AR_SERVER_INFO_AP_RPC_SOCKET: "AP_RPC_SOCKET",
            AR_SERVER_INFO_AP_LOG_FILE: "AP_LOG_FILE",
            AR_SERVER_INFO_AP_DEFN_CHECK: "AP_DEFN_CHECK",
            AR_SERVER_INFO_MAX_LOG_FILE_SIZE: "MAX_LOG_FILE_SIZE",
            AR_SERVER_INFO_CLUSTERED_INDEX: "CLUSTERED_INDEX",
            AR_SERVER_INFO_ACTLINK_DIR: "ACTLINK_DIR",
            AR_SERVER_INFO_ACTLINK_SHELL: "ACTLINK_SHELL",
            AR_SERVER_INFO_USER_CACHE_UTILS: "USER_CACHE_UTILS",
            AR_SERVER_INFO_EMAIL_TIMEOUT: "EMAIL_TIMEOUT",
            AR_SERVER_INFO_EXPORT_VERSION: "EXPORT_VERSION",
            AR_SERVER_INFO_ENCRYPT_AL_SQL: "ENCRYPT_AL_SQL",
            AR_SERVER_INFO_SCC_ENABLED: "SCC_ENABLED",
            AR_SERVER_INFO_SCC_PROVIDER_NAME: "SCC_PROVIDER_NAME",
            AR_SERVER_INFO_SCC_TARGET_DIR: "SCC_TARGET_DIR",
            AR_SERVER_INFO_SCC_COMMENT_CHECKIN: "SCC_COMMENT_CHECKIN",
            AR_SERVER_INFO_SCC_COMMENT_CHECKOUT: "SCC_COMMENT_CHECKOUT",
            AR_SERVER_INFO_SCC_INTEGRATION_MODE: "SCC_INTEGRATION_MODE",
            AR_SERVER_INFO_EA_RPC_SOCKET: "EA_RPC_SOCKET",
            AR_SERVER_INFO_EA_RPC_TIMEOUT: "EA_RPC_TIMEOUT",
            AR_SERVER_INFO_USER_INFO_LISTS: "USER_INFO_LISTS",
            AR_SERVER_INFO_USER_INST_TIMEOUT: "USER_INST_TIMEOUT",
            AR_SERVER_INFO_DEBUG_GROUPID: "DEBUG_GROUPID",
            AR_SERVER_INFO_APPLICATION_AUDIT: "APPLICATION_AUDIT",
            AR_SERVER_INFO_EA_SYNC_TIMEOUT: "EA_SYNC_TIMEOUT",
            AR_SERVER_INFO_SERVER_TIME: "SERVER_TIME",
            AR_SERVER_INFO_SVR_SEC_CACHE: "SVR_SEC_CACHE",
            AR_SERVER_INFO_LOGFILE_APPEND: "LOGFILE_APPEND",
            AR_SERVER_INFO_MINIMUM_API_VER: "MINIMUM_API_VER",
            AR_SERVER_INFO_MAX_AUDIT_LOG_FILE_SIZE: "MAX_AUDIT_LOG_FILE_SIZE",
            AR_SERVER_INFO_CANCEL_QUERY: "CANCEL_QUERY",
            AR_SERVER_INFO_MULT_ASSIGN_GROUPS: "MULT_ASSIGN_GROUPS",
            AR_SERVER_INFO_ARFORK_LOG_FILE: "ARFORK_LOG_FILE",
            AR_SERVER_INFO_DSO_PLACEHOLDER_MODE: "DSO_PLACEHOLDER_MODE",
            AR_SERVER_INFO_DSO_POLLING_INTERVAL: "DSO_POLLING_INTERVAL",
            AR_SERVER_INFO_DSO_SOURCE_SERVER: "DSO_SOURCE_SERVER",
            AR_SERVER_INFO_DS_POOL: "DS_POOL",
            AR_SERVER_INFO_DSO_TIMEOUT_NORMAL: "DSO_TIMEOUT_NORMAL",
            AR_SERVER_INFO_ENC_PUB_KEY: "ENC_PUB_KEY",
            AR_SERVER_INFO_ENC_PUB_KEY_EXP: "ENC_PUB_KEY_EXP",
            AR_SERVER_INFO_ENC_DATA_KEY_EXP: "ENC_DATA_KEY_EXP",
            AR_SERVER_INFO_ENC_DATA_ENCR_ALG: "ENC_DATA_ENCR_ALG",
            AR_SERVER_INFO_ENC_SEC_POLICY: "ENC_SEC_POLICY",
            AR_SERVER_INFO_ENC_SESS_H_ENTRIES: "ENC_SESS_H_ENTRIES",
            AR_SERVER_INFO_DSO_TARGET_CONNECTION: "DSO_TARGET_CONNECTION",
            AR_SERVER_INFO_PREFERENCE_PRIORITY: "PREFERENCE_PRIORITY",
            AR_SERVER_INFO_ORACLE_QUERY_ON_CLOB: "ORACLE_QUERY_ON_CLOB",
            AR_SERVER_INFO_MESSAGE_CAT_SCHEMA: "MESSAGE_CAT_SCHEMA",
            AR_SERVER_INFO_ALERT_SCHEMA: "ALERT_SCHEMA",
            AR_SERVER_INFO_LOCALIZED_SERVER: "LOCALIZED_SERVER",
            AR_SERVER_INFO_SVR_EVENT_LIST: "SVR_EVENT_LIST",
            AR_SERVER_INFO_DISABLE_ADMIN_OPERATIONS: "DISABLE_ADMIN_OPERATIONS",
            AR_SERVER_INFO_DISABLE_ESCALATIONS: "DISABLE_ESCALATIONS",
            AR_SERVER_INFO_ALERT_LOG_FILE: "ALERT_LOG_FILE",
            AR_SERVER_INFO_DISABLE_ALERTS: "DISABLE_ALERTS",
            AR_SERVER_INFO_CHECK_ALERT_USERS: "CHECK_ALERT_USERS",
            AR_SERVER_INFO_ALERT_SEND_TIMEOUT: "ALERT_SEND_TIMEOUT",
            AR_SERVER_INFO_ALERT_OUTBOUND_PORT: "ALERT_OUTBOUND_PORT",
            AR_SERVER_INFO_ALERT_SOURCE_AR: "ALERT_SOURCE_AR",
            AR_SERVER_INFO_ALERT_SOURCE_FB: "ALERT_SOURCE_FB",
            AR_SERVER_INFO_DSO_USER_PASSWD: "DSO_USER_PASSWD",
            AR_SERVER_INFO_DSO_TARGET_PASSWD: "DSO_TARGET_PASSWD",
            AR_SERVER_INFO_APP_SERVICE_PASSWD: "APP_SERVICE_PASSWD",
            AR_SERVER_INFO_MID_TIER_PASSWD: "MID_TIER_PASSWD",
            AR_SERVER_INFO_PLUGIN_LOG_FILE: "PLUGIN_LOG_FILE",
            AR_SERVER_INFO_SVR_STATS_REC_MODE: "SVR_STATS_REC_MODE",
            AR_SERVER_INFO_SVR_STATS_REC_INTERVAL: "SVR_STATS_REC_INTERVAL",
            AR_SERVER_INFO_DEFAULT_WEB_PATH: "DEFAULT_WEB_PATH",
            AR_SERVER_INFO_FILTER_API_RPC_TIMEOUT: "FILTER_API_RPC_TIMEOUT",
            AR_SERVER_INFO_DISABLED_CLIENT: "DISABLED_CLIENT",
            AR_SERVER_INFO_PLUGIN_PASSWD: "PLUGIN_PASSWD",
            AR_SERVER_INFO_PLUGIN_ALIAS: "PLUGIN_ALIAS",
            AR_SERVER_INFO_PLUGIN_TARGET_PASSWD: "PLUGIN_TARGET_PASSWD",
            AR_SERVER_INFO_REM_WKFLW_PASSWD: "REM_WKFLW_PASSWD",
            AR_SERVER_INFO_REM_WKFLW_TARGET_PASSWD: "REM_WKFLW_TARGET_PASSWD",
            AR_SERVER_INFO_EXPORT_SVR_OPS: "EXPORT_SVR_OPS",
            AR_SERVER_INFO_INIT_FORM: "INIT_FORM",
            AR_SERVER_INFO_ENC_PUB_KEY_ALG: "ENC_PUB_KEY_ALG",
            AR_SERVER_INFO_IP_NAMES: "IP_NAMES",
            AR_SERVER_INFO_DSO_CACHE_CHK_INTERVAL: "DSO_CACHE_CHK_INTERVAL",
            AR_SERVER_INFO_DSO_MARK_PENDING_RETRY: "DSO_MARK_PENDING_RETRY",
            AR_SERVER_INFO_DSO_RPCPROG_NUM: "DSO_RPCPROG_NUM",
            AR_SERVER_INFO_DELAY_RECACHE_TIME: "DELAY_RECACHE_TIME",
            AR_SERVER_INFO_DFLT_ALLOW_CURRENCIES: "DFLT_ALLOW_CURRENCIES",
            AR_SERVER_INFO_CURRENCY_INTERVAL: "CURRENCY_INTERVAL",
            AR_SERVER_INFO_ORACLE_CURSOR_SHARE: "ORACLE_CURSOR_SHARE",
            AR_SERVER_INFO_DB2_DB_ALIAS: "DB2_DB_ALIAS",
            AR_SERVER_INFO_DB2_SERVER: "DB2_SERVER",
            AR_SERVER_INFO_DFLT_FUNC_CURRENCIES: "DFLT_FUNC_CURRENCIES",
            AR_SERVER_INFO_EMAIL_IMPORT_FORM: "EMAIL_IMPORT_FORM",
            AR_SERVER_INFO_EMAIL_AIX_USE_OLD_EMAIL: "EMAIL_AIX_USE_OLD_EMAIL",
            AR_SERVER_INFO_TWO_DIGIT_YEAR_CUTOFF: "TWO_DIGIT_YEAR_CUTOFF",
            AR_SERVER_INFO_ALLOW_BACKQUOTE_IN_PROCESS: "ALLOW_BACKQUOTE_IN_PROCESS",
            AR_SERVER_INFO_DB_CONNECTION_RETRIES: "DB_CONNECTION_RETRIES"
    }
    
    ars_const['AR_SERVER_STAT'] = {
            AR_SERVER_STAT_START_TIME: "START_TIME",
            AR_SERVER_STAT_BAD_PASSWORD: "BAD_PASSWORD",
            AR_SERVER_STAT_NO_WRITE_TOKEN: "NO_WRITE_TOKEN",
            AR_SERVER_STAT_NO_FULL_TOKEN: "NO_FULL_TOKEN",
            AR_SERVER_STAT_CURRENT_USERS: "CURRENT_USERS",
            AR_SERVER_STAT_WRITE_FIXED: "WRITE_FIXED",
            AR_SERVER_STAT_WRITE_FLOATING: "WRITE_FLOATING",
            AR_SERVER_STAT_WRITE_READ: "WRITE_READ",
            AR_SERVER_STAT_FULL_FIXED: "FULL_FIXED",
            AR_SERVER_STAT_FULL_FLOATING: "FULL_FLOATING",
            AR_SERVER_STAT_FULL_NONE: "FULL_NONE",
            AR_SERVER_STAT_API_REQUESTS: "API_REQUESTS",
            AR_SERVER_STAT_API_TIME: "API_TIME",
            AR_SERVER_STAT_ENTRY_TIME: "ENTRY_TIME",
            AR_SERVER_STAT_RESTRUCT_TIME: "RESTRUCT_TIME",
            AR_SERVER_STAT_OTHER_TIME: "OTHER_TIME",
            AR_SERVER_STAT_CACHE_TIME: "CACHE_TIME",
            AR_SERVER_STAT_GET_E_COUNT: "GET_E_COUNT",
            AR_SERVER_STAT_GET_E_TIME: "GET_E_TIME",
            AR_SERVER_STAT_SET_E_COUNT: "SET_E_COUNT",
            AR_SERVER_STAT_SET_E_TIME: "SET_E_TIME",
            AR_SERVER_STAT_CREATE_E_COUNT: "CREATE_E_COUNT",
            AR_SERVER_STAT_CREATE_E_TIME: "CREATE_E_TIME",
            AR_SERVER_STAT_DELETE_E_COUNT: "DELETE_E_COUNT",
            AR_SERVER_STAT_DELETE_E_TIME: "DELETE_E_TIME",
            AR_SERVER_STAT_MERGE_E_COUNT: "MERGE_E_COUNT",
            AR_SERVER_STAT_MERGE_E_TIME: "MERGE_E_TIME",
            AR_SERVER_STAT_GETLIST_E_COUNT: "GETLIST_E_COUNT",
            AR_SERVER_STAT_GETLIST_E_TIME: "GETLIST_E_TIME",
            AR_SERVER_STAT_E_STATS_COUNT: "E_STATS_COUNT",
            AR_SERVER_STAT_E_STATS_TIME: "E_STATS_TIME",
            AR_SERVER_STAT_FILTER_PASSED: "FILTER_PASSED",
            AR_SERVER_STAT_FILTER_FAILED: "FILTER_FAILED",
            AR_SERVER_STAT_FILTER_DISABLE: "FILTER_DISABLE",
            AR_SERVER_STAT_FILTER_NOTIFY: "FILTER_NOTIFY",
            AR_SERVER_STAT_FILTER_MESSAGE: "FILTER_MESSAGE",
            AR_SERVER_STAT_FILTER_LOG: "FILTER_LOG",
            AR_SERVER_STAT_FILTER_FIELDS: "FILTER_FIELDS",
            AR_SERVER_STAT_FILTER_PROCESS: "FILTER_PROCESS",
            AR_SERVER_STAT_FILTER_TIME: "FILTER_TIME",
            AR_SERVER_STAT_ESCL_PASSED: "ESCL_PASSED",
            AR_SERVER_STAT_ESCL_FAILED: "ESCL_FAILED",
            AR_SERVER_STAT_ESCL_DISABLE: "ESCL_DISABLE",
            AR_SERVER_STAT_ESCL_NOTIFY: "ESCL_NOTIFY",
            AR_SERVER_STAT_ESCL_LOG: "ESCL_LOG",
            AR_SERVER_STAT_ESCL_FIELDS: "ESCL_FIELDS",
            AR_SERVER_STAT_ESCL_PROCESS: "ESCL_PROCESS",
            AR_SERVER_STAT_ESCL_TIME: "ESCL_TIME",
            AR_SERVER_STAT_TIMES_BLOCKED: "TIMES_BLOCKED",
            AR_SERVER_STAT_NUMBER_BLOCKED: "NUMBER_BLOCKED",
            AR_SERVER_STAT_CPU: "CPU",
            AR_SERVER_STAT_SQL_DB_COUNT: "SQL_DB_COUNT",
            AR_SERVER_STAT_SQL_DB_TIME: "SQL_DB_TIME",
            AR_SERVER_STAT_FTS_SRCH_COUNT: "FTS_SRCH_COUNT",
            AR_SERVER_STAT_FTS_SRCH_TIME: "FTS_SRCH_TIME",
            AR_SERVER_STAT_SINCE_START: "SINCE_START",
            AR_SERVER_STAT_IDLE_TIME: "IDLE_TIME",
            AR_SERVER_STAT_NET_RESP_TIME: "NET_RESP_TIME",
            AR_SERVER_STAT_FILTER_FIELDP: "FILTER_FIELDP",
            AR_SERVER_STAT_ESCL_FIELDP: "ESCL_FIELDP",
            AR_SERVER_STAT_FILTER_SQL: "FILTER_SQL",
            AR_SERVER_STAT_ESCL_SQL: "ESCL_SQL",
            AR_SERVER_STAT_NUM_THREADS: "NUM_THREADS",
            AR_SERVER_STAT_FILTER_GOTO_ACTION: "FILTER_GOTO_ACTION",
            AR_SERVER_STAT_FILTER_CALL_GUIDE: "FILTER_CALL_GUIDE",
            AR_SERVER_STAT_FILTER_EXIT_GUIDE: "FILTER_EXIT_GUIDE",
            AR_SERVER_STAT_FILTER_GOTO_GUIDE_LB: "FILTER_GOTO_GUIDE_LB",
            AR_SERVER_STAT_FILTER_FIELDS_SQL: "FILTER_FIELDS_SQL",
            AR_SERVER_STAT_FILTER_FIELDS_PROCESS: "FILTER_FIELDS_PROCESS",
            AR_SERVER_STAT_FILTER_FIELDS_FLTAPI: "FILTER_FIELDS_FLTAPI",
            AR_SERVER_STAT_ESCL_FIELDS_SQL: "ESCL_FIELDS_SQL",
            AR_SERVER_STAT_ESCL_FIELDS_PROCESS: "ESCL_FIELDS_PROCESS",
            AR_SERVER_STAT_ESCL_FIELDS_FLTAPI: "ESCL_FIELDS_FLTAPI"
        }
    
    ars_const['AR_FIELD_CREATE'] = {
        0 : 'UNKNOWN',
        AR_FIELD_OPEN_AT_CREATE: 'OPEN', 
        AR_FIELD_PROTECTED_AT_CREATE: 'PROTECTED'
    }
    ars_const['AR_ASSIGN_TYPE'] = {
            AR_ASSIGN_TYPE_NONE: "AR_ASSIGN_TYPE_NONE",
            AR_ASSIGN_TYPE_VALUE: "AR_ASSIGN_TYPE_VALUE",
            AR_ASSIGN_TYPE_FIELD: "AR_ASSIGN_TYPE_FIELD",
            AR_ASSIGN_TYPE_PROCESS: "AR_ASSIGN_TYPE_PROCESS",
            AR_ASSIGN_TYPE_ARITH: "AR_ASSIGN_TYPE_ARITH",
            AR_ASSIGN_TYPE_FUNCTION: "AR_ASSIGN_TYPE_FUNCTION",
            AR_ASSIGN_TYPE_DDE: "AR_ASSIGN_TYPE_DDE",
            AR_ASSIGN_TYPE_SQL: "AR_ASSIGN_TYPE_SQL",
            AR_ASSIGN_TYPE_FILTER_API: "AR_ASSIGN_TYPE_FILTER_API"
    }
    ars_const['AR_OPROP'] = {
            AR_OPROP_VENDOR_NAME: "VENDOR_NAME",
            AR_OPROP_VENDOR_PRODUCT: "VENDOR_PRODUCT",
            AR_OPROP_VENDOR_VERSION: "VENDOR_VERSION",
            AR_OPROP_GUID: "GUID",
            AR_OPROP_COPYRIGHT: "COPYRIGHT",
            AR_OPROP_SCC_LOCKED_BY: "SCC_LOCKED_BY",
            AR_OPROP_SCC_VERSION: "SCC_VERSION",
            AR_OPROP_SCC_TIMESTAMP: "SCC_TIMESTAMP",
            AR_OPROP_SCC_USER: "SCC_USER",
            AR_OPROP_SCC_LOCATION: "SCC_LOCATION",
            AR_OPROP_SCC_DATA_LOCKED_BY: "SCC_DATA_LOCKED_BY",
            AR_OPROP_SCC_DATA_VERSION: "SCC_DATA_VERSION",
            AR_OPROP_SCC_DATA_TIMESTAMP: "SCC_DATA_TIMESTAMP",
            AR_OPROP_SCC_DATA_USER: "SCC_DATA_USER",
            AR_OPROP_SCC_DATA_LOCATION: "SCC_DATA_LOCATION",
            AR_OPROP_WINDOW_OPEN_IF_SAMPLE_SERVER_SCHEMA: "WINDOW_OPEN_IF_SAMPLE_SERVER_SCHEMA",
            AR_OPROP_WINDOW_OPEN_ELSE_SAMPLE_SERVER_SCHEMA: "WINDOW_OPEN_ELSE_SAMPLE_SERVER_SCHEMA",
            AR_OPROP_FORM_NAME_WEB_ALIAS: "FORM_NAME_WEB_ALIAS",
            AR_OPROP_VIEW_LABEL_WEB_ALIAS: "VIEW_LABEL_WEB_ALIAS",
            AR_OPROP_APP_WEB_ALIAS: "APP_WEB_ALIAS",
            AR_OPROP_INTERVAL_VALUE: "INTERVAL_VALUE",
            AR_OPROP_INTEGRITY_KEY: "INTEGRITY_KEY"
    }
    ars_const['AR_SCHEMA'] = {
            AR_SCHEMA_NONE: "NONE",
            AR_SCHEMA_REGULAR: "REGULAR",
            AR_SCHEMA_JOIN: "JOIN",
            AR_SCHEMA_VIEW: "VIEW",
            AR_SCHEMA_DIALOG: "DIALOG",
            AR_SCHEMA_VENDOR: "VENDOR"
    }
    ars_const['AR_LIST_SCHEMA'] = {    
            AR_LIST_SCHEMA_ALL: "AR_LIST_SCHEMA_ALL",
            AR_LIST_SCHEMA_REGULAR: "AR_LIST_SCHEMA_REGULAR",
            AR_LIST_SCHEMA_JOIN: "AR_LIST_SCHEMA_JOIN",
            AR_LIST_SCHEMA_VIEW: "AR_LIST_SCHEMA_VIEW",
            AR_LIST_SCHEMA_UPLINK: "AR_LIST_SCHEMA_UPLINK",
            AR_LIST_SCHEMA_DOWNLINK: "AR_LIST_SCHEMA_DOWNLINK",
            AR_LIST_SCHEMA_DIALOG: "AR_LIST_SCHEMA_DIALOG",
            AR_LIST_SCHEMA_ALL_WITH_DATA: "AR_LIST_SCHEMA_ALL_WITH_DATA",
            AR_LIST_SCHEMA_VENDOR: "AR_LIST_SCHEMA_VENDOR"
    }
    ars_const['AR_ARITH_OP'] = {
            AR_ARITH_OP_ADD: "+",
            AR_ARITH_OP_SUBTRACT: "-",
            AR_ARITH_OP_MULTIPLY: "*",
            AR_ARITH_OP_DIVIDE: "/",
            AR_ARITH_OP_MODULO: "%",
            AR_ARITH_OP_NEGATE: "-"
    }
    ars_const['AR_LOC'] = {
            AR_LOC_NULL: "NULL",
            AR_LOC_FILENAME: "FILENAME",
            AR_LOC_BUFFER: "BUFFER"
    }
    ars_const['AR_REL_OP'] = {        
            AR_REL_OP_EQUAL: "==",
            AR_REL_OP_GREATER: ">",
            AR_REL_OP_GREATER_EQUAL: ">=",
            AR_REL_OP_LESS: "<",
            AR_REL_OP_LESS_EQUAL: "<=",
            AR_REL_OP_NOT_EQUAL: "!=",
            AR_REL_OP_LIKE: "LIKE",
            AR_REL_OP_IN: "IN"
    }
    ars_const['AR_COND_OP'] = {        
            AR_COND_OP_NONE: "AR_COND_OP_NONE",
            AR_COND_OP_AND: "AR_COND_OP_AND",
            AR_COND_OP_OR: "AR_COND_OP_OR",
            AR_COND_OP_NOT: "AR_COND_OP_NOT",
            AR_COND_OP_REL_OP: "AR_COND_OP_REL_OP",
            AR_COND_OP_FROM_FIELD: "AR_COND_OP_FROM_FIELD"
    }
    ars_const['ARCONOWNER'] = {
            ARCONOWNER_NONE: "NONE",
            ARCONOWNER_ALL: "ALL",
            ARCONOWNER_SCHEMA: "SCHEMA"
    }
    ars_const['ARREF_DATA'] = {
            ARREF_DATA_ARSREF: "ARSREF",
            ARREF_DATA_EXTREF: "EXTREF"
            }
    ars_const['ARREF'] = {
            ARREF_NONE: "NONE",
            ARREF_ALL: "ALL",
            ARREF_SCHEMA: "SCHEMA",
            ARREF_FILTER: "FILTER",
            ARREF_ESCALATION: "ESCALATION",
            ARREF_ACTLINK: "ACTLINK",
            ARREF_CONTAINER: "CONTAINER",
            ARREF_CHAR_MENU: "CHAR_MENU",
            ARREF_LAST_SERVER_OBJ: "LAST_SERVER_OBJ",
            ARREF_ICON: "ICON",
            ARREF_SMALL_ICON: "SMALL_ICON",
            ARREF_MAXIMIZE_FORMS: "MAXIMIZE_FORMS",
            ARREF_APPLICATION_FORMS: "APPLICATION_FORMS",
            ARREF_ABOUT_BOX_IMAGE: "ABOUT_BOX_IMAGE",
            ARREF_ABOUT_BOX_FORM: "ABOUT_BOX_FORM",
            ARREF_NULL_STRING: "NULL_STRING",
            ARREF_APPLICATION_HELP_EXT: "ARREF_APPLICATION_HELP_EXT",
            ARREF_APPLICATION_HELP_FILE: "ARREF_APPLICATION_HELP_FILE",
            ARREF_APPLICATION_PRIMARY_FORM: "ARREF_APPLICATION_PRIMARY_FORM",
            ARREF_APPLICATION_FORM_VUI: "ARREF_APPLICATION_FORM_VUI",
            ARREF_APPLICATION_DISABLE_BEGIN_TASK: "ARREF_APPLICATION_DISABLE_BEGIN_TASK",
            ARREF_APPLICATION_HELP_INDEX_EXT: "ARREF_APPLICATION_HELP_INDEX_EXT",
            ARREF_APPLICATION_HELP_INDEX_FILE: "ARREF_APPLICATION_HELP_INDEX_FILE",
            ARREF_APPLICATION_HELP_FILE_NAME: "ARREF_APPLICATION_HELP_FILE_NAME",
            ARREF_PACKINGLIST_GUIDE: "ARREF_PACKINGLIST_GUIDE",
            ARREF_PACKINGLIST_APP: "ARREF_PACKINGLIST_APP",
            ARREF_PACKINGLIST_PACK: "ARREF_PACKINGLIST_PACK",
            ARREF_GROUP_DATA: "ARREF_GROUP_DATA",
            ARREF_DISTMAPPING_DATA: "ARREF_DISTMAPPING_DATA",
            ARREF_APPLICATION_HAS_EXT_HELP: "ARREF_APPLICATION_HAS_EXT_HELP",
            ARREF_APPLICATION_SUPPORT_FILES: "ARREF_APPLICATION_SUPPORT_FILES",
            ARREF_PACKINGLIST_DSOPOOL: "ARREF_PACKINGLIST_DSOPOOL",
            ARREF_PACKINGLIST_FILTER_GUIDE: "ARREF_PACKINGLIST_FILTER_GUIDE",
            ARREF_FLASH_BOARD_DEF: "ARREF_FLASH_BOARD_DEF",
            ARREF_FLASH_DATA_SOURCE_DEF: "ARREF_FLASH_DATA_SOURCE_DEF",
            ARREF_FLASH_VARIABLE_DEF: "ARREF_FLASH_VARIABLE_DEF",
            ARREF_WS_PROPERTIES: "ARREF_WS_PROPERTIES",
            ARREF_WS_OPERATION: "ARREF_WS_OPERATION",
            ARREF_WS_ARXML_MAPPING: "ARREF_WS_ARXML_MAPPING",
            ARREF_WS_WSDL: "ARREF_WS_WSDL",
            ARREF_PACKINGLIST_WEBSERVICE: "ARREF_PACKINGLIST_WEBSERVICE",
            ARREF_WS_PUBLISHING_LOC: "ARREF_WS_PUBLISHING_LOC",
            ARREF_APPLICATION_HELP_FILE_NAME2: "ARREF_APPLICATION_HELP_FILE_NAME2",
            ARREF_APPLICATION_HELP_EXT2: "ARREF_APPLICATION_HELP_EXT2",
            ARREF_APPLICATION_HELP_FILE2: "ARREF_APPLICATION_HELP_FILE2",
            ARREF_APPLICATION_HELP_INDEX_EXT2: "ARREF_APPLICATION_HELP_INDEX_EXT2",
            ARREF_APPLICATION_HELP_INDEX_FILE2: "ARREF_APPLICATION_HELP_INDEX_FILE2",
            ARREF_APPLICATION_HELP_FILE_NAME3: "ARREF_APPLICATION_HELP_FILE_NAME3",
            ARREF_APPLICATION_HELP_EXT3: "ARREF_APPLICATION_HELP_EXT3",
            ARREF_APPLICATION_HELP_FILE3: "ARREF_APPLICATION_HELP_FILE3",
            ARREF_APPLICATION_HELP_INDEX_EXT3: "ARREF_APPLICATION_HELP_INDEX_EXT3",
            ARREF_APPLICATION_HELP_INDEX_FILE3: "ARREF_APPLICATION_HELP_INDEX_FILE3",
            ARREF_APPLICATION_HELP_FILE_NAME4: "ARREF_APPLICATION_HELP_FILE_NAME4",
            ARREF_APPLICATION_HELP_EXT4: "ARREF_APPLICATION_HELP_EXT4",
            ARREF_APPLICATION_HELP_FILE4: "ARREF_APPLICATION_HELP_FILE4",
            ARREF_APPLICATION_HELP_INDEX_EXT4: "ARREF_APPLICATION_HELP_INDEX_EXT4",
            ARREF_APPLICATION_HELP_INDEX_FILE4: "ARREF_APPLICATION_HELP_INDEX_FILE4",
            ARREF_APPLICATION_HELP_FILE_NAME5: "ARREF_APPLICATION_HELP_FILE_NAME5",
            ARREF_APPLICATION_HELP_EXT5: "ARREF_APPLICATION_HELP_EXT5",
            ARREF_APPLICATION_HELP_FILE5: "ARREF_APPLICATION_HELP_FILE5",
            ARREF_APPLICATION_HELP_INDEX_EXT5: "ARREF_APPLICATION_HELP_INDEX_EXT5",
            ARREF_APPLICATION_HELP_INDEX_FILE5: "ARREF_APPLICATION_HELP_INDEX_FILE5",
            ARREF_APPLICATION_HELP_LABEL: "ARREF_APPLICATION_HELP_LABEL",
            ARREF_APPLICATION_HELP_LABEL2: "ARREF_APPLICATION_HELP_LABEL2",
            ARREF_APPLICATION_HELP_LABEL3: "ARREF_APPLICATION_HELP_LABEL3",
            ARREF_APPLICATION_HELP_LABEL4: "ARREF_APPLICATION_HELP_LABEL4",
            ARREF_APPLICATION_HELP_LABEL5: "ARREF_APPLICATION_HELP_LABEL5",
            ARREF_WS_XML_SCHEMA_LOC: "ARREF_WS_XML_SCHEMA_LOC",
            ARREF_LAST_RESERVED: "ARREF_LAST_RESERVED"
            }
    ars_const['AR_FILTER_ACTION'] = {
            AR_FILTER_ACTION_NONE: "NONE",
            AR_FILTER_ACTION_NOTIFY: "NOTIFY",
            AR_FILTER_ACTION_MESSAGE: "MESSAGE",
            AR_FILTER_ACTION_LOG: "LOG",
            AR_FILTER_ACTION_FIELDS: "FIELDS",
            AR_FILTER_ACTION_PROCESS: "PROCESS",
            AR_FILTER_ACTION_FIELDP: "FIELDP",
            AR_FILTER_ACTION_SQL: "SQL",
            AR_FILTER_ACTION_GOTOACTION: "GOTOACTION",
            AR_FILTER_ACTION_CALLGUIDE: "CALLGUIDE",
            AR_FILTER_ACTION_EXITGUIDE: "EXITGUIDE",
            AR_FILTER_ACTION_GOTOGUIDELABEL: "GOTOGUIDELABEL"
            }
    ars_const['AR_ACTIVE_LINK_ACTION'] = {
            AR_ACTIVE_LINK_ACTION_NONE: "NONE",
            AR_ACTIVE_LINK_ACTION_MACRO: "MACRO",
            AR_ACTIVE_LINK_ACTION_FIELDS: "FIELDS",
            AR_ACTIVE_LINK_ACTION_PROCESS: "PROCESS",
            AR_ACTIVE_LINK_ACTION_MESSAGE: "MESSAGE",
            AR_ACTIVE_LINK_ACTION_SET_CHAR: "SET_CHAR",
            AR_ACTIVE_LINK_ACTION_DDE: "DDE",
            AR_ACTIVE_LINK_ACTION_FIELDP: "FIELDP",
            AR_ACTIVE_LINK_ACTION_SQL: "SQL",
            AR_ACTIVE_LINK_ACTION_AUTO: "AUTO",
            AR_ACTIVE_LINK_ACTION_OPENDLG: "OPENDLG",
            AR_ACTIVE_LINK_ACTION_COMMITC: "COMMITC",
            AR_ACTIVE_LINK_ACTION_CLOSEWND: "CLOSEWND",
            AR_ACTIVE_LINK_ACTION_CALLGUIDE: "CALLGUIDE",
            AR_ACTIVE_LINK_ACTION_EXITGUIDE: "EXITGUIDE",
            AR_ACTIVE_LINK_ACTION_GOTOGUIDELABEL: "GOTOGUIDELABEL",
            AR_ACTIVE_LINK_ACTION_WAIT: "WAIT",
            AR_ACTIVE_LINK_ACTION_GOTOACTION: "GOTOACTION"
        }
    ars_const['AR_ACTIVE_LINK_ACTION_OPEN'] = {
            AR_ACTIVE_LINK_ACTION_OPEN_DLG: "DLG",
            AR_ACTIVE_LINK_ACTION_OPEN_SEARCH: "OPEN_SEARCH",
            AR_ACTIVE_LINK_ACTION_OPEN_SUBMIT: "SUBMIT",
            AR_ACTIVE_LINK_ACTION_OPEN_MODIFY_LST: "MODIFY_LST",
            AR_ACTIVE_LINK_ACTION_OPEN_MODIFY_DETAIL: "MODIFY_DETAIL",
            AR_ACTIVE_LINK_ACTION_OPEN_MODIFY_SPLIT: "MODIFY_SPLIT",
            AR_ACTIVE_LINK_ACTION_OPEN_DSPLY_LST: "DSPLY_LST",
            AR_ACTIVE_LINK_ACTION_OPEN_DSPLY_DETAIL: "DSPLY_DETAIL",
            AR_ACTIVE_LINK_ACTION_OPEN_DSPLY_SPLIT: "DSPLY_SPLIT",
            AR_ACTIVE_LINK_ACTION_OPEN_REPORT: "REPORT"
        }
    ars_const['AR_EXECUTE_ON'] = {
            AR_EXECUTE_ON_NONE: "NONE",
            AR_EXECUTE_ON_BUTTON: "BUTTON",
            AR_EXECUTE_ON_RETURN: "RETURN",
            AR_EXECUTE_ON_SUBMIT: "SUBMIT",
            AR_EXECUTE_ON_MODIFY: "MODIFY",
            AR_EXECUTE_ON_DISPLAY: "DISPLAY",
            AR_EXECUTE_ON_MODIFY_ALL: "MODIFY_ALL",
            AR_EXECUTE_ON_MENU_OPEN: "MENU_OPEN",
            AR_EXECUTE_ON_MENU_CHOICE: "MENU_CHOICE",
            AR_EXECUTE_ON_LOSE_FOCUS: "LOSE_FOCUS",
            AR_EXECUTE_ON_SET_DEFAULT: "SET_DEFAULT",
            AR_EXECUTE_ON_QUERY: "QUERY",
            AR_EXECUTE_ON_AFTER_MODIFY: "AFTER_MODIFY",
            AR_EXECUTE_ON_AFTER_SUBMIT: "AFTER_SUBMIT",
            AR_EXECUTE_ON_GAIN_FOCUS: "GAIN_FOCUS",
            AR_EXECUTE_ON_WINDOW_OPEN: "WINDOW_OPEN",
            AR_EXECUTE_ON_WINDOW_CLOSE: "WINDOW_CLOSE",
            AR_EXECUTE_ON_UNDISPLAY: "UNDISPLAY",
            AR_EXECUTE_ON_COPY_SUBMIT: "COPY_SUBMIT",
            AR_EXECUTE_ON_LOADED: "LOADED",
            AR_EXECUTE_ON_INTERVAL: "INTERVAL"
        }
    ars_const['AR_SORT'] = {
        AR_SORT_ASCENDING: "ASCENDING",
        AR_SORT_DESCENDING: "DESCENDING"
    }
    ars_const['AR_PERMISSIONS'] = {
            AR_PERMISSIONS_NONE: "NONE",
            AR_PERMISSIONS_VISIBLE: "VISIBLE",
            AR_PERMISSIONS_HIDDEN: "HIDDEN",
            AR_PERMISSIONS_VIEW: "VIEW",
            AR_PERMISSIONS_CHANGE: "CHANGE"
        }
    
    # don't change the strings in the following dictionary
    # unless you know what you do!!!!
    # each string will be used in a following dictionary
    # to associate the appropriate AR_DVAL to the AR_DPROP!
    
    ars_const['AR_DPROP'] = {
            AR_DPROP_NONE: "NONE",
            AR_DPROP_TRIM_TYPE: "TRIM_TYPE",
            AR_DPROP_CNTL_TYPE: "CNTL_TYPE",
            AR_FIXED_POINT_PRECISION: "AR_FIXED_POINT_PRECISION",
            AR_DPROP_BBOX: "BBOX",
            AR_DPROP_VISIBLE: "VISIBLE",
            AR_DPROP_ENABLE: "ENABLE",
            AR_DPROP_HELP: "HELP",
            AR_DPROP_Z_ORDER: "Z_ORDER",
            AR_DPROP_COLOR_FILL: "COLOR_FILL",
            AR_DPROP_DEPTH_EFFECT: "DEPTH_EFFECT",
            AR_DPROP_DEPTH_AMOUNT: "DEPTH_AMOUNT",
            AR_DPROP_COLOR_LINE: "COLOR_LINE",
            AR_DPROP_COLOR_TEXT: "COLOR_TEXT",
            AR_DPROP_PROMPT: "PROMPT",
            AR_DPROP_HIDE_WEBHELP: "HIDE_WEBHELP",
            AR_DPROP_LABEL: "LABEL",
            AR_DPROP_LABEL_BBOX: "LABEL_BBOX",
            AR_DPROP_LABEL_FONT_STYLE: "LABEL_FONT_STYLE",
            AR_DPROP_LABEL_FONT_SIZE: "LABEL_FONT_SIZE",
            AR_DPROP_LABEL_COLOR_TEXT: "LABEL_COLOR_TEXT",
            AR_DPROP_LABEL_JUSTIFY: "LABEL_JUSTIFY",
            AR_DPROP_LABEL_ALIGN: "LABEL_ALIGN",
            AR_DPROP_LABEL_POS_SECTOR: "LABEL_POS_SECTOR",
            AR_DPROP_LABEL_POS_JUSTIFY: "LABEL_POS_JUSTIFY",
            AR_DPROP_LABEL_POS_ALIGN: "LABEL_POS_ALIGN",
            AR_DPROP_LABEL_COLOR_FILL: "LABEL_COLOR_FILL",
            AR_DPROP_LABEL_COLOR_LINE: "LABEL_COLOR_LINE",
            AR_DPROP_COORDS: "COORDS",
            AR_DPROP_LINE_WIDTH: "LINE_WIDTH",
            AR_DPROP_LINE_PATTERN: "LINE_PATTERN",
            AR_DPROP_JOINT_STYLE: "JOINT_STYLE",
            AR_DPROP_ENDCAP_START: "ENDCAP_START",
            AR_DPROP_ENDCAP_END: "ENDCAP_END",
            AR_DPROP_DATA_ROWS: "DATA_ROWS",
            AR_DPROP_DATA_COLS: "DATA_COLS",
            AR_DPROP_DATA_SPIN: "DATA_SPIN",
            AR_DPROP_DATA_MENU: "DATA_MENU",
            AR_DPROP_DATA_RADIO: "DATA_RADIO",
            AR_DPROP_DATA_MENU_BBOX: "DATA_MENU_BBOX",
            AR_DPROP_DATA_EXPAND_BBOX: "DATA_EXPAND_BBOX",
            AR_DPROP_TEXT: "TEXT",
            AR_DPROP_TEXT_FONT_STYLE: "TEXT_FONT_STYLE",
            AR_DPROP_TEXT_FONT_SIZE: "TEXT_FONT_SIZE",
            AR_DPROP_HTML_TEXT: "HTML_TEXT",
            AR_DPROP_HTML_TEXT_COLOR: "HTML_TEXT_COLOR",
            AR_DPROP_JUSTIFY: "JUSTIFY",
            AR_DPROP_ALIGN: "ALIGN",
            AR_DPROP_IMAGE: "IMAGE",
            AR_DPROP_PUSH_BUTTON_IMAGE: "PUSH_BUTTON_IMAGE",
            AR_DPROP_BUTTON_TEXT: "BUTTON_TEXT",
            AR_DPROP_BUTTON_2D: "BUTTON_2D",
            AR_DPROP_BUTTON_IMAGE_POSITION: "BUTTON_IMAGE_POSITION",
            AR_DPROP_BUTTON_SCALE_IMAGE: "BUTTON_SCALE_IMAGE",
            AR_DPROP_BUTTON_MAINTAIN_RATIO: "BUTTON_MAINTAIN_RATIO",
            AR_DPROP_MENU_TEXT: "MENU_TEXT",
            AR_DPROP_MENU_POS: "MENU_POS",
            AR_DPROP_MENU_MODE: "MENU_MODE",
            AR_DPROP_MENU_PARENT: "MENU_PARENT",
            AR_DPROP_MENU_HELP: "MENU_HELP",
            AR_DPROP_TOOLTIP: "TOOLTIP",
            AR_DPROP_TOOLBAR_POS: "TOOLBAR_POS",
            AR_DPROP_TOOLBAR_MODE: "TOOLBAR_MODE",
            AR_DPROP_TOOLBAR_TEXT: "TOOLBAR_TEXT",
            AR_DPROP_TAB_MODE: "TAB_MODE",
            AR_DPROP_TAB_COORD: "TAB_COORD",
            AR_DPROP_TAB_TEXT: "TAB_TEXT",
            AR_DPROP_TAB_ORDER: "TAB_ORDER",
            AR_DPROP_DATETIME_POPUP: "DATETIME_POPUP",
            AR_DPROP_BACKGROUND_MODE: "BACKGROUND_MODE",
            AR_DPROP_TAB_NEXT: "TAB_NEXT",
            AR_DPROP_DATA_BBOX: "DATA_BBOX",
            AR_DPROP_VIEW_GRID_BBOX: "VIEW_GRID_BBOX",
            AR_DPROP_VUI_DEFAULT: "VUI_DEFAULT",
            AR_DPROP_PANE_LAYOUT: "PANE_LAYOUT",
            AR_DPROP_DETAIL_PANE_VISIBILITY: "DETAIL_PANE_VISIBILITY",
            AR_DPROP_PROMPT_PANE_VISIBILITY: "PROMPT_PANE_VISIBILITY",
            AR_DPROP_RESULT_PANE_VISIBILITY: "RESULT_PANE_VISIBILITY",
            AR_DPROP_DETAIL_PANE_COLOR: "DETAIL_PANE_COLOR",
            AR_DPROP_DETAIL_PANE_IMAGE: "DETAIL_PANE_IMAGE",
            AR_DPROP_IMAGE_ALIGN: "IMAGE_ALIGN",
            AR_DPROP_IMAGE_JUSTIFY: "IMAGE_JUSTIFY",
            AR_DPROP_DISPLAY_PARENT: "DISPLAY_PARENT",
            AR_DPROP_PAGE_ORDER: "PAGE_ORDER",
            AR_DPROP_PAGE_LABEL_DISPLAY: "PAGE_LABEL_DISPLAY",
            AR_DPROP_PAGE_ARRANGEMENT: "PAGE_ARRANGEMENT",
            AR_DPROP_DEFAULT_PAGE: "DEFAULT_PAGE",
            AR_DPROP_TITLE_BAR_ICON_IMAGE: "TITLE_BAR_ICON_IMAGE",
            AR_DPROP_DETAIL_PANE_WIDTH: "DETAIL_PANE_WIDTH",
            AR_DPROP_DETAIL_PANE_HEIGHT: "DETAIL_PANE_HEIGHT",
            AR_DPROP_DETAIL_BANNER_VISIBILITY: "DETAIL_BANNER_VISIBILITY",
            AR_DPROP_PROMPT_BANNER_VISIBILITY: "PROMPT_BANNER_VISIBILITY",
            AR_DPROP_RESULT_BANNER_VISIBILITY: "RESULT_BANNER_VISIBILITY",
            AR_DPROP_ALIAS_SINGULAR: "ALIAS_SINGULAR",
            AR_DPROP_ALIAS_PLURAL: "ALIAS_PLURAL",
            AR_DPROP_ALIAS_SHORT_SINGULAR: "ALIAS_SHORT_SINGULAR",
            AR_DPROP_ALIAS_SHORT_PLURAL: "ALIAS_SHORT_PLURAL",
            AR_DPROP_ALIAS_ABBREV_SINGULAR: "ALIAS_ABBREV_SINGULAR",
            AR_DPROP_ALIAS_ABBREV_PLURAL: "ALIAS_ABBREV_PLURAL",
            AR_DPROP_NAMED_SEARCHES: "NAMED_SEARCHES",
            AR_DPROP_MENU_ACCESS: "MENU_ACCESS",
            AR_DPROP_PANE_VISIBILITY_OPTION: "PANE_VISIBILITY_OPTION",
            AR_DPROP_REQUEST_IDENTIFIER: "REQUEST_IDENTIFIER",
            AR_DPROP_QUERY_LIST_COLOR: "QUERY_LIST_COLOR",
            AR_DPROP_COLUMN_WIDTH: "COLUMN_WIDTH",
            AR_DPROP_COLUMN_ORDER: "COLUMN_ORDER",
            AR_DPROP_SORT_SEQ: "SORT_SEQ",
            AR_DPROP_SORT_DIR: "SORT_DIR",
            AR_DPROP_DRILL_DOWN: "DRILL_DOWN",
            AR_DPROP_REFRESH: "REFRESH",
            AR_DPROP_AUTO_REFRESH: "AUTO_REFRESH",
            AR_DPROP_AUTOFIT_COLUMNS: "AUTOFIT_COLUMNS",
            AR_DPROP_APPLY_DIRTY: "APPLY_DIRTY",
            AR_DPROP_IMAGE_CACHE: "IMAGE_CACHE",
            AR_DPROP_ENUM_LABELS: "ENUM_LABELS",
            AR_DPROP_MANAGE_EXPAND_BOX: "MANAGE_EXPAND_BOX",
            AR_DPROP_ATTACH_ADD_LABEL: "ATTACH_ADD_LABEL",
            AR_DPROP_ATTACH_DELETE_LABEL: "ATTACH_DELETE_LABEL",
            AR_DPROP_ATTACH_DISPLAY_LABEL: "ATTACH_DISPLAY_LABEL",
            AR_DPROP_ATTACH_SAVE_LABEL: "ATTACH_SAVE_LABEL",
            AR_DPROP_ATTACH_LABEL_TITLE: "ATTACH_LABEL_TITLE",
            AR_DPROP_ATTACH_FILENAME_TITLE: "ATTACH_FILENAME_TITLE",
            AR_DPROP_ATTACH_FILESIZE_TITLE: "ATTACH_FILESIZE_TITLE",
            AR_DPROP_HIDE_PAGE_TABS_BORDERS: "HIDE_PAGE_TABS_BORDERS",
            AR_DPROP_DISPLAY_AS_TEXT_ONLY: "DISPLAY_AS_TEXT_ONLY",
            AR_DPROP_AR_OBJECT_NAME: "AR_OBJECT_NAME",
            AR_DPROP_DISPLAY_FIELD_APP: "DISPLAY_FIELD_APP",
            AR_DPROP_ZERO_SIZE_WHEN_HIDDEN: "ZERO_SIZE_WHEN_HIDDEN",
            AR_DPROP_ACCESSIBLE_HINT: "ACCESSIBLE_HINT",
            AR_DPROP_INITIAL_CURRENCY_TYPE: "INITIAL_CURRENCY_TYPE",
            AR_DPROP_TABLE_DISPLAY_TYPE: "TABLE_DISPLAY_TYPE",
            AR_DPROP_TABLE_SELINIT: "TABLE_SELINIT",
            AR_DPROP_TABLE_SELREFRESH: "TABLE_SELREFRESH",
            AR_DPROP_TABLE_CHUNK_SIZE: "TABLE_CHUNK_SIZE",
            AR_DPROP_TABLE_CHUNK_NEXT: "TABLE_CHUNK_NEXT",
            AR_DPROP_TABLE_CHUNK_PREV: "TABLE_CHUNK_PREV",
            AR_DPROP_TABLE_NOT_REFRESHED: "TABLE_NOT_REFRESHED",
            AR_DPROP_TABLE_ENTRIES_RETURNED: "TABLE_ENTRIES_RETURNED",
            AR_DPROP_TABLE_AUTOREFRESH: "TABLE_AUTOREFRESH",
            AR_DPROP_TABLE_DRILL_COL: "TABLE_DRILL_COL",
            AR_DPROP_TABLE_SELROWS_DISABLE: "TABLE_SELROWS_DISABLE",
            AR_DPROP_TABLE_SELECT_ALL: "TABLE_SELECT_ALL",
            AR_DPROP_TABLE_DESELECT_ALL: "TABLE_DESELECT_ALL",
            AR_DPROP_TABLE_REFRESH: "TABLE_REFRESH",
            AR_DPROP_TABLE_REPORT: "TABLE_REPORT",
            AR_DPROP_TABLE_DELETE: "TABLE_DELETE",
            AR_DPROP_TABLE_READ: "TABLE_READ",
            AR_DPROP_TABLE_UNREAD: "TABLE_UNREAD",
            AR_DPROP_TABLE_SELECTIONCOLUMN_LABEL: "TABLE_SELECTIONCOLUMN_LABEL",
            AR_DPROP_TABLE_COL_DISPLAY_TYPE: "TABLE_COL_DISPLAY_TYPE",
            AR_DPROP_TABLE_COL_INITVAL: "TABLE_COL_INITVAL",
            AR_DPROP_FIXED_TABLE_HEADERS: "FIXED_TABLE_HEADERS"
    }
    # the following AR_DVAL* dictionaries can all be looked up by the
    # according AR_DPROP string! As those strings do not necessarily match
    # the prefix of the AR_DVAL entities, there is a slight mismatch between the two
    
    ars_const['AR_DPROP']['AR_DPROP_TRIM_TYPE'] = {
            AR_DVAL_TRIM_NONE: "TRIM_NONE",
            AR_DVAL_TRIM_LINE: "TRIM_LINE",
            AR_DVAL_TRIM_SHAPE: "TRIM_SHAPE",
            AR_DVAL_TRIM_TEXT: "TRIM_TEXT",
            AR_DVAL_TRIM_IMAGE: "TRIM_IMAGE"
            }
    ars_const['AR_DPROP']['AR_DPROP_CNTL_TYPE'] = {
            AR_DVAL_CNTL_BUTTON: "CNTL_BUTTON",
            AR_DVAL_CNTL_MENU: "CNTL_MENU",
            AR_DVAL_CNTL_TOOLBAR: "CNTL_TOOLBAR",
            AR_DVAL_CNTL_TAB_SWITCH: "CNTL_TAB_SWITCH",
            AR_DVAL_CNTL_URL: "CNTL_URL",
            AR_DVAL_CNTL_CHART: "CNTL_CHART",
            AR_DVAL_CNTL_METER: "CNTL_METER"
            }
    ars_const['AR_DPROP']['AR_DPROP_ENABLE'] = {
            AR_DVAL_ENABLE_DEFAULT: "ENABLE_DEFAULT",
            AR_DVAL_ENABLE_READ_ONLY: "ENABLE_READ_ONLY",
            AR_DVAL_ENABLE_READ_WRITE: "ENABLE_READ_WRITE",
            AR_DVAL_ENABLE_DISABLE: "ENABLE_DISABLE"
            }
    ars_const['AR_DPROP']['AR_DPROP_COLOR_FILL'] = {
            AR_DVAL_COLOR_NONE: "COLOR_NONE",
            AR_DVAL_COLOR_BG: "COLOR_BG",
            AR_DVAL_COLOR_FG: "COLOR_FG",
            AR_DVAL_COLOR_EDIT_BG: "COLOR_EDIT_BG",
            AR_DVAL_COLOR_EDIT_FG: "COLOR_EDIT_FG",
            AR_DVAL_COLOR_FOCUS: "COLOR_FOCUS",
            AR_DVAL_COLOR_INSET1: "COLOR_INSET1",
            AR_DVAL_COLOR_INSET2: "COLOR_INSET2"
            }
    ars_const['AR_DPROP']['AR_DPROP_DEPTH_EFFECT'] = {
            AR_DVAL_DEPTH_EFFECT_FLAT: "DEPTH_EFFECT_FLAT",
            AR_DVAL_DEPTH_EFFECT_RAISED: "DEPTH_EFFECT_RAISED",
            AR_DVAL_DEPTH_EFFECT_SUNKEN: "DEPTH_EFFECT_SUNKEN",
            AR_DVAL_DEPTH_EFFECT_FLOATING: "DEPTH_EFFECT_FLOATING",
            AR_DVAL_DEPTH_EFFECT_ETCHED: "DEPTH_EFFECT_ETCHED"
            }
    ars_const['AR_DPROP']['AR_DPROP_LABEL_JUSTIFY'] = {
            AR_DVAL_JUSTIFY_DEFAULT: "JUSTIFY_DEFAULT",
            AR_DVAL_JUSTIFY_LEFT: "JUSTIFY_LEFT",
            AR_DVAL_JUSTIFY_CENTER: "JUSTIFY_CENTER",
            AR_DVAL_JUSTIFY_FILL: "JUSTIFY_FILL",
            AR_DVAL_JUSTIFY_RIGHT: "JUSTIFY_RIGHT",
            AR_DVAL_JUSTIFY_TILE: "JUSTIFY_TILE"
            }
    ars_const['AR_DPROP']['AR_DPROP_LABEL_POS_JUSTIFY'] = {
            AR_DVAL_JUSTIFY_DEFAULT: "JUSTIFY_DEFAULT",
            AR_DVAL_JUSTIFY_LEFT: "JUSTIFY_LEFT",
            AR_DVAL_JUSTIFY_CENTER: "JUSTIFY_CENTER",
            AR_DVAL_JUSTIFY_FILL: "JUSTIFY_FILL",
            AR_DVAL_JUSTIFY_RIGHT: "JUSTIFY_RIGHT",
            AR_DVAL_JUSTIFY_TILE: "JUSTIFY_TILE"
            }
    ars_const['AR_DPROP']['AR_DPROP_JUSTIFY'] = {
            AR_DVAL_JUSTIFY_DEFAULT: "JUSTIFY_DEFAULT",
            AR_DVAL_JUSTIFY_LEFT: "JUSTIFY_LEFT",
            AR_DVAL_JUSTIFY_CENTER: "JUSTIFY_CENTER",
            AR_DVAL_JUSTIFY_FILL: "JUSTIFY_FILL",
            AR_DVAL_JUSTIFY_RIGHT: "JUSTIFY_RIGHT",
            AR_DVAL_JUSTIFY_TILE: "JUSTIFY_TILE"
            }
    ars_const['AR_DPROP']['AR_DPROP_LABEL_ALIGN'] = {
            AR_DVAL_ALIGN_DEFAULT: "ALIGN_DEFAULT",
            AR_DVAL_ALIGN_TOP: "ALIGN_TOP",
            AR_DVAL_ALIGN_MIDDLE: "ALIGN_MIDDLE",
            AR_DVAL_ALIGN_FILL: "ALIGN_FILL",
            AR_DVAL_ALIGN_BOTTOM: "ALIGN_BOTTOM",
            AR_DVAL_ALIGN_TILE: "ALIGN_TILE"
            }
    ars_const['AR_DPROP']['AR_DPROP_LABEL_POS_SECTOR'] = {
            AR_DVAL_SECTOR_NONE: "SECTOR_NONE",
            AR_DVAL_SECTOR_CENTER: "SECTOR_CENTER",
            AR_DVAL_SECTOR_NORTH: "SECTOR_NORTH",
            AR_DVAL_SECTOR_EAST: "SECTOR_EAST",
            AR_DVAL_SECTOR_SOUTH: "SECTOR_SOUTH",
            AR_DVAL_SECTOR_WEST: "SECTOR_WEST"
    }
    ars_const['AR_DPROP']['AR_DPROP_JOINT_STYLE'] = {
            AR_DVAL_JOINT_EXTENDED: "JOINT_EXTENDED",
            AR_DVAL_JOINT_SHARP: "JOINT_SHARP",
            AR_DVAL_JOINT_ROUNDED: "JOINT_ROUNDED",
            AR_DVAL_JOINT_SMOOTH: "JOINT_SMOOTH",
            AR_DVAL_JOINT_MAX_SMOOTH: "JOINT_MAX_SMOOTH"
    }
    ars_const['AR_DPROP']['AR_DPROP_ENDCAP_END'] = {
            AR_DVAL_ENDCAP_ROUND: "ENDCAP_ROUND",
            AR_DVAL_ENDCAP_FLUSH: "ENDCAP_FLUSH",
            AR_DVAL_ENDCAP_EXTENDED: "ENDCAP_EXTENDED",
            AR_DVAL_ENDCAP_ARROW1: "ENDCAP_ARROW1"
    }
    ars_const['AR_DPROP']['AR_DPROP_DATA_RADIO'] = {
            AR_DVAL_RADIO_DROPDOWN: "RADIO_DROPDOWN",
            AR_DVAL_RADIO_RADIO: "RADIO_RADIO",
            AR_DVAL_RADIO_CHECKBOX: "RADIO_CHECKBOX"
    }
    ars_const['AR_DPROP']['AR_DPROP_BUTTON_IMAGE_POSITION'] = {
            AR_DVAL_IMAGE_CENTER: "IMAGE_CENTER",
            AR_DVAL_IMAGE_LEFT: "IMAGE_LEFT",
            AR_DVAL_IMAGE_RIGHT: "IMAGE_RIGHT",
            AR_DVAL_IMAGE_ABOVE: "IMAGE_ABOVE",
            AR_DVAL_IMAGE_BELOW: "IMAGE_BELOW"
    }
    ars_const['AR_DPROP']['AR_DPROP_MENU_MODE'] = {
            AR_DVAL_CNTL_ITEM: "CNTL_ITEM",
            AR_DVAL_CNTL_ON: "CNTL_ON",
            AR_DVAL_CNTL_SEPARATOR: "CNTL_SEPARATOR",
            AR_DVAL_CNTL_CHOICE: "CNTL_CHOICE",
            AR_DVAL_CNTL_DIALOG: "CNTL_DIALOG",
            AR_DVAL_CNTL_A_MENU: "CNTL_A_MENU"
    }
    ars_const['AR_DPROP']['AR_DPROP_DATETIME_POPUP'] = {
            AR_DVAL_DATETIME_BOTH: "DATETIME_BOTH",
            AR_DVAL_DATETIME_TIME: "DATETIME_TIME",
            AR_DVAL_DATETIME_DATE: "DATETIME_DATE"
    }
    ars_const['AR_DPROP']['AR_DPROP_BACKGROUND_MODE'] = {
            AR_DVAL_BKG_MODE_OPAQUE: "BKG_MODE_OPAQUE",
            AR_DVAL_BKG_MODE_TRANSPARENT: "BKG_MODE_TRANSPARENT"
    }
    ars_const['AR_DPROP']['AR_DPROP_DETAIL_PANE_VISIBILITY'] = {
            AR_DVAL_PANE_ALWAYS_HIDDEN: "PANE_ALWAYS_HIDDEN",
            AR_DVAL_PANE_HIDDEN: "PANE_HIDDEN",
            AR_DVAL_PANE_VISIBLE: "PANE_VISIBLE",
            AR_DVAL_PANE_ALWAYS_VISIBLE: "PANE_ALWAYS_VISIBLE"
    }
    ars_const['AR_DPROP']['AR_DPROP_PAGE_LABEL_DISPLAY'] = {
            AR_DVAL_PAGE_DISPLAY_TOP: "PAGE_DISPLAY_TOP",
            AR_DVAL_PAGE_DISPLAY_BOTTOM: "PAGE_DISPLAY_BOTTOM",
            AR_DVAL_PAGE_DISPLAY_LEFT: "PAGE_DISPLAY_LEFT",
            AR_DVAL_PAGE_DISPLAY_RIGHT: "PAGE_DISPLAY_RIGHT",
            AR_DVAL_PAGE_DISPLAY_NONE: "PAGE_DISPLAY_NONE"
    }
    ars_const['AR_DPROP']['AR_DPROP_PAGE_ARRANGEMENT'] = {
            AR_DVAL_PAGE_SCROLL: "PAGE_SCROLL",
            AR_DVAL_PAGE_LAYER: "PAGE_LAYER"
    }
    ars_const['AR_DPROP']['AR_DPROP_PANE_VISIBILITY_OPTION'] = {
            AR_DVAL_PANE_VISIBILITY_USER_CHOICE: "PANE_VISIBILITY_USER_CHOICE",
            AR_DVAL_PANE_VISIBILITY_ADMIN: "PANE_VISIBILITY_ADMIN"
    }
    ars_const['AR_DPROP']['AR_DPROP_SORT_DIR'] = {
            AR_DVAL_SORT_DIR_ASCENDING: "SORT_DIR_ASCENDING",
            AR_DVAL_SORT_DIR_DESCENDING: "SORT_DIR_DESCENDING"
    }
    ars_const['AR_DPROP']['AR_DPROP_DRILL_DOWN'] = {
            AR_DVAL_DRILL_DOWN_NONE: "DRILL_DOWN_NONE",
            AR_DVAL_DRILL_DOWN_ENABLE: "DRILL_DOWN_ENABLE"
    }
    ars_const['AR_DPROP']['AR_DPROP_REFRESH'] = {
            AR_DVAL_REFRESH_NONE: "REFRESH_NONE",
            AR_DVAL_REFRESH_TABLE_MAX: "REFRESH_TABLE_MAX"
    }
    ars_const['AR_DPROP']['AR_DPROP_AUTO_REFRESH'] = {
            AR_DVAL_AUTO_REFRESH_NONE: "AUTO_REFRESH_NONE",
            AR_DVAL_AUTO_REFRESH_TABLE_MAX: "AUTO_REFRESH_TABLE_MAX"
    }
    ars_const['AR_DPROP']['AR_DPROP_AUTOFIT_COLUMNS'] = {
            AR_DVAL_AUTOFIT_COLUMNS_NONE: "AUTOFIT_COLUMNS_NONE",
            AR_DVAL_AUTOFIT_COLUMNS_SET: "AUTOFIT_COLUMNS_SET"
    }
    ars_const['AR_DPROP']['AR_DPROP_MANAGE_EXPAND_BOX'] = {
            AR_DVAL_EXPAND_BOX_DEFAULT: "EXPAND_BOX_DEFAULT",
            AR_DVAL_EXPAND_BOX_HIDE: "EXPAND_BOX_HIDE",
            AR_DVAL_EXPAND_BOX_SHOW: "EXPAND_BOX_SHOW"
    }
    ars_const['AR_DPROP']['AR_DPROP_TABLE_DISPLAY_TYPE'] = {
            AR_DVAL_TABLE_DISPLAY_TABLE: "TABLE_DISPLAY_TABLE",
            AR_DVAL_TABLE_DISPLAY_RESULTS_LIST: "TABLE_DISPLAY_RESULTS_LIST",
            AR_DVAL_TABLE_DISPLAY_NOTIFICATION: "TABLE_DISPLAY_NOTIFICATION"
    }
    ars_const['AR_DPROP']['AR_DPROP_TABLE_COL_DISPLAY_TYPE'] = {
            AR_DVAL_TABLE_COL_DISPLAY_NONEDITABLE: "DISPLAY_NONEDITABLE",
            AR_DVAL_TABLE_COL_DISPLAY_EDITABLE: "DISPLAY_EDITABLE",
            AR_DVAL_TABLE_COL_DISPLAY_HTML: "DISPLAY_HTML"
    }
    ars_const['AR_DPROP']['AR_DPROP_TABLE_SELINIT'] = {
            AR_DVAL_TABLE_SELINIT_SELFIRE: "TABLE_SELINIT_SELFIRE",
            AR_DVAL_TABLE_SELINIT_SELNOFIRE: "TABLE_SELINIT_SELNOFIRE",
            AR_DVAL_TABLE_SELINIT_NOSEL: "TABLE_SELINIT_NOSEL"
    }
    ars_const['AR_DPROP']['AR_DPROP_TABLE_SELREFRESH'] = {
            AR_DVAL_TABLE_SELREFRESH_RETFIRE: "TABLE_SELREFRESH_RETFIRE",
            AR_DVAL_TABLE_SELREFRESH_RETNOFIRE: "TABLE_SELREFRESH_RETNOFIRE",
            AR_DVAL_TABLE_SELREFRESH_FIRSTFIRE: "TABLE_SELREFRESH_FIRSTFIRE",
            AR_DVAL_TABLE_SELREFRESH_FIRSTNOFIRE: "TABLE_SELREFRESH_FIRSTNOFIRE",
            AR_DVAL_TABLE_SELREFRESH_NOSEL: "TABLE_SELREFRESH_NOSEL"
    }
    ars_const['AR_DPROP']['AR_DPROP_TABLE_SELROWS_DISABLE'] = {
            AR_DVAL_TABLE_SELROWS_MULTI_SELECT: "TABLE_SELROWS_MULTI_SELECT",
            AR_DVAL_TABLE_SELROWS_DISABLE_YES: "TABLE_SELROWS_DISABLE_YES",
            AR_DVAL_TABLE_SELROWS_SINGLE_SELECT: "TABLE_SELROWS_SINGLE_SELECT",
            AR_DVAL_TABLE_SELROWS_DISABLE_NO: "TABLE_SELROWS_DISABLE_NO" # marked as obsolete
    }
    ars_const['AR_FIELD_TYPE'] = {
            AR_FIELD_TYPE_DATA: "Data",
            AR_FIELD_TYPE_TRIM: "Trim",
            AR_FIELD_TYPE_CONTROL: "Control",
            AR_FIELD_TYPE_PAGE: "Page",
            AR_FIELD_TYPE_PAGE_HOLDER: "Page Holder",
            AR_FIELD_TYPE_TABLE: "Table",
            AR_FIELD_TYPE_COLUMN: "Column",
            AR_FIELD_TYPE_ATTACH: "Attachment",
            AR_FIELD_TYPE_ATTACH_POOL: "Attachment Pool",
            AR_FIELD_TYPE_ALL: "AR_FIELD_TYPE_ALL"
        }
    ars_const['AR_DPROP_TABLE_COL_DISPLAY_TYPE'] = {
            AR_DVAL_TABLE_COL_DISPLAY_NONEDITABLE: "TABLE_COL_DISPLAY_NONEDITABLE",
            AR_DVAL_TABLE_COL_DISPLAY_EDITABLE: "TABLE_COL_DISPLAY_EDITABLE",
            AR_DVAL_TABLE_COL_DISPLAY_HTML: "TABLE_COL_DISPLAY_HTML"
    }
    ars_const['AR_DPROP_FIXED_TABLE_HEADERS'] = {
            AR_DVAL_FIXED_TABLE_HEADERS_DISABLE: "FIXED_TABLE_HEADERS_DISABLE",
            AR_DVAL_FIXED_TABLE_HEADERS_ENABLE: "FIXED_TABLE_HEADERS_ENABLE"
    }
    ars_const['AR_KEYWORD'] = {
            AR_KEYWORD_DEFAULT: "$DEFAULT$",
            AR_KEYWORD_USER: "$USER$",
            AR_KEYWORD_TIMESTAMP: "$TIMESTAMP$",
            AR_KEYWORD_TIME_ONLY: "$TIME$",
            AR_KEYWORD_DATE_ONLY: "$DATE$",
            AR_KEYWORD_SCHEMA: "$SCHEMA$",
            AR_KEYWORD_SERVER: "$SERVER$",
            AR_KEYWORD_WEEKDAY: "$WEEKDAY$",
            AR_KEYWORD_GROUPS: "$GROUPS$",
            AR_KEYWORD_OPERATION: "$OPERATION$",
            AR_KEYWORD_HARDWARE: "$HARDWARE$",
            AR_KEYWORD_OS: "$OS$",
            AR_KEYWORD_DATABASE: "$DATABASE$",
            AR_KEYWORD_LASTID: "$LASTID$",
            AR_KEYWORD_LASTCOUNT: "$LASTCOUNT$",
            AR_KEYWORD_VERSION: "$VERSION$",
            AR_KEYWORD_VUI: "$VUI$",
            AR_KEYWORD_GUIDETEXT: "$GUIDETEXT$",
            AR_KEYWORD_FIELDHELP: "$FIELDHELP$",
            AR_KEYWORD_GUIDE: "$GUIDE$",
            AR_KEYWORD_APPLICATION: "$APPLICATION$",
            AR_KEYWORD_LOCALE: "$LOCALE$",
            AR_KEYWORD_CLIENT_TYPE: "$CLIENT-TYPE$",
            AR_KEYWORD_SCHEMA_ALIAS: "$SCHEMA-ALIAS$",
            AR_KEYWORD_ROWSELECTED: "$ROWSELECTED$",
            AR_KEYWORD_ROWCHANGED: "$ROWCHANGED$",
            AR_KEYWORD_BROWSER: "$BROWSER$",
            AR_KEYWORD_VUI_TYPE: "$VUI_TYPE$",
            AR_KEYWORD_TCPPORT: "$TCPPORT$",
            AR_KEYWORD_HOMEURL: "$HOMEURL$",
            AR_KEYWORD_NO: "$NO$"
            }
    ars_const['ARFieldValueTag'] = {
            0 : "??? WHAT DOES THIS MEAN", 
            AR_FIELD: "AR_FIELD",
            AR_VALUE: "AR_VALUE",
            AR_ARITHMETIC: "AR_ARITHMETIC",
            AR_STAT_HISTORY: "AR_STAT_HISTORY",
            AR_VALUE_SET: "AR_VALUE_SET",
            AR_CURRENCY_FLD: "AR_CURRENCY_FLD",
            AR_FIELD_TRAN: "TR",
            AR_FIELD_DB: "DB",
            AR_LOCAL_VARIABLE: "LOCAL",
            AR_QUERY: "AR_QUERY",
            AR_CURRENCY_FLD_TRAN: "CUR_TR",
            AR_CURRENCY_FLD_DB: "CUR_DB",
            AR_CURRENCY_FLD_CURRENT: "CUR_CURRENT",
            AR_FIELD_CURRENT: "CURRENT"
        }
    ars_const['AR_VUI_TYPE'] = {
            AR_VUI_TYPE_NONE: "AR_VUI_TYPE_NONE",
            AR_VUI_TYPE_WINDOWS: "AR_VUI_TYPE_WINDOWS",
            AR_VUI_TYPE_WEB: "AR_VUI_TYPE_WEB",
            AR_VUI_TYPE_WEB_ABS_POS: "AR_VUI_TYPE_WEB_ABS_POS",
            AR_VUI_TYPE_WIRELESS: "AR_VUI_TYPE_WIRELESS",
        }
    ars_const['AR_OPERATION'] = {
            AR_OPERATION_NONE: "NONE",
            AR_OPERATION_GET: "GET",
            AR_OPERATION_SET: "MODIFY",
            AR_OPERATION_CREATE: "SUBMIT",
            AR_OPERATION_DELETE: "DELETE",
            AR_OPERATION_MERGE: "MERGE",
            AR_OPERATION_GUIDE: "GUIDE"
        }
    ars_const['AR_DEBUG'] = {
            AR_DEBUG_SERVER_NONE: "SERVER_NONE",
            AR_DEBUG_SERVER_SQL: "SERVER_SQL",
            AR_DEBUG_SERVER_FILTER: "SERVER_FILTER",
            AR_DEBUG_SERVER_USER: "SERVER_USER",
            AR_DEBUG_SERVER_ESCALATION: "SERVER_ESCALATION",
            AR_DEBUG_SERVER_API: "SERVER_API",
            AR_DEBUG_THREAD: "THREAD",
            AR_DEBUG_SERVER_ALERT: "SERVER_ALERT",
            AR_DEBUG_SERVER_ARFORK: "SERVER_ARFORK",
            AR_DEBUG_SERVER_DISTRIB: "SERVER_DISTRIB",
            AR_DEBUG_SERVER_APPROVAL: "SERVER_APPROVAL",
            AR_DEBUG_SERVER_PLUGIN: "SERVER_PLUGIN"
        }
    ars_const['AR_QUERY_VALUE_MULTI'] = {
            AR_QUERY_VALUE_MULTI_ERROR: "ERROR",
            AR_QUERY_VALUE_MULTI_FIRST: "FIRST",
            AR_QUERY_VALUE_MULTI_SET: "SET"
        }
    ars_const['AR_ACCESS_OPTION'] = {
            AR_ACCESS_OPTION_UNCHANGED: "UNCHANGED",
            AR_ACCESS_OPTION_READ_ONLY: "READ_ONLY",
            AR_ACCESS_OPTION_READ_WRITE: "READ_WRITE",
            AR_ACCESS_OPTION_DISABLE: "DISABLE"
        }
    ars_const ['AR_FOCUS'] = {
            AR_FOCUS_UNCHANGED: "UNCHANGED",
            AR_FOCUS_SET_TO_FIELD: "SET_TO_FIELD"
        }
    ars_const['AR_FUNCTION'] = {
            AR_FUNCTION_DATE: "DATE",
            AR_FUNCTION_TIME: "TIME",
            AR_FUNCTION_MONTH: "MONTH",
            AR_FUNCTION_DAY: "DAY",
            AR_FUNCTION_YEAR: "YEAR",
            AR_FUNCTION_WEEKDAY: "WEEKDAY",
            AR_FUNCTION_HOUR: "HOUR",
            AR_FUNCTION_MINUTE: "MINUTE",
            AR_FUNCTION_SECOND: "SECOND",
            AR_FUNCTION_TRUNC: "TRUNC",
            AR_FUNCTION_ROUND: "ROUND",
            AR_FUNCTION_CONVERT: "CONVERT",
            AR_FUNCTION_LENGTH: "LENGTH",
            AR_FUNCTION_UPPER: "UPPER",
            AR_FUNCTION_LOWER: "LOWER",
            AR_FUNCTION_SUBSTR: "SUBSTR",
            AR_FUNCTION_LEFT: "LEFT",
            AR_FUNCTION_RIGHT: "RIGHT",
            AR_FUNCTION_LTRIM: "LTRIM",
            AR_FUNCTION_RTRIM: "RTRIM",
            AR_FUNCTION_LPAD: "LPAD",
            AR_FUNCTION_RPAD: "RPAD",
            AR_FUNCTION_REPLACE: "REPLACE",
            AR_FUNCTION_STRSTR: "STRSTR",
            AR_FUNCTION_MIN: "MIN",
            AR_FUNCTION_MAX: "MAX",
            AR_FUNCTION_COLSUM: "COLSUM",
            AR_FUNCTION_COLCOUNT: "COLCOUNT",
            AR_FUNCTION_COLAVG: "COLAVG",
            AR_FUNCTION_COLMIN: "COLMIN",
            AR_FUNCTION_COLMAX: "COLMAX",
            AR_FUNCTION_DATEADD: "DATEADD",
            AR_FUNCTION_DATEDIFF: "DATEDIFF",
            AR_FUNCTION_DATENAME: "DATENAME",
            AR_FUNCTION_DATENUM: "DATENUM",
            AR_FUNCTION_CURRCONVERT: "CURRCONVERT",
            AR_FUNCTION_CURRSETDATE: "CURRSETDATE",
            AR_FUNCTION_CURRSETTYPE: "CURRSETTYPE",
            AR_FUNCTION_CURRSETVALUE: "CURRSETVALUE"
        }
    ars_const['AR_NO_MATCH'] = {
            AR_NO_MATCH_ERROR: "Display 'No Match' Error",
            AR_NO_MATCH_SET_NULL: "Set Fields to NULL",
            AR_NO_MATCH_NO_ACTION: "Take No Action",
            AR_NO_MATCH_SUBMIT: "Create a New Request"
        }
    ars_const['AR_MULTI_MATCH'] = {
            AR_MULTI_MATCH_ERROR: "Display 'Any Match' Error",
            AR_MULTI_MATCH_SET_NULL: "Set Fields to NULL",
            AR_MULTI_MATCH_USE_FIRST: "Use First Matching Request",
            AR_MULTI_MATCH_PICKLIST: "AR_MULTI_MATCH_PICKLIST",
            AR_MULTI_MATCH_MODIFY_ALL: "Modify All Matching Requests",
            AR_MULTI_MATCH_NO_ACTION: "Take no Action"
        }
    ars_const['AR_MENU_REFRESH'] = {
            AR_MENU_REFRESH_CONNECT: "CONNECT",
            AR_MENU_REFRESH_OPEN: "OPEN",
            AR_MENU_REFRESH_INTERVAL: "INTERVAL"
        }
    ars_const['AR_MENU_TYPE'] = {
            AR_MENU_TYPE_NONE: "NONE",
            AR_MENU_TYPE_VALUE: "VALUE",
            AR_MENU_TYPE_MENU: "MENU"
        }
    ars_const['AR_MENU_FILE'] = {
            AR_MENU_FILE_SERVER: "SERVER",
            AR_MENU_FILE_CLIENT: "CLIENT"
        }
    ars_const['AR_CHAR_MENU_DD'] = {
            AR_CHAR_MENU_DD_NONE: "NONE",
            AR_CHAR_MENU_DD_FORM: "FORM",
            AR_CHAR_MENU_DD_FIELD: "FIELD"
        }
    ars_const['AR_CHAR_MENU_DD_NAME'] = {
            AR_CHAR_MENU_DD_DB_NAME: "DB_NAME",
            AR_CHAR_MENU_DD_LOCAL_NAME: "LOCAL_NAME",
            AR_CHAR_MENU_DD_ID: "ID"
        }
    ars_const['AR_CHAR_MENU_DD_FORMAT'] = {
            AR_CHAR_MENU_DD_FORMAT_NONE: "NONE",
            AR_CHAR_MENU_DD_FORMAT_ID: "ID",
            AR_CHAR_MENU_DD_FORMAT_NAME: "NAME",
            AR_CHAR_MENU_DD_FORMAT_QUOTES: "QUOTES",
            AR_CHAR_MENU_DD_FORMAT_DOLLARS: "DOLLARS",
            AR_CHAR_MENU_DD_FORMAT_ID_NAME: "ID_NAME",
            AR_CHAR_MENU_DD_FORMAT_NAMEL: "NAMEL",
            AR_CHAR_MENU_DD_FORMAT_QUOTESL: "QUOTESL",
            AR_CHAR_MENU_DD_FORMAT_DOLLARSL: "DOLLARSL",
            AR_CHAR_MENU_DD_FORMAT_ID_L: "ID_L",
            AR_CHAR_MENU_DD_FORMAT_NAME_L: "NAME_L",
            AR_CHAR_MENU_DD_FORMAT_L_NAME: "L_NAME"
        }
    ars_const['AR_CHAR_MENU'] = {
            AR_CHAR_MENU_NONE: "NONE",
            AR_CHAR_MENU_LIST: "LIST",
            AR_CHAR_MENU_QUERY: "QUERY",
            AR_CHAR_MENU_FILE: "FILE",
            AR_CHAR_MENU_SQL: "SQL",
            AR_CHAR_MENU_SS: "SS",
            AR_CHAR_MENU_DATA_DICTIONARY: "DATA_DICTIONARY"
        }
    ars_const['AR_LICENSE_TAG'] = {
            AR_LICENSE_TAG_WRITE: "WRITE",
            AR_LICENSE_TAG_FULL_TEXT: "FULL_TEXT",
            AR_LICENSE_TAG_RESERVED1: "RESERVED1"
        }
    ars_const['AR_NOTIFY_BEHAVIOR_SEND_MULTIPLE'] = {
            AR_NOTIFY_BEHAVIOR_SEND_MULTIPLE: "SEND_MULTIPLE"
        }
    ars_const['AR_NOTIFY_PERMISSION_DEFAULT'] = {
            AR_NOTIFY_PERMISSION_DEFAULT: "PERMISSION_DEFAULT"
        }
    ars_const['AR_NOTIFY'] = {
            AR_NOTIFY_NONE: "NONE",
            AR_NOTIFY_VIA_NOTIFIER: "VIA_NOTIFIER",
            AR_NOTIFY_VIA_EMAIL: "VIA_EMAIL",
            AR_NOTIFY_VIA_DEFAULT: "VIA_DEFAULT",
            AR_NOTIFY_VIA_XREF: "VIA_XREF",
            AR_NOTIFY_PRIORITY_MAX: "PRIORITY_MAX"
        }
    ars_const['ARCON'] = {
            ARCON_ALL: "ALL",
            ARCON_GUIDE: "GUIDE",
            ARCON_APP: "APP",
            ARCON_PACK: "PACK",
            ARCON_FILTER_GUIDE: "FILTER_GUIDE",
            ARCON_WEBSERVICE: "WEBSERVICE",
            ARCON_LAST_RESERVED: "LAST_RESERVED"
        }
    ars_const['AR_CASE_SENSITIVE'] = {
            AR_CASE_SENSITIVE_UNKNOWN: "UNKNOWN",
            AR_CASE_SENSITIVE_YES: "CASE_SENSITIVE_YES",
            AR_CASE_SENSITIVE_NO: "CASE_SENSITIVE_NO"
        }
    ars_const['AR_FULLTEXTINFO'] = {
            AR_FULLTEXTINFO_COLLECTION_DIR: "COLLECTION_DIR",
            AR_FULLTEXTINFO_STOPWORD: "STOPWORD",
            AR_FULLTEXTINFO_REINDEX: "REINDEX",
            AR_FULLTEXTINFO_CASE_SENSITIVE_SRCH: "CASE_SENSITIVE_SRCH",
            AR_FULLTEXTINFO_STATE: "STATE",
            AR_FULLTEXTINFO_FTS_MATCH_OP: "FTS_MATCH_OP",
            AR_FULLTEXTINFO_HOMEDIR: "HOMEDIR",
            AR_FULLTEXTINFO_DEBUG: "DEBUG",
            AR_MAX_FULLTEXT_INFO_USED: "AR_MAX_FULLTEXT_INFO_USED"
        }
    ars_const['AR_FULLTEXT_REINDEX'] = {
            AR_FULLTEXT_REINDEX: "AR_FULLTEXT_REINDEX" # only useful for set operation
        }
    ars_const['AR_CASE'] = {
            AR_CASE_SENSITIVE_SEARCH: "SENSITIVE_SEARCH",
            AR_CASE_INSENSITIVE_SEARCH: "INSENSITIVE_SEARCH"
        }
    ars_const['AR_FULLTEXT_STATE'] = {
            AR_FULLTEXT_STATE_OFF: "STATE_OFF",
            AR_FULLTEXT_STATE_ON: "STATE_ON"
        }
    ars_const['AR_FULLTEXT_FTS'] = {
            AR_FULLTEXT_FTS_MATCH_FORCE_L_T_WILD: "AR_FULLTEXT_FTS_MATCH_FORCE_L_T_WILD",
            AR_FULLTEXT_FTS_MATCH_FORCE_T_WILD: "AR_FULLTEXT_FTS_MATCH_FORCE_T_WILD",
            AR_FULLTEXT_FTS_MATCH_IGNORE_L_WILD: "AR_FULLTEXT_FTS_MATCH_IGNORE_L_WILD",
            AR_FULLTEXT_FTS_MATCH_REMOVE_WILD: "AR_FULLTEXT_FTS_MATCH_REMOVE_WILD",
            AR_FULLTEXT_FTS_MATCH_UNCHANGED: "AR_FULLTEXT_FTS_MATCH_UNCHANGED"
        }
    ars_const['AR_BYTE_LIST'] = {
            AR_BYTE_LIST_SELF_DEFINED: "AR_BYTE_LIST_SELF_DEFINED",
            AR_BYTE_LIST_WIN30_BITMAP: "AR_BYTE_LIST_WIN30_BITMAP",
            AR_BYTE_LIST_JPEG: "AR_BYTE_LIST_JPEG",
            AR_BYTE_LIST_TIFF: "AR_BYTE_LIST_TIFF",
            AR_BYTE_LIST_TARGA: "AR_BYTE_LIST_TARGA",
            AR_BYTE_LIST_PCX: "AR_BYTE_LIST_PCX",
            AR_BYTE_LIST_LOCALIZED_FILE: "AR_BYTE_LIST_LOCALIZED_FILE",
            AR_BYTE_LIST_AUTH_STRING: "AR_BYTE_LIST_AUTH_STRING"
        }
    ars_const['AR_FIELD'] = {
            AR_FIELD_NONE: "AR_FIELD_NONE",
            AR_FIELD_REGULAR: "AR_FIELD_REGULAR",
            AR_FIELD_JOIN: "AR_FIELD_JOIN",
            AR_FIELD_VIEW: "AR_FIELD_VIEW",
            AR_FIELD_VENDOR: "AR_FIELD_VENDOR"
        }
    ars_const['AR_CLIENT_TYPE'] = {
            AR_CLIENT_TYPE_UNKNOWN: "UNKNOWN",
            AR_CLIENT_TYPE_PRE_50: "PRE_50",
            AR_CLIENT_TYPE_WAT: "WAT",
            AR_CLIENT_TYPE_WUT: "WUT",
            AR_CLIENT_TYPE_WIP: "WIP",
            AR_CLIENT_TYPE_DSO: "DSO",
            AR_CLIENT_TYPE_ODBC: "ODBC",
            AR_CLIENT_TYPE_APPROVAL: "APPROVAL",
            AR_CLIENT_TYPE_WEB_SERVER: "WEB_SERVER",
            AR_CLIENT_TYPE_MID_TIER: "MID_TIER",
            AR_CLIENT_TYPE_PALM_PILOT: "PALM_PILOT",
            AR_CLIENT_TYPE_FLASHBOARDS: "FLASHBOARDS",
            AR_CLIENT_TYPE_FLASHBOARDS_MID_TIER: "FLASHBOARDS_MID_TIER",
            AR_CLIENT_TYPE_EIE: "EIE",
            AR_CLIENT_TYPE_RELOAD: "RELOAD",
            AR_CLIENT_TYPE_CACHE: "CACHE",
            AR_CLIENT_TYPE_DIST: "DIST",
            AR_CLIENT_TYPE_RUN_MACRO: "RUN_MACRO",
            AR_CLIENT_TYPE_MAIL: "MAIL",
            AR_CLIENT_TYPE_IMPORT_CMD: "IMPORT_CMD",
            AR_CLIENT_TYPE_REPORT_PLUGIN: "REPORT_PLUGIN",
            AR_CLIENT_TYPE_ALERT: "ALERT",
            AR_CLIENT_TYPE_MAIL_DAEMON: "MAIL_DAEMON",
            AR_CLIENT_TYPE_END_OF_PRODUCT: "END_OF_PRODUCT",
            AR_CLIENT_TYPE_UNPRODUCTIZED_START: "UNPRODUCTIZED_START",
            AR_CLIENT_TYPE_DRIVER: "DRIVER",
            AR_CLIENT_TYPE_DISPATCHER: "DISPATCHER",
            AR_CLIENT_TYPE_HELP: "HELP",
            AR_CLIENT_TYPE_JANITOR: "JANITOR",
            AR_CLIENT_TYPE_MENU: "MENU",
            AR_CLIENT_TYPE_STRUCT: "STRUCT",
            AR_CLIENT_TYPE_TEXT: "TEXT",
            AR_CLIENT_TYPE_SQLED: "SQLED",
            AR_CLIENT_TYPE_CHANGE_SEL: "CHANGE_SEL"
        }
    ars_const['AR_KEY_OPERATION'] = {
            AR_KEY_OPERATION_CREATE: "CREATE",
            AR_KEY_OPERATION_DELETE: "DELETE",
            AR_KEY_OPERATION_GET: "GET",
            AR_KEY_OPERATION_GETLIST: "GETLIST",
            AR_KEY_OPERATION_MERGE: "MERGE",
            AR_KEY_OPERATION_SET: "SET",
            AR_KEY_OPERATION_SET_ALL: "SET_ALL",
            AR_KEY_OPERATION_QUERY: "QUERY",
            AR_KEY_OPERATION_GUIDE: "GUIDE"
        }
    ars_const['AR_PATTERN_KEY'] = {
            AR_PATTERN_KEY_DIGIT: "DIGIT",
            AR_PATTERN_KEY_ALPHA: "ALPHA",
            AR_PATTERN_KEY_ALNUM: "ALNUM",
            AR_PATTERN_KEY_PRINT: "PRINT",
            AR_PATTERN_KEY_UPPER: "UPPER",
            AR_PATTERN_KEY_LOWER: "LOWER",
            AR_PATTERN_KEY_MENU: "MENU"
        }
    ars_const['AR_GROUP_TYPE'] = {    
            AR_GROUP_TYPE_VIEW: "AR_GROUP_TYPE_VIEW",
            AR_GROUP_TYPE_CHANGE: "AR_GROUP_TYPE_CHANGE"
        }
    ars_const['AR_MENU'] = {
            AR_MENU_APPEND: "AR_MENU_APPEND",
            AR_MENU_OVERWRITE: "AR_MENU_OVERWRITE"
        }
    ars_const['AR_LICENSE_TYPE'] = {
        AR_LICENSE_TYPE_NONE: "NONE",
        AR_LICENSE_TYPE_FIXED: "FIXED",
        AR_LICENSE_TYPE_FLOATING: "FLOATING"
    }
    ars_const['AR_SVR_EVENT_CHG'] = {
            AR_SVR_EVENT_CHG_SCHEMA: "AR_SVR_EVENT_CHG_SCHEMA",
            AR_SVR_EVENT_CHG_FIELD: "AR_SVR_EVENT_CHG_FIELD",
            AR_SVR_EVENT_CHG_CHARMENU: "AR_SVR_EVENT_CHG_CHARMENU",
            AR_SVR_EVENT_CHG_FILTER: "AR_SVR_EVENT_CHG_FILTER",
            AR_SVR_EVENT_CHG_IMPORT: "AR_SVR_EVENT_CHG_IMPORT",
            AR_SVR_EVENT_CHG_ACTLINK: "AR_SVR_EVENT_CHG_ACTLINK",
            AR_SVR_EVENT_CHG_ESCAL: "AR_SVR_EVENT_CHG_ESCAL",
            AR_SVR_EVENT_CHG_VUI: "AR_SVR_EVENT_CHG_VUI",
            AR_SVR_EVENT_CHG_CONTAINER: "AR_SVR_EVENT_CHG_CONTAINER",
            AR_SVR_EVENT_CHG_USERS: "AR_SVR_EVENT_CHG_USERS",
            AR_SVR_EVENT_CHG_GROUPS: "AR_SVR_EVENT_CHG_GROUPS",
            AR_SVR_EVENT_CHG_SVR_SETTINGS: "AR_SVR_EVENT_CHG_SVR_SETTINGS",
            AR_SVR_EVENT_CHG_ALERT_USERS: "AR_SVR_EVENT_CHG_ALERT_USERS",
            AR_MAX_SVR_EVENT_USED: "AR_MAX_SVR_EVENT_USED"
        }
    ars_const['AR_RETURN'] = {
            AR_RETURN_OK: "OK",
            AR_RETURN_WARNING: "WARNING",
            AR_RETURN_ERROR: "ERROR",
            AR_RETURN_FATAL: "FATAL",
            AR_RETURN_BAD_STATUS: "BAD_STATUS",
            AR_RETURN_PROMPT: "PROMPT",
            AR_RETURN_ACCESSIBLE: "ACCESSIBLE"
        }
    
    ars_const['rest'] = {
            AR_LOG_FILE: "AR_LOG_FILE",
            AR_MAX_ACTIONS: "AR_MAX_ACTIONS",
            AR_MAX_AL_MESSAGE_SIZE: "AR_MAX_AL_MESSAGE_SIZE",
            AR_MAX_AUTOMATION_SIZE: "AR_MAX_AUTOMATION_SIZE",
#            AR_MAX_BLOB_SIZE: "AR_MAX_BLOB_SIZE",
            AR_MAX_BUFFER_SIZE: "AR_MAX_BUFFER_SIZE",
            AR_MAX_CMENU_SIZE: "AR_MAX_CMENU_SIZE",
            AR_MAX_COMMAND_SIZE: "AR_MAX_COMMAND_SIZE",
            AR_MAX_COM_NAME: "AR_MAX_COM_NAME",
            AR_MAX_COM_METHOD_NAME: "AR_MAX_COM_METHOD_NAME",
            AR_MAX_COM_ID_SIZE: "AR_MAX_COM_ID_SIZE",
            AR_MAX_CURRENCY_CODE_SIZE: "AR_MAX_CURRENCY_CODE_SIZE",
            AR_MAX_CURRENCY_RATIO_SIZE: "AR_MAX_CURRENCY_RATIO_SIZE",
            AR_MAX_DDE_ITEM: "AR_MAX_DDE_ITEM",
            AR_MAX_DDE_NAME: "AR_MAX_DDE_NAME",
            AR_MAX_DECIMAL_SIZE: "AR_MAX_DECIMAL_SIZE",
            AR_MAX_DEFAULT_SIZE: "AR_MAX_DEFAULT_SIZE",
            AR_MAX_EMAIL_ADDR: "AR_MAX_EMAIL_ADDR",
            AR_MAX_ENTRYID_SIZE: "AR_MAX_ENTRYID_SIZE",
#            AR_MAX_FIELD_ID: "AR_MAX_FIELD_ID",
            AR_MAX_GOTOGUIDE_LABEL_SIZE: "AR_MAX_GOTOGUIDE_LABEL_SIZE",
            AR_MAX_GROUPLIST_SIZE: "AR_MAX_GROUPLIST_SIZE",
            AR_MAX_INDEX_BYTES: "AR_MAX_INDEX_BYTES",
            AR_MAX_INDEX_FIELDS: "AR_MAX_INDEX_FIELDS",
            AR_MAX_LANG_SIZE: "AR_MAX_LANG_SIZE",
            AR_MAX_LICENSE_NAME_SIZE: "AR_MAX_LICENSE_NAME_SIZE",
            AR_MAX_LICENSE_KEY_SIZE: "AR_MAX_LICENSE_KEY_SIZE",
            AR_MAX_MACRO_VALUE: "AR_MAX_MACRO_VALUE",
            AR_MAX_MENU_ITEMS: "AR_MAX_MENU_ITEMS",
            AR_MAX_MENU_LEVELS: "AR_MAX_MENU_LEVELS",
            AR_MAX_LEVELS_DYNAMIC_MENU: "AR_MAX_LEVELS_DYNAMIC_MENU",
            AR_MAX_MESSAGE_SIZE: "AR_MAX_MESSAGE_SIZE",
            AR_MAX_MULT_ENTRIES: "AR_MAX_MULT_ENTRIES",
            AR_MAX_NAME_SIZE: "AR_MAX_NAME_SIZE",
            AR_MAX_ACCESS_NAME_SIZE: "AR_MAX_ACCESS_NAME_SIZE",
            AR_MAX_NAME_CHARACTERS: "AR_MAX_NAME_CHARACTERS",
            AR_MAX_NOTIFY_USER: "AR_MAX_NOTIFY_USER",
            AR_MAX_PATTERN_SIZE: "AR_MAX_PATTERN_SIZE",
            AR_MAX_RELATED_SIZE: "AR_MAX_RELATED_SIZE",
            AR_MAX_SCHEMAID_SIZE: "AR_MAX_SCHEMAID_SIZE",
            AR_MAX_SERVER_SIZE: "AR_MAX_SERVER_SIZE",
            AR_MAX_SDESC_SIZE: "AR_MAX_SDESC_SIZE",
            AR_MAX_SUBJECT_SIZE: "AR_MAX_SUBJECT_SIZE",
            AR_MAX_HOSTID_SIZE: "AR_MAX_HOSTID_SIZE",
            AR_MAX_TARGET_STRING_SIZE: "AR_MAX_TARGET_STRING_SIZE",
            AR_MAX_WAIT_CONT_TITLE_SIZE: "AR_MAX_WAIT_CONT_TITLE_SIZE",
            AR_MAX_FILENAME_SIZE: "AR_MAX_FILENAME_SIZE",
            AR_MAX_FILENAME_BASE: "AR_MAX_FILENAME_BASE",
            AR_MAX_FULL_FILENAME: "AR_MAX_FULL_FILENAME",
            AR_MAX_COLFLD_COLLENGTH: "AR_MAX_COLFLD_COLLENGTH",
            AR_MAX_SVR_EVENT_DETAILS: "AR_MAX_SVR_EVENT_DETAILS",
            AR_MAX_SVR_EVENT_LIST: "AR_MAX_SVR_EVENT_LIST",
            AR_MAX_TABLENAME_SIZE: "AR_MAX_TABLENAME_SIZE",
            AR_MAX_TBLFLD_NUMCOLS: "AR_MAX_TBLFLD_NUMCOLS",
            AR_MAX_TBLFLD_RETROWS: "AR_MAX_TBLFLD_RETROWS",
            AR_MAX_FLATFILE_LIMIT: "AR_MAX_FLATFILE_LIMIT",
            AR_MONITOR_CONFIGFILE: "AR_MONITOR_CONFIGFILE",
            AR_MONITOR_PID: "AR_MONITOR_PID",
            AR_SCHEMA_MAX_SCHEMA_TYPE: "MAX_SCHEMA_TYPE",
            AR_MAX_SERVER_STAT_USED: "AR_MAX_SERVER_STAT_USED",
            AR_SYSTEM_NAME: "AR_SYSTEM_NAME",
            AR_WARN_FLATFILE_LIMIT: "AR_WARN_FLATFILE_LIMIT",
        }
    ars_const['AR_HOME'] = {
            AR_HOME_CONFIGDIR: "AR_HOME_CONFIGDIR",
            AR_HOME_CONFIGFILE: "AR_HOME_CONFIGFILE",
            AR_HOME_DB_CONFIGFILE: "AR_HOME_DB_CONFIGFILE",
            AR_HOME_AUDIT_CONFIGFILE: "AR_HOME_AUDIT_CONFIGFILE",
            AR_HOME_DEFAULT: "AR_HOME_DEFAULT",
            AR_HOME_CONFIGFILE: "AR_HOME_CONFIGFILE",
            AR_HOME_DB_CONFIGFILE: "AR_HOME_DB_CONFIGFILE",
            AR_HOME_AUDIT_CONFIGFILE: "AR_HOME_AUDIT_CONFIGFILE"
        }
    ars_const['AR_ENV'] = {
            AR_ENV_CONFIGDIR: "AR_ENV_CONFIGDIR",
            AR_ENV_INSTALLDIR: "AR_ENV_INSTALLDIR",
            AR_ENV_MONITOR_CONFIG: "AR_ENV_MONITOR_CONFIG",
        }
    ars_const['AR_STAT'] = {
            AR_STAT_HISTORY_USER: "AR_STAT_HISTORY_USER",
            AR_STAT_HISTORY_TIME: "AR_STAT_HISTORY_TIME",
            AR_STAT_OP_COUNT: "AR_STAT_OP_COUNT",
            AR_STAT_OP_SUM: "AR_STAT_OP_SUM",
            AR_STAT_OP_AVERAGE: "AR_STAT_OP_AVERAGE",
            AR_STAT_OP_MINIMUM: "AR_STAT_OP_MINIMUM",
            AR_STAT_OP_MAXIMUM: "AR_STAT_OP_MAXIMUM"
        }
    ars_const['AR_MERGE_ENTRY_DUP'] = {
            AR_MERGE_ENTRY_DUP_ERROR: "AR_MERGE_ENTRY_DUP_ERROR",
            AR_MERGE_ENTRY_DUP_NEW_ID: "AR_MERGE_ENTRY_DUP_NEW_ID",
            AR_MERGE_ENTRY_DUP_OVERWRITE: "AR_MERGE_ENTRY_DUP_OVERWRITE",
            AR_MERGE_ENTRY_DUP_MERGE: "AR_MERGE_ENTRY_DUP_MERGE",
        }
    ars_const['AR_CURRENCY_PART'] = {
            AR_CURRENCY_PART_FIELD: "AR_CURRENCY_PART_FIELD",
            AR_CURRENCY_PART_VALUE: "AR_CURRENCY_PART_VALUE",
            AR_CURRENCY_PART_TYPE: "AR_CURRENCY_PART_TYPE",
            AR_CURRENCY_PART_DATE: "AR_CURRENCY_PART_DATE",
            AR_CURRENCY_PART_FUNCTIONAL: "AR_CURRENCY_PART_FUNCTIONAL",
            }
    ars_const['AR_CURRENT'] = {
            AR_CURRENT_SERVER_TAG: "AR_CURRENT_SERVER_TAG",
            AR_CURRENT_SCHEMA_TAG: "AR_CURRENT_SCHEMA_TAG",
            AR_CURRENT_SCREEN_TAG: "AR_CURRENT_SCREEN_TAG",
            AR_CURRENT_TRAN_TAG: "AR_CURRENT_TRAN_TAG",
            AR_CURRENT_API_VERSION: "AR_CURRENT_API_VERSION",
            AR_CURRENT_CURRENCY_RATIOS: "AR_CURRENT_CURRENCY_RATIOS",
            }
    ars_const['AR_DDE'] = {
            AR_DDE_EXECUTE: "AR_DDE_EXECUTE",
            AR_DDE_POKE: "AR_DDE_POKE",
            AR_DDE_REQUEST: "AR_DDE_REQUEST",
            }
    ars_const['AR_COM_PARM'] = {
            AR_COM_PARM_NULL: "AR_COM_PARM_NULL",
            AR_COM_PARM_FIELDID: "AR_COM_PARM_FIELDID",
            AR_COM_PARM_VALUE: "AR_COM_PARM_VALUE",
            }
    ars_const['AR_COM_METHOD'] = {
            AR_COM_METHOD_NULL: "AR_COM_METHOD_NULL",
            AR_COM_METHOD_FIELDID: "AR_COM_METHOD_FIELDID",
            }
    ars_const['AR_FILTER'] = {
            AR_FILTER_FIELD_IDS_NONE: "AR_FILTER_FIELD_IDS_NONE",
            AR_FILTER_FIELD_IDS_ALL: "AR_FILTER_FIELD_IDS_ALL",
            AR_FILTER_FIELD_IDS_LIST: "AR_FILTER_FIELD_IDS_LIST",
            AR_FILTER_FIELD_IDS_CHANGED: "AR_FILTER_FIELD_IDS_CHANGED",
            }
    ars_const['AR_GOTO'] = {
            AR_GOTO_FIELD_XREF: "AR_GOTO_FIELD_XREF",
            AR_GOTO_ABSOLUTE_ORDER: "AR_GOTO_ABSOLUTE_ORDER",
            AR_GOTO_OFFSET_FORWARD: "AR_GOTO_OFFSET_FORWARD",
            AR_GOTO_OFFSET_BACKWARD: "AR_GOTO_OFFSET_BACKWARD",
            }
    ars_const['AR_REPORT_ATTR'] = {
            AR_REPORT_ATTR_LAYOUT: "AR_REPORT_ATTR_LAYOUT",
            AR_REPORT_ATTR_IDLIST: "AR_REPORT_ATTR_IDLIST",
            AR_REPORT_ATTR_NAME: "AR_REPORT_ATTR_NAME",
            AR_REPORT_ATTR_TITLE: "AR_REPORT_ATTR_TITLE",
            AR_REPORT_ATTR_HEADER: "AR_REPORT_ATTR_HEADER",
            AR_REPORT_ATTR_FOOTER: "AR_REPORT_ATTR_FOOTER",
            AR_REPORT_ATTR_LINES: "AR_REPORT_ATTR_LINES",
            AR_REPORT_ATTR_TOP: "AR_REPORT_ATTR_TOP",
            AR_REPORT_ATTR_BOTTOM: "AR_REPORT_ATTR_BOTTOM",
            AR_REPORT_ATTR_CHARS: "AR_REPORT_ATTR_CHARS",
            AR_REPORT_ATTR_LEFT: "AR_REPORT_ATTR_LEFT",
            AR_REPORT_ATTR_RIGHT: "AR_REPORT_ATTR_RIGHT",
            AR_REPORT_ATTR_COL_SEP: "AR_REPORT_ATTR_COL_SEP",
            AR_REPORT_ATTR_ONE_REC_PER_PAGE: "AR_REPORT_ATTR_ONE_REC_PER_PAGE",
            AR_REPORT_ATTR_COMPRESSED: "AR_REPORT_ATTR_COMPRESSED",
            AR_REPORT_ATTR_TITLE_SEP_CHAR: "AR_REPORT_ATTR_TITLE_SEP_CHAR",
            AR_REPORT_ATTR_PAGE_BREAKS: "AR_REPORT_ATTR_PAGE_BREAKS",
            AR_REPORT_ATTR_TYPE: "AR_REPORT_ATTR_TYPE",
            AR_REPORT_ATTR_FILENAME: "AR_REPORT_ATTR_FILENAME",
            AR_REPORT_ATTR_PRINT_ORIENT: "AR_REPORT_ATTR_PRINT_ORIENT",
            AR_REPORT_ATTR_SCHEMANAME: "AR_REPORT_ATTR_SCHEMANAME",
            AR_REPORT_ATTR_SERVERNAME: "AR_REPORT_ATTR_SERVERNAME",
            AR_REPORT_ATTR_QUERY: "AR_REPORT_ATTR_QUERY",
            AR_REPORT_ATTR_ENTRYIDS: "AR_REPORT_ATTR_ENTRYIDS",
            AR_REPORT_ATTR_QUERY_OVERRIDE: "AR_REPORT_ATTR_QUERY_OVERRIDE",
            AR_REPORT_ATTR_OPERATION: "AR_REPORT_ATTR_OPERATION",
            AR_REPORT_ATTR_LOCATION: "AR_REPORT_ATTR_LOCATION"
            }
    ars_const['AR_REPORT'] = {
            AR_REPORT_REC_SEP: "AR_REPORT_REC_SEP",
            AR_REPORT_LONG_FIELD_FORMAT: "AR_REPORT_LONG_FIELD_FORMAT",
            AR_REPORT_COL_TITLE_PER: "AR_REPORT_COL_TITLE_PER",
            }
    ars_const['AR_REPORT_LOCATION'] = {
            AR_REPORT_LOCATION_EMBEDDED: "AR_REPORT_LOCATION_EMBEDDED",
            AR_REPORT_LOCATION_LOCAL: "AR_REPORT_LOCATION_LOCAL",
            AR_REPORT_LOCATION_REPORTING_FORM: "AR_REPORT_LOCATION_REPORTING_FORM",
            AR_REPORT_LOCATION_FIELD: "AR_REPORT_LOCATION_FIELD",
            }
    ars_const['AR_USER_LIST'] = {
            AR_USER_LIST_MYSELF: "AR_USER_LIST_MYSELF",
            AR_USER_LIST_REGISTERED: "AR_USER_LIST_REGISTERED",
            AR_USER_LIST_CURRENT: "AR_USER_LIST_CURRENT",
            }
    ars_const['AR_QBE_MATCH'] = {
            AR_QBE_MATCH_ANYWHERE: "ANYWHERE",
            AR_QBE_MATCH_LEADING: "LEADING",
            AR_QBE_MATCH_EQUAL: "EQUAL",
            }
    ars_const['AR_ATTACH_FIELD_TYPE'] = {
            AR_ATTACH_FIELD_TYPE_EMBED: "EMBED",
            AR_ATTACH_FIELD_TYPE_LINK: "LINK",
            }
    ars_const['AR_EXPORT_FORMAT'] = {
            AR_EXPORT_FORMAT_AR_DEF: "DEF",
            AR_EXPORT_FORMAT_XML: "XML",
            }
    ars_const['AR_STRUCT_ITEM'] = {
            AR_STRUCT_ITEM_SCHEMA: "AR_STRUCT_ITEM_SCHEMA",
            AR_STRUCT_ITEM_SCHEMA_DEFN: "AR_STRUCT_ITEM_SCHEMA_DEFN",
            AR_STRUCT_ITEM_SCHEMA_VIEW: "AR_STRUCT_ITEM_SCHEMA_VIEW",
            AR_STRUCT_ITEM_SCHEMA_MAIL: "AR_STRUCT_ITEM_SCHEMA_MAIL",
            AR_STRUCT_ITEM_FILTER: "AR_STRUCT_ITEM_FILTER",
            AR_STRUCT_ITEM_ACTIVE_LINK: "AR_STRUCT_ITEM_ACTIVE_LINK",
            AR_STRUCT_ITEM_ADMIN_EXT: "AR_STRUCT_ITEM_ADMIN_EXT",
            AR_STRUCT_ITEM_CHAR_MENU: "AR_STRUCT_ITEM_CHAR_MENU",
            AR_STRUCT_ITEM_ESCALATION: "AR_STRUCT_ITEM_ESCALATION",
            AR_STRUCT_ITEM_DIST_MAP: "AR_STRUCT_ITEM_DIST_MAP",
            AR_STRUCT_ITEM_SCHEMA_VIEW_MIN: "AR_STRUCT_ITEM_SCHEMA_VIEW_MIN",
            AR_STRUCT_ITEM_CONTAINER: "AR_STRUCT_ITEM_CONTAINER",
            AR_STRUCT_ITEM_DIST_POOL: "AR_STRUCT_ITEM_DIST_POOL",
            AR_STRUCT_ITEM_VUI: "AR_STRUCT_ITEM_VUI",
            AR_STRUCT_ITEM_FIELD: "AR_STRUCT_ITEM_FIELD",
            AR_STRUCT_ITEM_SCHEMA_VIEW_2: "AR_STRUCT_ITEM_SCHEMA_VIEW_2",
            AR_STRUCT_ITEM_XML_NONE: "AR_STRUCT_ITEM_XML_NONE",
            AR_STRUCT_ITEM_XML_SCHEMA: "AR_STRUCT_ITEM_XML_SCHEMA",
            AR_STRUCT_ITEM_XML_FILTER: "AR_STRUCT_ITEM_XML_FILTER",
            AR_STRUCT_ITEM_XML_ACTIVE_LINK: "AR_STRUCT_ITEM_XML_ACTIVE_LINK",
            AR_STRUCT_ITEM_XML_CHAR_MENU: "AR_STRUCT_ITEM_XML_CHAR_MENU",
            AR_STRUCT_ITEM_XML_ESCALATION: "AR_STRUCT_ITEM_XML_ESCALATION",
            AR_STRUCT_ITEM_XML_DIST_MAP: "AR_STRUCT_ITEM_XML_DIST_MAP",
            AR_STRUCT_ITEM_XML_CONTAINER: "AR_STRUCT_ITEM_XML_CONTAINER",
            AR_STRUCT_ITEM_XML_DIST_POOL: "AR_STRUCT_ITEM_XML_DIST_POOL",
            AR_STRUCT_ITEM_XML_VUI: "AR_STRUCT_ITEM_XML_VUI",
            AR_STRUCT_ITEM_XML_FIELD: "AR_STRUCT_ITEM_XML_FIELD",
            }
    ars_const['AR_IMPORT_OPT'] = {
            AR_IMPORT_OPT_CREATE: "AR_IMPORT_OPT_CREATE",
            AR_IMPORT_OPT_OVERWRITE: "AR_IMPORT_OPT_OVERWRITE",
            }
    ars_const['AR_SUBMITTER_MODE'] = {
            AR_SUBMITTER_MODE_LOCKED: "AR_SUBMITTER_MODE_LOCKED",
            AR_SUBMITTER_MODE_CHANGEABLE: "AR_SUBMITTER_MODE_CHANGEABLE",
            }
    ars_const['AR_SAVE_LOGIN'] = {
            AR_SAVE_LOGIN_USER_OPTION: "AR_SAVE_LOGIN_USER_OPTION",
            AR_SAVE_LOGIN_ADMIN_SAVE: "AR_SAVE_LOGIN_ADMIN_SAVE",
            AR_SAVE_LOGIN_ADMIN_NO_SAVE: "AR_SAVE_LOGIN_ADMIN_NO_SAVE",
            }
    ars_const['AR_TIMEMARK'] = {
            AR_TIMEMARK_ALL: "AR_TIMEMARK_ALL",
            AR_TIMEMARK_NOTFOUND: "AR_TIMEMARK_NOTFOUND",
            AR_TIMEMARK_END_OF_MONTH: "AR_TIMEMARK_END_OF_MONTH",
            }
    ars_const['AR_ESCALATION_TYPE'] = {
            AR_ESCALATION_TYPE_INTERVAL: "AR_ESCALATION_TYPE_INTERVAL",
            AR_ESCALATION_TYPE_TIMEMARK: "AR_ESCALATION_TYPE_TIMEMARK",
            }
    ars_const['AR_LONGVALUE_TYPE'] = {
            AR_LONGVALUE_TYPE_HELPTEXT: "AR_LONGVALUE_TYPE_HELPTEXT",
            AR_LONGVALUE_TYPE_CHANGEDIARY: "AR_LONGVALUE_TYPE_CHANGEDIARY",
            }
    ars_const['AR_FIELD_DELETE'] = {
            AR_FIELD_CLEAN_DELETE: "AR_FIELD_CLEAN_DELETE",
            AR_FIELD_DATA_DELETE: "AR_FIELD_DATA_DELETE",
            AR_FIELD_FORCE_DELETE: "AR_FIELD_FORCE_DELETE",
            }
    ars_const['AR_FIELD_MAPPING'] = {
            AR_FIELD_MAPPING_PRIMARY: "AR_FIELD_MAPPING_PRIMARY",
            AR_FIELD_MAPPING_SECONDARY: "AR_FIELD_MAPPING_SECONDARY",
            }
    ars_const['AR_ATTRIB'] = {
            AR_ATTRIB_NONE: "AR_ATTRIB_NONE",
            AR_ATTRIB_VISIBLE: "AR_ATTRIB_VISIBLE",
            AR_ATTRIB_HIDDEN: "AR_ATTRIB_HIDDEN",
            }
    ars_const['AR_JOIN_OPTION'] = {
            AR_JOIN_OPTION_NONE: "AR_JOIN_OPTION_NONE",
            AR_JOIN_OPTION_OUTER: "AR_JOIN_OPTION_OUTER",
            }
    ars_const['AR_JOIN_SETOPTION'] = {
            AR_JOIN_SETOPTION_NONE: "AR_JOIN_SETOPTION_NONE",
            AR_JOIN_SETOPTION_REF: "AR_JOIN_SETOPTION_REF",
            }
    ars_const['AR_JOIN_DELOPTION'] = {
            AR_JOIN_DELOPTION_NONE: "AR_JOIN_DELOPTION_NONE",
            AR_JOIN_DELOPTION_FORCE: "AR_JOIN_DELOPTION_FORCE",
            }
    ars_const['AR_SCHEMA_DELETE'] = {
            AR_SCHEMA_CLEAN_DELETE: "AR_SCHEMA_CLEAN_DELETE",
            AR_SCHEMA_DATA_DELETE: "AR_SCHEMA_DATA_DELETE",
            AR_SCHEMA_FORCE_DELETE: "AR_SCHEMA_FORCE_DELETE",
            }
    ars_const['AR_SUPPORT_FILE'] = {
            AR_SUPPORT_FILE_NONE: "AR_SUPPORT_FILE_NONE",
            AR_SUPPORT_FILE_EXTERNAL_REPORT: "AR_SUPPORT_FILE_EXTERNAL_REPORT",
            }
    ars_const['AR_DISPLAY_TYPE'] = {
            AR_DISPLAY_TYPE_NONE: "AR_DISPLAY_TYPE_NONE",
            AR_DISPLAY_TYPE_TEXT: "AR_DISPLAY_TYPE_TEXT",
            AR_DISPLAY_TYPE_NUMTEXT: "AR_DISPLAY_TYPE_NUMTEXT",
            AR_DISPLAY_TYPE_CHECKBOX: "AR_DISPLAY_TYPE_CHECKBOX",
            AR_DISPLAY_TYPE_CHOICE: "AR_DISPLAY_TYPE_CHOICE",
            AR_DISPLAY_TYPE_BUTTON: "AR_DISPLAY_TYPE_BUTTON",
            AR_DISPLAY_TYPE_TRIM: "AR_DISPLAY_TYPE_TRIM",
            }
    ars_const['AR_DISPLAY_OPT'] = {
            AR_DISPLAY_OPT_VISIBLE: "AR_DISPLAY_OPT_VISIBLE",
            AR_DISPLAY_OPT_HIDDEN: "AR_DISPLAY_OPT_HIDDEN",
            }
    ars_const['AR_DISPLAY_LABEL'] = {
            AR_DISPLAY_LABEL_LEFT: "AR_DISPLAY_LABEL_LEFT",
            AR_DISPLAY_LABEL_TOP: "AR_DISPLAY_LABEL_TOP",
            }
    ars_const['AR_SIGNAL'] = {
            AR_SIGNAL_CONFIG_CHANGED: "AR_SIGNAL_CONFIG_CHANGED",
            AR_SIGNAL_GROUP_CACHE_CHANGED: "AR_SIGNAL_GROUP_CACHE_CHANGED",
            AR_SIGNAL_LICENSE_CHANGED: "AR_SIGNAL_LICENSE_CHANGED",
            AR_SIGNAL_ALERT_USER_CHANGED: "AR_SIGNAL_ALERT_USER_CHANGED",
            AR_SIGNAL_DSO_SIGNAL: "AR_SIGNAL_DSO_SIGNAL",
            AR_SIGNAL_USER_CACHE_CHANGED: "AR_SIGNAL_USER_CACHE_CHANGED",
            }
    ars_const['AR_WRITE_TO'] = {
            AR_WRITE_TO_FILE: "AR_WRITE_TO_FILE",
            AR_WRITE_TO_STATUS_LIST: "AR_WRITE_TO_STATUS_LIST",
            }
    ars_const['AR_WORKFLOW_CONN'] = {
            AR_WORKFLOW_CONN_NONE: "AR_WORKFLOW_CONN_NONE",
            AR_WORKFLOW_CONN_SCHEMA_LIST: "AR_WORKFLOW_CONN_SCHEMA_LIST",
            }
    ars_const['AR_ENC_SEC_POLICY_ENCRYPT'] = {
            AR_ENC_SEC_POLICY_ENCRYPT_ALLOWED: "AR_ENC_SEC_POLICY_ENCRYPT_ALLOWED",
            AR_ENC_SEC_POLICY_ENCRYPT_REQUIRED: "AR_ENC_SEC_POLICY_ENCRYPT_REQUIRED",
            AR_ENC_SEC_POLICY_ENCRYPT_DISALLOWED: "AR_ENC_SEC_POLICY_ENCRYPT_DISALLOWED",
            }
    ars_const['AR_LOCAL_TEXT'] = {
            AR_LOCAL_TEXT_SYSTEM_MESSAGE: "AR_LOCAL_TEXT_SYSTEM_MESSAGE",
            AR_LOCAL_TEXT_ACT_LINK_MESSAGE: "AR_LOCAL_TEXT_ACT_LINK_MESSAGE",
            AR_LOCAL_TEXT_FILTER_MESSAGE: "AR_LOCAL_TEXT_FILTER_MESSAGE",
            AR_LOCAL_TEXT_ACT_LINK_HELP: "AR_LOCAL_TEXT_ACT_LINK_HELP",
            AR_LOCAL_TEXT_FORM_HELP: "AR_LOCAL_TEXT_FORM_HELP",
            AR_LOCAL_TEXT_FIELD_HELP: "AR_LOCAL_TEXT_FIELD_HELP",
            AR_LOCAL_TEXT_CONTAIN_DESC: "AR_LOCAL_TEXT_CONTAIN_DESC",
            AR_LOCAL_TEXT_LIST_MENU_DEFN: "AR_LOCAL_TEXT_LIST_MENU_DEFN",
            AR_LOCAL_TEXT_EXTERN_REPORT: "AR_LOCAL_TEXT_EXTERN_REPORT",
            AR_LOCAL_TEXT_CONTAINER_LABEL: "AR_LOCAL_TEXT_CONTAINER_LABEL",
            AR_LOCAL_TEXT_CONTAINER_HELP: "AR_LOCAL_TEXT_CONTAINER_HELP",
            AR_LOCAL_TEXT_APPLICATION_HELP: "AR_LOCAL_TEXT_APPLICATION_HELP",
            AR_LOCAL_TEXT_APPLICATION_ABOUT: "AR_LOCAL_TEXT_APPLICATION_ABOUT",
            AR_LOCAL_TEXT_APPLICATION_HELP_INDEX: "AR_LOCAL_TEXT_APPLICATION_HELP_INDEX",
            AR_LOCAL_TEXT_FLASHBRD_MESSAGE: "AR_LOCAL_TEXT_FLASHBRD_MESSAGE",
            AR_LOCAL_TEXT_FLASHBRD_LABEL: "AR_LOCAL_TEXT_FLASHBRD_LABEL",
            AR_LOCAL_TEXT_ACTIVE_MESSAGE: "AR_LOCAL_TEXT_ACTIVE_MESSAGE",
            AR_LOCAL_TEXT_INACTIVE_MESSAGE: "AR_LOCAL_TEXT_INACTIVE_MESSAGE",
            AR_LOCAL_TEXT_RETURN_TYPE_MSG_TEXT: "AR_LOCAL_TEXT_RETURN_TYPE_MSG_TEXT",
            AR_LOCAL_TEXT_RETURN_TYPE_BIN_ATTACH: "AR_LOCAL_TEXT_RETURN_TYPE_BIN_ATTACH",
            }
    ars_const['AR_ALERT_SOURCE'] = {
            AR_ALERT_SOURCE_GP: "AR_ALERT_SOURCE_GP",
            AR_ALERT_SOURCE_AR: "AR_ALERT_SOURCE_AR",
            AR_ALERT_SOURCE_FIRST: "AR_ALERT_SOURCE_FIRST",
            AR_ALERT_SOURCE_CHECK: "AR_ALERT_SOURCE_CHECK",
            AR_ALERT_SOURCE_FB: "AR_ALERT_SOURCE_FB",
            }
    ars_const['AR_ALERT'] = {
            AR_ALERT_ACK: "AR_ALERT_ACK",
            AR_ALERT_USER_BROADCAST: "AR_ALERT_USER_BROADCAST",
            AR_ALERT_STRING_SEP: "AR_ALERT_STRING_SEP",
            AR_MAX_SVR_EVENT_TYPE_STR: "AR_MAX_SVR_EVENT_TYPE_STR",
            }
    ars_const['AR_SVR_EVENT'] = {
            AR_SVR_EVENT_USER_ADDED: "AR_SVR_EVENT_USER_ADDED",
            AR_SVR_EVENT_USER_MODIFIED: "AR_SVR_EVENT_USER_MODIFIED",
            AR_SVR_EVENT_USER_DELETED: "AR_SVR_EVENT_USER_DELETED",
            AR_SVR_EVENT_GROUP_ADDED: "AR_SVR_EVENT_GROUP_ADDED",
            AR_SVR_EVENT_GROUP_MODIFIED: "AR_SVR_EVENT_GROUP_MODIFIED",
            AR_SVR_EVENT_GROUP_DELETED: "AR_SVR_EVENT_GROUP_DELETED",
            }
    ars_const['AR_SVR_STATS_RECMODE'] = {
            AR_SVR_STATS_RECMODE_OFF: "AR_SVR_STATS_RECMODE_OFF",
            AR_SVR_STATS_RECMODE_CUMUL_ONLY: "AR_SVR_STATS_RECMODE_CUMUL_ONLY",
            AR_SVR_STATS_RECMODE_CUMUL_QUEUE: "AR_SVR_STATS_RECMODE_CUMUL_QUEUE",
            }
    ars_const['AR_DSO_UPDATE'] = {
            AR_DSO_UPDATE_IMMEDIATELY: "AR_DSO_UPDATE_IMMEDIATELY",
            AR_DSO_UPDATE_HOURLY: "AR_DSO_UPDATE_HOURLY",
            AR_DSO_UPDATE_DAILY: "AR_DSO_UPDATE_DAILY",
            AR_DSO_UPDATE_ON_RETURN: "AR_DSO_UPDATE_ON_RETURN",
            AR_DSO_UPDATE_NO_UPDATE: "AR_DSO_UPDATE_NO_UPDATE",
            }
    ars_const['AR_DSO_TRANSFER'] = {
            AR_DSO_TRANSFER_DATA_ONLY: "AR_DSO_TRANSFER_DATA_ONLY",
            AR_DSO_TRANSFER_OWNERSHIP: "AR_DSO_TRANSFER_OWNERSHIP",
            AR_DSO_TRANSFER_COPY: "AR_DSO_TRANSFER_COPY",
            AR_DSO_TRANSFER_COPY_DELETE: "AR_DSO_TRANSFER_COPY_DELETE",
            AR_DSO_TRANSFER_DUP_ERROR: "AR_DSO_TRANSFER_DUP_ERROR",
            AR_DSO_TRANSFER_DUP_OVERWRITE: "AR_DSO_TRANSFER_DUP_OVERWRITE",
            AR_DSO_TRANSFER_DUP_CREATE_NEW: "AR_DSO_TRANSFER_DUP_CREATE_NEW",
            }
    ars_const['AR_DSO_MAP_BY'] = {
            AR_DSO_MAP_BY_FIELD_IDS: "AR_DSO_MAP_BY_FIELD_IDS",
            AR_DSO_MAP_BY_CUSTOM: "AR_DSO_MAP_BY_CUSTOM",
            AR_DSO_MAP_BY_FIELD_NAMES: "AR_DSO_MAP_BY_FIELD_NAMES",
            }
    ars_const['AR_SESS'] = {
            AR_SESS_POOLED: "AR_SESS_POOLED",
            AR_SESS_CLIENT_TYPE: "AR_SESS_CLIENT_TYPE",
            AR_SESS_VUI_TYPE: "AR_SESS_VUI_TYPE",
            }
    ars_const['AR_XML_DOC'] = {
            AR_XML_DOC_CHAR_STR: "AR_XML_DOC_CHAR_STR",
            AR_XML_DOC_FILE_NAME: "AR_XML_DOC_FILE_NAME",
            AR_XML_DOC_URL: "AR_XML_DOC_URL",
            AR_XML_DOC_FILE_HANDLE: "AR_XML_DOC_FILE_HANDLE",
            }
    ars_const['AR_ENC_ECC'] = {
            AR_ENC_ECC_163: "AR_ENC_ECC_163",
            AR_ENC_ECC_239: "AR_ENC_ECC_239",
            AR_ENC_ECC_571: "AR_ENC_ECC_571",
            }
    ars_const['AR_ENC_RMOD'] = {
            AR_ENC_RMOD_512: "AR_ENC_RMOD_512",
            AR_ENC_RMOD_1024: "AR_ENC_RMOD_1024",
            AR_ENC_RMOD_2048: "AR_ENC_RMOD_2048",
            }
    ars_const['AR_ENC'] = {
            AR_ENC_DES_SINGLE_KEY_CBC: "AR_ENC_DES_SINGLE_KEY_CBC",
            AR_ENC_RC4_KEY_LEN_128: "AR_ENC_RC4_KEY_LEN_128",
            AR_ENC_RC4_KEY_LEN_2048: "AR_ENC_RC4_KEY_LEN_2048",
            }
    ars_const['AR_DATEPARTS'] = {
            AR_DATEPARTS_YEAR: "AR_DATEPARTS_YEAR",
            AR_DATEPARTS_MONTH: "AR_DATEPARTS_MONTH",
            AR_DATEPARTS_DAY: "AR_DATEPARTS_DAY",
            AR_DATEPARTS_WEEK: "AR_DATEPARTS_WEEK",
            AR_DATEPARTS_WEEKDAY: "AR_DATEPARTS_WEEKDAY",
            }
    ars_const['rest'] = {
            AR_REP_SCHEMA_TAG: "AR_REP_SCHEMA_TAG",
            AR_ASSIGN_SQL_SCHEMA_NAME: "AR_ASSIGN_SQL_SCHEMA_NAME",
            AR_ORDER_MAX: "AR_ORDER_MAX",
            AR_MAX_FUNC_CURRENCY_LIMIT_TEXT_SIZE: "AR_MAX_FUNC_CURRENCY_LIMIT_TEXT_SIZE",
            AR_FIELD_LIMIT_NONE: "AR_FIELD_LIMIT_NONE",
            AR_STRUCT_XML_OFFSET: "AR_STRUCT_XML_OFFSET",
            AR_STRUCT_SUPPRESS_NONSTRUCTURAL_CHANGE_TAG: "AR_STRUCT_SUPPRESS_NONSTRUCTURAL_CHANGE_TAG",
            AR_PRECISION_NONE: "AR_PRECISION_NONE",
            AR_HOUR_A_DAY: "AR_HOUR_A_DAY",
            AR_HIDDEN_INCREMENT: "AR_HIDDEN_INCREMENT",
            ARMAX_CON_LABEL_LEN: "ARMAX_CON_LABEL_LEN",
            ARMAX_CON_DESCRIPTION_LEN: "ARMAX_CON_DESCRIPTION_LEN",
            AR_CLIENT_TYPE_END_OF_RESERVED_RANGE: "AR_CLIENT_TYPE_END_OF_RESERVED_RANGE",
            AR_DIRECTORY_AR_TAG: "AR_DIRECTORY_AR_TAG",
            AR_DIRECTORY_FILE: "AR_DIRECTORY_FILE",
            AR_APPL_AUDIT_FILE: "AR_APPL_AUDIT_FILE",
            AR_APPL_VIOLATION_FILE: "AR_APPL_VIOLATION_FILE",
            AR_NO_LICENSE_DB_LIMIT: "AR_NO_LICENSE_DB_LIMIT",
            AR_NO_LICENSE_DB_COUNT: "AR_NO_LICENSE_DB_COUNT",
            AR_LICENSE_POOL_NON_RESERVED_POOL: "AR_LICENSE_POOL_NON_RESERVED_POOL",
            AR_DEFAULT_INTERVAL: "AR_DEFAULT_INTERVAL",
            AR_NATIVE_ENCRYPTION: "AR_NATIVE_ENCRYPTION",
            AR_UNICODE_ENCRYPTION: "AR_UNICODE_ENCRYPTION",
            AR_ENCRYPTION_VERSION_2: "AR_ENCRYPTION_VERSION_2",
            AR_SERVER_MIN_AUDIT_LOG_FILE_SIZE: "AR_SERVER_MIN_AUDIT_LOG_FILE_SIZE",
            AR_DEFAULT_VALUE_NONE: "AR_DEFAULT_VALUE_NONE",
            AR_START_WITH_FIRST_ENTRY: "AR_START_WITH_FIRST_ENTRY",
            AR_NO_MAX_LIST_RETRIEVE: "AR_NO_MAX_LIST_RETRIEVE",
            AR_MERGE_NO_REQUIRED_INCREMENT: "AR_MERGE_NO_REQUIRED_INCREMENT",
            AR_MERGE_NO_PATTERNS_INCREMENT: "AR_MERGE_NO_PATTERNS_INCREMENT",
            AR_MAX_LOCAL_VARIABLES: "AR_MAX_LOCAL_VARIABLES",
            AR_CURRENCY_CODE_LEN: "AR_CURRENCY_CODE_LEN",
            AR_FIELD_OFFSET: "AR_FIELD_OFFSET",
            AR_TEXT_OVERFLOW: "AR_TEXT_OVERFLOW",
            AR_DISPLAY_TAG_SQL: "AR_DISPLAY_TAG_SQL",
            AR_TWO_DIGIT_YEAR_CUTOFF_INCREMENT: "AR_TWO_DIGIT_YEAR_CUTOFF_INCREMENT"
            }
    
    ars_const['weekdays_short_en'] = {
            1 : 'Mon',
            2 : 'Tue',
            4 : 'Wed',
            8 : 'Thu',
            16 : 'Fri',
            32 : 'Sat',
            64 : 'Sun'
    }
    
    # the following part may not be run through for higher versions! they
    # are deprecated!
    if float(version) == 51:
        ars_const['AR_NOTIF_SOURCE'] = { # does not have any equivalent in later releases!
            AR_NOTIF_SOURCE_GP: "AR_NOTIF_SOURCE_GP",
            AR_NOTIF_SOURCE_AR: "AR_NOTIF_SOURCE_AR",
            AR_NOTIF_SOURCE_FIRST: "AR_NOTIF_SOURCE_FIRST",
            AR_NOTIF_SOURCE_CHECK: "AR_NOTIF_SOURCE_CHECK",
            AR_NOTIF_SOURCE_FB: "AR_NOTIF_SOURCE_FB"
        }
        ars_const['AR_NOTIFY'] = { 
            AR_NOTIFY_ACK: "AR_NOTIFY_ACK",
            AR_NOTIFY_USER_BROADCAST: "AR_NOTIFY_USER_BROADCAST",
            AR_NOTIFY_STRING_SEP: "AR_NOTIFY_STRING_SEP"
        }
        ars_const['AR_LICENSE_TYPE'].update({
            AR_LICENSE_TYPE_FIXED2: "FIXED2"
         })
        ars_const['rest'].update({
            AR_ENCRYPTION_VERSION: "AR_ENCRYPTION_VERSION",
        })
    if float(version) >= 60:
        ars_const['AR_KEYWORD'].update({
            AR_KEYWORD_ROLES: "$ROLES$",
            AR_KEYWORD_EVENTTYPE: "$EVENTTYPE$",
            AR_KEYWORD_EVENTSRCWINID: "$EVENTSRCWINID$",
            AR_KEYWORD_CURRENTWINID: "$CURRENTWINID$",
            AR_KEYWORD_LASTOPENEDWINID: "$LASTOPENEDWINID$",
            AR_KEYWORD_NO: "$NO$",
        })
        ars_const['AR_LICENSE_TYPE'].update({
                AR_LICENSE_TYPE_RESTRICTED_READ: "Restricted Read"
            })
        ars_const['AR_MULTI_MATCH'].update({
            AR_MULTI_MATCH_USE_LOCALE: "USE_LOCALE"
            })
        ars_const['AR_SERVER_INFO'].update({
            AR_SERVER_INFO_DB_CHAR_SET: "DB_CHAR_SET",
            AR_SERVER_INFO_CURR_PART_VALUE_STR: "CURR_PART_VALUE_STR",
            AR_SERVER_INFO_CURR_PART_TYPE_STR: "CURR_PART_TYPE_STR",
            AR_SERVER_INFO_CURR_PART_DATE_STR: "CURR_PART_DATE_STR",
            AR_SERVER_INFO_HOMEPAGE_FORM: "HOMEPAGE_FORM",
            AR_SERVER_INFO_DISABLE_FTS_INDEXER: "DISABLE_FTS_INDEXER",
            AR_SERVER_INFO_DISABLE_ARCHIVE: "DISABLE_ARCHIVE",
            AR_SERVER_INFO_SERVERGROUP_MEMBER: "SERVERGROUP_MEMBER",
            AR_SERVER_INFO_SERVERGROUP_LOG_FILE: "SERVERGROUP_LOG_FILE",
            AR_SERVER_INFO_FLUSH_LOG_LINES: "FLUSH_LOG_LINES",
            AR_SERVER_INFO_SERVERGROUP_INTERVAL: "SERVERGROUP_INTERVAL",
            AR_SERVER_INFO_JAVA_VM_OPTIONS: "JAVA_VM_OPTIONS",
            AR_SERVER_INFO_PER_THREAD_LOGS: "PER_THREAD_LOGS",
            AR_SERVER_INFO_CONFIG_FILE: "CONFIG_FILE",
            AR_SERVER_INFO_SSTABLE_CHUNK_SIZE: "SSTABLE_CHUNK_SIZE",
            AR_SERVER_INFO_SG_EMAIL_STATE: "SG_EMAIL_STATE",
            AR_SERVER_INFO_SG_FLASHBOARDS_STATE: "SG_FLASHBOARDS_STATE",
            AR_SERVER_INFO_SERVERGROUP_NAME: "SERVERGROUP_NAME",
            AR_SERVER_INFO_SG_ADMIN_SERVER_NAME: "SG_ADMIN_SERVER_NAME",
            AR_SERVER_INFO_LOCKED_WKFLW_LOG_MODE: "LOCKED_WKFLW_LOG_MODE",
            AR_SERVER_INFO_ROLE_CHANGE: "ROLE_CHANGE",
            AR_SERVER_INFO_SG_ADMIN_SERVER_PORT: "SG_ADMIN_SERVER_PORT"
        })
        ars_const['AR_SERVER_STAT'].update({
            AR_SERVER_STAT_WRITE_RESTRICTED_READ: 'WRITE_RESTRICTED_READ'
        })
        ars_const['AR_DPROP'].update({
            AR_DPROP_CHARFIELD_DISPLAY_TYPE: "AR_DPROP_CHARFIELD_DISPLAY_TYPE",
            AR_DPROP_AR_SERVER_NAME: "AR_DPROP_AR_SERVER_NAME",
            AR_DPROP_AUTO_FIELD_ALIGN: "AR_DPROP_AUTO_FIELD_ALIGN",
            AR_DPROP_AUTO_FIELD_COLPROP: "AR_DPROP_AUTO_FIELD_COLPROP",
            AR_DPROP_AUTO_FIELD_NAVPROP: "AR_DPROP_AUTO_FIELD_NAVPROP",
            AR_DPROP_AUTO_FIELD_NEW_COLUMN: "AR_DPROP_AUTO_FIELD_NEW_COLUMN",
            AR_DPROP_AUTO_FIELD_NEW_SECTION: "AR_DPROP_AUTO_FIELD_NEW_SECTION",
            AR_DPROP_AUTO_FIELD_ORDER: "AR_DPROP_AUTO_FIELD_ORDER",
            AR_DPROP_AUTO_FIELD_ROWNUM: "AR_DPROP_AUTO_FIELD_ROWNUM",
            AR_DPROP_AUTO_FIELD_ROWPART: "AR_DPROP_AUTO_FIELD_ROWPART",
            AR_DPROP_AUTO_FIELD_SPACER: "AR_DPROP_AUTO_FIELD_SPACER",
            AR_DPROP_AUTO_FIELD_TYPE: "AR_DPROP_AUTO_FIELD_TYPE",
            AR_DPROP_AUTO_LAYOUT: "AR_DPROP_AUTO_LAYOUT",
            AR_DPROP_AUTO_LAYOUT_STYLE_SHEET: "AR_DPROP_AUTO_LAYOUT_STYLE_SHEET",
            AR_DPROP_AUTO_LAYOUT_VUI_NAV: "AR_DPROP_AUTO_LAYOUT_VUI_NAV",
            AR_DPROP_AUTO_SET_OVERLAP_FIELD: "AR_DPROP_AUTO_SET_OVERLAP_FIELD",
            AR_DPROP_ENTRYPOINT_LABEL_DEFAULT_NEW: "AR_DPROP_ENTRYPOINT_LABEL_DEFAULT_NEW",
            AR_DPROP_ENTRYPOINT_LABEL_DEFAULT_SEARCH: "AR_DPROP_ENTRYPOINT_LABEL_DEFAULT_SEARCH",
            AR_DPROP_FORMACTION_FIELDS: "AR_DPROP_FORMACTION_FIELDS",
            AR_DPROP_FORMACTION_FLDS_EXCLUDE: "AR_DPROP_FORMACTION_FLDS_EXCLUDE",
            AR_DPROP_FORMACTION_PAGE_PROPERTIES: "AR_DPROP_FORMACTION_PAGE_PROPERTIES",
            AR_DPROP_PAGE_ARRANGEMENT: "AR_DPROP_PAGE_ARRANGEMENT",
            AR_DPROP_PAGE_ARRANGEMENT: "AR_DPROP_PAGE_ARRANGEMENT",
            AR_DPROP_TABLE_COL_WRAP_TEXT: "AR_DPROP_TABLE_COL_WRAP_TEXT",
            AR_DPROP_VIEWFIELD_BORDERS: "AR_DPROP_VIEWFIELD_BORDERS",
            AR_DPROP_VIEWFIELD_SCROLLBARS: "AR_DPROP_VIEWFIELD_SCROLLBARS"
        })
        ars_const['AR_DPROP']['AR_DPROP_TABLE_COL_WRAP_TEXT'] = {
            AR_DVAL_TABLE_COL_WRAP_TEXT_DISABLE: "TABLE_COL_WRAP_TEXT_DISABLE",
            AR_DVAL_TABLE_COL_WRAP_TEXT_ENABLE: "TABLE_COL_WRAP_TEXT_ENABLE"
        }
        ars_const['AR_DPROP']['AR_DPROP_VIEWFIELD_BORDERS'] = {
            AR_DVAL_VIEWFIELD_BORDERS_DEFAULT: "VIEWFIELD_BORDERS_DEFAULT",
            AR_DVAL_VIEWFIELD_BORDERS_ENABLE: "VIEWFIELD_BORDERS_ENABLE",
            AR_DVAL_VIEWFIELD_BORDERS_NONE: "VIEWFIELD_BORDERS_NONE"
        }
        ars_const['AR_DPROP']['AR_DPROP_VIEWFIELD_SCROLLBARS'] = {
            AR_DVAL_VIEWFIELD_SCROLLBARS_AUTO: "VIEWFIELD_SCROLLBARS_AUTO",
            AR_DVAL_VIEWFIELD_SCROLLBARS_HIDDEN: "VIEWFIELD_SCROLLBARS_HIDDEN",
            AR_DVAL_VIEWFIELD_SCROLLBARS_ON: "VIEWFIELD_SCROLLBARS_ON"
        }
        ars_const['AR_DPROP']['AR_DPROP_AUTO_FIELD_ALIGN'] = {
            AR_DVAL_AUTO_FIELD_ALIGN_LEFT: "AUTO_FIELD_ALIGN_LEFT",
            AR_DVAL_AUTO_FIELD_ALIGN_RIGHT: "AUTO_FIELD_ALIGN_RIGHT"
        }
        ars_const['AR_DPROP']['AR_DPROP_CHARFIELD_DISPLAY_TYPE'] = {
            AR_DVAL_CHARFIELD_DROPDOWN: "CHARFIELD_DROPDOWN",
            AR_DVAL_CHARFIELD_EDIT: "CHARFIELD_EDIT",
            AR_DVAL_CHARFIELD_MASKED: "CHARFIELD_MASKED"
        }
        ars_const['AR_LOCK_TYPE'] = {
            AR_LOCK_TYPE_NONE: 'NONE',
            AR_LOCK_TYPE_READONLY: 'READONLY',
            AR_LOCK_TYPE_HIDDEN: 'HIDDEN'
        }
        ars_const['AR_FUNCTION'].update({
            AR_FUNCTION_LENGTHC: "LENGTHC",
            AR_FUNCTION_LEFTC: "LEFTC",
            AR_FUNCTION_RIGHTC: "RIGHTC",
            AR_FUNCTION_LPADC: "LPADC",
            AR_FUNCTION_RPADC: "RPADC",
            AR_FUNCTION_STRSTRC: "STRSTRC",
            AR_FUNCTION_SUBSTRC: "SUBSTRC",
            AR_FUNCTION_ENCRYPT: "ENCRYPT",
            AR_FUNCTION_DECRYPT: "DECRYPT"
        })
        ars_const['AR_DPROP']['Rest'] = { # FIXME!
            AR_DVAL_AUTO_FIELD_APPTITLE: "AUTO_FIELD_APPTITLE",
            AR_DVAL_AUTO_FIELD_GROUPTITLE: "AUTO_FIELD_GROUPTITLE",
            AR_DVAL_AUTO_FIELD_LEVEL1: "AR_DVAL_AUTO_FIELD_LEVEL1",
            AR_DVAL_AUTO_FIELD_LEVEL2: "AR_DVAL_AUTO_FIELD_LEVEL2",
            AR_DVAL_AUTO_FIELD_LEVEL3: "AR_DVAL_AUTO_FIELD_LEVEL3",
            AR_DVAL_AUTO_FIELD_NAV: "AR_DVAL_AUTO_FIELD_NAV",
            AR_DVAL_AUTO_FIELD_PAGETITLE: "AR_DVAL_AUTO_FIELD_PAGETITLE",
            AR_DVAL_AUTO_FIELD_REGULAR: "AR_DVAL_AUTO_FIELD_REGULAR",
            AR_DVAL_AUTO_FIELD_SPACER_OFF: "AR_DVAL_AUTO_FIELD_SPACER_OFF",
            AR_DVAL_AUTO_FIELD_SPACER_ON: "AR_DVAL_AUTO_FIELD_SPACER_ON",
            AR_DVAL_AUTO_LAYOUT_OFF: "AR_DVAL_AUTO_LAYOUT_OFF",
            AR_DVAL_AUTO_LAYOUT_ON: "AR_DVAL_AUTO_LAYOUT_ON",
            AR_DVAL_AUTO_LAYOUT_VUI_NAV_OFF: "AR_DVAL_AUTO_LAYOUT_VUI_NAV_OFF",
            AR_DVAL_AUTO_LAYOUT_VUI_NAV_ON: "AR_DVAL_AUTO_LAYOUT_VUI_NAV_ON",
            AR_DVAL_AUTO_REFRESH_NONE: "AR_DVAL_AUTO_REFRESH_NONE",
            AR_DVAL_AUTO_REFRESH_TABLE_MAX: "AR_DVAL_AUTO_REFRESH_TABLE_MAX",
            AR_DVAL_DRILL_DOWN_ENABLE: "AR_DVAL_DRILL_DOWN_ENABLE",
            AR_DVAL_DRILL_DOWN_NONE: "AR_DVAL_DRILL_DOWN_NONE",
            AR_DVAL_EXPAND_BOX_DEFAULT: "AR_DVAL_EXPAND_BOX_DEFAULT",
            AR_DVAL_EXPAND_BOX_HIDE: "AR_DVAL_EXPAND_BOX_HIDE",
            AR_DVAL_EXPAND_BOX_SHOW: "AR_DVAL_EXPAND_BOX_SHOW",
            AR_DVAL_PANE_VISIBILITY_ADMIN: "AR_DVAL_PANE_VISIBILITY_ADMIN",
            AR_DVAL_PANE_VISIBILITY_USER_CHOICE: "AR_DVAL_PANE_VISIBILITY_USER_CHOICE",
            AR_DVAL_REFRESH_NONE: "AR_DVAL_REFRESH_NONE",
            AR_DVAL_REFRESH_TABLE_MAX: "AR_DVAL_REFRESH_TABLE_MAX",
            AR_DVAL_SORT_DIR_ASCENDING: "AR_DVAL_SORT_DIR_ASCENDING",
            AR_DVAL_SORT_DIR_DESCENDING: "AR_DVAL_SORT_DIR_DESCENDING",
            AR_DVAL_TABLE_DISPLAY_NOTIFICATION: "AR_DVAL_TABLE_DISPLAY_NOTIFICATION",
            AR_DVAL_TABLE_DISPLAY_RESULTS_LIST: "AR_DVAL_TABLE_DISPLAY_RESULTS_LIST",
            AR_DVAL_TABLE_DISPLAY_TABLE: "AR_DVAL_TABLE_DISPLAY_TABLE",
            AR_DVAL_TABLE_SELINIT_NOSEL: "AR_DVAL_TABLE_SELINIT_NOSEL",
            AR_DVAL_TABLE_SELINIT_SELFIRE: "AR_DVAL_TABLE_SELINIT_SELFIRE",
            AR_DVAL_TABLE_SELINIT_SELNOFIRE: "AR_DVAL_TABLE_SELINIT_SELNOFIRE",
            AR_DVAL_TABLE_SELREFRESH_FIRSTFIRE: "AR_DVAL_TABLE_SELREFRESH_FIRSTFIRE",
            AR_DVAL_TABLE_SELREFRESH_FIRSTNOFIRE: "AR_DVAL_TABLE_SELREFRESH_FIRSTNOFIRE",
            AR_DVAL_TABLE_SELREFRESH_NOSEL: "AR_DVAL_TABLE_SELREFRESH_NOSEL",
            AR_DVAL_TABLE_SELREFRESH_RETFIRE: "AR_DVAL_TABLE_SELREFRESH_RETFIRE",
            AR_DVAL_TABLE_SELREFRESH_RETNOFIRE: "AR_DVAL_TABLE_SELREFRESH_RETNOFIRE",
            AR_DVAL_TABLE_SELROWS_DISABLE_NO: "AR_DVAL_TABLE_SELROWS_DISABLE_NO",
            AR_DVAL_TABLE_SELROWS_DISABLE_YES: "AR_DVAL_TABLE_SELROWS_DISABLE_YES",
            AR_DVAL_TABLE_SELROWS_MULTI_SELECT: "AR_DVAL_TABLE_SELROWS_MULTI_SELECT",
            AR_DVAL_TABLE_SELROWS_SINGLE_SELECT: "AR_DVAL_TABLE_SELROWS_SINGLE_SELECT",
            AR_DVAL_AUTOFIT_COLUMNS_NONE: "AR_DVAL_AUTOFIT_COLUMNS_NONE",
            AR_DVAL_AUTOFIT_COLUMNS_SET: "AR_DVAL_AUTOFIT_COLUMNS_SET",
            AR_DVAL_AUTO_REFRESH_NONE: "AR_DVAL_AUTO_REFRESH_NONE",
            AR_DVAL_AUTO_REFRESH_TABLE_MAX: "AR_DVAL_AUTO_REFRESH_TABLE_MAX",
            AR_DVAL_DRILL_DOWN_ENABLE: "AR_DVAL_DRILL_DOWN_ENABLE",
            AR_DVAL_DRILL_DOWN_NONE: "AR_DVAL_DRILL_DOWN_NONE",
            AR_DVAL_EXPAND_BOX_DEFAULT: "AR_DVAL_EXPAND_BOX_DEFAULT",
        }
        ars_const['AR_DPROP'].update({  
            AR_SMOPROP_NONE: "AR_SMOPROP_NONE",
            AR_SMOPROP_OBJECT_VERSION: "AR_SMOPROP_OBJECT_VERSION",
            AR_SMOPROP_APP_OWNER: "AR_SMOPROP_APP_OWNER",
            AR_SMOPROP_OBJECT_LOCK_TYPE: "AR_SMOPROP_OBJECT_LOCK_TYPE",
            AR_SMOPROP_OBJECT_LOCK_KEY: "AR_SMOPROP_OBJECT_LOCK_KEY",
            AR_SMOPROP_ENTRYPOINT_DEFAULT_NEW_ORDER: "AR_SMOPROP_ENTRYPOINT_DEFAULT_NEW_ORDER",
            AR_SMOPROP_ENTRYPOINT_DEFAULT_SEARCH_ORDER: "AR_SMOPROP_ENTRYPOINT_DEFAULT_SEARCH_ORDER",
            AR_SMOPROP_NO_APP_STATS_LOGGING: "AR_SMOPROP_NO_APP_STATS_LOGGING",
            AR_SMOPROP_APP_LIC_VERSION: "AR_SMOPROP_APP_LIC_VERSION",
            AR_SMOPROP_APP_LIC_DESCRIPTOR: "AR_SMOPROP_APP_LIC_DESCRIPTOR",
            AR_SMOPROP_APP_LIC_USER_LICENSABLE: "AR_SMOPROP_APP_LIC_USER_LICENSABLE",
            AR_SMOPROP_APP_ACCESS_POINT: "AR_SMOPROP_APP_ACCESS_POINT",
            AR_SMOPROP_MAX: "AR_SMOPROP_MAX"
        })
        ars_const['AR_OPROP'].update({
            AR_OPROP_RESERVED : 'AR_OPROP_RESERVED'       
                                      })
        ars_const['ARREF'].update({
            ARREF_ENTRYPOINT_ORDER: "ENTRYPOINT_ORDER",
            ARREF_ENTRYPOINT_START_ACTLINK: "ENTRYPOINT_START_ACTLINK",
            ARREF_APP_AUTOLAYOUT_SS: "APP_AUTOLAYOUT_SS",
            ARREF_APP_FORMACTION_FIELDS: "APP_FORMACTION_FIELDS",
            ARREF_ENCAPSULATED_APP_DATA: "ENCAPSULATED_APP_DATA",
            ARREF_APP_DEFAULT_OBJ_PERMS: "APP_DEFAULT_OBJ_PERMS",
            ARREF_APP_ADD_FORMACTION_FIELDS: "APP_ADD_FORMACTION_FIELDS",
            ARREF_APP_FORMACTION_RESULTS_LIST_FIXED_HEADER: "APP_FORMACTION_RESULTS_LIST_FIXED_HEADER",
            ARREF_APP_FORMACTION_PAGE_PROPERTIES: "APP_FORMACTION_PAGE_PROPERTIES",
            ARREF_APP_OBJECT_VERSION: "APP_OBJECT_VERSION",
            ARREF_APP_PACKING_LISTS: "APP_PACKING_LISTS",
            ARREF_APP_DATA_MERGE_IMP_QUAL: "APP_DATA_MERGE_IMP_QUAL",
            ARREF_APP_DATA_MERGE_IMP_OPTION: "APP_DATA_MERGE_IMP_OPTION"
        })
        ars_const['AR_ACTIVE_LINK_ACTION_OPEN'].update({
            AR_ACTIVE_LINK_ACTION_OPEN_MODIFY: "MODIFY",
            AR_ACTIVE_LINK_ACTION_OPEN_DSPLY: "DISPLAY"})
    
    if float(version) >= 63:
        ars_const['AR_SERVER_INFO'].update({
            AR_SERVER_INFO_PLUGIN_LOOPBACK_RPC: "PLUGIN_LOOPBACK_RPC",
            AR_SERVER_INFO_CACHE_MODE: "CACHE_MODE",
            AR_SERVER_INFO_DB_FREESPACE: "DB_FREESPACE",
            AR_SERVER_INFO_GENERAL_AUTH_ERR: "GENERAL_AUTH_ERR",
            AR_SERVER_INFO_AUTH_CHAINING_MODE: "AUTH_CHAINING_MODE",
            AR_SERVER_INFO_RPC_NON_BLOCKING_IO: "RPC_NON_BLOCKING_IO",
            AR_SERVER_INFO_SYS_LOGGING_OPTIONS: "SYS_LOGGING_OPTIONS",
            AR_SERVER_INFO_EXT_AUTH_CAPABILITIES: "EXT_AUTH_CAPABILITIES",
            AR_SERVER_INFO_DSO_ERROR_RETRY: "DSO_ERROR_RETRY"
        })
        ars_const['AR_KEYWORD'].update({
            AR_KEYWORD_INBULKTRANS: "$INBULKTRANS$",
            AR_KEYWORD_FIELDID: "$FIELDID$",
            AR_KEYWORD_FIELDNAME: "$FIELDNAME$",
            AR_KEYWORD_FIELDLABEL: "$FIELDLABEL$",
            AR_KEYWORD_SERVERTIMESTAMP: "$SERVERTIMESTAMP$",
            AR_KEYWORD_GROUPIDS: "$GROUPIDS$"
        })
    
        ars_const['AR_DPROP'].update({
            AR_DPROP_VUI_DEFAULT_PROCESS: "VUI_DEFAULT_PROCESS",
            AR_DPROP_WEB_HEADER_CONTENT: "WEB_HEADER_CONTENT",
            AR_DPROP_WEB_FOOTER_CONTENT: "WEB_FOOTER_CONTENT",
            AR_DPROP_PATH_TO_BKG_IMAGE: "PATH_TO_BKG_IMAGE",
            AR_DPROP_WEB_TOOLBAR_VISIBILITY: "WEB_TOOLBAR_VISIBILITY",
            AR_DPROP_PREFIX_MINval: "PREFIX_MINval",
            AR_DPROP_PREFIX_NEW: "PREFIX_NEW",
            AR_DPROP_PREFIX_SEARCH: "PREFIX_SEARCH",
            AR_DPROP_PREFIX_MODIFY: "PREFIX_MODIFY",
            AR_DPROP_PREFIX_MODIFY_ALL: "PREFIX_MODIFY_ALL",
            AR_DPROP_PREFIX_DISPLAY: "PREFIX_DISPLAY",
            AR_DPROP_PREFIX_MATCHING_REQ: "PREFIX_MATCHING_REQ",
            AR_DPROP_PREFIX_MAXval: "PREFIX_MAXval",
            AR_DPROP_PREFIX_NO_MATCHING_REQ: "PREFIX_NO_MATCHING_REQ"
        })
        ars_const['AR_OPROP'].update({
            AR_SMOPROP_APP_BSM_TAG: "AR_SMOPROP_APP_BSM_TAG"
        })
        ars_const['AR_FIELD'].update({
            AR_FIELD_INHERITANCE: "AR_FIELD_INHERITANCE"
        })
        ars_const['AR_ARCHIVE'] = {
            AR_ARCHIVE_NONE : "None",
            AR_ARCHIVE_FORM: "AR_ARCHIVE_FORM",
            AR_ARCHIVE_DELETE: "AR_ARCHIVE_DELETE",
            AR_ARCHIVE_FILE_XML: "AR_ARCHIVE_FILE_XML",
            AR_ARCHIVE_FILE_ARX: "AR_ARCHIVE_FILE_ARX",
            AR_ARCHIVE_NO_ATTACHMENTS: "AR_ARCHIVE_NO_ATTACHMENTS",
            AR_ARCHIVE_NO_DIARY: "AR_ARCHIVE_NO_DIARY"
        }
        ars_const['AR_SVR_EVENT_ARCHIVE'] = {
            AR_SVR_EVENT_ARCHIVE_FORM: "AR_SVR_EVENT_ARCHIVE_FORM",
            AR_SVR_EVENT_ARCHIVE_DELETE: "AR_SVR_EVENT_ARCHIVE_DELETE",
            AR_SVR_EVENT_ARCHIVE_FORM_DELETE: "AR_SVR_EVENT_ARCHIVE_FORM_DELETE",
            AR_SVR_EVENT_ARCHIVE_XML: "AR_SVR_EVENT_ARCHIVE_XML",
            AR_SVR_EVENT_ARCHIVE_ARX: "AR_SVR_EVENT_ARCHIVE_ARX"
        }
        ars_const['AR_SVR_EVENT_SERVGROUP'] = {
            AR_SVR_EVENT_SERVGROUP_FAILOVER: "AR_SVR_EVENT_SERVGROUP_FAILOVER",
            AR_SVR_EVENT_SERVGROUP_RELINQUISH: "AR_SVR_EVENT_SERVGROUP_RELINQUISH",
            AR_SVR_EVENT_SERVGROUP_TAKEOVER: "AR_SVR_EVENT_SERVGROUP_TAKEOVER"
        }
        ars_const['AR_SESS'].update({
            AR_SESS_CHUNK_RESPONSE_SIZE: "AR_SESS_CHUNK_RESPONSE_SIZE",
            AR_SESS_TIMEOUT_NORMAL: "AR_SESS_TIMEOUT_NORMAL",
            AR_SESS_TIMEOUT_LONG: "AR_SESS_TIMEOUT_LONG",
            AR_SESS_TIMEOUT_XLONG: "AR_SESS_TIMEOUT_XLONG",
            AR_SESS_LOCK_TO_SOCKET_NUMBER: "AR_SESS_LOCK_TO_SOCKET_NUMBER",
            AR_SESS_OVERRIDE_PREV_IP: "AR_SESS_OVERRIDE_PREV_IP",
            AR_SESS_API_CMD_LOG: "AR_SESS_API_CMD_LOG",
            AR_SESS_API_RES_LOG: "AR_SESS_API_RES_LOG"
        })
        ars_const['AR_CLIENT_TYPE'].update({
            AR_CLIENT_TYPE_SIGNAL: "arsignal",
            AR_CLIENT_TYPE_DEBUGGER: "debugger",
            AR_CLIENT_TYPE_OBJSTR: "object store API",
            AR_CLIENT_TYPE_OBJSTR_SYNC: "object store sync utility",
            AR_CLIENT_TYPE_CHANGE_ID: "archgid",
            AR_CLIENT_TYPE_LABEL: "arlabel"
       })
    if float(version) >= 70:
        ars_const['AR_OPROP'].update({
            AR_OPROP_NEXT_ID_BLOCK_SIZE: "AR_OPROP_NEXT_ID_BLOCK_SIZE",
            AR_OPROP_GUIDE_PARAMETERS: "AR_OPROP_GUIDE_PARAMETERS",
            AR_SMOPROP_PRIMARY_FIELDSET: "AR_SMOPROP_PRIMARY_FIELDSET"
        })
        ars_const['AR_CLIENT_TYPE'].update({
            AR_CLIENT_TYPE_SERVER_ADMIN_PLUGIN: "Server Admin plugin",
            AR_CLIENT_TYPE_SIM_PUBLISHING_SERVER: "bmc sim publishing server",
            AR_CLIENT_TYPE_SIM_SME: "bmc sim service model editor",
            AR_CLIENT_TYPE_CMDB_ENGINE: "cmdb engine",
            AR_CLIENT_TYPE_CMDB_DRIVER: "cmdb driver",
            AR_CLIENT_TYPE_RECON_ENGINE: "cmdb reconciliation engine"
        })
        ars_const['AR_SERVER_INFO'].update({
            AR_SERVER_INFO_PREF_SERVER_OPTION: "PREF_SERVER_OPTION",
            AR_SERVER_INFO_FTINDEXER_LOG_FILE: "FTINDEXER_LOG_FILE",
            AR_SERVER_INFO_EXCEPTION_OPTION: "EXCEPTION_OPTION",
            AR_SERVER_INFO_ERROR_EXCEPTION_LIST: "ERROR_EXCEPTION_LIST",
            AR_SERVER_INFO_DSO_MAX_QUERY_SIZE: "DSO_MAX_QUERY_SIZE",
            AR_SERVER_INFO_ADMIN_OP_TRACKING: "ADMIN_OP_TRACKING",
            AR_SERVER_INFO_ADMIN_OP_PROGRESS: "ADMIN_OP_PROGRESS",
            AR_SERVER_INFO_PLUGIN_DEFAULT_TIMEOUT: "PLUGIN_DEFAULT_TIMEOUT",
            AR_SERVER_INFO_EA_IGNORE_EXCESS_GROUPS: "EA_IGNORE_EXCESS_GROUPS",
            AR_SERVER_INFO_EA_GROUP_MAPPING: "EA_GROUP_MAPPING",
            AR_SERVER_INFO_PLUGIN_LOG_LEVEL: "PLUGIN_LOG_LEVEL",
            AR_SERVER_INFO_FT_THRESHOLD_LOW: "FT_THRESHOLD_LOW",
            AR_SERVER_INFO_FT_THRESHOLD_HIGH: "FT_THRESHOLD_HIGH",
            AR_SERVER_INFO_NOTIFY_WEB_PATH: "NOTIFY_WEB_PATH",
            AR_SERVER_INFO_DISABLE_NON_UNICODE_CLIENTS: "DISABLE_NON_UNICODE_CLIENTS",
            AR_SERVER_INFO_FT_COLLECTION_DIR: "FT_COLLECTION_DIR",
            AR_SERVER_INFO_FT_CONFIGURATION_DIR: "FT_CONFIGURATION_DIR",
            AR_SERVER_INFO_FT_TEMP_DIR: "FT_TEMP_DIR",
            AR_SERVER_INFO_FT_REINDEX: "FT_REINDEX",
            AR_SERVER_INFO_FT_DISABLE_SEARCH: "FT_DISABLE_SEARCH",
            AR_SERVER_INFO_FT_CASE_SENSITIVITY: "FT_CASE_SENSITIVITY",
            AR_SERVER_INFO_FT_SEARCH_MATCH_OP: "FT_SEARCH_MATCH_OP",
            AR_SERVER_INFO_FT_STOP_WORDS: "FT_STOP_WORDS",
            AR_SERVER_INFO_FT_RECOVERY_INTERVAL: "FT_RECOVERY_INTERVAL",
            AR_SERVER_INFO_FT_OPTIMIZE_THRESHOLD: "FT_OPTIMIZE_THRESHOLD",
            AR_SERVER_INFO_MAX_PASSWORD_ATTEMPTS: "MAX_PASSWORD_ATTEMPTS",
            AR_SERVER_INFO_GUESTS_RESTRICT_READ: "GUESTS_RESTRICT_READ",
            AR_SERVER_INFO_ORACLE_CLOB_STORE_INROW: "ORACLE_CLOB_STORE_INROW",
            AR_SERVER_INFO_NEXT_ID_BLOCK_SIZE: "NEXT_ID_BLOCK_SIZE",
            AR_SERVER_INFO_NEXT_ID_COMMIT: "NEXT_ID_COMMIT",
            AR_SERVER_INFO_RPC_CLIENT_XDR_LIMIT: "RPC_CLIENT_XDR_LIMIT"
            })
        ars_const['AR_KEYWORD'].update({
            AR_KEYWORD_EVENTDATA: "$EVENTDATA$"})
        ars_const['AR_IMPORT_OPT'].update({
            AR_IMPORT_OPT_NOT_OVERWRITE_PERMISSION: 'NOT_OVERWRITE_PERMISSION'
        })
        ars_const['AR_PLUGIN_LOG'] = {
            AR_PLUGIN_LOG_ALL : 'ALL',
            AR_PLUGIN_LOG_CONFIG : 'CONFIG',
            AR_PLUGIN_LOG_FINE : 'FINE',
            AR_PLUGIN_LOG_FINER : 'FINER',
            AR_PLUGIN_LOG_FINEST : 'FINEST',
            AR_PLUGIN_LOG_INFO : 'INFO',
            AR_PLUGIN_LOG_OFF : 'OFF',
            AR_PLUGIN_LOG_SEVERE : 'SEVERE',
            AR_PLUGIN_LOG_WARNING : 'WARNING'
        }
        ars_const['AR_AUDIT'] = {
            AR_AUDIT_COPY : 'COPY',
            AR_AUDIT_LOG : 'LOG',
            AR_AUDIT_LOG_SHADOW : 'LOG_SHADOW',
            AR_AUDIT_NONE : 'NONE'
        }
        ars_const['AR_AUTH_CHAINING_MODE'] = {
            AR_AUTH_CHAINING_MODE_ARS_AREA_OS : 'ARS_AREA_OS',
            AR_AUTH_CHAINING_MODE_ARS_OS_AREA : 'ARS_OS_AREA',
            AR_AUTH_CHAINING_MODE_MAX : 'MAX'
        }
        ars_const['AR_DEBUG'].update({
            AR_DEBUG_SERVER_FTINDEXER : 'SERVER_FTINDEXER'
        })
        ars_const['AR_DPROP'].update({
            AR_DPROP_AR_GRAPH_PLUGIN_NAME : 'AR_GRAPH_PLUGIN_NAME',
            AR_DPROP_EXPAND_COLLAPSE_TREE_LEVELS : 'EXPAND_COLLAPSE_TREE_LEVELS',
            AR_DPROP_FIELD_CUSTOMSTYLE : 'FIELD_CUSTOMSTYLE',
            AR_DPROP_NAVBAR_INITIAL_SELECTED_ITEM : 'NAVBAR_INITIAL_SELECTED_ITEM',
            AR_DPROP_NAVBAR_SELECT_ITEM_ON_CLICK : 'NAVBAR_SELECT_ITEM_ON_CLICK',
            AR_DPROP_NAVBAR_WORKFLOW_ON_SELECTED_ITEM : 'NAVBAR_WORKFLOW_ON_SELECTED_ITEM',
            AR_DPROP_TABLE_PREFERENCES : 'TABLE_PREFERENCES',
            AR_DPROP_TABLE_TREE_CUSTOM_NULL_VALUE : 'TABLE_TREE_CUSTOM_NULL_VALUE'
        })
        ars_const['AR_DPROP']['AR_DPROP_CNTL_TYPE'].update({
            AR_DVAL_CNTL_HORIZNAV : 'HORIZNAV',
            AR_DVAL_CNTL_NAV_ITEM : 'NAV_ITEM',
            AR_DVAL_CNTL_VERTICALNAV : 'VERTICALNAV'
        })
        ars_const['AR_DPROP']['AR_DPROP_EXPAND_COLLAPSE_TREE_LEVELS'] = {
            AR_DVAL_COLLAPSE_ALL_LEVELS: 'COLLAPSE_ALL_LEVELS',
            AR_DVAL_EXPAND_ALL_LEVELS: 'EXPAND_ALL_LEVELS'
        }
        ars_const['AR_DPROP']['AR_DPROP_NAVBAR_WORKFLOW_ON_SELECTED_ITEM'] = {
            AR_DVAL_NAVBAR_SELITEM_FIRE: 'SELITEM_FIRE',
            AR_DVAL_NAVBAR_SELITEM_NOFIRE: 'SELITEM_NOFIRE'
        }
        ars_const['AR_DPROP']['AR_DPROP_TABLE_DISPLAY_TYPE'].update({
            AR_DVAL_TABLE_DISPLAY_MULTI_TABLE_TREE: 'MULTI_TABLE_TREE',
            AR_DVAL_TABLE_DISPLAY_SINGLE_TABLE_TREE: 'SINGLE_TABLE_TREE'
        })
    
        ars_const['AR_EXCEPTION_DIAG'] = {
            AR_EXCEPTION_DIAG_EXCLUDE_STACK : 'EXCLUDE_STACK',
            AR_EXCEPTION_DIAG_INCLUDE_ALL : 'INCLUDE_ALL'
        }
        ars_const['AR_USER_LIST'].update({
            AR_USER_LIST_INVALID: 'INVALID'
        })
        ars_const['AR_FIELD_BITOPTION'] = {
            AR_FIELD_BITOPTION_AUDIT : 'AUDIT',
            AR_FIELD_BITOPTION_AUDIT_LOG_KEY_MASK : 'AUDIT_LOG_KEY_MASK',
            AR_FIELD_BITOPTION_AUDIT_MASK : 'AUDIT_MASK',
            AR_FIELD_BITOPTION_COPY : 'COPY',
            AR_FIELD_BITOPTION_LOG_KEY1 : 'LOG_KEY1',
            AR_FIELD_BITOPTION_LOG_KEY2 : 'LOG_KEY2',
            AR_FIELD_BITOPTION_LOG_KEY3 : 'LOG_KEY3',
            AR_FIELD_BITOPTION_NONE : 'NONE'
        }
        ars_const['AR_FIELD_BITOPTION'] = {
            AR_FULL_TEXT_DISABLE_SEARCHING: 'DISABLE_SEARCHING',
            AR_FULL_TEXT_ENABLE_SEARCHING: 'ENABLE_SEARCHING',
            AR_FULL_TEXT_SEARCH_CASE_INSENSITIVE: 'SEARCH_CASE_INSENSITIVE',
            AR_FULL_TEXT_SEARCH_CASE_SENSITIVE: 'SEARCH_CASE_SENSITIVE'
        }
        ars_const['AR_GROUP_TYPE'].update({
            AR_GROUP_TYPE_NONE : 'NONE'
        })
        ars_const['AR_SVR_EVENT'].update({
            AR_SVR_EVENT_COMPGROUP_ADDED : 'COMPGROUP_ADDED',
            AR_SVR_EVENT_COMPGROUP_DELETED : 'COMPGROUP_DELETED',
            AR_SVR_EVENT_COMPGROUP_MODIFIED: 'COMPGROUP_MODIFIED'
        })
        ars_const['AR_PREF_SERVER'] = {
            AR_PREF_SERVER_USER_OPTION : 'USER_OPTION',
            AR_PREF_SERVER_USE_NOT_THIS_SERVER : 'USE_NOT_THIS_SERVER',
            AR_PREF_SERVER_USE_THIS_SERVER : 'USE_THIS_SERVER'
        }
        ars_const['AR_SETFIELD_OPT'] = {
            AR_SETFIELD_OPT_DELETE_LISTED_DISPLAY_INSTANCES : 'DELETE_LISTED_DISPLAY_INSTANCES',
            AR_SETFIELD_OPT_PRESERVE_DELETE_BITS : 'PRESERVE_DELETE_BITS',
            AR_SETFIELD_OPT_PRESERVE_UNLISTED_DISPLAY_INSTANCES : 'PRESERVE_UNLISTED_DISPLAY_INSTANCES'
        }
        ars_const['AR_SIGNAL'].update({
            AR_SIGNAL_COMPUTED_GROUP_CHANGED : 'COMPUTED_GROUP_CHANGED',
            AR_SIGNAL_RECACHE : 'RECACHE'
        })
    
        ars_const['rest'].update({
            AR_ENCRYPTION_VERSION_1: 'AR_ENCRYPTION_VERSION_1',
            AR_ENCRYPTION_VERSION_3: 'AR_ENCRYPTION_VERSION_3',
            AR_EXT_AUTH_DATA_NO_NOTIF_VALIDATION : 'AR_EXT_AUTH_DATA_NO_NOTIF_VALIDATION',
            AR_FULLTEXTINFO_TEMP_DIR : 'AR_FULLTEXTINFO_TEMP_DIR',
            AR_FULLTEXT_OPTIONS_LITERAL : 'AR_FULLTEXT_OPTIONS_LITERAL',
            AR_MAX_DECIMAL_FIELD_VALUE_LIMIT : 'AR_MAX_DECIMAL_FIELD_VALUE_LIMIT',
            AR_MAX_ENCRYPTED_PASSWORD_SIZE : 'AR_MAX_ENCRYPTED_PASSWORD_SIZE',
            AR_MAX_PASSWORD_SIZE : 'AR_MAX_PASSWORD_SIZE',
            AR_MIN_DECIMAL_FIELD_VALUE_LIMIT : 'AR_MIN_DECIMAL_FIELD_VALUE_LIMIT',
            AR_REPORT_ATTR_CHAR_ENCODING : 'AR_REPORT_ATTR_CHAR_ENCODING',
            AR_RETRIEVE_ALL_ENTRIES : 'AR_RETRIEVE_ALL_ENTRIES',
            AR_SCHEMA_SHADOW_DELETE : 'AR_SCHEMA_SHADOW_DELETE',
     })
    if float(version) == 71:
        # the following constants have been renamed in 7.5 and would lead to
        # errors.
        ars_const['AR_KEYWORD'].update({
            AR_KEYWORD_FILTER_ERRNO: "$FILTER_ERRNO$",
            AR_KEYWORD_FILTER_ERRMSG: "$FILTER_ERRMSG$",
            AR_KEYWORD_FILTER_ERRAPPENDMSG: "$FILTER_ERRAPPENDMSG$"})
        
    if float(version) >= 71:
        ARActiveLinkActionStruct._mapping_.update({
           AR_ACTIVE_LINK_ACTION_SERVICE: 'u.service'})
        
        ars_const['AR_ACTIVE_LINK_ACTION'] .update({
           AR_ACTIVE_LINK_ACTION_SERVICE: 'SERVICE'})
        
        ars_const['AR_EXECUTE_ON'].update ({
                    AR_EXECUTE_ON_EVENT : 'EVENT'})
        ars_const['AR_CACHE_DPROP'] = {
            AR_CACHE_DPROP_ALL : '',
            AR_CACHE_DPROP_FIELD : 'DPROP_FIELD',
            AR_CACHE_DPROP_NONE : 'DPROP_NONE',
            AR_CACHE_DPROP_VUI : 'DPROP_VUI'
        }
        ars_const['AR_CLIENT_TYPE'].update({
            AR_CLIENT_TYPE_ASSIGNMENT_ENGINE: 'ASSIGNMENT_ENGINE',
            AR_CLIENT_TYPE_WEBSERVICE: 'WEBSERVICE'
        })
        ars_const['AR_SERVER_INFO'].update({
            AR_SERVER_INFO_CACHE_DISP_PROP : 'CACHE_DISP_PROP',
            AR_SERVER_INFO_DB_MAX_ATTACH_SIZE : 'DB_MAX_ATTACH_SIZE',
            AR_SERVER_INFO_DB_MAX_TEXT_SIZE : 'DB_MAX_TEXT_SIZE',
            AR_SERVER_INFO_GUID_PREFIX : 'GUID_PREFIX',
            AR_SERVER_INFO_MINIMUM_CMDB_API_VER : 'MINIMUM_CMDB_API_VER',
            AR_SERVER_INFO_MULTIPLE_ARSYSTEM_SERVERS : 'MULTIPLE_ARSYSTEM_SERVERS',
            AR_SERVER_INFO_ORACLE_BULK_FETCH_COUNT : 'ORACLE_BULK_FETCH_COUNT',
            AR_SERVER_INFO_PLUGIN_PORT : 'PLUGIN_PORT',
            AR_SERVER_INFO_USE_CON_NAME_IN_STATS : 'USE_CON_NAME_IN_STATS'
        })
        ars_const['AR_IMPORT_OPT'].update({
            AR_IMPORT_OPT_PRESERVE_HISTORY: 'PRESERVE_HISTORY',
            AR_IMPORT_OPT_WORKFLOW_MERGE_ATTACHLIST: 'WORKFLOW_MERGE_ATTACHLIST',
            AR_IMPORT_OPT_WORKFLOW_PRESERVE_DEFN: 'WORKFLOW_PRESERVE_DEFN'
        })
        ars_const['AR_CORE_FIELDS_OPTION'] = {
            AR_CORE_FIELDS_OPTION_DISABLE_STATUS_HISTORY : 'DISABLE_STATUS_HISTORY',
            AR_CORE_FIELDS_OPTION_NONE : 'NONE'
        }
        ars_const['AR_AUDIT'].update({
            AR_AUDIT_FORCE_DISABLE : 'FORCE_DISABLE'
        })
        
        ars_const['AR_KEY_OPERATION'].update({
            AR_KEY_OPERATION_ERRHANDLE : 'AR_KEY_OPERATION_ERRHANDLE',
            AR_KEY_OPERATION_SERVICE : 'AR_KEY_OPERATION_SERVICE',
        })
        
        ars_const['AR_SVR_EVENT'].update({
            AR_SVR_EVENT_APPLICATION_ADDED : 'AR_SVR_EVENT_APPLICATION_ADDED',
            AR_SVR_EVENT_APPLICATION_DELETED : 'AR_SVR_EVENT_APPLICATION_DELETED',
            AR_SVR_EVENT_APPLICATION_MODIFIED : 'AR_SVR_EVENT_APPLICATION_MODIFIED',
            AR_SVR_EVENT_CHG_LICENSES : 'AR_SVR_EVENT_CHG_LICENSES',
            AR_SVR_EVENT_IMPORT_CREATE_OBJECT : 'AR_SVR_EVENT_IMPORT_CREATE_OBJECT',
            AR_SVR_EVENT_IMPORT_SET_OBJECT : 'AR_SVR_EVENT_IMPORT_SET_OBJECT',
            AR_SVR_EVENT_ROLE_ADDED : 'AR_SVR_EVENT_ROLE_ADDED',
            AR_SVR_EVENT_ROLE_DELETED : 'AR_SVR_EVENT_ROLE_DELETED',
            AR_SVR_EVENT_ROLE_MODIFIED : 'AR_SVR_EVENT_ROLE_MODIFIED'
        })
        
        ars_const['AR_USER_LIST'].update({
            AR_USER_LIST_APPLICATION : 'AR_USER_LIST_APPLICATION'
        })
        ars_const['AR_DPROP'].update({
            AR_DPROP_BUTTON_ALT_TEXT : 'BUTTON_ALT_TEXT',
            AR_DPROP_QUERY_LIST_BKG_COLOR : 'QUERY_LIST_BKG_COLOR',
            AR_DPROP_TABLE_USE_LOCALE : 'TABLE_USE_LOCALE',
            AR_DPROP_AUTO_MAXIMIZE_WINDOW : 'AUTO_MAXIMIZE_WINDOW',
            AR_DPROP_ATTACH_DESELECT_LABEL : 'ATTACH_DESELECT_LABEL'
        })
        ars_const['AR_DPROP']['AR_DVAL_AUTO_MAXIMIZE_WINDOW'] = {
            AR_DVAL_AUTO_MAXIMIZE_WINDOW_DISABLE : 'AUTO_MAXIMIZE_WINDOW_DISABLE',
            AR_DVAL_AUTO_MAXIMIZE_WINDOW_ENABLE : 'AUTO_MAXIMIZE_WINDOW_ENABLE'
        }
        ars_const['AR_OPROP'].update({
            AR_OPROP_CACHE_DISP_PROP : 'AR_OPROP_CACHE_DISP_PROP',
            AR_OPROP_CORE_FIELDS_OPTION_MASK : 'AR_OPROP_CORE_FIELDS_OPTION_MASK',
            AR_OPROP_POOL_NUMBER : 'AR_OPROP_POOL_NUMBER'
        })
        ars_const['AR_OPERATION'].update({
            AR_OPERATION_SERVICE : 'AR_OPERATION_SERVICE',
        })
        ars_const['rest'].update({
            ARI_WF_SETOPTION_OW : 'ARI_WF_SETOPTION_OW',
#            ARTIMESTAMP_MAX : 'ARTIMESTAMP_MAX',
            AR_CURRENT_CMDB_API_VERSION : 'AR_CURRENT_CMDB_API_VERSION',
            AR_MAX_CURRENCY_FIELD_VALUE_LIMIT : 'AR_MAX_CURRENCY_FIELD_VALUE_LIMIT',
            AR_MAX_GUID_PREFIX_SIZE : 'AR_MAX_GUID_PREFIX_SIZE',
            AR_MIN_CURRENCY_FIELD_VALUE_LIMIT : 'AR_MIN_CURRENCY_FIELD_VALUE_LIMIT',
        })
    if float(version) >= 75:
        ars_const['AR_CHECKDB'] = {
            AR_CHECKDB_ASSIGN_SHORT_LONG : 'AR_CHECKDB_ASSIGN_SHORT_LONG',
            AR_CHECKDB_PROP_SHORT_LONG : 'AR_CHECKDB_PROP_SHORT_LONG',
            AR_CHECKDB_QUERY_SHORT_LONG : 'AR_CHECKDB_QUERY_SHORT_LONG',
            AR_CHECKDB_TYPE_NONE : 'AR_CHECKDB_TYPE_NONE'
        }
        ars_const['AR_CLIENT_TYPE'].update({
            AR_CLIENT_TYPE_DEVELOPER_STUDIO: 'DEVELOPER_STUDIO',
            AR_CLIENT_TYPE_FT_TEXT_READER: 'FT_TEXT_READER',
            AR_CLIENT_TYPE_NORMALIZATION_ENGINE: 'NORMALIZATION_ENGINE'
        })
        ars_const['AR_DPROP'].update({
            AR_DPROP_CHARFIELD_AUTO_COMPLETE: "AR_DPROP_CHARFIELD_AUTO_COMPLETE",
            AR_DPROP_CHARFIELD_AUTO_COMPLETE_MATCH_BY: 'AR_DPROP_CHARFIELD_AUTO_COMPLETE_MATCH_BY',
            AR_DPROP_COLOR_FILL_GRADIENT: 'AR_DPROP_COLOR_FILL_GRADIENT',
            AR_DPROP_COLOR_FILL_GRADIENT_EFFECT: 'AR_DPROP_COLOR_FILL_GRADIENT_EFFECT',
            AR_DPROP_COLOR_FILL_OPACITY: 'AR_DPROP_COLOR_FILL_OPACITY',
            AR_DPROP_COLOR_GRADIENT_EFFECT_HEADER: 'AR_DPROP_COLOR_GRADIENT_EFFECT_HEADER',
            AR_DPROP_COLOR_GRADIENT_HEADER: 'AR_DPROP_COLOR_GRADIENT_HEADER',
            AR_DPROP_ENABLE_CLEAR: 'AR_DPROP_ENABLE_CLEAR',
            AR_DPROP_FIELD_HIGHLIGHT: 'AR_DPROP_FIELD_HIGHLIGHT',
            AR_DPROP_FIELD_HIGHLIGHT_END_COLOR: 'AR_DPROP_FIELD_HIGHLIGHT_END_COLOR',
            AR_DPROP_FIELD_HIGHLIGHT_START_COLOR: 'AR_DPROP_FIELD_HIGHLIGHT_START_COLOR',
            AR_DPROP_FIELD_MAX_HEIGHT: 'AR_DPROP_FIELD_MAX_HEIGHT',
            AR_DPROP_FIELD_MAX_WIDTH: 'AR_DPROP_FIELD_MAX_WIDTH',
            AR_DPROP_FIELD_MIN_HEIGHT: 'AR_DPROP_FIELD_MIN_HEIGHT',
            AR_DPROP_FIELD_MIN_WIDTH: 'AR_DPROP_FIELD_MIN_WIDTH',
            AR_DPROP_FIELD_ROUNDED: 'AR_DPROP_FIELD_ROUNDED',
            AR_DPROP_FIELD_ROUNDED_BOTTOM_LEFT_RADIUS: 'AR_DPROP_FIELD_ROUNDED_BOTTOM_LEFT_RADIUS',
            AR_DPROP_FIELD_ROUNDED_BOTTOM_RIGHT_RADIUS: 'AR_DPROP_FIELD_ROUNDED_BOTTOM_RIGHT_RADIUS',
            AR_DPROP_FIELD_ROUNDED_TOP_LEFT_RADIUS: 'AR_DPROP_FIELD_ROUNDED_TOP_LEFT_RADIUS',
            AR_DPROP_FIELD_ROUNDED_TOP_RIGHT_RADIUS: 'AR_DPROP_FIELD_ROUNDED_TOP_RIGHT_RADIUS',
            AR_DPROP_FORM_LOCK_ALLVUI: 'AR_DPROP_FORM_LOCK_ALLVUI',
            AR_DPROP_HIDE_PANELHOLDER_BORDERS: 'AR_DPROP_HIDE_PANELHOLDER_BORDERS',
            AR_DPROP_LAYOUT_POLICY: 'AR_DPROP_LAYOUT_POLICY',
            AR_DPROP_LOCALIZATION_REQUIRED: 'AR_DPROP_LOCALIZATION_REQUIRED',
            AR_DPROP_ORIENTATION: 'AR_DPROP_ORIENTATION',
            AR_DPROP_PAGEHOLDER_DISPLAY_TYPE: 'AR_DPROP_PAGEHOLDER_DISPLAY_TYPE',
            AR_DPROP_PAGEHOLDER_INIT_PAGE: 'AR_DPROP_PAGEHOLDER_INIT_PAGE',
            AR_DPROP_PAGEHOLDER_MARGIN_BOTTOM: 'AR_DPROP_PAGEHOLDER_MARGIN_BOTTOM',
            AR_DPROP_PAGEHOLDER_MARGIN_LEFT: 'AR_DPROP_PAGEHOLDER_MARGIN_LEFT',
            AR_DPROP_PAGEHOLDER_MARGIN_RIGHT: 'AR_DPROP_PAGEHOLDER_MARGIN_RIGHT',
            AR_DPROP_PAGEHOLDER_MARGIN_TOP: 'AR_DPROP_PAGEHOLDER_MARGIN_TOP',
            AR_DPROP_PAGEHOLDER_SPACING: 'AR_DPROP_PAGEHOLDER_SPACING',
            AR_DPROP_PAGE_BODY_STATE: 'AR_DPROP_PAGE_BODY_STATE',
            AR_DPROP_PAGE_FIELD_TYPE:'AR_DPROP_PAGE_FIELD_TYPE',
            AR_DPROP_PAGE_HEADER_COLOR: 'AR_DPROP_PAGE_HEADER_COLOR',
            AR_DPROP_PAGE_HEADER_STATE: 'AR_DPROP_PAGE_HEADER_STATE',
            AR_DPROP_PAGE_INITIAL_SIZE: 'AR_DPROP_PAGE_INITIAL_SIZE',
            AR_DPROP_PAGE_MAX_SIZE: 'AR_DPROP_PAGE_MAX_SIZE',
            AR_DPROP_PAGE_MIN_SIZE: 'AR_DPROP_PAGE_MIN_SIZE',
            AR_DPROP_PANELHOLDER_SPLITTER: 'AR_DPROP_PANELHOLDER_SPLITTER',
            AR_DPROP_TABLE_PAGE_ARRAY_BOTTOM_MARGIN: 'AR_DPROP_TABLE_PAGE_ARRAY_BOTTOM_MARGIN',
            AR_DPROP_TABLE_PAGE_ARRAY_HOR_SPACE: 'AR_DPROP_TABLE_PAGE_ARRAY_HOR_SPACE',
            AR_DPROP_TABLE_PAGE_ARRAY_LEFT_MARGIN: 'AR_DPROP_TABLE_PAGE_ARRAY_LEFT_MARGIN',
            AR_DPROP_TABLE_PAGE_ARRAY_RIGHT_MARGIN: 'AR_DPROP_TABLE_PAGE_ARRAY_RIGHT_MARGIN',
            AR_DPROP_TABLE_PAGE_ARRAY_TOP_MARGIN: 'AR_DPROP_TABLE_PAGE_ARRAY_TOP_MARGIN',
            AR_DPROP_TABLE_PAGE_ARRAY_VER_SPACE: 'AR_DPROP_TABLE_PAGE_ARRAY_VER_SPACE',
            AR_DPROP_TABLE_PAGE_VISIBLE_COLUMNS: 'AR_DPROP_TABLE_PAGE_VISIBLE_COLUMNS',
            AR_DPROP_TABLE_PANEL_BBOX: 'AR_DPROP_TABLE_PANEL_BBOX',
            AR_DPROP_VIEW_RTL: 'AR_DPROP_VIEW_RTL',
            AR_DPROP_VUI_LOCK_VUI: 'AR_DPROP_VUI_LOCK_VUI'
        })
        ars_const['AR_DPROP']['AR_DPROP_TABLE_DISPLAY_TYPE'].update({
            AR_DVAL_TABLE_DISPLAY_PAGE_ARRAY : 'AR_DVAL_TABLE_DISPLAY_PAGE_ARRAY'
        })
        ars_const['AR_DPROP']['AR_DPROP_TABLE_COL_DISPLAY_TYPE'].update({
            AR_DVAL_TABLE_COL_DISPLAY_PAGE_DATA : 'AR_DVAL_TABLE_COL_DISPLAY_PAGE_DATA'
        })
        ars_const['AR_DPROP']['AR_DPROP_VIEW_RTL'] = {
            AR_DVAL_VIEW_RTL_DISABLE : 'AR_DVAL_VIEW_RTL_DISABLE',
            AR_DVAL_VIEW_RTL_ENABLE : 'AR_DVAL_VIEW_RTL_ENABLE'
        }
        ars_const['AR_OPROP'].update({
            AR_OPROP_TRANSACTION_HANDLE_ID : 'AR_OPROP_TRANSACTION_HANDLE_ID',
            AR_OPROP_MAX_VENDOR_TEMP_TABLES : ':AR_OPROP_MAX_VENDOR_TEMP_TABLES'
        })
        ars_const['AR_ENC'].update({
            AR_ENC_AES_FIPS_KEY_LEN_128: "AR_ENC_AES_FIPS_KEY_LEN_128",
            AR_ENC_AES_FIPS_KEY_LEN_256: 'AR_ENC_AES_FIPS_KEY_LEN_256',
            AR_ENC_AES_KEY_LEN_128: 'AR_ENC_AES_KEY_LEN_128',
            AR_ENC_AES_KEY_LEN_256: 'AR_ENC_AES_KEY_LEN_256'
        })
        ars_const['AR_EXECUTE_ON'].update ({
            AR_EXECUTE_ON_HOVER_FIELD : 'AR_EXECUTE_ON_HOVER_FIELD',
            AR_EXECUTE_ON_HOVER_FIELD_DATA: 'AR_EXECUTE_ON_HOVER_FIELD_DATA',
            AR_EXECUTE_ON_HOVER_FIELD_LABEL: 'AR_EXECUTE_ON_HOVER_FIELD_LABEL',
            AR_EXECUTE_ON_MASK_EXP_V10: 'AR_EXECUTE_ON_MASK_EXP_V10',
            AR_EXECUTE_ON_MASK_FOCUS_FIELD: 'AR_EXECUTE_ON_MASK_FOCUS_FIELD',
            AR_EXECUTE_ON_MASK_MAX: 'AR_EXECUTE_ON_MASK_MAX',
            AR_EXECUTE_ON_PAGE_COLLAPSE: 'AR_EXECUTE_ON_PAGE_COLLAPSE',
            AR_EXECUTE_ON_PAGE_EXPAND: 'AR_EXECUTE_ON_PAGE_EXPAND',
            AR_EXECUTE_ON_TABLE_CONTENT_CHANGE: 'AR_EXECUTE_ON_TABLE_CONTENT_CHANGE'
        })
        ars_const['AR_FILTER_ACTION'].update({
            AR_FILTER_ACTION_SERVICE: 'AR_FILTER_ACTION_SERVICE'
            })
        ars_const['AR_FUNCTION'].update({
            AR_FUNCTION_HOVER: 'AR_FUNCTION_HOVER',
            AR_FUNCTION_TEMPLATE: 'AR_FUNCTION_TEMPLATE'
        })
        ars_const['AR_IMPORT_OPT'].update({
            AR_IMPORT_OPT_PRESERVE_EXTRA_APP_FORMS: 'AR_IMPORT_OPT_PRESERVE_EXTRA_APP_FORMS',
            AR_IMPORT_OPT_PRESERVE_INDEX: 'AR_IMPORT_OPT_PRESERVE_INDEX',
            AR_IMPORT_OPT_PRESERVE_VUI_NAMESPACE: 'AR_IMPORT_OPT_PRESERVE_VUI_NAMESPACE',
            AR_IMPORT_OPT_WITH_APP_OWNER: 'AR_IMPORT_OPT_WITH_APP_OWNER',
            AR_IMPORT_OPT_WORKFLOW_PRESERVE_ATTACHLIST: 'AR_IMPORT_OPT_WORKFLOW_PRESERVE_ATTACHLIST',
            AR_IMPORT_OPT_WORKFLOW_REMOVE_ATTACHLIST: 'AR_IMPORT_OPT_WORKFLOW_REMOVE_ATTACHLIST'
        })
        ars_const['AR_KEYWORD'].update({
            AR_KEYWORD_ERRNO: "$ERRNO$",
            AR_KEYWORD_ERRMSG: "$ERRMSG$",
            AR_KEYWORD_ERRAPPENDMSG: "$ERRAPPENDMSG$",
            AR_KEYWORD_INCLNTMANAGEDTRANS: 'AR_KEYWORD_INCLNTMANAGEDTRANS'
            })
        ars_const['AR_LENGTH_UNIT'] = {
            AR_LENGTH_UNIT_BYTE : 'BYTE',
            AR_LENGTH_UNIT_CHAR : 'CHAR'    
        }
        ars_const['AR_SERVER_INFO'].update({
            AR_SERVER_INFO_ALERT_LOG_FORM: 'AR_SERVER_INFO_ALERT_LOG_FORM',
            AR_SERVER_INFO_API_LOG_FORM: 'AR_SERVER_INFO_API_LOG_FORM',
            AR_SERVER_INFO_ARSIGNALD_LOG_FILE: 'AR_SERVER_INFO_ARSIGNALD_LOG_FILE',
            AR_SERVER_INFO_CLIENT_MANAGED_TRANSACTION_TIMEOUT: 'AR_SERVER_INFO_CLIENT_MANAGED_TRANSACTION_TIMEOUT',
            AR_SERVER_INFO_CMDB_INSTALL_DIR: 'AR_SERVER_INFO_CMDB_INSTALL_DIR',
            AR_SERVER_INFO_COMMON_LOG_FORM: 'AR_SERVER_INFO_COMMON_LOG_FORM',
            AR_SERVER_INFO_CURRENT_ENC_SEC_POLICY: 'AR_SERVER_INFO_CURRENT_ENC_SEC_POLICY',
            AR_SERVER_INFO_CUR_ENC_PUB_KEY: 'AR_SERVER_INFO_CUR_ENC_PUB_KEY',
            AR_SERVER_INFO_DISABLE_AUDIT_ONLY_CHANGED_FIELDS: 'AR_SERVER_INFO_DISABLE_AUDIT_ONLY_CHANGED_FIELDS',
            AR_SERVER_INFO_DSO_LOG_ERR_FORM: 'AR_SERVER_INFO_DSO_LOG_ERR_FORM',
            AR_SERVER_INFO_DSO_LOG_LEVEL: 'AR_SERVER_INFO_DSO_LOG_LEVEL',
            AR_SERVER_INFO_DSO_MAIN_POLL_INTERVAL: 'AR_SERVER_INFO_DSO_MAIN_POLL_INTERVAL',
            AR_SERVER_INFO_DS_PENDING_ERR: 'AR_SERVER_INFO_DS_PENDING_ERR',
            AR_SERVER_INFO_ENC_ALGORITHM: 'AR_SERVER_INFO_ENC_ALGORITHM',
            AR_SERVER_INFO_ENC_LEVEL: 'AR_SERVER_INFO_ENC_LEVEL',
            AR_SERVER_INFO_ENC_LEVEL_INDEX: 'AR_SERVER_INFO_ENC_LEVEL_INDEX',
            AR_SERVER_INFO_ENC_LIBRARY_LEVEL: 'AR_SERVER_INFO_ENC_LIBRARY_LEVEL',
            AR_SERVER_INFO_ESCL_LOG_FORM: 'AR_SERVER_INFO_ESCL_LOG_FORM',
            AR_SERVER_INFO_FILTER_LOG_FORM: 'AR_SERVER_INFO_FILTER_LOG_FORM',
            AR_SERVER_INFO_FIPS_ALG: 'AR_SERVER_INFO_FIPS_ALG',
            AR_SERVER_INFO_FIPS_CLIENT_MODE: 'AR_SERVER_INFO_FIPS_CLIENT_MODE',
            AR_SERVER_INFO_FIPS_DUAL_MODE_INDEX: 'AR_SERVER_INFO_FIPS_DUAL_MODE_INDEX',
            AR_SERVER_INFO_FIPS_MODE_INDEX: 'AR_SERVER_INFO_FIPS_MODE_INDEX',
            AR_SERVER_INFO_FIPS_PUB_KEY: 'AR_SERVER_INFO_FIPS_PUB_KEY',
            AR_SERVER_INFO_FIPS_SERVER_MODE: 'AR_SERVER_INFO_FIPS_SERVER_MODE',
            AR_SERVER_INFO_FIPS_STATUS: 'AR_SERVER_INFO_FIPS_STATUS',
            AR_SERVER_INFO_FIRE_ESCALATIONS: 'AR_SERVER_INFO_FIRE_ESCALATIONS',
            AR_SERVER_INFO_FTINDX_LOG_FORM: 'AR_SERVER_INFO_FTINDX_LOG_FORM',
            AR_SERVER_INFO_FT_SERVER_NAME: 'AR_SERVER_INFO_FT_SERVER_NAME',
            AR_SERVER_INFO_FT_SERVER_PORT: 'AR_SERVER_INFO_FT_SERVER_PORT',
            AR_SERVER_INFO_LICENSE_USAGE: 'AR_SERVER_INFO_LICENSE_USAGE',
            AR_SERVER_INFO_LOG_FORM_SELECTED: 'AR_SERVER_INFO_LOG_FORM_SELECTED',
            AR_SERVER_INFO_LOG_TO_FORM: 'AR_SERVER_INFO_LOG_TO_FORM',
            AR_SERVER_INFO_MAX_CLIENT_MANAGED_TRANSACTIONS: 'AR_SERVER_INFO_MAX_CLIENT_MANAGED_TRANSACTIONS',
            AR_SERVER_INFO_MAX_RECURSION_LEVEL: 'AR_SERVER_INFO_MAX_RECURSION_LEVEL',
            AR_SERVER_INFO_MAX_VENDOR_TEMP_TABLES: 'AR_SERVER_INFO_MAX_VENDOR_TEMP_TABLES',
            AR_SERVER_INFO_NEW_ENC_ALGORITHM: 'AR_SERVER_INFO_NEW_ENC_ALGORITHM',
            AR_SERVER_INFO_NEW_ENC_DATA_ALG: 'AR_SERVER_INFO_NEW_ENC_DATA_ALG',
            AR_SERVER_INFO_NEW_ENC_DATA_KEY_EXP: 'AR_SERVER_INFO_NEW_ENC_DATA_KEY_EXP',
            AR_SERVER_INFO_NEW_ENC_LEVEL: 'AR_SERVER_INFO_NEW_ENC_LEVEL',
            AR_SERVER_INFO_NEW_ENC_LEVEL_INDEX: 'AR_SERVER_INFO_NEW_ENC_LEVEL_INDEX',
            AR_SERVER_INFO_NEW_ENC_PUB_KEY: 'AR_SERVER_INFO_NEW_ENC_PUB_KEY',
            AR_SERVER_INFO_NEW_ENC_PUB_KEY_EXP: 'AR_SERVER_INFO_NEW_ENC_PUB_KEY_EXP',
            AR_SERVER_INFO_NEW_ENC_PUB_KEY_INDEX: 'AR_SERVER_INFO_NEW_ENC_PUB_KEY_INDEX',
            AR_SERVER_INFO_NEW_ENC_SEC_POLICY: 'AR_SERVER_INFO_NEW_ENC_SEC_POLICY',
            AR_SERVER_INFO_NEW_FIPS_ALG: 'AR_SERVER_INFO_NEW_FIPS_ALG',
            AR_SERVER_INFO_NEW_FIPS_MODE_INDEX: 'AR_SERVER_INFO_NEW_FIPS_MODE_INDEX',
            AR_SERVER_INFO_NEW_FIPS_SERVER_MODE: 'AR_SERVER_INFO_NEW_FIPS_SERVER_MODE',
            AR_SERVER_INFO_OBJ_RESERVATION_MODE: 'AR_SERVER_INFO_OBJ_RESERVATION_MODE',
            AR_SERVER_INFO_PLUGIN_LIST: 'AR_SERVER_INFO_PLUGIN_LIST',
            AR_SERVER_INFO_PLUGIN_PATH_LIST: 'AR_SERVER_INFO_PLUGIN_PATH_LIST',
            AR_SERVER_INFO_PRELOAD_NUM_SCHEMA_SEGS: 'AR_SERVER_INFO_PRELOAD_NUM_SCHEMA_SEGS',
            AR_SERVER_INFO_PRELOAD_NUM_THREADS: 'AR_SERVER_INFO_PRELOAD_NUM_THREADS',
            AR_SERVER_INFO_PRELOAD_THREAD_INIT_ONLY: 'AR_SERVER_INFO_PRELOAD_THREAD_INIT_ONLY',
            AR_SERVER_INFO_RECORD_OBJECT_RELS: 'AR_SERVER_INFO_RECORD_OBJECT_RELS',
            AR_SERVER_INFO_REGISTRY_LOCATION: 'AR_SERVER_INFO_REGISTRY_LOCATION',
            AR_SERVER_INFO_REGISTRY_PASSWORD: 'AR_SERVER_INFO_REGISTRY_PASSWORD',
            AR_SERVER_INFO_REGISTRY_USER: 'AR_SERVER_INFO_REGISTRY_USER',
            AR_SERVER_INFO_RE_LOG_DIR: 'AR_SERVER_INFO_RE_LOG_DIR',
            AR_SERVER_INFO_SG_AIE_STATE: 'AR_SERVER_INFO_SG_AIE_STATE',
            AR_SERVER_INFO_SHARED_LIB: 'AR_SERVER_INFO_SHARED_LIB',
            AR_SERVER_INFO_SHARED_LIB_PATH: 'AR_SERVER_INFO_SHARED_LIB_PATH',
            AR_SERVER_INFO_SQL_LOG_FORM: 'AR_SERVER_INFO_SQL_LOG_FORM',
            AR_SERVER_INFO_SVRGRP_LOG_FORM: 'AR_SERVER_INFO_SVRGRP_LOG_FORM',
            AR_SERVER_INFO_THREAD_LOG_FORM: 'AR_SERVER_INFO_THREAD_LOG_FORM',
            AR_SERVER_INFO_USER_LOG_FORM: 'AR_SERVER_INFO_USER_LOG_FORM',
            AR_SERVER_INFO_VERCNTL_OBJ_MOD_LOG_MODE: 'AR_SERVER_INFO_VERCNTL_OBJ_MOD_LOG_MODE',
            AR_SERVER_INFO_VERCNTL_OBJ_MOD_LOG_SAVE_DEF: 'AR_SERVER_INFO_VERCNTL_OBJ_MOD_LOG_SAVE_DEF',
            AR_SERVER_INFO_WFD_QUEUES: 'AR_SERVER_INFO_WFD_QUEUES'
        })
    if float(version) >= 7603:
        ars_const['AR_DPROP'].update({
            AR_DPROP_ALIGNED : 'AR_DPROP_ALIGNED',
            AR_DPROP_APPLIST_MODE : 'AR_DPROP_APPLIST_MODE',
            AR_DPROP_ATTACH_FIELD_IMAGE_CACHE : 'AR_DPROP_ATTACH_FIELD_IMAGE_CACHE',
            AR_DPROP_AUTO_RESIZE : 'AR_DPROP_AUTO_RESIZE',
            AR_DPROP_FIELD_DRAGGABLE : 'AR_DPROP_FIELD_DRAGGABLE',
            AR_DPROP_FIELD_DROPPABLE : 'AR_DPROP_FIELD_DROPPABLE',
            AR_DPROP_FIELD_PROCESS_ENTRY_MODE : 'AR_DPROP_FIELD_PROCESS_ENTRY_MODE',
            AR_DPROP_FLOW_LAYOUT_VERT_SPACE : 'AR_DPROP_FLOW_LAYOUT_VERT_SPACE',
            AR_DPROP_HEADER_HEIGHT : 'AR_DPROP_HEADER_HEIGHT',
            AR_DPROP_LOCALIZE_FIELD : 'AR_DPROP_LOCALIZE_FIELD',
            AR_DPROP_LOCALIZE_FIELD_DATA : 'AR_DPROP_LOCALIZE_FIELD_DATA',
            AR_DPROP_LOCALIZE_VIEW : 'AR_DPROP_LOCALIZE_VIEW',
            AR_DPROP_NAV_ITEM_TEXT_COLOR : 'AR_DPROP_NAV_ITEM_TEXT_COLOR',
            AR_DPROP_NAVIGATION_MODE : 'AR_DPROP_NAVIGATION_MODE',
            AR_DPROP_PANEL_AVOID_WHITESPACE : 'AR_DPROP_PANEL_AVOID_WHITESPACE',
            AR_DPROP_PANEL_FIT_TO_CONTENT : 'AR_DPROP_PANEL_FIT_TO_CONTENT',
            AR_DPROP_PANEL_MARGIN_BOTTOM : 'AR_DPROP_PANEL_MARGIN_BOTTOM',
            AR_DPROP_PANEL_MARGIN_LEFT : 'AR_DPROP_PANEL_MARGIN_LEFT',
            AR_DPROP_PANEL_MARGIN_RIGHT : 'AR_DPROP_PANEL_MARGIN_RIGHT',
            AR_DPROP_PANEL_MARGIN_TOP : 'AR_DPROP_PANEL_MARGIN_TOP',
            AR_DPROP_PANEL_SLACK_DISTRIBUTION_ORDER : 'AR_DPROP_PANEL_SLACK_DISTRIBUTION_ORDER',
            AR_DPROP_PANEL_SLACK_ORDER : 'AR_DPROP_PANEL_SLACK_ORDER',
            AR_DPROP_RIGHT_BBOX : 'AR_DPROP_RIGHT_BBOX',
            AR_DPROP_SHOWURL : 'AR_DPROP_SHOWURL',
            AR_DPROP_SKIN_STYLE : 'AR_DPROP_SKIN_STYLE',
            AR_DPROP_TABLE_CELL_BKG_COLOR : 'AR_DPROP_TABLE_CELL_BKG_COLOR',
            AR_DPROP_TABLE_COL_ENABLE_SORT : 'AR_DPROP_TABLE_COL_ENABLE_SORT',
            AR_DPROP_TABLE_COL_IMAGE_LIST : 'AR_DPROP_TABLE_COL_IMAGE_LIST',
            AR_DPROP_TABLE_COLUMN_CHECKBOX : 'AR_DPROP_TABLE_COLUMN_CHECKBOX',
            AR_DPROP_TABLE_ROOT_NODE_ALT_TEXT : 'AR_DPROP_TABLE_ROOT_NODE_ALT_TEXT',
            AR_DPROP_TABLE_ROOT_NODE_IMAGE : 'AR_DPROP_TABLE_ROOT_NODE_IMAGE'
        })
        ars_const['AR_DPROP']['AR_DPROP_APPLIST_MODE'] = {
            AR_DVAL_APP_TRADITIONAL : 'AR_DVAL_APP_TRADITIONAL',
            AR_DVAL_APP_FLYOUT : 'AR_DVAL_APP_FLYOUT'
        }
        ars_const['AR_DPROP']['AR_DPROP_ALIGNED'] = {
            AR_DVAL_ALIGNED_LEFT : 'AR_DVAL_ALIGNED_LEFT',
            AR_DVAL_ALIGNED_RIGHT : 'AR_DVAL_ALIGNED_RIGHT'          
        }
        ars_const['AR_DPROP']['AR_DPROP_LOCALIZE_VIEW'] = {
            AR_DVAL_LOCALIZE_VIEW_SKIP : 'AR_DVAL_LOCALIZE_VIEW_SKIP',
            AR_DVAL_LOCALIZE_VIEW_ALL : 'AR_DVAL_LOCALIZE_VIEW_ALL'
        }
        ars_const['AR_DPROP']['AR_DPROP_LOCALIZE_FIELD'] = {
            AR_DVAL_LOCALIZE_FIELD_SKIP : 'AR_DVAL_LOCALIZE_FIELD_SKIP',
            AR_DVAL_LOCALIZE_FIELD_ALL : 'AR_DVAL_LOCALIZE_FIELD_ALL'
        }
        ars_const['AR_DPROP']['AR_DPROP_AUTO_RESIZE'] = {
            AR_DVAL_RESIZE_NONE : 'AR_DVAL_RESIZE_NONE',
            AR_DVAL_RESIZE_NONE : 'AR_DVAL_RESIZE_NONE'
        }
        ars_const['AR_DPROP']['AR_DPROP_TABLE_COL_DISPLAY_TYPE'].update({
            AR_DVAL_TABLE_COL_DISPLAY_DROPDOWN_MENU : 'AR_DVAL_TABLE_COL_DISPLAY_DROPDOWN_MENU'
        })
        ars_const['AR_DPROP']['AR_DPROP_NAVIGATION_MODE'] = {
            AR_DVAL_NAV_EXPANDABLE : 'AR_DVAL_NAV_EXPANDABLE',
            AR_DVAL_NAV_FLYOUT : 'AR_DVAL_NAV_FLYOUT'
        }
        ars_const['AR_DPROP']['AR_DPROP_TABLE_COL_ENABLE_SORT'] = {
            AR_DVAL_TABLE_COL_SORT_DISABLED : 'AR_DVAL_TABLE_COL_SORT_DISABLED',
            AR_DVAL_TABLE_COL_SORT_ENABLED : 'AR_DVAL_TABLE_COL_SORT_ENABLED'
        }
        ars_const['AR_DPROP']['AR_DPROP_TABLE_COLUMN_CHECKBOX'] = {
            AR_DVAL_TABLE_COLUMN_CHECKBOX_DISABLE : 'AR_DVAL_TABLE_COLUMN_CHECKBOX_DISABLE',
            AR_DVAL_TABLE_COLUMN_CHECKBOX_ENABLE : 'AR_DVAL_TABLE_COLUMN_CHECKBOX_ENABLE'
        }
        ars_const['AR_DPROP']['AR_DPROP_FIELD_PROCESS_ENTRY_MODE'] = {
            AR_DVAL_FIELD_PROCESS_NOT_REQUIRED : 'AR_DVAL_FIELD_PROCESS_NOT_REQUIRED',
            AR_DVAL_FIELD_PROCESS_REQUIRED : 'AR_DVAL_FIELD_PROCESS_REQUIRED'
        }
        ars_const['AR_OPROP'].update({
            AR_OPROP_FT_SCAN_TIME_MONTH_MASK : 'AR_OPROP_FT_SCAN_TIME_MONTH_MASK',
            AR_OPROP_FT_SCAN_TIME_WEEKDAY_MASK : 'AR_OPROP_FT_SCAN_TIME_WEEKDAY_MASK',
            AR_OPROP_FT_SCAN_TIME_HOUR_MASK: 'AR_OPROP_FT_SCAN_TIME_HOUR_MASK',
            AR_OPROP_FT_SCAN_TIME_MINUTE: 'AR_OPROP_FT_SCAN_TIME_MINUTE',
            AR_OPROP_FT_SCAN_TIME_INTERVAL: 'AR_OPROP_FT_SCAN_TIME_INTERVAL',
            AR_OPROP_FT_MFS_CATEGORY_NAME: 'AR_OPROP_FT_MFS_CATEGORY_NAME',
            AR_OPROP_FT_MFS_INDEX_TABLE_FIELD: 'AR_OPROP_FT_MFS_INDEX_TABLE_FIELD',
            AR_OPROP_FT_STRIP_TAGS: 'AR_OPROP_FT_STRIP_TAGS',
            AR_OPROP_FT_FILTER_SEARCH: 'AR_OPROP_FT_FILTER_SEARCH',
            AR_OPROP_STATIC_PERMISSION_INHERITED: 'AR_OPROP_STATIC_PERMISSION_INHERITED',
            AR_OPROP_DYNAMIC_PERMISSION_INHERITED: 'AR_OPROP_DYNAMIC_PERMISSION_INHERITED',
            AR_OPROP_MFS_OPTION_MASK: 'AR_OPROP_MFS_OPTION_MASK',
            AR_OPROP_MFS_WEIGHTED_RELEVANCY_FIELDS: 'AR_OPROP_MFS_WEIGHTED_RELEVANCY_FIELDS',
            AR_OPROP_FORM_ALLOW_DELETE: 'AR_OPROP_FORM_ALLOW_DELETE',
            AR_OPROP_TABLE_PERSIST_DIRTY_ROWS: 'AR_OPROP_TABLE_PERSIST_DIRTY_ROWS',
            AR_OPROP_APP_INTEGRATION_WORKFLOW: 'AR_OPROP_APP_INTEGRATION_WORKFLOW',
            AR_OPROP_LOCALIZE_FORM_DATA : 'AR_OPROP_LOCALIZE_FORM_DATA',
            AR_OPROP_LOCALIZE_FORM_VIEWS: 'AR_OPROP_LOCALIZE_FORM_VIEWS',
            AR_OPROP_LOCALIZE_FIELD_DATA: 'AR_OPROP_LOCALIZE_FIELD_DATA',
            AR_OPROP_OBJECT_MODE: 'AR_OPROP_OBJECT_MODE',
            AR_OPROP_OVERLAY_GROUP: 'AR_OPROP_OVERLAY_GROUP',
            AR_OPROP_OVERLAY_DESIGN_GROUP: 'AR_OPROP_OVERLAY_DESIGN_GROUP',
            AR_OPROP_OVERLAY_PROP: 'AR_OPROP_OVERLAY_PROP',
            AR_OPROP_DRILL_DOWN_IN_WEB_REPORTS: 'AR_OPROP_DRILL_DOWN_IN_WEB_REPORTS',
            AR_OPROP_DISPLAY_FORM_SINGLETON: 'AR_OPROP_DISPLAY_FORM_SINGLETON'
        })
        ars_const['AR_SERVER_INFO'].update({
            AR_SERVER_INFO_FT_FORM_REINDEX: 'AR_SERVER_INFO_FT_FORM_REINDEX'
        })
        
    if float(version) >= 7604:
        ars_const['AR_DPROP'].update({
            AR_DPROP_AUTO_COMPLETE_AFTER_KEYSTROKES : 'AR_DPROP_AUTO_COMPLETE_AFTER_KEYSTROKES',
            AR_DPROP_AUTO_COMPLETE_HIDE_MENU_BUTTON : 'AR_DPROP_AUTO_COMPLETE_HIDE_MENU_BUTTON',
            AR_DPROP_FIELD_FLOAT_EFFECT : 'AR_DPROP_FIELD_FLOAT_EFFECT',
            AR_DPROP_FIELD_FLOAT_STYLE : 'AR_DPROP_FIELD_FLOAT_STYLE',
            AR_DPROP_PANEL_BORDER_THICKNESS : 'AR_DPROP_PANEL_BORDER_THICKNESS',
            AR_DPROP_PANELHOLDER_SHRINKTOFIT : 'AR_DPROP_PANELHOLDER_SHRINKTOFIT',
            AR_DPROP_ROW_LABEL : 'AR_DPROP_ROW_LABEL',
            AR_DPROP_ROW_LABEL_PLURAL : 'AR_DPROP_ROW_LABEL_PLURAL',
            AR_DPROP_SORT_AGGREGATION_TYPE : 'AR_DPROP_SORT_AGGREGATION_TYPE',
            AR_DPROP_SORT_GROUP : 'AR_DPROP_SORT_GROUP'
        })
except AttributeError:
    _, err, _ = sys.exc_info()
    print ("pyars.cars has detected an anomaly with the constant definitions")
    print (err)
    print ("pyars.cars will be imported nonetheless")
