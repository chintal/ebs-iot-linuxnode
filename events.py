

import os
import dataset
from datetime import datetime
from datetime import timedelta
from cached_property import threaded_cached_property_with_ttl
from six.moves.urllib.parse import urlparse
from twisted.internet.task import deferLater

from .basenode import BaseIoTNode
from .resources import CacheableResource


WEBRESOURCE = 1
TEXT = 2


class ScheduledResourceClass(CacheableResource):

    @threaded_cached_property_with_ttl(ttl=3)
    def next_use(self):
        return self.node.event_manager(WEBRESOURCE).next(
            resource=self.filename
        ).start_time


class Event(object):
    def __init__(self, manager, eid, etype=None, resource=None,
                 start_time=None, duration=None):
        self._manager = manager
        self._eid = eid

        self._etype = None
        self.etype = etype

        self._resource = None
        self.resource = resource

        self._start_time = None
        self.start_time = start_time

        self._duration = None
        self.duration = duration
        if not self._etype:
            self.load()

    @property
    def eid(self):
        return self._eid

    @property
    def etype(self):
        return self._etype

    @etype.setter
    def etype(self, value):
        if value not in [None, WEBRESOURCE, TEXT]:
            raise ValueError
        self._etype = value

    @property
    def resource(self):
        return self._resource

    @resource.setter
    def resource(self, value):
        if self.etype == WEBRESOURCE:
            self._resource = os.path.basename(urlparse(value).path)
        elif self.etype == TEXT:
            self._resource = value

    @property
    def start_time(self):
        return self._start_time

    @start_time.setter
    def start_time(self, value):
        if not value:
            return
        if isinstance(value, datetime):
            self._start_time = value
        else:
            self._start_time = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')

    @property
    def duration(self):
        return self._duration or None

    @duration.setter
    def duration(self, value):
        self._duration = int(value) if value else None

    def commit(self):
        with self._manager.db as db:
            db[self.tname].upsert(
                row={'eid': self._eid,
                     'etype': self._etype,
                     'resource': self._resource,
                     'start_time': self._start_time,
                     'duration': self._duration},
                keys=['eid']
            )

    def load(self):
        with self._manager.db as db:
            data = db[self.tname].find_one(eid=self._eid)
            if not data:
                return
            self.etype = data['etype']
            self.resource = data['resource']
            self._start_time = data['start_time']
            self.duration = data['duration']

    @property
    def tname(self):
        return self._manager.db_table_name

    def __repr__(self):
        return "{0:3} {2} {3:.2f} {1}".format(
            self.eid, self.resource, self.etype,
            (self.start_time - datetime.now()).total_seconds()
        )


class EventManager(object):
    def __init__(self, node, emid):
        self._emid = emid
        self._node = node
        self._db = None
        self._db_dir = None
        self._execute_task = None
        self._current_event = None
        self._current_event_resource = None
        _ = self.db

    def insert(self, eid, **kwargs):
        event = Event(self, eid, **kwargs)
        event.commit()

    def remove(self, eid):
        with self.db as db:
            db[self.db_table_name].delete(eid=eid)

    def _pointers(self, cond, resource=None, follow=False):
        if not resource:
            r = self.db[self.db_table_name].find(order_by='start_time')
        else:
            r = self.db[self.db_table_name].find(order_by='start_time',
                                                 resource=resource)
        e = None
        l = None
        for e in r:
            if l and cond(l, e):
                break
            l = e
        if l:
            if not follow:
                return Event(self, l['eid'])
            else:
                if e:
                    ne = Event(self, e['eid'])
                else:
                    ne = None
                return Event(self, l['eid']), ne

    def previous(self, resource=None, follow=False):
        return self._pointers(
            lambda l, e: e['start_time'] >= datetime.now(),
            resource=resource, follow=follow
        )

    def next(self, resource=None, follow=False):
        return self._pointers(
            lambda l, e: l['start_time'] >= datetime.now(),
            resource=resource, follow=follow
        )

    def get(self, eid):
        return Event(self, eid)

    def prune(self):
        # TODO This doesn't work!
        # with self.db as db:
        #     r = db[self.db_table_name].find(start_time={'lt': datetime.now()})
        #     for result in r:
        #         print("Removing {0}".format(r))
        #         self.remove(result['eid'])
        results = self.db[self.db_table_name].find(order_by='start_time')
        for result in results:
            if result['start_time'] >= datetime.now():
                break
            self._node.log.warn("Pruning missed event {event}", event=result)
            self.remove(result['eid'])

    def render(self):
        for result in self.db[self.db_table_name].find(order_by='start_time'):
            print(Event(self, result['eid']))

    @property
    def db_table_name(self):
        return "events_{0}".format(self._emid)

    @property
    def db(self):
        if self._db is None:
            self._db = dataset.connect(self.db_url)
            self._db.get_table(self.db_table_name)
        return self._db

    @property
    def db_url(self):
        return 'sqlite:///{0}'.format(os.path.join(self.db_dir, 'events.db'))

    @property
    def db_dir(self):
        return self._node.db_dir

    @property
    def current_event(self):
        return self._current_event
    
    @property
    def current_event_resource(self):
        return self._current_event_resource

    def _trigger_event(self, event):
        raise NotImplementedError

    def _finish_event(self, _):
        self._node.log.debug("Successfully finished event {eid}",
                             eid=self._current_event)
        self._current_event = None
        self._current_event_resource = None

    def _event_scheduler(self):
        event = None
        nevent = None
        le, ne = self.previous(follow=True)
        if le:
            ltd = datetime.now() - le.start_time
            # self._node.log.debug("S LTD {ltd}", ltd=ltd)
            if abs(ltd) < timedelta(seconds=5):
                event = le
                nevent = ne
        if not event:
            ne, nne = self.next(follow=True)
            if ne:
                ntd = ne.start_time - datetime.now()
                # self._node.log.debug("S NTD {ntd}", ntd=ntd)
                if abs(ntd) < timedelta(seconds=3):
                    event = ne
                    nevent = nne
        if event:
            self._trigger_event(event)
        self._execute_task = self._event_scheduler_hop(nevent)

    def _event_scheduler_hop(self, next_event=None):
        if not next_event:
            next_event = self.next()
        if not next_event:
            next_start = timedelta(seconds=60)
        else:
            next_start = next_event.start_time - datetime.now()
            if next_start > timedelta(seconds=60):
                next_start = timedelta(seconds=60)
        # self._node.log.debug("SCHED HOP {ns}", ns=next_start.seconds)
        return deferLater(self._node.reactor, next_start.seconds,
                          self._event_scheduler)

    def start(self):
        self._event_scheduler()


