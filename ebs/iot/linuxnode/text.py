

import os
from kivy.core.text import FontContextManager

from .basemixin import BaseMixin
from .basemixin import BaseGuiMixin
from .log import NodeLoggingMixin


class AdvancedTextMixin(NodeLoggingMixin, BaseMixin):
    pass


class AdvancedTextGuiMixin(AdvancedTextMixin, BaseGuiMixin):
    def __init__(self, *args, **kwargs):
        super(AdvancedTextGuiMixin, self).__init__(*args, **kwargs)
        self._text_font_context = None

    def install(self):
        if self.config.text_use_fcm:
            self._text_create_fcm()

    def _text_create_fcm(self):
        fc = self._appname
        if self.config.text_fcm_system:
            fc = "system://{0}".format(fc)
        self._text_font_context = fc
        self.log.info("Creating FontContextManager {0} using fonts in {1}"
                      .format(fc, self.config.text_fcm_fonts))
        FontContextManager.create(fc)

        for filename in os.listdir(self.config.text_fcm_fonts):
            self.log.debug("Installing Font {0} to FCM {1}".format(filename, self._text_font_context))
            FontContextManager.add_font(fc, os.path.join(self.config.text_fcm_fonts, filename))

    @property
    def text_font_params(self):
        params = {}
        if self._text_font_context:
            params.update({
                'font_context': self._text_font_context
            })
        else:
            params.update({
                'font_name': self.config.text_font_name
            })
        return params
