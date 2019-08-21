

import os
from six.moves.urllib.parse import urlparse
from twisted.internet.task import deferLater

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from kivy.animation import Animation

from .basemixin import BaseMixin
from .basemixin import BaseGuiMixin
from .resources import ASSET
from .widgets import StandardImage

WEBRESOURCE = 1

Base = declarative_base()
metadata = Base.metadata


class WebResourceGalleryModel(Base):
    __tablename__ = 'gallery_1'

    id = Column(Integer, primary_key=True)
    seq = Column(Integer, unique=True, index=True)
    rtype = Column(Integer)
    resource = Column(Text, index=True)
    duration = Column(Integer)

    def __repr__(self):
        return "{0:3} {1} {2} [{3}]".format(
            self.seq, self.rtype, self.resource, self.duration or ''
        )


class GalleryResource(object):
    def __init__(self, manager, seq=None, rtype=None,
                 resource=None, duration=None):
        self._manager = manager
        self._seq = seq

        self._rtype = None
        self.rtype = rtype

        self._resource = None
        self.resource = resource

        self._duration = duration

        if not self._rtype:
            self.load()

    @property
    def seq(self):
        return self._seq

    @property
    def rtype(self):
        return self._rtype

    @rtype.setter
    def rtype(self, value):
        if value not in [None, WEBRESOURCE]:
            raise ValueError
        self._rtype = value

    @property
    def resource(self):
        return self._resource

    @resource.setter
    def resource(self, value):
        if self._rtype == WEBRESOURCE:
            self._resource = os.path.basename(urlparse(value).path)

    def commit(self):
        session = self._manager.db()
        try:
            try:
                robj = session.query(self._db_model).filter_by(seq=self.seq).one()
            except NoResultFound:
                robj = self._db_model()
                robj.seq = self.seq

            robj.rtype = self.rtype
            robj.resource = self.resource
            robj.duration = self._duration

            session.add(robj)
            session.flush()
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def load(self):
        session = self._manager.db()
        try:
            robj = session.query(self._db_model).filter_by(seq=self._seq).one()
            self.rtype = robj.rtype
            self.resource = robj.resource
            self._duration = robj.duration
        except:
            session.rollback()
            raise
        finally:
            session.close()

    @property
    def _db_model(self):
        return self._manager.db_model


class GalleryManager(object):
    def __init__(self, node, gmid, default_duration=10):
        # TODO Extract db layer from here and EM into reusable format?
        self._gmid = gmid
        self._node = node
        self._seq = 0

        self._db_engine = None
        self._db = None
        self._db_dir = None
        _ = self.db

        self._default_duration = default_duration

    @property
    def default_duration(self):
        return self._default_duration

    def flush(self, force=False):
        self._node.log.debug("Flushing gallery resources")
        session = self.db()
        try:
            results = self.db_get_resources(session).all()
        except NoResultFound:
            session.close()
            return
        try:
            for robj in results:
                session.delete(robj)
                # Orphan the resource so that the cache infrastructure
                # will clear the files as needed
                r = self._node.resource_manager.get(robj.resource)
                r.rtype = None
                r.commit()
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
        if force:
            self._trigger_transition()

    def load(self, items):
        self._node.log.debug("Loading gallery resource list")
        self.flush()
        for idx, (resource, duration) in enumerate(items):
            robj = GalleryResource(
                self, seq=idx, rtype=WEBRESOURCE,
                resource=resource, duration=duration
            )
            robj.commit()
            r = self._node.resource_manager.get(resource)
            r.rtype = ASSET
            r.commit()
        self._fetch()

    def add_item(self, item):
        raise NotImplementedError

    def remove_item(self, item):
        raise NotImplementedError

    @property
    def current_seq(self):
        return self._seq

    @property
    def next_seq(self):
        session = self.db()
        try:
            self.db_get_resources(session=session,
                                  seq=self.current_seq + 1).one()
            return self.current_seq + 1
        except NoResultFound:
            pass
        except:
            self.render()
            raise
        finally:
            session.close()
        try:
            self.db_get_resources(session=session,
                                  seq=0).one()
            return 0
        except NoResultFound:
            return -1
        finally:
            session.close()

    def step(self):
        self._seq = self.next_seq
        print(self._seq)
        duration = self._trigger_transition()
        if not duration:
            duration = self.default_duration
        return deferLater(self._node.reactor, duration, self.step)

    def _trigger_transition(self):
        raise NotImplementedError

    def render(self):
        session = self.db()
        try:
            results = self.db_get_resources(session).all()
        except:
            session.rollback()
            raise
        finally:
            session.close()
        for result in results:
            print(GalleryResource(self, result.seq))

    def db_get_resources(self, session, seq=None):
        q = session.query(self.db_model)
        if seq is not None:
            q = q.filter(
                self.db_model.seq == seq
            )
        else:
            q = q.order_by(self.db_model.seq)
        return q

    @property
    def db_model(self):
        if self._gmid == WEBRESOURCE:
            return WebResourceGalleryModel

    @property
    def db(self):
        if self._db is None:
            self._db_engine = create_engine(self.db_url)
            metadata.create_all(self._db_engine)
            self._db = sessionmaker(expire_on_commit=False)
            self._db.configure(bind=self._db_engine)
        return self._db

    @property
    def db_url(self):
        return 'sqlite:///{0}'.format(os.path.join(self.db_dir, 'gallery.db'))

    @property
    def db_dir(self):
        return self._node.db_dir

    def _fetch(self):
        self._node.log.info("Triggering Gallery Fetch")
        session = self.db()
        try:
            results = self.db_get_resources(session).all()
        except:
            session.rollback()
            raise
        finally:
            session.close()
        for e in results:
            r = self._node.resource_manager.get(e.resource)
            self._node.resource_manager.prefetch(
                r, semaphore=self._node.http_semaphore_download
            )


