# Copyright (c) 2017 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
import base64

from . import six
from deprecation import deprecated

try:
    from passlib.context import CryptContext
except ImportError:
    def get_crypt_context():
        "This function requires passlib!"
        return None
else:
    def get_crypt_context():
        "Return the default signac crypto context."
        return CryptContext(schemes=('bcrypt', ))

try:
    import keyring
except ImportError:
    def get_keyring():
        "This function requires keyring!"
        return None
else:
    def get_keyring():
        "Return the system user keyring."
        return keyring.get_keyring()

# this is here because of issues importing the same variable in
# signac/__init__.py from the top level namespace
__version__ = '1.2.0'


# this class is deprecated
class SimpleKeyring(object):
    """Simple in-memory keyring for caching."""

    def __init__(self):
        self._cache = dict()

    @classmethod
    def _encode(cls, msg):
        if msg is None:
            return
        if six.PY2:
            return base64.b64encode(msg)
        else:
            return base64.b64encode(msg.encode())

    @classmethod
    def _decode(cls, msg):
        if msg is None:
            return
        if six.PY2:
            return base64.b64decode(msg)
        else:
            return base64.b64decode(msg).decode()

    @deprecated(deprecated_ino="1.3", removed_in="2.0", current_version=__version__,
                details="Obsolete.")
    def __contains__(self, key):
        return key in self._cache

    @deprecated(deprecated_ino="1.3", removed_in="2.0", current_version=__version__,
                details="Obsolete.")
    def __set__(self, key, value):
        self._cache[key] = self._encode(self._secret, value)

    @deprecated(deprecated_ino="1.3", removed_in="2.0", current_version=__version__,
                details="Obsolete.")
    def __getitem__(self, key):
        return self._decode(self._cache.__getitem__(key))

    @deprecated(deprecated_ino="1.3", removed_in="2.0", current_version=__version__,
                details="Obsolete.")
    def setdefault(self, key, value):
        return self._decode(self._cache.setdefault(key, self._encode(value)))


@deprecated(deprecated_ino="1.3", removed_in="2.0", current_version=__version__,
            details="Obsolete.")
def parse_pwhash(pwhash):
    "Extract hash configuration from hash string."
    if get_crypt_context().identify(pwhash) == 'bcrypt':
        return dict(
            rounds=int(pwhash.split('$')[2]),
            salt=pwhash[-53:-31])
