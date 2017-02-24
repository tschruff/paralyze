from paralyze.core.io import vtk as vtk_utils
from paralyze.core.field import io as field_io
from paralyze.core.io import xml as xml_utils

from xml.etree import ElementTree

import sys
import os

import numpy as np


def save_field_as_vtk_image_file(block, blocks, field_id, abs_folder_path, binary=False):
    assert blocks.has_data(field_id)

    if not os.path.exists(abs_folder_path):
        os.mkdir(abs_folder_path)

    if binary:
        print('WARNING: Binary io output is currently not supported. Switching to ascii mode!')
        binary = False

    abs_file_path = os.path.join(abs_folder_path, field_id)

    if blocks.np() > 1:

        abs_tile_path = abs_file_path + '_{:d}.vti'

        field = block[field_id]
        bci = blocks.globalCellInterval(block.id)

        # write header file only on root block
        if block == blocks.root_block():

            v_str = '{v[0]:f} {v[1]:f} {v[2]:f}'

            attrib = {'type': 'PImageData',
                      'version': '0.1',
                      'byte_order': 'LittleEndian' if sys.byteorder == 'little' else 'BigEndian'}
            root = ElementTree.Element('VTKFile', attrib=attrib)

            gci = blocks.globalCellInterval()

            attrib = {'WholeExtent': '0 %d 0 %d 0 %d' % (gci.xMax+1, gci.yMax+1, gci.zMax+1),
                      'GhostLevel': '%d' % field.ghost_level(),
                      'Origin': v_str.format(v=blocks.origin()),
                      'Spacing': v_str.format(v=blocks.dx())}
            pimage = ElementTree.SubElement(root, 'PImageData', attrib=attrib)

            cell_data = ElementTree.SubElement(pimage, 'PCellData')

            attrib = {'type': vtk_utils.vtk_dtype_str(block[field_id].dtype),
                      'Name': str(field_id),
                      'NumberOfComponents': '1',
                      'format': 'binary' if binary else 'ascii'}
            ElementTree.SubElement(cell_data, 'DataArray', attrib=attrib)

            header_path = abs_file_path + '.pvti'
            rel_tile_path = os.path.basename(abs_tile_path)

            for b in blocks:
                ci = blocks.globalCellInterval(b.id)
                extent_str = '%d %d %d %d %d %d' % (ci.xMin, ci.xMax+1, ci.yMin, ci.yMax+1, ci.zMin, ci.zMax+1)
                attrib = {'Extent': extent_str, 'Source': rel_tile_path.format(b.id)}
                ElementTree.SubElement(pimage, 'Piece', attrib=attrib)

            with open(header_path, 'wb+') as header:
                header.write(xml_utils.prettiefy(root))

        field_io.save_as_vtk_image_file(field, abs_tile_path.format(block.id), binary=binary, extent=bci,
                                        origin=blocks.origin(), spacing=blocks.dx())

    else:
        field = blocks.root_block()[field_id]
        field_io.save_as_vtk_image_file(field, abs_file_path + '.vti', binary=binary)


def save_field_as_vxl_file(block, blocks, field_id, abs_folder_path):
    assert blocks.has_data(field_id)

    if not os.path.exists(abs_folder_path):
        os.mkdir(abs_folder_path)

    abs_file_path = os.path.join(abs_folder_path, field_id)

    if blocks.np() > 1:

        abs_tile_path = abs_file_path + '_{:d}.vxl'
        rel_tile_path = os.path.basename(abs_tile_path)

        if block == blocks.root_block():

            v_str = '{v[0]:f} {v[1]:f} {v[2]:f}'
            c_str = '{c[0]:d} {c[1]:d} {c[2]:d}'

            attrib = {'byteOrder': sys.byteorder,
                      'offset': v_str.format(v=blocks.origin()),
                      'size': c_str.format(c=blocks.globalCellInterval().size),
                      'spacing': v_str.format(v=blocks.dx()),
                      'type': np.dtype(block[field_id].dtype).name,
                      'version': '0.1'}
            root = ElementTree.Element('VoxelVolume', attrib=attrib)

            for b in blocks:
                attrib = {'file': rel_tile_path.format(b.id),
                          'origin': c_str.format(c=blocks.globalCellInterval(b.id).min),
                          'size': c_str.format(c=b.cellInterval().size)}
                ElementTree.SubElement(root, 'File', attrib=attrib)

            with open(abs_file_path+'.pvxl', 'wb+') as header:
                header.write(xml_utils.prettiefy(root))

        field = block[field_id]
        field_io.save_as_vxl_file(field, abs_tile_path.format(block.id))

    else:
        field = block[field_id]
        field_io.save_as_vxl_file(field, abs_file_path+'.vxl')


def save_field(block, file_format, **kwargs):
    if file_format == 'vtk':
        return save_field_as_vtk_image_file(block, **kwargs)
    if file_format == 'vxl':
        return save_field_as_vxl_file(block, **kwargs)
    raise ValueError('Unsupported file format %s! Supported format are: vtk, vxl' % file_format)
