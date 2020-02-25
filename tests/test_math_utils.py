import numpy as np

from sliceofpy.math_utils import get_intersection

def test_get_intersection():
    c1 = np.array([1,1,1])

    c2 = np.array([3,1,1])
    arr = get_intersection(c1, c2, x=2)
    assert all(arr == np.array([2,1,1]))

    c2 = np.array([1,3,1])
    arr = get_intersection(c1, c2, y=2)
    assert all(arr == np.array([1,2,1]))

    c2 = np.array([1,1,3])
    arr = get_intersection(c1, c2, z=2)
    assert all(arr == np.array([1,1,2]))
