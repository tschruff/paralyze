import os

current = os.path.dirname(__file__)

SHADER_FOLDER = os.path.join(current, 'shaders')


def get_shader(name):
    return os.path.join(SHADER_FOLDER, name)