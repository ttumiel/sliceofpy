import numpy as np
from mecode import G
import logging, os
import matplotlib.pyplot as plt

from .math_utils import get_intersection, distance_between
from .infill import solid, criss_cross, gap_fill, Axis

logger = logging.getLogger(__name__)
logging.basicConfig()
logger.setLevel(logging.DEBUG)

material_nozzle_temps = {
    "PLA": 215,
    "ABS": 235,
}

material_bed_temps = {
    "PLA": 60,
    "ABS": 100,
}

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


class Face():
    def __init__(self, vertices, face_num):
        self.v = vertices
        self.face_num = face_num
        self.contour_points = []

    def add_contour_pts(self, pt):
        self.contour_points.append(pt)

    def __str__(self):
        return f"Face {self.face_num}: {str(self.v)} " + ("" if len(self.contour_points) == 0 else str(self.contour_points))

    def __repr__(self):
        return str(self)

class FaceQueue():
    def __init__(self):
        self.q = []
        self.store = []

    def get_matches(self, face):
        return sum(f in face.v for f in self.q[-1].v)

    def insert(self, face):
        if len(self.q) == 0:
            self.q.append(face)
        else:
            matches = self.get_matches(face)
            if matches >= 2:
                # actually doesn't matter which side to put on, as
                # long as its consistent
                self.q.append(face)
            else:
                self.store.append(face)

            if len(self.store) > 0:
                added_from_store = False
                while True:
                    for f in self.store:
                        if self.get_matches(f) >= 2:
                            self.q.append(f)
                            added_from_store = True
                            break

                    if added_from_store:
                        self.store.remove(f)
                        added_from_store = False
                    else:
                        break

    def __len__(self):
        return len(self.q)

    def __getitem__(self, idx):
        return self.q[idx]

    def __str__(self):
        return str(self.q)

    def __repr__(self):
        return str(self)

def parse_vertex(vertex_str):
    "Generates a numpy vector vertex from the unprocessed string"
    return np.array([float(coord) for coord in vertex_str.split()[1:]])

def parse_face(face_string):
    "Parses a face string into a numpy vector. Potentially >3 dims"
    face = np.array([int(coord)-1 for coord in face_string.split()[1:]])
    return face

def parse_obj(filename):
    vertices = []
    faces = []
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith("v"):
                vertices.append(parse_vertex(line))
            elif line.startswith("f"):
                faces.append(parse_face(line))

    vertices = np.stack(vertices)

    return faces, vertices

def is_lower_point(vert_zs, zi):
    return sum(vert_zs == zi) == 1 and sum(vert_zs<zi) == 0

def center_vertices(vertices):
    "Corrects any offsets in the vertices for better printing."
    x_min,y_min,z_min = vertices.min(axis=0)
    x_max,y_max,z_max = vertices.max(axis=0)
    if z_min != 0:
        logger.warning("Base height is not zero. Compensating.")
        vertices[:,2] -= z_min
        z_max -= z_min

    # add tolerances?
    x_offset = (x_max + x_min)/2
    if x_offset != 0:
        logger.warning("X-axis is not centered. Centering.")
        vertices[:,0] -= x_offset

    y_offset = (y_max + y_min)/2
    if y_offset != 0:
        logger.warning("Y-axis is not centered. Centering.")
        vertices[:,1] -= y_offset

    return z_max


def generate_contours(filename, layer_height, scale):
    "Find the contours of all the intersecting vertices"
    faces, vertices = parse_obj(filename)
    z_max = center_vertices(vertices)

    num_slices = int(np.ceil(z_max*scale/layer_height))
    print(f"Number of slices: {num_slices}")

    face_qs = []

    for i in range(num_slices):
        zi = i*layer_height
        face_q = FaceQueue()

        # Find all the vertices intersecting with this z-plane
        # Then generate contours
        for face_num,face in enumerate(faces):
            current_verts = vertices[face]
            current_zs = current_verts[:, 2]

            lowers = current_verts[current_zs <= zi]
            uppers = current_verts[current_zs > zi]
            if len(lowers) != 0 and len(uppers) != 0: # and not is_lower_point(current_zs, zi):
                # add face to list of intersected faces
                f_class = Face(face, face_num)
                face_q.insert(f_class)

                # process face
                for low_vert in lowers:
                    for upp_vert in uppers:
                        contour_pt = get_intersection(low_vert, upp_vert, z=zi)
                        f_class.add_contour_pts(contour_pt)

        face_qs.append(face_q)
    return face_qs, vertices

def process_gcode_template(filename, tmp_name, **kwargs):
    "Process gcode template with necessary kwargs and write into tmp file"
    fn = os.path.join(__location__, filename)
    with open(fn) as f:
        data = f.read()

    with open(tmp_name, "w") as f:
        f.write(data.format(**kwargs))

def process_temp(temp, lookup):
    if isinstance(temp, (float,int)) or temp.isdigit():
        return float(temp)
    elif temp.upper() in lookup:
        return lookup[temp.upper()]
    else:
        raise ValueError("Temperature not recognized")

