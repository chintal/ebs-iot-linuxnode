

import os
import time
import dataset
from functools import partial
from appdirs import user_cache_dir
from .http import HttpClientMixin
from .config import cache_max_size


ASSET = 1
CONTENT = 2


class CacheableResource(object):
    def __init__(self, manager, filename, url=None, rtype=None):
        self._manager = manager
        self._filename = filename
        self._url = url
        self._rtype = rtype
        if not self._rtype:
            self.load()

    @property
    def filename(self):
        return self._filename

    @property
    def url(self):
        return self._url

    @property
    def rtype(self):
        return self._rtype

    @property
    def cache_path(self):
        return self._manager.cache_path(self.filename)

    @property
    def available(self):
        return self._manager.cache_has(self.filename)

    @property
    def is_asset(self):
        if self.rtype == ASSET:
            return True
        else:
            return False

    @property
    def is_content(self):
        if self.rtype == CONTENT:
            return True
        else:
            return False

    def commit(self):
        with self._manager.db as db:
            db['resources'].upsert(
                row={'filename': self.filename,
                     'url': self.url,
                     'rtype': self.rtype},
                keys=['filename']
            )

    def load(self):
        with self._manager.db as db:
            data = db['resources'].find_one(filename=self.filename)
            if not data:
                return
            self._url = data['url']
            self._rtype = data['rtype']


class ResourceManager(object):
    def __init__(self, node, **kwargs):
        self._resource_class = kwargs.pop('resource_class', CacheableResource)
        self._node = node
        self._db = None
        self._db_dir = None
        self._cache_dir = None
        super(ResourceManager, self).__init__(**kwargs)

    def has(self, filename):
        # Check if a resource is in defined by the manager.
        # This makes no guarantees about it existing in the cache.
        with self.db as db:
            data = db['resources'].find_one(filename=filename)
            if not data:
                return False
            else:
                return True

    def get(self, filename):
        # Get the resource object bound to the manager.
        # This makes no guarantees about it existing in the cache.
        # Check the available property of the returned resource to know if
        # it is there.
        return self._resource_class(self, filename)

    def insert(self, filename, url=None, rtype=CONTENT):
        # Create a resource object and insert it into the manager.
        # This makes no guarantees about it existing in the cache.
        resource = self._resource_class(self, filename, url, rtype)
        resource.commit()

    def prefetch(self, resource):
        # Given a resource belonging to this resource manager, download it
        # to the cache if it isn't already there or update its mtime if it is.
        if not resource.available:
            self._node.log.debug("Downloading {filename}",
                                 filename=resource.filename)
            d = self._node.http_download(resource.url, resource.cache_path)

            # Update timestamps for the downloaded file to reflect start of
            # download instead of end. Consider if this is wise.
            def _cb_set_file_times(fpath, times, _):
                with open(fpath, 'a'):
                    os.utime(fpath, times)
            d.addCallback(partial(_cb_set_file_times, resource.cache_path,
                                  (time.time(), time.time())))

            return d
        else:
            # TODO handle resume here instead
            # Check actual content length, available content length, and
            # download the rest if they aren't equal.
            with open(resource.cache_path, 'a'):
                os.utime(resource.cache_path, None)

    @property
    def db(self):
        if self._db is None:
            self._db = dataset.connect(self.db_url)
            self._db.get_table('resources')
        return self._db

    @property
    def db_url(self):
        return 'sqlite:///{0}'.format(os.path.join(self.db_dir, 'resources.db'))

    @property
    def db_dir(self):
        if not self._db_dir:
            self._db_dir = os.path.join(self.cache_dir, 'db')
            os.makedirs(self._db_dir, exist_ok=True)
        return self._db_dir

    @property
    def cache_dir(self):
        if not self._cache_dir:
            self._cache_dir = user_cache_dir(self._node.appname)
            os.makedirs(self._cache_dir, exist_ok=True)
        return self._cache_dir


class NothingToTrimError(Exception):
    pass


