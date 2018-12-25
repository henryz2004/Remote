from . import interpolation
from typing import List


class AnimationService:

    def __init__(self):

        self.animations: List[Animation] = []

    def add_animation(self, animation):

        self.animations.append(animation)

    def update(self, delta):

        self.animations = [animation for animation in self.animations if animation.state != Animation.FINISHED]
        for animation in self.animations:
            animation.update(delta)


class Animation:

    FINISHED = -1
    STOPPED = 0
    PLAYING = 1

    def __init__(self, callback):

        self.callback = callback
        self.state = Animation.STOPPED      # State of playback: -1 = finished, 0 = not playing, 1 = playing

    def start(self):

        self.state = Animation.PLAYING

    def pause(self):

        self.state = Animation.STOPPED

    def end(self):

        self.state = Animation.FINISHED
        self.callback()

    def update(self, delta):

        if self.state != Animation.PLAYING:
            return


class Translation(Animation):

    def __init__(self, start_pos, end_pos, duration, interpolator: interpolation.Interpolator, callback):
        super().__init__(callback)

        self.start_pos = start_pos
        self.pos = start_pos
        self.end_pos = end_pos

        self.t = 0              # Current time step in milliseconds
        # If animation duration isn't specified, calculate
        if duration is None:
            self.end_t = interpolator.compute_duration(start_pos, end_pos)

        # Otherwise, calculate the coefficients needed to complete animation in time
        else:
            self.end_t = duration   # End time step in milliseconds - can be "None"
            interpolator.compute_coefficients(duration)

        self.interpolator = interpolator

    def update(self, delta):
        super().update(delta)

        self.t += delta

        if self.t >= self.end_t:
            self.end()

        else:
            self.interpolator.interpolate(self, delta)

    def end(self):
        super().end()

        self.pos = self.end_pos

