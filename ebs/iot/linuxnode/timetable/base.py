

import arrow
from twisted.internet.task import deferLater
from twisted.internet.defer import CancelledError

from ebs.iot.linuxnode.log import NodeLoggingMixin
from ebs.iot.linuxnode.basemixin import BaseGuiMixin

from ebs.iot.linuxnode.tables.animated import BasicAnimatedTable
from ebs.iot.linuxnode.tables.entries import BasicRenderableTableEntry
from ebs.iot.linuxnode.tables.spec import BasicTablePalette
from ebs.iot.linuxnode.tables.spec import BasicTableSpec
from ebs.iot.linuxnode.tables.spec import BasicColumnSpec


class TimetableEntry(BasicRenderableTableEntry):
    def __init__(self, data):
        super(TimetableEntry, self).__init__(data)

    @property
    def name(self):
        raise NotImplementedError

    @property
    def ts_start(self):
        raise NotImplementedError

    @property
    def ts_end(self):
        raise NotImplementedError


class Timetable(BasicAnimatedTable):
    _prior_window = 360
    _post_window = 60
    _period_page = 12

    def __init__(self, node, spec=None):
        self._redraw_task = None
        self._current_page = 0
        if not spec:
            spec = BasicTableSpec([
                BasicColumnSpec("Name", 'name'),
                BasicColumnSpec("Start Time", "ts_start"),
                BasicColumnSpec("End Time", "ts_end")],
                show_column_header=True,
                row_height=90, row_spacing=10, font_size='42sp', font_bold=False)
        super(Timetable, self).__init__(node, spec)

    def build(self, entries):
        # self._current_page = 0
        return super(Timetable, self).build(entries=entries)

    @property
    def active_entries(self):
        return [x for x in sorted(self._entries, key=lambda y: y.ts_start)
                if x.ts_start.shift(minutes=-1 * self._prior_window) < arrow.now() < x.ts_end.shift(minutes=self._post_window)]

    def start(self):
        self._node.log.info("Starting Timetable Redraw Task for {0}".format(self))
        self._current_page = 0
        self.step()

    def step(self):
        self._node.log.debug("Drawing page {0} / {1}".format(self._current_page + 1, self.total_pages))
        self.redraw_entries(entries=self.page_entities(self._current_page))
        self._current_page += 1
        if self._current_page >= self.total_pages:
            self._current_page = 0

        duration = self._period_page
        self._redraw_task = deferLater(self._node.reactor, duration, self.step)

        def _cancel_handler(failure):
            failure.trap(CancelledError)
        self._redraw_task.addErrback(_cancel_handler)

        return self._redraw_task

    def stop(self):
        self._node.log.info("Stopping Timetable Redraw Task for {0}".format(self))
        if self._redraw_task:
            self._redraw_task.cancel()


class BaseTimetableMixin(NodeLoggingMixin):
    _timetable_class = Timetable
    _timetable_entry_class = TimetableEntry

    def __init__(self, *args, **kwargs):
        super(BaseTimetableMixin, self).__init__(*args, **kwargs)
        self._timetable = self._timetable_class(self)

    def timetable_update(self, data, incremental=False):
        self._timetable.update([self._timetable_entry_class(x) for x in data],
                               incremental)


class BaseTimetableGuiMixin(BaseTimetableMixin, BaseGuiMixin):
    def __init__(self, *args, **kwargs):
        self._timetable_palette = None
        self._timetable_gui = None
        self._task_timetable_redraw = None
        super(BaseTimetableGuiMixin, self).__init__(*args, **kwargs)

    @property
    def timetable_palette(self):
        if not self._timetable_palette:
            self._timetable_palette = BasicTablePalette(
                color_cell_background=self.gui_color_2,
                color_cell_foreground=self.gui_color_foreground,
                color_header_cell_background=self.gui_color_1,
                color_header_cell_foreground=self.gui_color_foreground,
                color_grid_background=self.gui_color_background,
            )
        return self._timetable_palette

    @property
    def timetable_gui(self):
        if not self._timetable_gui:
            self._timetable.palette = self.timetable_palette
            self._timetable_gui = self._timetable.build(entries=self._timetable.active_entries)
            self._timetable.start()
        return self._timetable_gui

    def _timetable_redraw(self):
        self._timetable.build(entries=self._timetable.active_entries)
