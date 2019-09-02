
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout


class BaseGuiStructureMixin(object):
    def __init__(self, *args, **kwargs):
        self._gui_root = None
        self._gui_structure_root = None
        self._gui_primary_root = None
        self._gui_footer = None
        self._gui_anchor_br = None
        self._gui_anchor_bl = None
        self._gui_anchor_tr = None
        self._gui_status_stack = None
        self._gui_notification_stack = None
        self._gui_notification_row = None
        self._gui_debug_stack = None
        self._gui_content_root = None
        self._gui_main_content = None
        self._gui_sidebar_right = None
        self._gui_sidebar_right_users = set()
        self._gui_sidebar_left = None
        self._gui_animation_layer = None
        super(BaseGuiStructureMixin, self).__init__(*args, **kwargs)

    @property
    def gui_anchor_bottom_right(self):
        if not self._gui_anchor_br:
            self._gui_anchor_br = AnchorLayout(anchor_x='right',
                                               anchor_y='bottom',
                                               pos_hint={'pos': [0, 0]})
            self.gui_primary_root.add_widget(self._gui_anchor_br)
        return self._gui_anchor_br

    @property
    def gui_anchor_bottom_left(self):
        if not self._gui_anchor_bl:
            self._gui_anchor_bl = AnchorLayout(anchor_x='left',
                                               anchor_y='bottom',
                                               pos_hint={'pos': [0, 0]})
            self.gui_primary_root.add_widget(self._gui_anchor_bl)
        return self._gui_anchor_bl

    @property
    def gui_anchor_top_right(self):
        if not self._gui_anchor_tr:
            self._gui_anchor_tr = AnchorLayout(anchor_x='right',
                                               anchor_y='top',
                                               pos_hint={'pos': [0, 0]})
            self.gui_primary_root.add_widget(self._gui_anchor_tr)
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
            self._gui_notification_stack = GridLayout(cols=1,
                                                      padding='8sp',
                                                      spacing='8sp',
                                                      size_hint_y=None,)

            def _set_height(_, mheight):
                self.gui_notification_stack.height = mheight
            self.gui_notification_stack.bind(minimum_height=_set_height)
            self.gui_anchor_bottom_left.add_widget(self._gui_notification_stack)
        return self._gui_notification_stack

    @property
    def gui_notification_row(self):
        if not self._gui_notification_row:
            self._gui_notification_row = StackLayout(orientation='lr-bt',
                                                     spacing='8sp')
            self.gui_notification_stack.add_widget(self._gui_notification_row)
        return self._gui_notification_row

    def gui_notification_update(self):
        self.gui_notification_row.do_layout()
        self.gui_notification_stack.do_layout()

    @property
    def gui_debug_stack(self):
        if not self._gui_debug_stack:
            self._gui_debug_stack = StackLayout(orientation='tb-rl',
                                                padding='8sp')
            self.gui_anchor_top_right.add_widget(self._gui_debug_stack)
        return self._gui_debug_stack

    @property
    def gui_footer(self):
        if not self._gui_footer:
            _ = self.gui_primary_root
            self._gui_footer = BoxLayout(
                orientation='vertical', size_hint=(1, None),
                height=80, padding=['0sp', '0sp', '0sp', '8sp']
            )
        return self._gui_footer

    def gui_footer_show(self):
        if not self._gui_footer.parent:
            self.gui_structure_root.add_widget(self._gui_footer)

    def gui_footer_hide(self):
        if self._gui_footer.parent:
            self.gui_structure_root.remove_widget(self._gui_footer)

    @property
    def gui_primary_root(self):
        if not self._gui_primary_root:
            self._gui_primary_root = FloatLayout()
            self.gui_structure_root.add_widget(self._gui_primary_root)
        return self._gui_primary_root

    @property
    def gui_structure_root(self):
        if not self._gui_structure_root:
            self._gui_structure_root = BoxLayout(orientation='vertical')
            self.gui_root.add_widget(self._gui_structure_root)
        return self._gui_structure_root

    @property
    def gui_main_content(self):
        if not self._gui_main_content:
            self._gui_main_content = FloatLayout()
            self.gui_content_root.add_widget(self._gui_main_content)
        return self._gui_main_content

    @property
    def gui_sidebar_right(self):
        if not self._gui_sidebar_right:
            x_hint = self.config.sidebar_width / (1 - self.config.sidebar_width)
            self._gui_sidebar_right = BoxLayout(orientation='vertical',
                                                size_hint=(x_hint, 1))
        return self._gui_sidebar_right

    def gui_sidebar_right_show(self, key):
        if not key:
            key = 'unspecified'
        self._gui_sidebar_right_users.add(key)
        if not self.gui_sidebar_right.parent:
            self.log.debug("Showing right sidebar")
            self.gui_content_root.add_widget(self.gui_sidebar_right)

    def gui_sidebar_right_hide(self, key):
        if key not in self._gui_sidebar_right_users:
            return
        self._gui_sidebar_right_users.remove(key)
        if len(self._gui_sidebar_right_users):
            return
        if self.gui_sidebar_right.parent:
            self.log.debug("Hiding right sidebar")
            self.gui_content_root.remove_widget(self.gui_sidebar_right)

    # @property
    # def gui_sidebar_left(self):
    #     if not self._gui_sidebar_left:
    #         self._gui_sidebar_left = FloatLayout(size_hint=((0.28/0.72), 1))
    #     return self._gui_sidebar_left
    #
    # def gui_sidebar_left_show(self):
    #     if not self.gui_sidebar_left.parent:
    #         print(self.gui_content_root.children)
    #         self.gui_content_root.add_widget(
    #             self.gui_sidebar_left,
    #             index=len(self.gui_content_root.children)
    #         )
    #         self.gui_content_root.do_layout()
    #         print(self.gui_content_root.children)
    #
    # def gui_sidebar_left_hide(self):
    #     if self.gui_sidebar_left.parent:
    #         self.gui_content_root.remove_widget(self.gui_sidebar_left)

    @property
    def gui_content_root(self):
        if not self._gui_content_root:
            self._gui_content_root = GridLayout(rows=1, spacing=10)
            self.gui_root.add_widget(self._gui_content_root,
                                     len(self.gui_root.children) - 1)
        return self._gui_content_root

    @property
    def gui_animation_layer(self):
        if not self._gui_animation_layer:
            self._gui_animation_layer = FloatLayout()
            self.gui_root.add_widget(self._gui_animation_layer,
                                     len(self.gui_root.children) - 1)
        return self._gui_animation_layer

    @property
    def gui_root(self):
        if not self._gui_root:
            self._gui_root = FloatLayout()
        return self._gui_root

