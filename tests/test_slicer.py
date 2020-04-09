import os
from sliceofpy.slicer import generate_gcode

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

def test_generate_gcode_block():
    generate_gcode(os.path.join(__location__, "./block.obj"))

def test_generate_gcode_pyramid():
    generate_gcode(os.path.join(__location__, "./pyramid.obj"))

def test_generate_gcode_ring():
    generate_gcode(os.path.join(__location__, "./ring.obj"))

def test_generate_gcode_doubleblock():
    generate_gcode(os.path.join(__location__, "./2block.obj"))

def test_generate_gcode_icecream(): # mmm
    generate_gcode(os.path.join(__location__, "./icecream.obj"))

def test_generate_gcode_torus():
    generate_gcode(os.path.join(__location__, "./torus.obj"))
