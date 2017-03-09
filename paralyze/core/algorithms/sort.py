import numpy as np


def get_bucket_indexes(array, buckets, func=None):
    """

    Parameters
    ----------
    array: list or numpy.ndarray

    buckets: list
        A list of generic bucket-like objects which must implement the __contains__ member. Array items
        are tested for membership in buckets according to

        >>> indexes = []
        >>> for item in array:
        >>>     for bucket in buckets:
        >>>         if item in bucket:
        >>>             indexes[array.index(item)] = buckets.index(bucket)

    func: function
        A function object that maps array items to the required class attribute queried by the bucket, i.e.

        >>> array = map(func, array)

    Returns
    -------
    indexes:
        A numpy.ndarray with the same shape like array containing the bucket indexes. If an item is in none
        of the buckets the index is -1.
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
