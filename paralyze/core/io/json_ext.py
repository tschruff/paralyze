from paralyze.core import AABB, Cell, CellInterval, Interval, Vector, type_cast

from json import JSONDecoder, JSONEncoder


class ParalyzeJSONEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, AABB):
            return {
                "__type__": "AABB",
                "min_corner": obj.min,
                "max_corner": obj.max,
                "dtype": obj.dtype.name
            }
        if isinstance(obj, Vector):
            return {
                "__type__": "Vector",
                "value": obj.tolist(),
                "dtype": obj.dtype.name
            }
        if isinstance(obj, Interval):
            return {
                "__type__": "Interval",
                "min": obj.min,
                "max": obj.max,
                "bounds": obj.bounds
            }
        if isinstance(obj, Cell):
            return {
                "__type__": "Cell",
                "value": obj.tolist()
            }
        if isinstance(obj, CellInterval):
            return {
                "__type__": "CellInterval",
                "min_cell": obj.min,
                "max_cell": obj.max
            }
        # Let the base class default method raise the TypeError
        return JSONEncoder.default(self, obj)


class ParalyzeJSONDecoder(JSONDecoder):
    """The ParalyzeJSONDecoder is an extension of the standard JSONDecoder that
    can also decode custom paralyze types given by their string representation,
    i.e. what str(object) returns, or by a more complex dict-style
    representation that offers more flexibility during object construction.

    Examples
    --------

    Paralyze types can be specified either by their string representation or by
    their json specific dict-style representation. Obviously, the dict-style
    representation is more complex, but it also offers more flexibility during
    object construction as all items specified in the dict body will be passed
    to the object constructor.

    The ``AABB`` class for example has an optional ``dtype`` argument in the
    constructor, that can be used to override the default dtype of an AABB,
    which is 'float64'.

    >>> import json
    >>> obj = json.load({"aabb": "[<0,0,0>,<2,2,4>]"}, cls=ParalyzeJSONDecoder)
    >>> str(obj)
    '[<0.0,0.0,0.0>,<2.0,2.0,4.0>]'
    >>> obj
    AABB(Vector((0.0,0.0,0.0)), Vector((2.0,2.0,4.0)))
    >>> obj = json.load({"aabb": {
            "__type__": "AABB",
            "min_corner": "<0,0,0>",
            "max_corner": {
                "__type__": "Vector",
                "value": [2,2,4]
            },
            "dtype": "int64"
        }}, cls=ParalyzeJSONDecoder)
    >>> str(obj)
    '[<0,0,0>,<2,2,4>]'
    >>> obj
    AABB(Vector(0,0,0), Vector(2,2,4))

    """
    def __init__(self):
        JSONDecoder.__init__(self)

    def decode(self, s):
        """Decodes the given str ``s``.

        Will raise a JSONDecodeError if ``s`` is not a valid JSON document.
        """
        obj = JSONDecoder.decode(self, s)
        return self.decode_paralyze_types(obj)

    def decode_paralyze_types(self, obj):
        """Recursively search trough ``obj`` and convert strings to
        paralyze types that have been registered in the ``type_cast`` method.

        """
        if isinstance(obj, str):
            obj = type_cast(obj)

        if isinstance(obj, dict):
            for index in obj.keys():
                obj[index] = self.decode_paralyze_types(obj[index])
            obj = ParalyzeJSONDecoder.decode_object(obj)

        if isinstance(obj, list):
            for index in range(len(obj)):
                obj[index] = self.decode_paralyze_types(obj[index])

        return obj

    @staticmethod
    def decode_object(d):
        """Decodes the dict type ``d``.

        As a convention, custom types have a ``__type__`` item that specifies
        the type ``d`` should be converted to.
        """

        if '__type__' not in d:
            return d

        custom_type = d.pop('__type__')
        if custom_type == 'AABB':
            return AABB(**d)
        if custom_type == 'Vector':
            return Vector(**d)
        if custom_type == 'Interval':
            return Interval(**d)
        if custom_type == 'Cell':
            return Cell(**d)
        if custom_type == 'CellInterval':
            return CellInterval(**d)
        else:
            # Oops... better put this back together.
            d['__type__'] = custom_type
            return d
