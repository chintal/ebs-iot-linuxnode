

class CompositeAnimationManager(object):
    def __init__(self):
        self._animations = []
        self._finish_handler = None

    def add(self, animation, widget):
        self._animations.append((animation, widget))

    def _anim_done_handler(self, anim, widget):
        self._animations.remove((anim, widget))
        if not self._animations:
            self._finish_handler()

    def when_done(self, handler):
        self._finish_handler = handler

    def start(self):
        for animation, widget in self._animations:
            animation.bind(on_complete=self._anim_done_handler)
            animation.start(widget)

    def cancel(self):
        for anim, widget in self._animations:
            anim.cancel_all(widget)

    def clear(self):
        self.cancel()
        self._animations = []
