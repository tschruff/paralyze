import numpy as np


NUMPY_TO_VTK_DTYPE_STR = {'int8': 'Int8',
                          'uint8': 'UInt8',
                          'int16': 'Int16',
                          'uint16': 'UInt16',
                          'int32': 'Int32',
                          'uint32': 'UInt32',
                          'int64': 'Int64',
                          'uint64': 'UInt64',
                          'float32': 'Float32',
                          'float64': 'Float64'}


def vtk_dtype_str(np_dtype):
    """ Maps numpy data types (dtypes) to a string representation of the respective utils data type.

    utils types: Int8, UInt8, Int16, UInt16, Int32, UInt32, Int64, UInt64, Float32, Float64
    :rtype: str
    """
    return NUMPY_TO_VTK_DTYPE_STR[np.dtype(np_dtype).name]