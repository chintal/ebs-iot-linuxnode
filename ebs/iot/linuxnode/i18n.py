

import os
import logging
import gettext
from twisted import logger
from babel import Locale
from babel.messages import Catalog
from babel.messages import Message
from functools import partial


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


class TranslationManager(object):
    def __init__(self, supported_languages, catalog_dirs, twisted_logging=False):
        self._langages = supported_languages or ['en_US']
        self._catalog_dirs = catalog_dirs
        self._twisted_logging = twisted_logging
        self._log = None
        self._locales = {}
        self._contexts = {}

    def install(self):
        for language in self._langages:
            self.install_language(language)
        self._install_catalogs()

    def _install_catalogs(self):
        for d in self._catalog_dirs:
            os.makedirs(d, exist_ok=True)

    @property
    def catalog_dirs(self):
        return self._catalog_dirs

    @property
    def log(self):
        if not self._log:
            if self._twisted_logging:
                self._log = logger.Logger(namespace="i18n", source=self)
            else:
                self._log = logging.getLogger('i18n')
        return self._log

    def install_language(self, language):
        """
        Install a single language to the application's locale set. This function uses babel
        to install the appropriate locale, which can later be used to render things like
        dates, numbers, and currencies.

        Locales should not be used directly, and instead should be used using the
        translator.

        It is currently not intended for languages to be installed on the fly. Do this before
        attempting any translations.

        :param language: locale code in the form 'en_US'
        """
        lle = Locale.parse(language, sep='_')
        self.log.info("Installing Locale {0} : {1}".format(language, lle.display_name))
        self._locales[language] = lle

    def _create_context(self, context_name, catalog_dir):
        self.log.warn("Could not find Template file for {0} in {1}. Creating."
                      "".format(context_name, catalog_dir))
        pass

    def _create_context_lang(self, context_name, language, catalog_dir):
        self.log.warn("Could not find Language file {0} for {1} in {2}. Creating."
                      "".format(language, context_name, catalog_dir))
        pass

    def install_context(self, context_name, language, catalog_dir=None):
        """
        Install an i18n context. Language would be a locale code of the form "en_US".
        While not mandated, context name would typically be of the form "<module>".

        i18n Contexts are objects which can manage specific i18n strategies and contain
        and apply special helper functions for translating a string.
        """

        if not self._catalog_dirs:
            raise AttributeError("Atempted to create an i18n context without "
                                 "configuring any catalog directories!")

        if not catalog_dir:
            self.log.info("Catalog directory not specified. Using {0}."
                          "".format(self._catalog_dirs[0]))
            catalog_dir = self._catalog_dirs[0]

        if catalog_dir not in self._catalog_dirs:
            self.log.error("Attempted to use a catalog which is not configured! "
                           "Using {0} instead.".format(self._catalog_dirs[0]))
            catalog_dir = self._catalog_dirs[0]

        ctx = "{0}.{1}".format(context_name, language)
        if ctx in self._contexts.keys():
            raise KeyError(ctx)

        try:
            translator = gettext.translation(context_name, catalog_dir, languages=[language])
        except FileNotFoundError:
            self._create_context_lang(context_name, language, catalog_dir)
            translator = gettext.translation(context_name, catalog_dir, languages=[language])

        translator.install()

        self._contexts[ctx] = {
            'locale': self._locales[language],
            'i18n': translator.gettext,
            'catalog': catalog_dir,
        }

    def _i18n_msg(self, context, message):
        """
        Translate an atomic string message using the provided context. Conversion by
        this function applies a standard gettext / po mechanism. If the string is not
        included in the i18n catalogs, it will be added for later manual translation.
        """
        print("Converting {1} using ctx {0}".format(context, message))
        return context['i18n'](message)

    def _translate(self, context, obj):
        """
        Translate a translatable object using the provided context. This function
        should dispatch to specific functions depending on the type of the object.
        If the context has special helper / preprocessing functions installed, they
        are applied here.
          - Numbers, dates, times, currencies : Locale
          - Strings : _i18n
        """
        return self._i18n_msg(context, obj)

    def translator(self, context_name, language):
        """
        Generate and return an i18n function which uses the provided context. This
        can be used to replicate the typical _() structure.
        """
        ctx = self._contexts["{0}.{1}".format(context_name, language)]
        return partial(self._translate, ctx)
