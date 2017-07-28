from .settings import SETTINGS

import sys
import warnings

if sys.platform in ("linux", "linux2"):
    ARCH = 'linux'
elif sys.platform == "darwin":
    ARCH = 'macOS'
elif sys.platform in ("win32", "win64"):
    ARCH = 'windows'
else:
    warnings.warn("detected system platform '%s' is not supported, you may encounter problems" % sys.platform)
    ARCH = 'not-supported'

VERSION_MAJOR = '0'
VERSION_MINOR = '1'
VERSION_RELEASE = '0a1'

__version__ = '.'.join([VERSION_MAJOR, VERSION_MINOR, VERSION_RELEASE])
