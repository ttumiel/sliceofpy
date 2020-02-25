import numpy as np

def get_intersection(c1, c2, **kwargs):
    "Calculate the intersection of a line between c1 and c1 and the given x, y or z coord."
    if 'x' in kwargs:
        x = kwargs['x']
        y = (x-c1[0])*(c2[1]-c1[1])/(c2[0]-c1[0]) + c1[1]
        z = (x-c1[0])*(c2[2]-c1[2])/(c2[0]-c1[0]) + c1[2]
    elif 'y' in kwargs:
        y = kwargs['y']
        x = (y-c1[1])*(c2[0]-c1[0])/(c2[1]-c1[1]) + c1[0]
        z = (y-c1[1])*(c2[2]-c1[2])/(c2[1]-c1[1]) + c1[2]
    elif 'z' in kwargs:
        z = kwargs['z']
        x = (z-c1[2])*(c2[0]-c1[0])/(c2[2]-c1[2]) + c1[0]
        y = (z-c1[2])*(c2[1]-c1[1])/(c2[2]-c1[2]) + c1[1]
    else:
        raise ValueError(f"Must specify one of x, y or z in kwargs:{kwargs}")
    return np.array([x, y, z])

def distance_between(c1, c2):
    assert len(c1) == 3
    assert len(c2) == 3
    return np.sqrt(np.sum(np.square(c1-c2)))
