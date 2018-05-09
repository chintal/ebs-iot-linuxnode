

from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.floatlayout import FloatLayout


class BaseGuiStructureMixin(object):
    def __init__(self, *args, **kwargs):
        self._gui_root = None
        self._gui_anchor_br = None
        self._gui_anchor_bl = None
        self._gui_anchor_tr = None
        self._gui_status_stack = None
        self._gui_notification_stack = None
        self._gui_debug_stack = None
        super(BaseGuiStructureMixin, self).__init__(*args, **kwargs)

    @property
    def gui_anchor_bottom_right(self):
        if not self._gui_anchor_br:
            self._gui_anchor_br = AnchorLayout(anchor_x='right',
                                               anchor_y='bottom')
            self.gui_root.add_widget(self._gui_anchor_br)
        return self._gui_anchor_br

    @property
    def gui_anchor_bottom_left(self):
        if not self._gui_anchor_bl:
            self._gui_anchor_bl = AnchorLayout(anchor_x='left',
                                               anchor_y='bottom')
            self.gui_root.add_widget(self._gui_anchor_bl)
        return self._gui_anchor_bl

    @property
    def gui_anchor_top_right(self):
        if not self._gui_anchor_tr:
            self._gui_anchor_tr = AnchorLayout(anchor_x='right',
                                               anchor_y='top')
            self.gui_root.add_widget(self._gui_anchor_tr)
        return self._gui_anchor_tr

    @property
    def gui_status_stack(self):
        if not self._gui_status_stack:
            self._gui_status_stack = StackLayout(orientation='bt-rl',
                                                 padding='8sp')
            self.gui_anchor_bottom_right.add_widget(self._gui_status_stack)
        return self._gui_status_stack

    @property
    def gui_notification_stack(self):
        if not self._gui_notification_stack:
            self._gui_notification_stack = StackLayout(orientation='bt-lr',
                                                       padding='8sp')
            self.gui_anchor_bottom_left.add_widget(self._gui_notification_stack)
        return self._gui_notification_stack

    @property
    def gui_debug_stack(self):
        if not self._gui_debug_stack:
            self._gui_debug_stack = StackLayout(orientation='tb-rl',
                                                padding='8sp')
            self.gui_anchor_top_right.add_widget(self._gui_debug_stack)
        return self._gui_debug_stack

    @property
    def gui_root(self):
        if not self._gui_root:
            self._gui_root = FloatLayout()
        return self._gui_root
