from .cell import CellInterval
from paralyze.core.io import vtk as vtk_utils
from paralyze.core.io import xml as xml_utils

from xml.etree import ElementTree

import numpy as np

import sys
import base64


def save_as_vtk_image_file(field, filename, binary=False, extent=None, origin=(0, 0, 0), spacing=(1, 1, 1)):

    if extent is None:
        extent = field.cellInterval()
    else:
        assert isinstance(extent, CellInterval)
        assert extent.size == field.cellInterval().size

    extent_str = '%d %d %d %d %d %d' % (extent.xMin, extent.xMax+1, extent.yMin, extent.yMax+1, extent.zMin, extent.zMax+1)
    origin_str = '%f %f %f' % (origin[0], origin[1], origin[2])
    spacing_str = '%f %f %f' % (spacing[0], spacing[1], spacing[2])
    endianness_str = 'LittleEndian' if sys.byteorder == 'little' else 'BigEndian'
    format_str = 'binary' if binary else 'ascii'

    # VTKFile element
    attrib = {'type': 'ImageData',
              'version': '0.1',
              'byte_order': endianness_str}
    root = ElementTree.Element('VTKFile', attrib=attrib)

    # ImageData element
    attrib = {'WholeExtent': extent_str,
              'Origin': origin_str,
              'Spacing': spacing_str}
    img = ElementTree.SubElement(root, 'ImageData', attrib=attrib)

    # Piece element
    attrib = {'Extent': extent_str}
    piece = ElementTree.SubElement(img, 'Piece', attrib=attrib)

    # CellData element
    cell_data = ElementTree.SubElement(piece, 'CellData')

    # DataArray element
    attrib = {'type': vtk_utils.vtk_dtype_str(field.dtype),
              'Name': str(field.id()),
              'NumberOfComponents': '1',
              'format': format_str}
    data_array = ElementTree.SubElement(cell_data, 'DataArray', attrib=attrib)

    i = 0
    vtk_array = np.zeros((field.size().prod(), ), dtype=field.dtype)
    for z in range(field.size()[2]):
        for y in range(field.size()[1]):
            for x in range(field.size()[0]):
                vtk_array[i] = field.data[x, y, z]
                i += 1

    if binary:
        data_array.text = base64.b64encode(vtk_array).decode('utf-8')
    else:
        old_opt = np.get_printoptions()
        np.set_printoptions(threshold=np.inf)
        data_array.text = np.array2string(vtk_array, max_line_width=np.inf)[1:-1]
        np.set_printoptions(**old_opt)

    with open(filename, 'wb+') as xml:
        xml.write(xml_utils.prettiefy(root))


def save_as_numpy_array(field, filename, **kwargs):
    pass


def save_as_vxl_file(field, filename):
    size = field.size()
    with open(filename, 'wb') as vxl:
        vxl.write('{s[0]:d} {s[1]:d} {s[2]:d}\n'.format(s=size).encode())
        for z in range(size[2]):
            for y in range(size[1]):
                for x in range(size[0]):
                    vxl.write(field.data[x, y, z])
