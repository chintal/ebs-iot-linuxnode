

import os
from babel import Locale
from functools import partial
from kivy.core.text import FontContextManager

from .basemixin import BaseMixin
from .basemixin import BaseGuiMixin
from .log import NodeLoggingMixin


indian_languages = [
    'en_IN',  # English
    'hi_IN',  # Hindi
    'te_IN',  # Telugu
    'ta_IN',  # Tamil
    'bn_IN',  # Bengali
    'pa_IN',  # Punjabi
    'ur_IN',  # Urdu
    'kn_IN',  # Kannada
    'or_IN',  # Oriya
    'gu_IN',  # Gujarati
    'ml_IN',  # Malayalam
]


class AdvancedTextMixin(NodeLoggingMixin, BaseMixin):
    _supported_languages = ['en_US']

    def __init__(self, *args, **kwargs):
        self._i18n_locales = {}
        self._i18n_contexts = {}
        super(AdvancedTextMixin, self).__init__(*args, **kwargs)

    def i18n_install_language(self, language):
        l = Locale.parse(language, sep='_')
        self.log.info("Installing Locale {0} : {1}".format(language, l.display_name))
        self._i18n_locales[language] = l

    @property
    def i18n_supported_languages(self):
        return self._supported_languages

    def i18n_install_context(self, context, language):
        if context in self._i18n_contexts.keys():
            raise KeyError(context)
        self._i18n_contexts[context] = {
            'locale': self._i18n_locales[language],
            'i18n': lambda x: x,
        }

    def _i18n(self, context, message):
        print("Converting {1} using ctx {0}".format(context, message))
        return context['i18n'](message)

    def _i18n_translate(self, context, obj):
        return self._i18n(context, obj)

    def i18n_translator(self, context):
        ctx = self._i18n_contexts[context]
        return partial(self._i18n_translate, ctx)

    def install(self):
        super(AdvancedTextMixin, self).install()
        for language in self._supported_languages:
            self.i18n_install_language(language)


class AdvancedTextGuiMixin(AdvancedTextMixin, BaseGuiMixin):
    def __init__(self, *args, **kwargs):
        self._text_font_context = None
        super(AdvancedTextGuiMixin, self).__init__(*args, **kwargs)

    @property
    def text_font_context(self):
        if not self._text_font_context and self.config.text_use_fcm:
            self._text_create_fcm()
        return self._text_font_context

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
        if self.text_font_context:
            params.update({
                'font_context': self._text_font_context
            })
        else:
            params.update({
                'font_name': self.config.text_font_name
            })
        return params
