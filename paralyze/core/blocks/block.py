
class Block(object):
    """ The Block class provides generic data storage in form of
    a simple Python dict.
    """

    def __init__(self, block_id):
        self._id = block_id
        self._data = {}

    def __getitem__(self, identifier):
        return self._data[identifier]

    def get(self, identifier, default=None):
        return self._data.get(identifier, default)

    @property
    def id(self):
        return self._id
