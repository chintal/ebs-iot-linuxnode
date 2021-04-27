

class BasicTablePalette(object):
    def __init__(self, **kwargs):
        self._color_cell_background = kwargs.pop('color_cell_background', None)
        self._color_cell_foreground = kwargs.pop('color_cell_foreground', None)
        self._color_header_cell_background = kwargs.pop('color_header_cell_background', None)
        self._color_header_cell_foreground = kwargs.pop('color_header_cell_foreground', None)
        self._color_grid_background = kwargs.pop('color_grid_background', None)

    @property
    def cell_background(self):
        return self._color_cell_background

    @property
    def cell_foreground(self):
        return self._color_cell_foreground

    @property
    def header_cell_background(self):
        return self._color_header_cell_background

    @property
    def header_cell_foreground(self):
        return self._color_header_cell_foreground

    @property
    def grid_background(self):
        return self._color_grid_background

    def __repr__(self):
        rv = "<{0}>".format(self.__class__.__name__)
        rv += "\n - grid_background : {}".format(self.grid_background)
        rv += "\n - cell_background : {}".format(self.cell_background)
        rv += "\n - cell_foreground : {}".format(self.cell_foreground)
        rv += "\n - header_cell_background : {}".format(self.header_cell_background)
        rv += "\n - header_cell_foreground : {}".format(self.header_cell_foreground)
        return rv


class BasicColumnSpec(object):
    def __init__(self, title, accessor, halign=None, font_bold=None, width=None, width_hint=None):
        self._parent = None
        self._title = title
        self._accessor = accessor
        self._halign = halign
        self._font_bold = font_bold
        self._width = width
        self._width_hint = width_hint

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value

    @property
    def title(self):
        return self._title

    @property
    def accessor(self):
        return self._accessor

    @property
    def halign(self):
        return self._halign or 'center'

    @property
    def font_bold(self):
        if self._font_bold is None:
            return self.parent.font_bold
        return self._font_bold

    @property
    def width(self):
        return self._width

    @property
    def width_hint(self):
        if self._width:
            return None
        return self._width_hint or 1


class BasicTableSpec(object):
    def __init__(self, column_specs, show_column_header, dedup_keys=False,
                 row_height=90, row_spacing=10, font_size='42sp',
                 font_bold=False):
        self._column_specs = column_specs
        for colspec in self._column_specs:
            colspec.parent = self
        self._show_column_header = show_column_header
        self._row_height = row_height
        self._row_spacing = row_spacing
        self._font_size = font_size
        self._font_bold = font_bold
        self._dedup_keys = dedup_keys

    @property
    def font_size(self):
        return self._font_size

    @property
    def font_bold(self):
        return self._font_bold

    @property
    def show_column_header(self) -> bool:
        return self._show_column_header

    @property
    def column_specs(self) -> list:
        return self._column_specs

    @property
    def row_height(self):
        return self._row_height

    @property
    def row_spacing(self):
        return self._row_spacing

    @property
    def dedup_keys(self):
        return self._dedup_keys
