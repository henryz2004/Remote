import math


class TimedAnimation:
    """
    Animation that stops after a certain amount of time has passed
    """

    def __init__(self, start_pos, end_pos, duration, interp_function, callback=None):

        self.initial = start_pos
        self.pos = start_pos            # Start position
        self.target = end_pos           # Target position
        self.cur_t = 0                  # Current time
        self.end_t = duration           # End time
        self.interp = interp_function   # Interpolation function
        self.callback = callback if callback else lambda *_: print("Animation has finished")
        self.alive = True               # Is the animation running

    def update(self, delta):

        self.cur_t += delta

        if self.cur_t >= self.end_t:
            self.pos = self.target
            self.alive = False
            self.callback()
            return

        self.interp(self, delta)


# TODO: Merge this and TimedAnimation
class TargetAnimation:
    """
    Animation that stops if position is near target position
    """

    def __init__(self, start_pos, end_pos, interp_function, callback=None, epsilon=5):

        self.initial = start_pos
        self.pos = start_pos
        self.target = end_pos
        self.cur_t = 0
        self.interp = interp_function
        self.callback = callback if callback else lambda *_: print("Animation has finished")
        self.epsilon = epsilon          # How close self.pos must be in order to terminate animation
        self.alive = True

    def update(self, delta):

        self.cur_t += delta

        if math.sqrt((self.target[0]-self.pos[0])**2 + (self.target[1]-self.pos[1])**2) <= self.epsilon:
            self.pos = self.target
            self.alive = False
            self.callback()
            return

        self.interp(self, delta)

    def find_change(self, l):

        w = self.target[0] - self.initial[0]
        h = self.target[1] - self.initial[1]
        if w == 0 and h == 0:
            dx = 0
            dy = 0
        elif w == 0:
            dx = 0
            dy = l
        elif h == 0:
            dx = l
            dy = 0
        else:
            dx = math.sqrt((l ** 2 * w ** 2) / (h ** 2 + w ** 2))
            dy = dx * h / w

        return dx, dy


def linear_interpolation(animation, delta):

    completion = animation.cur_t/animation.end_t        # Find how much of the animation is complete
    animation.pos = \
        [animation.initial[0] + (animation.target[0] - animation.initial[0]) * completion,
         animation.initial[1] + (animation.target[1] - animation.initial[1]) * completion]


def constant_linear_interpolation(animation, rate, delta):
    """
    Should not be used alone as interpolation function
    :param animation:   TargetAnimation
    :param rate:        Pixels per second
    :param delta:       Milliseconds since last tick
    :return:            None
    """

    # Solve for how much to translate horizontally and vertically
    l = rate/(1000/delta)
    dx, dy = animation.find_change(l)
    animation.pos = \
        [animation.pos[0] + dx,
         animation.pos[1] + dy]


def quadratic_interpolation(animation, delta):

    # y = a(x-h)**2 + k
    # vertex = (h, k)
    # point = (x, y)
    # y - k = a(x-h)**2
    # (y - k)/(x-h)**2 = a

    x, y = animation.end_t, 1
    a = y/x**2

    x0 = animation.cur_t
    y0 = a*x0**2

    animation.pos = \
        [animation.initial[0] + (animation.target[0] - animation.initial[0]) * y0,
         animation.initial[1] + (animation.target[1] - animation.initial[1]) * y0]


def constant_quadratic_interpolation(animation, coefficient, initial_velocity, constant, delta):

    # y = ax**2 + bx + c
    l = coefficient*(animation.cur_t/1000)**2 + initial_velocity*animation.cur_t/1000 + constant
    dx, dy = animation.find_change(l)
    animation.pos = \
        [animation.pos[0] + dx,
         animation.pos[1] + dy]
