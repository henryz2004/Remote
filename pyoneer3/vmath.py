# Vector math

import math


def add(vector1, vector2):

    assert len(vector1) == len(vector2), "Cannot sum two vectors of unequal length"
    return [vector1[i] + vector2[i] for i in range(len(vector1))]


def sub(vector1, vector2):

    assert len(vector1) == len(vector2), "Cannot subtract two vectors of unequal length"
    return [vector1[i] - vector2[i] for i in range(len(vector1))]


def mult(vector1, vector2):

    assert len(vector1) == len(vector2), "Cannot multiply two vectors of unequal length"
    return [vector1[i] * vector2[i] for i in range(len(vector1))]


def dot(vector1, vector2):

    assert len(vector1) == len(vector2), "Cannot take the dot product two vectors of unequal length"
    return sum(vector1[i] * vector2[i] for i in range(len(vector1)))


def magnitude(vector):

    squares = [x**2 for x in vector]
    return math.sqrt(sum(squares))


def normalize(vector):

    m = magnitude(vector)
    return [x/m for x in vector]


def angle_between(heading, point, precomp_dist=None):

    dist = precomp_dist if precomp_dist else math.sqrt(point[0]**2 + point[1]**2)

    projection = dot(point, heading)

    if dist > 0:
        angle = math.degrees(math.acos(max(-1, min(1, projection/dist))))
    else:
        angle = 0

    return dist, projection, angle
