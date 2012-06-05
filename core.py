"""
An attempt to make a pure python, pythonic, and very abstracted geometry
library that spans from vectors to NURBS, and includes lots of useful
algorithms. I intend to value abstraction and portability over
performance where necessary. Towards that end I don't plan to use numpy or
other awesome and amazing modules that performance-oriented developers might
use.

Here's some examples:

    >>> from core import Vector3d, Point3d
    >>> # test add
    ... v = Vector3d(0.0, 1.0, 2.0)
    >>> v1 = v + 1
    >>> v1
    Vector3d(0.0, 1.4472135955, 2.894427191)
    >>> v1.length - v.length
    0.99999999999999956
    >>>
    >>> v1 = Vector3d(0.0, 2.0, 1.0)
    >>> v1.length
    2.2360679774997898
    >>> v2 = v1 + 4
    >>> v2.length
    6.2360679774997889
    >>> v3 = v1 + -7
    >>> v1 + v3
    Vector3d(0.0, -2.260990337, -1.1304951685)
    >>> v1 - v2
    Vector3d(0.0, -3.577708764, -1.788854382)
    >>> v1 * v3
    -10.652475842498529
    >>> v3[0]
    0.0
    >>> v1['x']
    0.0
    >>> v1[:2]
    (0.0, 2.0)
    >>> v3[-1]
    -2.1304951684997055
    >>> v2
    Vector3d(0.0, 5.577708764, 2.788854382)
    >>> v3
    Vector3d(0.0, -4.260990337, -2.1304951685)
    >>> v4 = v3.cross(v2)
    >>> # v3 and v2 point in the same direction
    ... v4
    Vector3d(0.0, -0.0, 0.0)
    >>> # this is a vector of length 0
    ... # so it's length can't be adjusted
    ... v4.length = 1.0
    Traceback (most recent call last):
      File "<stdin>", line 3, in <module>
      File "core.py", line 119, in length
        v = self.normalized() * number
      File "core.py", line 147, in normalized
        raise ZeroDivisionError
    ZeroDivisionError
    >>> p1 = Point3d(*v3)
    >>> p2 = Point3d(3.45, 0.01, -2004.665)
    >>> p1.distanceTo(p2)
    2002.5420312440888
    >>> p2.vectorTo(p1)
    Vector3d(-3.45, -4.270990337, 2002.53450483)
    >>> p1 - p2
    Vector3d(-3.45, -4.270990337, 2002.53450483)

First development target: intersections!!

References

[Geometry]
    http://plib.sourceforge.net/sg/index.html

[API]
    Check out the python data model emulation stuff here:
    http://docs.python.org/reference/datamodel.html

classes:

    float
    Vec2
    Vec3
    Vec4
    Mat4
    Coord
    Line3
    LineSegment3
    Quat
    Sphere
    Box
    Frustum
"""

import math
import numbers

# For float comparison:
def isRoughlyZero(number):
    return round(number, 7) == 0
# though there are better ways to do this.
# It would be nice if this could handle all sorts of numbers
# see:
# http://floating-point-gui.de/errors/comparison/
# http://stackoverflow.com/questions/9528421/value-for-epsilon-in-python
# http://stackoverflow.com/questions/4028889/floating-point-equality-in-python
# http://stackoverflow.com/questions/3049101/floating-point-equality-in-python-and-in-general




