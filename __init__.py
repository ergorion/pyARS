"""pyARS

The main package for the Ergorion Remedy Utilities.

>>> from pyars import erars

>>> myars = erars.erARS('server', 'user', 'password')
>>> schemas = myars.GetListSchema()
>>> for schema in schemas:
>>>     print schema
>>> myars.Logoff()

"""

__revision__ = "$Id: __init__.py,v 1.1.1.5 2014/10/18 10:25:24 aseibert Exp $"

__version__ = "1.8.2"


