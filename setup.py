import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "sliceofpy",
    version = "0.0.1",
    author = "Thomas Tumiel",
    description = ("A cli 3D model slicer."),
    license = "MIT",
    keywords = "3D slicer",
    packages=['sliceofpy'],
    long_description=read('README.md'),
    entry_points = {
        'console_scripts': ['sliceofpy=sliceofpy.cli:cli'],
    },
    install_requires=[
        'numpy',
        'matplotlib',
        'mecode'
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
    ],
)
