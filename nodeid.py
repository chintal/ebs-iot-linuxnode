

import netifaces
import uuid

from .widgets import ColorLabel


class NodeIDMixin(object):
    _node_id_getter = "uuid"
    _node_id_params = {}

    def __init__(self, *args, **kwargs):
        super(NodeIDMixin, self).__init__(*args, **kwargs)
        self._id = None

    @property
    def id(self):
        if self._id is None:
            self._id = self._get_id()
        return self._id

    def _get_id(self):
        getter = "_get_node_id_{0}".format(self._node_id_getter)
        return getattr(self, getter)(**self._node_id_params).upper()

    @staticmethod
    def _get_node_id_uuid(**_):
        node_id = uuid.getnode()
        if (node_id >> 40) % 2:
            raise OSError("The system does not seem to have a valid MAC")
        return hex(node_id)[2:]

    @staticmethod
    def _get_node_id_netifaces(interface):
        mac = netifaces.ifaddresses(interface)[netifaces.AF_LINK][0]['addr']
        return mac.replace(':', '')


class NodeIDGuiMixin(NodeIDMixin):
    def __init__(self, *args, **kwargs):
        super(NodeIDGuiMixin, self).__init__(*args, **kwargs)
        self._gui_id_tag = None

    @property
    def gui_id_tag(self):
        if not self._gui_id_tag:
            self._gui_id_tag = ColorLabel(
                text=self.id, size_hint=(None, None),
                width=250, height=50, bgcolor=[0, 1, 0, 0.25],
                font_size='18sp', valign='middle', halign='center',
            )
            self.gui_status_stack.add_widget(self._gui_id_tag)
        return self._gui_id_tag

    def gui_setup(self):
        _ = self.gui_id_tag