class ResourceGalleryManager(GalleryManager):
    @property
    def resources(self):
        session = self.db()
        try:
            results = self.db_get_resources(session).all()
        except:
            session.rollback()
            raise
        finally:
            session.close()
        return [x.resource for x in results]

    def _trigger_transition(self):
        # If current_seq is -1, that means the gallery is empty. This may be
        # called repeatedly with -1. Use the returned duration to slow down
        # unnecessary requests. This function should also appropriately handle
        # creating or destroying gallery components.
        if self.current_seq == -1:
            self._node.gui_gallery_current = None
            return 30
        session = self.db()
        try:
            target = self.db_get_resources(session, seq=self.current_seq).one()
            if target.rtype == WEBRESOURCE:
                fp = self._node.resource_manager.get(target.resource).filepath
                if not os.path.exists(fp):
                    self._node.gui_gallery_current = None
                    return 10
                self._node.gui_gallery_current = fp
            return target.duration
        except:
            session.rollback()
        finally:
            session.close()

    def start(self):
        self._node.log.info("Starting Gallery Manager {gmid} of {name}",
                            gmid=self._gmid, name=self.__class__.__name__)
        self.step()


class GalleryMixin(BaseMixin):
    def __init__(self, *args, **kwargs):
        self._gallery_managers = {}
        super(GalleryMixin, self).__init__(*args, **kwargs)

    def gallery_manager(self, gmid):
        if gmid not in self._gallery_managers.keys():
            self.log.info("Initializing gallery manager {gmid}", gmid=gmid)
            self._gallery_managers[gmid] = ResourceGalleryManager(self, gmid)
        return self._gallery_managers[gmid]

    def gallery_load(self, gmid, items):
        self.gallery_manager(gmid).load(items)

    def gallery_start(self):
        self.gallery_manager(WEBRESOURCE).start()


class GalleryGuiMixin(GalleryMixin, BaseGuiMixin):
    _media_extentions_image = ['.png', '.jpg', '.bmp', '.gif', '.jpeg']

    def __init__(self, *args, **kwargs):
        self._gallery_visible = False
        self._gallery_image = None
        self._gallery_exit_animation = None
        self._gallery_entry_animation = None
        super(GalleryGuiMixin, self).__init__(*args, **kwargs)

    @property
    def gui_gallery_container(self):
        return self.gui_sidebar_right

    def gui_gallery_show(self):
        self._gallery_visible = True
        self.gui_sidebar_right_show()

    def gui_gallery_hide(self):
        self._gallery_visible = False
        self.gui_sidebar_right_hide()

    @property
    def gallery_animation_distance(self):
        return self.gui_gallery_container.height

    @property
    def gallery_exit_animation(self):
        if not self._gallery_exit_animation:
            def _when_done(_, instance):
                self.gui_animation_layer.remove_widget(instance)
            self._gallery_exit_animation = Animation(y=self.gallery_animation_distance)
            self._gallery_exit_animation.bind(on_complete=_when_done)
        return self._gallery_exit_animation

    @property
    def gallery_entry_animation(self):
        if not self._gallery_entry_animation:
            def _when_done(_, instance):
                self.gui_animation_layer.remove_widget(instance)
                instance.size_hint = (1, 1)
                self.gui_gallery_container.add_widget(instance)
            self._gallery_entry_animation = Animation(y=0)
            self._gallery_entry_animation.bind(on_complete=_when_done)
        return self._gallery_entry_animation

    @property
    def gui_gallery_current(self):
        return self._gallery_image

    @gui_gallery_current.setter
    def gui_gallery_current(self, value):
        if value is None:
            self.gui_gallery_hide()
            return
        if self._gallery_image:
            pos = self._gallery_image.pos
            self.gui_gallery_container.remove_widget(self._gallery_image)
            self._gallery_image.size_hint = (None, None)
            self._gallery_image.pos = pos
            self.gui_animation_layer.add_widget(self._gallery_image)
            self.gallery_exit_animation.start(self._gallery_image)

        if os.path.splitext(value)[1] in self._media_extentions_image:
            self._gallery_image = StandardImage(source=value, allow_stretch=True,
                                                keep_ratio=True, anim_delay=0.08)
            if not self._gallery_visible:
                self.gui_gallery_container.add_widget(self._gallery_image)
                self.gui_gallery_show()
                return
            self._gallery_image.size_hint = (None, None)
            self._gallery_image.size = self.gui_gallery_container.size
            self._gallery_image.pos = (
                self.gui_gallery_container.pos[0],
                self.gui_gallery_container.pos[1] - self.gallery_animation_distance
            )
            self.gui_animation_layer.add_widget(self._gallery_image)
            self.gallery_entry_animation.start(self._gallery_image)

    def gui_setup(self):
        super(GalleryGuiMixin, self).gui_setup()
