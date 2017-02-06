import numpy as np


def get_bucket_indexes(array, buckets, func=None):
    """

    :param array:
    :param buckets: A list of generic bucket-like objects which must implement the __contains__ member
    :param func: A function object that maps the data item to the required class attribute
    :return: A numpy array with the same shape as data containing the class indexes
    """
    # if items are in none of the classes they will have
    # an index of -1
    indexes = np.full_like(array, -1, dtype=int)

    if func:
        array = map(func, array)

    for i, item in enumerate(array):
        for j in range(len(buckets)):
            if item in buckets[j]:
                indexes[i] = j

    return indexes