class TextEventManager(EventManager):
    def _trigger_event(self, event):
        self._node.log.info("Executing Event : {0}".format(event))
        d = self._node.marquee_play(text=event.resource, duration=event.duration)
        d.addCallback(self._finish_event)
        self._current_event = event.eid
        self._current_event_resource = event.resource
        self.remove(event.eid)
        self.prune()


class WebResourceEventManager(EventManager):
    def _trigger_event(self, event):
        r = self._node.resource_manager.get(event.resource)
        if r.available:
            self._node.log.info("Executing Event : {0}".format(event))
            d = self._node.media_play(content=r, duration=event.duration)
            d.addCallback(self._finish_event)
            self._current_event = event.eid
            self._current_event_resource = event.resource
        else:
            self._node.log.warn("Media not ready for {event}",
                                event=event)
        self.remove(event.eid)
        self.prune()

    def _fetch(self):
        self._node.log.info("Triggering Fetch")
        for e in self.db[self.db_table_name].find(order_by='start_time'):
            if e['start_time'] - datetime.now() > timedelta(seconds=1200):
                break
            r = self._node.resource_manager.get(e['resource'])
            self._node.resource_manager.prefetch(
                r, semaphore=self._node.http_semaphore_download
            )
        self._fetch_task = deferLater(self._node.reactor, 600, self._fetch)

    def _fetch_scheduler(self):
        self._fetch()

    def _prefetch(self):
        self._node.log.info("Triggering Prefetch")
        for e in self.db[self.db_table_name].find(order_by='start_time'):
            if e['start_time'] - datetime.now() > timedelta(seconds=(3600 * 6)):
                break
            r = self._node.resource_manager.get(e['resource'])
            self._node.resource_manager.prefetch(
                r, semaphore=self._node.http_semaphore_background
            )
        self._prefetch_task = deferLater(self._node.reactor, 3600, self._prefetch)

    def _prefetch_scheduler(self):
        self._prefetch()

    def start(self):
        super(WebResourceEventManager, self).start()
        self._fetch_scheduler()
        self._prefetch_scheduler()


class EventManagerMixin(BaseIoTNode):
    def __init__(self, *args, **kwargs):
        self._event_managers = {}
        super(EventManagerMixin, self).__init__(*args, **kwargs)

    def event_manager(self, emid):
        if emid not in self._event_managers.keys():
            self.log.info("Initializing event manager {emid}", emid=emid)
            if emid == WEBRESOURCE:
                self._event_managers[emid] = WebResourceEventManager(self, emid)
            elif emid == TEXT:
                self._event_managers[emid] = TextEventManager(self, emid)
            else:
                self._event_managers[emid] = EventManager(self, emid)
        return self._event_managers[emid]

    @property
    def _cache_trim_exclusions(self):
        if self.event_manager(WEBRESOURCE).current_event_resource:
            return [self.event_manager(WEBRESOURCE).current_event_resource]
        else:
            return []
