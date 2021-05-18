

from ebs.iot.linuxnode.tables.renderable import BasicRenderableTable
from ebs.iot.linuxnode.tables.spec import BasicTableSpec


class TranslatableTableSpec(BasicTableSpec):
    def __init__(self, *args, **kwargs):
        self._languages = kwargs.pop('languages', [])
        self._metadata = kwargs.pop('i18n_metadata', {})
        super(TranslatableTableSpec, self).__init__(*args, **kwargs)

    def install_metadata(self, metadata):
        self._metadata.update(metadata)

    def install(self):
        super(TranslatableTableSpec, self).install()
        self._i18n_install_languages()

    def _i18n_install_languages(self):
        for language in self._languages:
            self.parent.log.debug("Installing Language {0} for Table {1}".format(language, self.name))
            self.i18n_install_language(language)

    @property
    def i18n_metadata(self):
        if not self._metadata:
            self._metadata = {
                'project': None,
                'version': None,
                'msgid_bugs_address': None,
                'language_team': None,
                'last_translator': None,
                'copyright_holder': None,
            }
        return self._metadata

    def i18n_install_language(self, language):
        if language not in self._languages:
            self._languages.append(language)
        self.parent.node.i18n.install_context(self.name, language, metadata=self.i18n_metadata)

    @property
    def languages(self):
        return self._languages

    def i18n_translator(self, language):
        return self.parent.node.i18n.translator(self.name, language)


class TranslatableRenderableTable(BasicRenderableTable):
    def __init__(self, *args, **kwargs):
        self._i18n_current = None
        super(TranslatableRenderableTable, self).__init__(*args, **kwargs)

    def install(self):
        super(TranslatableRenderableTable, self).install()
        self._i18n_current = self.spec.i18n_translator(self.spec.languages[0])

    @property
    def spec(self) -> TranslatableTableSpec:
        return self._spec

    @property
    def i18n(self):
        return self._i18n_current

    def preprocess(self, value):
        return self.i18n(value)
