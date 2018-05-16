

import os
import time
import dataset
from functools import partial
from appdirs import user_cache_dir
from twisted.internet.defer import succeed

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
    def filepath(self):
        return self.cache_path

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

    @property
    def is_orphaned(self):
        if not self.rtype:
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
        self._active_downloads = []
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
        if resource.filename in self._active_downloads:
            return
        if not resource.available:
            self._active_downloads.append(resource.filename)
            # self._node.log.debug("Requesting download of {filename}",
            #                      filename=resource.filename)
            d = self._node.http_download(resource.url, resource.cache_path)

            # Update timestamps for the downloaded file to reflect start of
            # download instead of end. Consider if this is wise.
            def _dl_finalize(r, times, _):
                with open(r.cache_path, 'a'):
                    os.utime(r.cache_path, times)

            d.addCallback(
                partial(_dl_finalize, resource, (time.time(), time.time()))
            )
            d.addBoth(
                lambda _: self._active_downloads.remove(resource.filename)
            )
            return d
        else:
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
        else:
            d = succeed(None)
        return d

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
            if os.path.isfile(self.cache_path(filename)) and \
                    not filename.endswith('.partial'):
                yield filename

    @property
    def cache_size(self):
        return sum(map(self.cache_file_size, self.cache_files))

    def cache_clear(self):
        raise NotImplementedError

    def cache_trim(self, max_size=None, space_for=0):
        # Trim the cache cache down to max_size by removing content items to
        # the provided max_size.
        #  - First remove all cache items which are orphaned (aren't in the
        #    resource database) one by one
        #  - Remove cache items which are defined as content by its rtype as
        #    per the auto-selected trimfunc.
        #
        # fifo
        #  - Selected if both 'next_use' and 'last_use' are not defined on
        #    the resource.
        #  - Remove the oldest cached content file by mtime, one by one.
        #  - Note that this implementation actually modifies a typical FIFO
        #    cache into a pseudo-LRU cache by it's updating cache item
        #    timestamps whenever prefetch is called.
        #
        # lru
        #  - Selected if the resource defines 'last_use' and not 'next_use'.
        #  - Remove the least recently used cached content file, one by one.
        #  - Note that if this is used, the application should be sure to set
        #    'last_use' to something meaningful, perhaps timestamp of
        #    creation time, before trim is called.
        #  - LRU is not intended for regular use, it's here for largely
        #    academic purposes.
        #
        # predictive
        #  - Selected if the resource defines 'next_use'. This is the
        #    preferred cache trimmer.
        #  - Remove cached content items which have no known 'next_use',
        #    one by one
        #  - Remove cached content with 'next_use' set to the past.
        #  - Remove cached content items with 'next_use' most in the future,
        #    up to about 30 minutes from the current time
        #
        # TODO This should maybe return a deferred
        if max_size is None:
            max_size = self.cache_max_size
        max_size = max_size - space_for
        if hasattr(self._resource_class, 'next_use'):
            trimmer = self._cache_trimmer_predictive
        elif hasattr(self._resource_class, 'last_use'):
            trimmer = self._cache_trimmer_lru
        else:
            trimmer = self._cache_trimmer_fifo
        current_size = self.cache_size
        self._node.log.debug("Attempting to trim cache to {max_size} from "
                             "{current_size} with {trimmer}",
                             max_size=max_size, current_size=current_size,
                             trimmer=trimmer.__name__)
        while current_size > max_size:
            resources = list(self.cache_resources)
            try:
                current_size -= self._cache_trimmer(resources, trimmer)
            except NothingToTrimError:
                return False
            # TODO Yield none for cooperate

    @property
    def cache_resources(self):
        return self._cache_resources()

    def _cache_resources(self):
        for filename in self.cache_files:
            resource = self.get(filename)
            yield resource

    def _cache_trimmer(self, resources, trimfunc):
        for resource in resources:
            if resource.is_orphaned:
                return self.cache_remove(resource.filename)
        return trimfunc([x for x in resources if x.is_content])

    def _cache_trimmer_fifo(self, resources):
        r = sorted(resources, key=lambda x: os.path.getmtime(x.cache_path))
        # self._cache_debug(r, 'by mtime',
        #                   lambda x: os.path.getmtime(x.cache_path))
        if len(r):
            return self.cache_remove(r[0].filename)
        else:
            raise NothingToTrimError()

    def _cache_trimmer_lru(self, resources):
        r = sorted(resources, key=lambda x: x.last_use)
        # self._cache_debug(r, 'by last_use', lambda x: x.last_use)
        if len(r):
            return self.cache_remove(r[0].filename)
        else:
            raise NothingToTrimError()

    def _cache_trimmer_predictive(self, resources):
        # No next_use
        r = [x for x in resources if not x.next_use]
        if len(r):
            return self._cache_trimmer_fifo(r)

        # Next_use, next_use in the past
        r = sorted((x for x in resources if x.next_use < time.time()),
                   key=lambda x: x.next_use)
        # self._cache_debug(r, 'by next_use in past', lambda x: x.next_use)
        if len(r):
            return self.cache_remove(r[0].filename)

        # Next_use, next_use in the future
        r = sorted((x for x in resources
                    if x.next_use > time.time() + (30 * 60 * 1000)),
                   key=lambda x: x.next_use, reverse=True)
        # self._cache_debug(r, 'by next_use in future', lambda x: x.next_use)
        if len(r):
            return self.cache_remove(r[0].filename)

        raise NothingToTrimError()

    def _cache_debug(self, resources, title, keyfunc):
        self._node.log.debug("------------------------------------")
        self._node.log.debug("Cache Content {0}".format(title))
        for r in resources:
            self._node.log.debug(
                "{key:<24} {filename}",
                filename=r.filename,
                key=keyfunc(r)
            )
        self._node.log.debug("----------------------------------- ")


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