def generate_gcode(filename, outfile="out.gcode", layer_height=0.2, scale=1, save_image=False,
    feedrate=3600, feedrate_writing=None, filament_diameter=1.75, extrusion_width=0.4,
    extrusion_multiplier=1, misc_infill="cross", misc_infill_kwargs={'gap_between_crosses': 5},
    num_solid_fill=3, temperature="PLA", bed_temperature="PLA", units="mm"):
    """
    Generate G-code from an `.obj` file.

    Arguments

    filename (str)
        The name of the input .obj file.
    outfile (str)
        The name of the output file.
        Default: out.gcode
    layer_height (float)
        The height of the layers when printing.
        Default: 0.2
    scale (float)
        Scale the entire model by a constant factor.
        Default: 1
    save_image (bool)
        Save an image of the nozzle path that will be executed.
        Default: False
    feedrate (float)
        The maximum speed at which the printer head should move.
        (mm/min)
        Default: 3600
    feedrate_writing (float)
        The speed at which the printer head should move when
        printing. (mm/min)
        Default: feedrate/2
    filament_diameter (float)
        The diameter of the filament in units (mm by default)
        Default: 1.75
    extrusion_width (float)
        The desired width of the printed extrusion.
        Default: 0.4
    extrusion_multiplier (float)
        A constant multiplier to adjust the extrusion rate.
        Default: 1
    misc_infill (str)
        The type of infill pattern for layers that are not on the
        top or the bottom. One of ["cross", "solid", "none"].
        Default: "cross"
    misc_infill_kwargs (dict)
        Miscellaneous keyword arguments to the misc_infill.
        Default: {'gap_between_crosses': 5}
    num_solid_fill (int)
        The number of solid infill layers at the top and bottom
        of the object.
        Default: 3
    temperature (str or float)
        The temperature of the printer head in degrees celsius.
        Either a float or use a default temperature value from
        ["PLA", "ABS"]
        Default: PLA
    bed_temperature (str or float)
        The temperature of the printer bed in degrees celsius.
        Either a float or use a default temperature value from
        ["PLA", "ABS"]
        Default: PLA
    units (str)
        The units to operate in. One of ["mm", "in"].
        Default: "mm"
    """
    face_qs, vertices = generate_contours(filename, layer_height, scale)

    feedrate_writing = feedrate_writing or feedrate//2
    flow_area = extrusion_multiplier*extrusion_width*layer_height
    flowrate = flow_area*feedrate_writing/60
    extrusion_rate = flow_area/(filament_diameter**2/4*np.pi)
    logger.info(f"The flowrate is set to {flowrate}mm^3/s")

    nozzle_temp = process_temp(temperature, material_nozzle_temps)
    bed_temp = process_temp(bed_temperature, material_bed_temps)
    logger.info(f"The nozzle temperature is set to {nozzle_temp} degrees celsius")
    logger.info(f"The bed temperature is set to {bed_temp} degrees celsius")

    total_distance, total_extruded = 0, 0

    process_gcode_template("./templates/header.gcode", "header.tmp", units=("0 \t\t\t\t\t;use inches" if units=="in" else "1 \t\t\t\t\t;use mm"), feedrate=feedrate, temperature=nozzle_temp, bed_temperature=bed_temp)
    process_gcode_template("./templates/footer.gcode", "footer.tmp", feedrate=feedrate)

    with G(outfile=outfile, filament_diameter=filament_diameter, layer_height=layer_height, header="header.tmp", footer="footer.tmp") as g:
        g.absolute()
        for layer_num, layer in enumerate(face_qs):
            g.write(f"\n; Printing layer {layer_num}\n; ====================")
            g.write(f"\n; Printing outline")
            for i, face in enumerate(layer):
                if i == 0:
                    # for the first face, check which way to move
                    if len(layer) > 1 and (all(face.contour_points[0] == layer[1].contour_points[0]) or all(face.contour_points[0] == layer[1].contour_points[1])):
                        start_pt = face.contour_points[1]
                        next_pt = face.contour_points[0]
                    else:
                        start_pt = face.contour_points[0]
                        next_pt = face.contour_points[1]

                    g.abs_move(*start_pt, rapid=True, F=feedrate)
                    last_pt = start_pt
                else:
                    # for the rest of the way just go to the contour pt that isn't the same as the last
                    next_pt = face.contour_points[1 if all(face.contour_points[0] == last_pt) else 0]

                # calculate how much to extrude
                distance = distance_between(next_pt, last_pt)
                total_distance += distance
                extrusion_amount = extrusion_rate*distance

                # move the cursor
                g.abs_move(*next_pt, F=feedrate_writing, E=total_extruded+extrusion_amount)
                total_extruded += extrusion_amount
                last_pt = next_pt

            # connect back to the start
            distance = distance_between(start_pt, last_pt)
            total_distance += distance
            extrusion_amount = extrusion_rate*distance
            g.abs_move(*start_pt, F=feedrate_writing, E=total_extruded+extrusion_amount)
            total_extruded += extrusion_amount

            # Add infill
            # TODO: check if the layer above is smaller and add infill
            if layer_num < num_solid_fill or layer_num >= len(face_qs) - num_solid_fill or misc_infill == "solid" or (layer_num != len(face_qs)-1 and check_layer_above(layer, face_qs[layer_num+1])):
                # TODO: remove global minima for the axis and start at the layer min/max
                axis = Axis.X if layer_num % 2 == 0 else Axis.Y
                total_distance, total_extruded = solid(g, layer, axis, vertices[:, axis].min().item(), vertices[:, axis].max().item(), extrusion_rate, total_extruded, total_distance, extrusion_width)
            elif misc_infill == "cross":
                total_distance, total_extruded = criss_cross(g, layer, vertices[:, Axis.X].min().item(), vertices[:, Axis.X].max().item(), vertices[:, Axis.Y].min().item(), vertices[:, Axis.Y].max().item(), extrusion_rate, total_extruded, total_distance, extrusion_width, **misc_infill_kwargs)

        logger.info(f"Total nozzle distance: {total_distance}mm")
        logger.info(f"Estimated filament used: {total_extruded}mm")
        # logger.info(f"Total volume: {}mm^3")

        # View output slices
    if save_image:
        g.view('matplotlib')
        plt.show(block=True)
        # plt.savefig('img.jpg')

    return g
