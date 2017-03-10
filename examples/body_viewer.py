# -----------------------------------------------------------------------------
# Copyright (c) 2009-2016 Nicolas P. Rougier. All rights reserved.
# Distributed under the (new) BSD License.
# -----------------------------------------------------------------------------
import numpy as np
from glumpy import app, gloo, gl
from glumpy.transforms import Position, Trackball

from paralyze.gui.programs import packing

# USER INPUT
# -------------------------------------------------------------------------------------------------

SPHERES = np.load('/Users/tobs/sciebo/Diss/Data/Packings/periodic-256/beds/ln-8-1.2.npy')
SCALE = 0.001


# GLUMPY APP
# -------------------------------------------------------------------------------------------------

window = app.Window(width=800, height=800, color=(1,1,1,1))

#SPHERES = data.get("protein.npy")
SPHERES['position'] *= SCALE
SPHERES['radius'] *= SCALE

n = len(SPHERES)
sphere_data = np.zeros(n, [('position', np.float32, 3),
                           ('radius', np.float32, 1),
                           ('color', np.float32, 3)])

sphere_data['position'] = SPHERES['position']
sphere_data['radius'] = SPHERES['radius']
sphere_data['color'] = np.random.random_sample((len(SPHERES), 3))

pack = packing()
pack['light_position'] = .128, .128, .5
pack["transform"] = Trackball(Position())
pack.bind(sphere_data.view(gloo.VertexBuffer))
pack['color'] *= .25
pack['color'] += .75

@window.event
def on_draw(dt):
    window.clear()
    pack.draw(gl.GL_POINTS)

@window.event
def on_init():
    gl.glEnable(gl.GL_DEPTH_TEST)

@window.event
def on_resize(width, height):


window.attach(pack["transform"])
app.run()
