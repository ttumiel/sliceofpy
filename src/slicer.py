import numpy as np
from mecode import G
import logging

logger = logging.getLogger(__name__)
logging.basicConfig()
logger.setLevel(logging.DEBUG)
class Face():
    def __init__(self, vertices, face_num):
        self.v = vertices
        self.face_num = face_num
        self.contour_points = []

    def add_contour_pts(self, pt):
        self.contour_points.append(pt)

    def __str__(self):
        return f"Face {self.face_num}: {str(self.v)}"

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


def center_vertices(vertices):
    "Corrects any offsets in the vertices for better printing."
    x_min,y_min,z_min = vertices.min(axis=0)
    x_max,y_max,z_max = vertices.max(axis=0)
    if z_min != 0:
        logger.warning("Base height is not zero. Compensating.")
        vertices[:,2] -= z_min

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
            if len(lowers) != 0 and len(uppers) != 0:
                # add face to list of intersected faces
                f_class = Face(face, face_num)
                face_q.insert(f_class)

                # process face
                for low_vert in lowers:
                    for upp_vert in uppers:
                        x = (zi-low_vert[2])*(upp_vert[0]-low_vert[0])/(upp_vert[2]-low_vert[2]) + low_vert[0]
                        y = (zi-low_vert[2])*(upp_vert[1]-low_vert[1])/(upp_vert[2]-low_vert[2]) + low_vert[1]
                        f_class.add_contour_pts(np.array([x, y, zi]))

        face_qs.append(face_q)
    return face_qs

def process_gcode_template(filename, tmp_name, **kwargs):
    "Process gcode template with necessary kwargs and write into tmp file"
    with open(filename) as f:
        data = f.read()

    with open(tmp_name, "w") as f:
        f.write(data.format(**kwargs))

def generate_gcode(filename, outfile="out.gcode", layer_height=0.2, scale=1, save_image=False,
    feedrate=3600, feedrate_writing=None, filament_diameter=1.75, extrusion_width=0.4, extrusion_multiplier=1, units="mm"):
    face_qs = generate_contours(filename, layer_height, scale)

    process_gcode_template("header.gcode", "header.tmp", units=("0 \t\t\t\t\t;use inches" if units=="in" else "1 \t\t\t\t\t;use mm"), feedrate=feedrate)
    process_gcode_template("footer.gcode", "footer.tmp", feedrate=feedrate)
        for layer in face_qs:
            for i, face in enumerate(layer):
                # for the first layer, check which way to move
                if i == 0:
                    if all(face.contour_points[0] == layer[1].contour_points[0]) or all(face.contour_points[0] == layer[1].contour_points[1]):
                        start_pt = face.contour_points[1]
                        next_pt = face.contour_points[0]
                    else:
                        start_pt = face.contour_points[0]
                        next_pt = face.contour_points[1]
                    g.move(*start_pt)
                    # start extruding TODO
                else:
                    # for the rest of the way just go to the contour pt that isn't the same as the last
                    next_pt = face.contour_points[1 if all(face.contour_points[0] == last_pt) else 0]

                # move the cursor
                g.move(*next_pt)
                last_pt = next_pt

        # connect back to the start
        g.move(*start_pt)

        # stop extruding