class CachingResourceManager(ResourceManager):
    _excluded_folders = ['log']

    def __init__(self, *args, **kwargs):
        super(CachingResourceManager, self).__init__(*args, **kwargs)
        self.cache_max_size = cache_max_size

    def prefetch(self, resource):
        # When done, trim the cache.
        d = super(CachingResourceManager, self).prefetch(resource)
        if d:
            d.addCallback(self.cache_trim)

    def cache_remove(self, filename):
        size = self.cache_file_size(filename)
        self._node.log.debug("Removing {filename} of size {size} from cache",
                             filename=filename, size=size)
        os.remove(self.cache_path(filename))
        return size

    def cache_has(self, filename):
        r = os.path.exists(self.cache_path(filename))
        if r:
            self._node.log.debug("{filename} found in the cache",
                                 filename=filename)
        return r

    def cache_path(self, filename):
        return os.path.join(self.cache_dir, filename)

    def cache_file_size(self, filename):
        try:
            rv = os.path.getsize(self.cache_path(filename))
            return rv
        except OSError:
            return 0

    @property
    def cache_files(self):
        return self._cache_files()

    def _cache_files(self):
        for filename in os.listdir(self.cache_dir):
            if os.path.isfile(self.cache_path(filename)):
                yield filename

    @property
    def cache_size(self):
        return sum(map(self.cache_file_size, self.cache_files))

    def cache_clear(self):
        raise NotImplementedError

    def cache_trim(self, max_size=None, space_for=0):
        # Trim the cache to the provided max_size.
        #  - Remove all cached content items which have no known next_use
        #  - Trim cache down to max_size by removing content items starting
        #    with the one with next_use most in the future, up to about 30
        #    minutes from the current time
        #
        # If next_use is not implemented, this will fallback to a simple
        # FIFO cache based on the mtime of the cached content item.
        #
        # TODO This should return a deferred
        if max_size is None:
            max_size = self.cache_max_size
        max_size = max_size - space_for
        if hasattr(self._resource_class, 'nextuse'):
            trimmer = self._cache_trimmer_predictive
        else:
            trimmer = self._cache_trimmer_fifo
        current_size = self.cache_size
        self._node.log.debug("Attempting to trim cache to {max_size} from "
                             "{current_size} with {trimmer}",
                             max_size=max_size, current_size=current_size,
                             trimmer=trimmer.__name__)
        while current_size > max_size:
            try:
                current_size -= trimmer()
            except NothingToTrimError:
                return False
            # TODO Yield none for cooperate

    @property
    def cache_resources(self):
        return self._cache_resources()

    def _cache_resources(self):
        for filename in self.cache_files:
            resource = self.get(filename)
            if resource.is_content or not resource.rtype:
                yield resource

    @property
    def cache_resources_mtime(self):
        return sorted(self.cache_resources, reverse=False,
                      key=lambda x: os.path.getmtime(x.cache_path))

    def _cache_trimmer_fifo(self):
        resources = self.cache_resources_mtime
        self._cache_debug(resources)
        if len(resources):
            return self.cache_remove(resources[0].filename)
        else:
            raise NothingToTrimError()

    def _cache_trimmer_predictive(self):
        raise NothingToTrimError()

    def _cache_debug(self, resources):
        self._node.log.debug("------------------")
        for r in resources:
            self._node.log.debug(
                "{mtime:<24} {filename}",
                filename=r.filename,
                mtime=os.path.getmtime(r.cache_path)
            )
        self._node.log.debug("------------------")


class ResourceManagerMixin(HttpClientMixin):
    def __init__(self, *args, **kwargs):
        self._resource_manager = None
        self._resource_class = kwargs.pop('resource_class', CacheableResource)
        super(ResourceManagerMixin, self).__init__(*args, **kwargs)

    @property
    def resource_manager(self):
        if not self._resource_manager:
            self.log.info("Initializing resource manager")
            self._resource_manager = CachingResourceManager(
                self, resource_class=self._resource_class,
            )
        return self._resource_manager

    def stop(self):
        super(ResourceManagerMixin, self).stop()
