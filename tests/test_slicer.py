import os
from sliceofpy.slicer import generate_gcode

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

def test_generate_gcode():
    generate_gcode(os.path.join(__location__, "./block.obj"))
