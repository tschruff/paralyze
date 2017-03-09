from paralyze.core import AABB, Cell, CellInterval, Interval, Vector, type_cast

from json import JSONDecoder, JSONEncoder


class ParalyzeJSONEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, AABB):
            return {'__type__': 'AABB', 'min_corner': obj.min, 'max_corner': obj.max}
        if isinstance(obj, Vector):
            return {'__type__': 'Vector', 'value': obj.tolist()}
        if isinstance(obj, Interval):
            return {'__type__': 'Interval', 'min': obj.min, 'max': obj.max, 'bounds': obj.bounds}
        if isinstance(obj, Cell):
            return {'__type__': 'Cell', 'value': obj.tolist()}
        if isinstance(obj, CellInterval):
            return {'__type__': 'CellInterval', 'min_cell': obj.min, 'max_cell': obj.max}
        # Let the base class default method raise the TypeError
        return JSONEncoder.default(self, obj)


class ParalyzeJSONDecoder(JSONDecoder):

    def __init__(self):
        JSONDecoder.__init__(self, object_hook=self.decode_ext)

    @staticmethod
    def decode_ext(d):
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
