from glumpy import gloo

from gui import get_shader


def packing():
    vertex = get_shader('packing.vert')
    fragment = get_shader('packing.frag')
    return gloo.Program(vertex, fragment)