class Vector3d(object):
    """A 3d vector object

    Perhaps these can be hashable if calling __hash__ returns a hash of a tuple
    of a vector's coordinates. That would be close to what I'm looking for:
    basically an object that for all intents and purposes can be treated like a
    tuple of floats, but which has many additional methods and hooks for
    functionality.
    """
    def __init__(self, x=0.0, y=0.0, z=0.0):
        # coords is the essence of the data structure. It's immutable and
        # iterable, allowing us to iterate over the values as well as providing
        # a little bit of protection from accidentally changing the values see
        # `classTest` in tests to understand more of the reasoning here.
        self.coords = (x, y, z)
        self.x = x
        self.y = y
        self.z = z

    @property
    def length(self):
        """get the vector length / amplitude
            >>> v = Vector3d(0.0, 2.0, 1.0)
            >>> v.length
            2.2360679774997898
        """
        # only calculate the length if asked to.
        return math.sqrt(sum(n**2 for n in self))

    def toLength(self, number):
        """Get a parallel vector with the input amplitude."""
        # depends on normalized() and __mult__
        # create a vector as long as the number
        return self.normalized() * number

    def toX(self, number):
        """For getting a copy of the same vector but with a new x value"""
        return Vector3d(number, self[1], self[2])

    def toY(self, number):
        """For getting a copy of the same vector but with a new y value"""
        return Vector3d(self[0], number, self[2])

    def toZ(self, number):
        """For getting a copy of the same vector but with a new z value"""
        return Vector3d(self[0], self[1], number)

    def normalized(self):
        """just returns the normalized version of self without editing self in
        place.
            >>> v.normalized()
            Vector3d(0.0, 0.894427191, 0.4472135955)
            >>> v
            Vector3d(0.0, 3.2995419076, 1.6497709538)
        """
        # think how important float accuracy is here!
        if isRoughlyZero(sum(n**2 for n in self)):
            raise ZeroDivisionError
        else:
            return self * (1 / self.length)

    def asList(self):
        """return vector as a list"""
        return [c for c in self]

    def asDict(self):
        """return dictionary representation of the vector"""
        return dict( zip( list('xyz'), self.coords ) )

    def __getitem__(self, key):
        """Treats the vector as a tuple or dict for indexes and slicing.
            >>> v
            Vector3d(2.0, 1.0, 2.2)
            >>> v[0]
            2.0
            >>> v[-1]
            2.2000000000000002
            >>> v[:2]
            (2.0, 1.0)
            >>> v['y']
            1.0
        """
        # dictionary
        if key in ('x','y','z'):
            return self.asDict()[key]
        # slicing and index calls
        else:
            return self.coords.__getitem__(key)

    def __iter__(self):
        """For iterating, the vectors coordinates are represented as a tuple."""
        return self.coords.__iter__()

    ## Time for some math

    def dot(self, other):
        """Gets the dot product of this vector and another.
            >>> v
            Vector3d(5, 1.20747670785, 60.0)
            >>> v1
            Vector3d(0.0, 2.0, 1.0)
            >>> v1.dot(v)
            62.41495341569977
        """
        return sum((p[0] * p[1]) for p in zip(self, other))

    def cross(self, other):
        """Gets the cross product between two vectors
            >>> v
            Vector3d(5, 1.20747670785, 60.0)
            >>> v1
            Vector3d(0.0, 2.0, 1.0)
            >>> v1.cross(v)
            Vector3d(118.792523292, 5.0, -10.0)
        """
        # I hope I did this right
        x = (self[1] * other[2]) - (self[2] * other[1])
        y = (self[2] * other[0]) - (self[0] * other[2])
        z = (self[0] * other[1]) - (self[1] * other[0])
        return Vector3d(x, y, z)

    def __add__(self, other):
        """we want to add single numbers as a way of changing the length of the
        vector, while it would be nice to be able to do vector addition with
        other vectors.
            >>> from core import Vector3d
            >>> # test add
            ... v = Vector3d(0.0, 1.0, 2.0)
            >>> v1 = v + 1
            >>> v1
            Vector3d(0.0, 1.4472135955, 2.894427191)
            >>> v1.length - v.length
            0.99999999999999956
            >>> v1 + v
            Vector3d(0.0, 2.4472135955, 4.894427191)
        """
        if isinstance(other, numbers.Number):
            # then add to the length of the vector
            # multiply the number by the normalized self, and then
            # add the multiplied vector to self
            return self.normalized() * other + self

        elif isinstance(other, Vector3d):
            # add all the coordinates together
            # there are probably more efficient ways to do this
            return Vector3d(*(sum(p) for p in zip(self, other)))
        else:
            raise NotImplementedError

    def __sub__(self, other):
        """Subtract a vector or number
            >>> v2 = Vector3d(-4.0, 1.2, 3.5)
            >>> v1 = Vector3d(2.0, 1.1, 0.0)
            >>> v2 - v1
            Vector3d(-6.0, 0.1, 3.5)
        """
        return self.__add__(other * -1)

    def __mul__(self, other):
        """if with a number, then scalar multiplication of the vector,
            if with a Vector, then dot product, I guess for now, because
            the asterisk looks more like a dot than an X.
            >>> v2 = Vector3d(-4.0, 1.2, 3.5)
            >>> v1 = Vector3d(2.0, 1.1, 0.0)
            >>> v2 * 1.25
            Vector3d(-5.0, 1.5, 4.375)
            >>> v2 * v1 #dot product
            -6.6799999999999997
        """
        if isinstance(other, numbers.Number):
            # scalar multiplication for numbers
            return Vector3d( *((n * other) for n in self))

        elif isinstance(other, Vector3d):
            # dot product for other vectors
            return self.dot(other)

    def __hash__(self):
        """This method provides a hashing value that is the same hashing value
        returned by the vector's coordinate tuple. This allows for testing for
        equality between vectors and tuples, as well as between vectors.

        Two vector instances (a and b) with the same coordinates would return True
        when compared for equality: a == b, a behavior that I would love to
        have, and which would seem very intuitive.

        They would also return true when compared for equality with a tuple
        equivalent to their coordinates. My hope is that this will greatly aid
        in filtering duplicate points where necessary - something I presume
        many geometry algorithms will need to look out for.

        I'm not sure it is a bad idea, but I intend this class to basically be a
        tuple of floats wrapped with additional functionality.
        """
        return self.coords.__hash__()

    def __eq__(self, other):
        """I am allowing these to compared to tuples, and to say that yes, they
        are equal. the idea here is that a Vector3d _is_ a tuple of floats, but
        with some extra methods.
        """
        return self.coords.__eq__(other)

    def __repr__(self):
        return 'Vector3d(%s, %s, %s)' % self.coords



