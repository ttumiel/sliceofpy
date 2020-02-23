import numpy as np
from mecode import G

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

def generate_contours(filename, slice_width=7, scale=1):
    "Find the contours of all the intersecting vertices"
    faces, vertices = parse_obj(filename)

    max_height = vertices.max()
    num_slices = int(np.ceil(max_height*scale/slice_width))
    print(f"Number of slices: {num_slices}")

    face_qs = []

    for i in range(num_slices):
        zi = i*slice_width
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

def generate_gcode(filename, outfile="out.gcode"):
    face_qs = generate_contours(filename)
    pass
