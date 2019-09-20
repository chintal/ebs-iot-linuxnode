

from .gallery import ImageGallery


class PDFPlayer(ImageGallery):
    _animation_vector = (-1, 0)

    def __init__(self, source, loop=True, **kwargs):
        self._source = source
        self._loop = loop
        super(PDFPlayer, self).__init__(**kwargs)
