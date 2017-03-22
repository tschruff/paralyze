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
    """Maps numpy data types (dtypes) to a string representation of the
    respective vtk data type.

    Performs the following data type mapping:

    +----------+----------+
    | np.dtype | vtk type |
    +==========+==========+
    | int8     | Int8     |
    +----------+----------+
    | uint8    | UInt8    |
    +----------+----------+
    | int16    | Int16    |
    +----------+----------+
    | uint16   | UInt16   |
    +----------+----------+
    | int32    | Int32    |
    +----------+----------+
    | uint32   | UInt32   |
    +----------+----------+
    | int64    | Int64    |
    +----------+----------+
    | uint64   | UInt64   |
    +----------+----------+
    | float32  | Float32  |
    +----------+----------+
    | float64  | Float64  |
    +----------+----------+

    Returns
    -------
    vtk_type_str: str
        The string representation of the corresponding vtk data type.
    """
    return NUMPY_TO_VTK_DTYPE_STR[np.dtype(np_dtype).name]
