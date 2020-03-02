import numpy as np
from enum import IntEnum

from .math_utils import get_intersection, distance_between

class Axis(IntEnum):
    X = 0
    Y = 1
    Z = 2

def find_faces_at_index(faces, coord_val, index):
    """Find all the faces that intersect `coord_val` along `index`

    Example
    Slice a list of faces along the x-axis so that you can tell
    where to fill the shape in, by drawing lines across the polygon.
    """
    return [face for face in faces
        if ((face.contour_points[0][index] > coord_val and face.contour_points[1][index] <= coord_val) or
            (face.contour_points[1][index] > coord_val and face.contour_points[0][index] <= coord_val))]

def get_intersections(faces, coord_val, index):
    "Get the intersections between a list of faces at a particular `coord_val` along `index`"
    # Does z even make sense?
    if index == Axis.X:
        coord = {"x": coord_val}
    elif index == Axis.Y:
        coord = {"y": coord_val}
    elif index == Axis.Z:
        coord = {"z": coord_val}
    return np.stack([get_intersection(face.contour_points[0], face.contour_points[1], **coord) for face in faces])

def fill_across_index(g, faces, index, current_val, order_axes_by, extrusion_rate, total_extruded, total_distance):
    "Fills a polygon across `index` in G-code"
    faces_at_val = find_faces_at_index(faces, current_val, index)
    if len(faces_at_val) == 0:
        return total_distance, total_extruded
    intersections = get_intersections(faces_at_val, current_val, index)

    # Sort by the correct index/axis
    idxs = np.argsort(intersections[:, order_axes_by])
    sorted_intersections = intersections[idxs]

    assert len(sorted_intersections)%2 == 0, "Not even. Something's funky..."
    for i in range(0, len(sorted_intersections), 2):
        # Move to starting point
        g.abs_move(*sorted_intersections[i], rapid=True)

        # Extrude across distance
        total_distance += distance_between(sorted_intersections[i], sorted_intersections[i+1])
        total_extruded = extrusion_rate*total_distance
        g.abs_move(*sorted_intersections[i+1], E=total_extruded)

    return total_distance, total_extruded


def gap_fill(g, faces, index, start_val, end_val, extrusion_rate, total_extruded, total_distance, n_fill_lines=None, gap=None):
    """Fill a polygon with a gap in between the lines that fill it.

    The gap has a size of either `gap` or is evenly divided by `n_fill_lines`
    """
    assert (n_fill_lines is not None) ^ (gap is not None)
    gap = gap or (end_val-start_val)/n_fill_lines
    order_axes_by = (index+1)%2

    for current_val in np.arange(start_val+gap, end_val, gap):
        total_distance, total_extruded = fill_across_index(g, faces, index, current_val, order_axes_by, extrusion_rate, total_extruded, total_distance)

    return total_distance, total_extruded

def solid(g, faces, index, start_val, end_val, extrusion_rate, total_extruded, total_distance, extrusion_width):
    "Apply a solid fill using a gap fill of size `extrusion_width`"
    g.write("\n; Printing solid infill")
    return gap_fill(g, faces, index, start_val, end_val, extrusion_rate, total_extruded, total_distance, gap=1)

def criss_cross(g, faces, x_min, x_max, y_min, y_max, extrusion_rate, total_extruded, total_distance, extrusion_width, number_of_crosses=None, gap_between_crosses=None):
    """Must specify either number_of_crosses or size_of_crosses but not both.

    Note
    Use a global coord min and max so that the criss crosses are
    on top of each other in consecutive layers.
    """
    assert (number_of_crosses is not None) ^ (gap_between_crosses is not None)
    x_gap = gap_between_crosses or (x_max-x_min)/number_of_crosses
    y_gap = gap_between_crosses or (y_max-y_min)/number_of_crosses

    g.write("\n; Printing x criss-crosses for cross infill")
    total_distance, total_extruded =  gap_fill(g, faces, Axis.X, x_min, x_max, extrusion_rate, total_extruded, total_distance, gap=x_gap)
    g.write("\n; Printing y criss-crosses for cross infill")
    return gap_fill(g, faces, Axis.Y, y_min, y_max, extrusion_rate, total_extruded, total_distance, gap=y_gap)
