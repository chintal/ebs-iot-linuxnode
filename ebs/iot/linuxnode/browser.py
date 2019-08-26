

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options

from .basemixin import BaseMixin
from .config import ConfigMixin
from .background import OverlayWindowGuiMixin


class BrowserManager(object):
    def __init__(self, node, bmid):
        self._bmid = bmid
        self._node = node
        self._target = None
        self._browser = None

    @property
    def options(self):
        start_page = self._node.config.browser_default_url
        chrome_options = Options()
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--app={0}".format(start_page))
        # if self._node.config.http_proxy_enabled:
        #     chrome_options.add_argument(
        #         "--proxy={0}".format(self._node.config.http_proxy_url)
        #     )
        return chrome_options

    @property
    def browser(self):
        if not self._browser:
            self._browser = Chrome(options=self.options)
        return self._browser

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        self.browser.get(value)
        self._target = value

    def clear(self):
        self.target = 'about:blank'

    def set_geometry(self, x, y, width, height):
        self._node.log.debug("Setting browser geometry : "
                             "({x}, {y}), ({width}, {height})",
                             x=x, y=y, width=width, height=height)
        self.browser.set_window_rect(x, y, width, height)

    def start(self):
        _ = self.browser

    def terminate(self):
        if not self._browser:
            return
        self._browser.close()


class BrowserMixin(ConfigMixin, BaseMixin):
    def __init__(self, *args, **kwargs):
        self._browser_managers = {}
        super(BrowserMixin, self).__init__(*args, **kwargs)

    def browser_manager(self, bmid):
        if bmid not in self._browser_managers.keys():
            self.log.info("Initializing browser manager {bmid}", bmid=bmid)
            self._browser_managers[bmid] = BrowserManager(self, bmid)
        return self._browser_managers[bmid]

    @property
    def browser(self):
        return self.browser_manager(0)

    def browser_start(self):
        self.browser_manager(0).start()
        self.gui_browser_show()

    def browser_stop(self):
        self.gui_browser_hide()
        self.browser_manager(0).clear()

    def gui_browser_show(self):
        pass

    def gui_browser_hide(self):
        pass

    def start(self):
        super(BrowserMixin, self).start()
        if self.config.browser_show_default:
            self._reactor.callLater(2, self.browser_start)

    def stop(self):
        for bmid in self._browser_managers.keys():
            self._browser_managers[bmid].terminate()


class BrowserGuiMixin(OverlayWindowGuiMixin):
    def __init__(self, *args, **kwargs):
        self._browser_visible = False
        super(BrowserGuiMixin, self).__init__(*args, **kwargs)

    @property
    def gui_browser_container(self):
        return self.gui_sidebar_right

    def gui_browser_show(self):
        if not self.overlay_mode:
            self.overlay_mode = True
        self._browser_visible = True
        self.gui_sidebar_right_show()
        self.browser.set_geometry(
            self.gui_sidebar_right.x, self.gui_sidebar_right.y,
            self.gui_sidebar_right.width, self.gui_sidebar_right.height
        )

    def gui_browser_hide(self):
        self._browser_visible = False
        self.gui_sidebar_right_hide()

    def gui_setup(self):
        super(BrowserGuiMixin, self).gui_setup()
