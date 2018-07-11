

import os
import time
import dataset
from datetime import datetime
from datetime import timedelta
from functools import partial
from twisted.internet.defer import succeed
from twisted.internet.task import cooperate
from twisted.web.client import ResponseFailed

from .http import HttpClientMixin
from .http_utils import _http_errors

ASSET = 1
CONTENT = 2


class CacheableResource(object):
    def __init__(self, manager, filename, url=None, rtype=None):
        self._manager = manager
        self._filename = filename
        self._url = url
        self._rtype = rtype
        self._cache_path = None
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
        if not self._cache_path:
            self._cache_path = self._manager.cache_path(self.filename)
        return self._cache_path

    @property
    def filepath(self):
        return self.cache_path

    @property
    def available(self):
        return os.path.exists(self.cache_path)

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

    @property
    def node(self):
        return self._manager.node

    def __repr__(self):
        return "{1} {0}".format(self.filename, self.rtype)


class ResourceManager(object):
    def __init__(self, node, **kwargs):
        self._resource_class = kwargs.pop('resource_class', CacheableResource)
        self._node = node
        self._db = None
        self._db_dir = None
        self._cache_dir = None
        self._active_downloads = []
        super(ResourceManager, self).__init__(**kwargs)

    @property
    def node(self):
        return self._node

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

    def prefetch(self, resource, retries=None, semaphore=None):
        # Given a resource belonging to this resource manager, download it
        # to the cache if it isn't already there or update its mtime if it is.
        if resource.filename in self._active_downloads:
            return
        if resource.available:
            with open(resource.cache_path, 'a'):
                os.utime(resource.cache_path, None)
            return

        if retries is None:
            retries = self._node.config.resource_prefetch_retries

        d = self._fetch(resource, semaphore=semaphore)

        def _retry(failure, attempts=1):
            failure.trap(ResponseFailed, *_http_errors)
            attempts = attempts - 1
            if attempts:
                self._node.reactor.callLater(
                    self._node.config.resource_prefetch_retry_delay,
                    self.prefetch, resource, retries=attempts
                )
        d.addErrback(partial(_retry, attempts=retries))
        return d

    def _fetch(self, resource, semaphore=None):
        self._active_downloads.append(resource.filename)
        # self._node.log.debug("Requesting download of {filename}",
        #                      filename=resource.filename)
        d = self._node.http_download(resource.url, resource.cache_path,
                                     semaphore=semaphore)

        # Update timestamps for the downloaded file to reflect start of
        # download instead of end. Consider if this is wise.
        def _dl_finalize(r, times, _):
            with open(r.cache_path, 'a'):
                os.utime(r.cache_path, times)

        d.addCallback(
            partial(_dl_finalize, resource, (time.time(), time.time()))
        )

        def _vacate_download(maybe_failure):
            self._active_downloads.remove(resource.filename)
            return maybe_failure
        d.addBoth(_vacate_download)
        return d

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
        return self._node.db_dir

    @property
    def cache_dir(self):
        return self._node.cache_dir


class NothingToTrimError(Exception):
    pass


class CachingResourceManager(ResourceManager):
    _excluded_folders = ['log']

    def __init__(self, *args, **kwargs):
        super(CachingResourceManager, self).__init__(*args, **kwargs)
        self.cache_max_size = self._node.config.cache_max_size

    def prefetch(self, resource, retries=None, semaphore=None):
        # When done, trim the cache.
        d = super(CachingResourceManager, self).prefetch(
            resource, retries=retries, semaphore=semaphore
        )
        if d:
            def fetch_postprocess(_):
                task = cooperate(
                    self.cache_trim()
                )
                td = task.whenDone()

                def _report_done(_):
                    self._node.log.debug("Cache trim complete.")
                td.addCallback(_report_done)
            d.addCallback(fetch_postprocess)
        else:
            d = succeed(True)
        return d

    def cache_remove(self, filename):
        size = self.cache_file_size(filename)
        # self._node.log.debug("Removing {filename} of size {size} from cache",
        #                      filename=filename, size=size)
        os.remove(self.cache_path(filename))
        return size

    def cache_has(self, filename):
        r = os.path.exists(self.cache_path(filename))
        # if r:
        #     self._node.log.debug("{filename} found in the cache",
        #                          filename=filename)
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
        #    resource database) one by one. Note that items are added to the
        #    database before any attempt is made to prefetch it.
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
                break
            yield None

    @property
    def cache_resources(self):
        return self._cache_resources()

    def _cache_resources(self):
        for filename in self.cache_files:
            if self.node.cache_trim_exclusions and \
                    filename in self.node.cache_trim_exclusions:
                continue
            resource = self.get(filename)
            yield resource

    def _cache_trimmer(self, resources, trimfunc):
        # TODO Check about dangling temporary files.
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
        # self._cache_debug(r, 'by no next_use', lambda x: x.next_use)
        if len(r):
            # self.node.log.debug("NO NEXT USE")
            return self._cache_trimmer_fifo(r)

        # Next_use, next_use in the past
        r = sorted((x for x in resources if x.next_use < datetime.now()),
                   key=lambda x: x.next_use)
        # self._cache_debug(r, 'by next_use in past', lambda x: x.next_use)
        if len(r):
            return self.cache_remove(r[0].filename)

        # Next_use, next_use in the future
        cutoff = datetime.now() + timedelta(minutes=20)
        r = sorted((x for x in resources if x.next_use > cutoff),
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
                "{key} {filename}",
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

    @property
    def cache_trim_exclusions(self):
        return []
