

from kivy.uix.boxlayout import BoxLayout

from ebs.iot.linuxnode.widgets.colors import ColorBoxLayout
from ebs.iot.linuxnode.widgets.labels import SelfScalingColorLabel


class BasicTableEntry(object):
    def __init__(self, data):
        self._data = data
        self._parent = None

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value

    @property
    def data(self):
        return self._data


class BasicRenderableTableEntry(BasicTableEntry):
    def __init__(self, data):
        self._gui_entry = None
        super(BasicRenderableTableEntry, self).__init__(data)

    def build(self, palette=None):
        if self._gui_entry:
            return self._gui_entry

        if not palette:
            palette = self.parent.palette

        self._gui_entry = ColorBoxLayout(orientation='horizontal', spacing=10,
                                         bgcolor=palette.grid_background,
                                         size_hint=(1, None),
                                         height=self.parent.spec.row_height)

        self._gui_entry.add_widget(BoxLayout(size_hint=(None, None), width=20,
                                             height=self.parent.spec.row_height))

        for colspec in self.parent.spec.column_specs:
            kwargs = dict(
                text=str(getattr(self, colspec.accessor)),
                bgcolor=palette.cell_background,
                color=palette.cell_foreground,
                size_hint=(colspec.width_hint, None),
                height=self.parent.spec.row_height,
                font_name=self.parent.spec.font_name,
                font_size=self.parent.spec.font_size,
                valign='middle', halign=colspec.halign,
                padding_x=15, width=colspec.width,
                bold=colspec.font_bold,
            )
            label = SelfScalingColorLabel(
                **{k: v for k, v in kwargs.items() if v is not None}
            )
            label.bind(size=label.setter('text_size'))
            self._gui_entry.add_widget(label)

        self._gui_entry.add_widget(BoxLayout(size_hint=(None, None), width=20,
                                             height=self.parent.spec.row_height))
        return self._gui_entry
