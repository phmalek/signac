import os

import logging
logger = logging.getLogger('config')

import json

DEFAULT_FILENAME = 'compdb.rc'
CONFIG_FILENAMES = ['compdb.rc',]
HOME = os.path.expanduser('~')
CONFIG_PATH = [HOME]
CWD = os.getcwd()

ENVIRONMENT_VARIABLES = {
    'author_name' :         'COMPDB_AUTHOR_NAME',
    'author_email':         'COMPDB_AUTHOR_EMAIL',
    'project':              'COMPDB_PROJECT',
    'project_dir' :         'COMPDB_PROJECT_DIR',
    'filestorage_dir':      'COMPDB_FILESTORAGE_DIR',
    'workspace_dir':        'COMPDB_WORKING_DIR',
    'database_host':        'COMPDB_DATABASE_HOST',
    'develop':              'COMPDB_DEVELOP',
    'connect_timeout_ms':   'COMPDB_CONNECT_TIMEOUT',
    'compmatdb_host':       'COMPDB_COMPMATDB_HOST',
}

REQUIRED_KEYS = [
    'author_name', 'author_email', 'project',
    'project_dir',  'filestorage_dir', 'workspace_dir',
    ]

DEFAULTS = {
    'database_host': 'localhost',
    'database_auth_mechanism': 'SSL-x509',
    'database_meta': 'compdb',
    'database_global_fs': 'compdb_fs',
    'database_compmatdb': 'compmatdb',
    'connect_timeout_ms': 5000,
}

LEGAL_ARGS = REQUIRED_KEYS + list(DEFAULTS.keys()) + [
    'global_fs_dir', 'develop', 'socket_timeout_ms', 'compmatdb_host',
    ]

LEGAL_ARGS.extend([
    'database_ssl_keyfile', 'database_ssl_certfile', 'database_ssl_ca_certs'
    ])

DIRS = ['workspace_dir', 'project_dir', 'filestorage_dir', 'global_fs_dir']
FILES = ['database_ssl_keyfile', 'database_ssl_certfile', 'database_ssl_ca_certs']

class Config(object):   

    def __init__(self, args = None):
        from copy import copy
        self._args = {}
        if args is not None:
            self.update(args)

    def __str__(self):
        return str(self._args)

    def read(self, filename = DEFAULT_FILENAME):
        try:
            with open(filename) as file:
                args = json.loads(file.read())
                logger.debug("Read: {}".format(args))
            self._args.update(args)
        except ValueError as error:
            msg = "Failed to read config file '{}'."
            raise RuntimeError(msg.format(filename))

    def _read_files(self):
        from os.path import dirname
        root = None
        for fn in search_config_files():
            try:
                logger.debug("Reading config file '{}'.".format(fn))
                self.read(fn)
                if root is None and 'project' in self:
                    root = dirname(fn)
            except Exception as error:
                msg = "Error while reading config file '{}'."
                logger.error(msg.format(fn))
        if root is not None:
            logger.debug("Found root: {}".format(dirname(fn)))
            self['project_dir'] = root

    def update(self, args):
        self._args.update(args)

    def load(self):
        logger.debug('Reading config...')
        self._read_files()
        self._args.update(read_environment())
        logger.debug('Verifying config...')
        self.verify()
        logger.debug('OK')

    def verify(self):
        verify(self._args)

    def write(self, filename = DEFAULT_FILENAME, indent = 0, keys = None):
        import tempfile
        if keys is None:
            args = self._args
        else:
            args = {k: self._args[k] for k in keys if k in self._args}
        with tempfile.NamedTemporaryFile() as file:
            with open(filename, 'w') as file:
                json.dump(args, file, indent = indent)
            os.rename(file.name, filename)

    def _dump(self, indent = 0, keys = None):
        if keys is None:
            args = self._args
        else:
            args = {k: self._args[k] for k in keys if k in self._args}
        return json.dumps(args, indent = indent, sort_keys = True)

    def dump(self, indent = 0, keys = None):
        print(self._dump(indent, keys))

    def __str__(self):
        return self._dump(indent = 1)

    def __getitem__(self, key):
        try:
            v = self._args.get(key)
            return DEFAULTS[key] if v is None else v
        except KeyError as error:
            msg = "Missing config key: '{key}'. "
            msg += "Try 'compdb config add {key} [your_value]"
            raise KeyError(msg.format(key = key)) from error

    def get(self, key, default = None):
        return self._args.get(key, DEFAULTS.get(key, default))

    def __setitem__(self, key, value):
        self._args[key] = value

    def __contains__(self, key):
        return key in self._args

    def __delitem__(self, key):
        del self._args[key]

def search_tree():
    from os import getcwd
    from os.path import realpath, join, isfile
    cwd = os.getcwd()
    while(True):
        for filename in CONFIG_FILENAMES:
            fn = realpath(join(cwd, filename))
            if isfile(fn):
                yield fn
                return
        up = realpath(join(cwd, '..'))
        if up == cwd:
            msg = "Did not find project configuration file."
            logger.debug(msg)
            return
            #raise FileNotFoundError(msg)
        else:
            cwd = up

def search_standard_dirs():
    from os.path import realpath, join, isfile
    for path in CONFIG_PATH:
        for filename in CONFIG_FILENAMES:
            fn = realpath(join(path, filename))
            if isfile(fn):
                yield fn
                return

def search_config_files():
    yield from search_standard_dirs()
    yield from search_tree()

def read_environment():
    logger.debug("Reading environment variables.")
    import os
    args = dict()
    for key, var in ENVIRONMENT_VARIABLES.items():
        try:
            args[key] = os.environ[var]
            logger.debug("{}='{}'".format(key, args[key]))
        except KeyError:
            pass
    return args

def verify(args):
    import os
    for key in args.keys():
        if not key in LEGAL_ARGS:
            msg = "Config key '{}' not recognized. Possible version conflict."
            logger.warning(msg.format(key))
            #raise KeyError(msg.format(key))

    #for key in REQUIRED_KEYS:
    #    if not key in args.keys():
    #        msg = "Missing required config key: '{}'."
    #        logger.warning(msg.format(key))
    #        #raise KeyError(msg.format(key))

    # sanity check
    #assert set(args.keys()).issubset(set(LEGAL_ARGS))
    #assert set(REQUIRED_KEYS).issubset(set(args.keys()))

    dirs = [dir for dir in DIRS if dir in args]
    for dir_key in dirs:
        if not os.path.isabs(args[dir_key]):
            msg = "Directory specified for '{}': '{}' is not an absolute path."
            logger.warning(msg.format(dir_key, args[dir_key]))

def load_config():
    config = Config()
    config.load()
    return config