class Point3d(Vector3d):
    """Works like a Vector3d. I might add some point specific methods.
    """
    def __init__(self, *args, **kwargs):
        super(Point3d, self).__init__(*args, **kwargs)

    def __repr__(self):
        return 'Point3d(%s, %s, %s)' % self.coords

    def distanceTo(self, other):
        """Find the distance between this point and another.
            >>> p1 = Point3d(-2.2, -0.5, 0.0034)
            >>> p2 = Point3d(3.45, 0.01, -2004.665)
            >>> p1.distanceTo(p2)
            2004.676426897508
        """
        return (other - self).length

    def vectorTo(self, other):
        """Find the vector to another point.
            >>> p1 = Point3d(-2.2, -0.5, 0.0034)
            >>> p2 = Point3d(3.45, 0.01, -2004.665)
            >>> p1.distanceTo(p2)
            2004.676426897508
            >>> p1.distanceTo(p2)
            2004.676426897508
            >>> p2.vectorTo(p1)
            Vector3d(-5.65, -0.51, 2004.6684)
            >>> p1 - p2
            Vector3d(-5.65, -0.51, 2004.6684)
        """
        return other - self

class PointSet(object):
    """This class is meant to hold a set of *unique* points.
    It enforces this using python's built in `set` type. But points may still
    be within some tolerance of each other.

    In general, this class should be preferred to PointList because many
    geometric algorithms will not assume duplicate points and could produce
    invalid results (such as 0 length edges, collapsed faces, etc) if run on
    points wiht duplicates.

    Basically this provides hooks to using a python 'set' containing tuples of
    the point coordinates.

    This should actually be an ordered set, not just a set. I'm not sure how
    much it matters though if the points can be looked up by their coordinates
    so easily.

    Perhaps the core set can be defined by a list and a dictionary. __iter__
    would call on the list, while one would be able to look up the hashed
    coordinate tuples as dictionary keys to get their index.

    I like this list/dictionary combo, because even though what I would truly
    want is an ordered set, OrderedSets as a class aren't introduced until
    Python 3.0 or maybe 2.7 (not sure). Ideally this library would be
    compatible with Python versions at least as early as 2.6 and hopefully 2.4
    as well.
    """
    def __init__(self, points=None):
        # can be initialized with an empty set.
        # this set needs to contain tuples of point coords
        # and then extend and manage the use of that set
        # intialize the dictionary and list first
        # becasue any input points will be placed there to start
        self.pointList = []
        self.pointDict = {}
        if points:
            # parse the points to create the pointList and pointDict
            # we want to be able to accept points as tuples, as lists, as
            # Point3d objects, and as Vector3d objects. I guess if I add them
            # as iterables, that would be the simplest.
            self.points = points

    @property
    def points(self):
        # go through the list and get each tuple as Point3d object
        return [Point3d(*c) for c in self.pointList]

    @points.setter
    def points(self, values):
        """This method parses incoming values being used to define points and
        filters them if necessary.
        """
        for i, val in enumerate(values):
            # Vector3ds will need to be unwrapped
            if isinstance(val, Vector3d):
                point = Point3d(*val)
            else:
                # just assume it is some sort of iterable
                point = Point3d(*(val[v] for v in range(3)))
            # here will build the dictionary, using indices as the only
            # value any given tuple refers to
            self.pointDict[point] = i
            # and here we also build up a list, for lookups by index
            self.pointList.append(point)

    def __getitem__(self, key):
        """This builds a dictionary / list-like api on the PointSet.
        The `key` might be an integer or a coordinate tuple, or a point.

        There is a design question here: should it initialize the object as a
        Point3d?

        And if Point3ds are already hashable, why am I using simple tuples when
        I could use Point3ds?
        """
        # if it's a tuple or point3d and return the index
        if isinstance(key, tuple) or isinstance(key, Vector3d):
            return self.pointDict[key]
        else:
            # assume it is an index or slice
            return self.pointList[key]




WorldX = Vector3d(1.0, 0.0, 0.0)
WorldY = Vector3d(0.0, 1.0, 0.0)
WorldZ = Vector3d(0.0, 0.0, 1.0)
