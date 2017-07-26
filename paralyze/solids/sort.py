import numpy as np


def get_bucket_indices(array, buckets, func=None):
    """Generates an array with indices of ``array`` items in ``bucket`` items.

    Parameters
    ----------
    array: list or numpy.ndarray
        The list of objects that will be sorted
    buckets: list
        The list of bucket-like objects.

        Bucket object must implement the __contains__ member as array items
        are tested for membership in buckets according to

        >>> indexes = []
        >>> for item in array:
        >>>     for bucket in buckets:
        >>>         if item in bucket: # calls bucket.__contains__(item)
        >>>             indexes[array.index(item)] = buckets.index(bucket)

    func: function
        The optional function object that maps array items to the required class
        attribute queried by the bucket, i.e.

        >>> array = map(func, array)

    Returns
    -------
    indices:
        A numpy.ndarray with the same shape like ``array`` containing the bucket
        indices.
        If an array item is in none of the buckets the index will be -1.
    """

    # if items are in none of the classes they will have
    # an index of -1
    indices = np.full_like(array, -1, dtype=np.int64)

    if func:
        array = map(func, array)

    for i, item in enumerate(array):
        for j in range(len(buckets)):
            if item in buckets[j]:
                indices[i] = j

    return indices
