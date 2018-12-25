import math


class Interpolator:

    def __init__(self, coefficients, constant=0):

        self.coefficients = coefficients
        self.constant = constant

    def interpolate(self, animation, delta):

        raise NotImplementedError()

    def compute_duration(self, start, end):

        raise NotImplementedError()

    def compute_coefficients(self, duration):

        raise NotImplementedError()

    @staticmethod
    def find_change(start, to, dist):

        w = to[0] - start[0]
        h = to[1] - start[1]
        if w == 0 and h == 0:
            dx = 0
            dy = 0
        elif w == 0:
            dx = 0
            dy = dist
        elif h == 0:
            dx = dist
            dy = 0
        else:
            dx = math.sqrt((dist ** 2 * w ** 2) / (h ** 2 + w ** 2))
            dy = dx * h / w

        return dx, dy


class LinearInterpolator(Interpolator):

    def __init__(self, rate: int, constant=0):
        super(LinearInterpolator, self).__init__(rate, constant)

    def interpolate(self, animation, delta):

        dist = self.coefficients * (delta/1000) + self.constant

        # Special cases: if the movement is only horizontally or vertically
        # No movement
        if animation.end_pos == animation.start_pos:
            return

        # Vertical movement only (x stays constant)
        elif animation.end_pos[0] - animation.start_pos[0] == 0:
            animation.pos[1] += dist

        # Horizontal movement only
        elif animation.end_pos[1] - animation.start_pos[1] == 0:
            animation.pos[0] += dist

        # Both horizontal and vertical movement
        else:
            dx, dy = Interpolator.find_change(animation.start_pos, animation.end_pos, dist)
            animation.pos[0] += dx
            animation.pos[1] += dy

    def compute_duration(self, start, end):

        # distance = coefficient * time + constant
        # distance - constant = coefficient * time
        # (distance - constant)/coefficient = time
        time = (math.sqrt((end[0]-start[0])**2 + (end[1]-start[1])**2) - self.constant)/self.coefficients
        return time * 1000

    def compute_coefficients(self, duration):
        pass
