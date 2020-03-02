# sliceofpy: 3D Object Slicing

A command line 3D object slicer. Easily understandable, pretty configurable.

## Install

Install from GitHub:

```bash
pip install git+https://github.com/ttumiel/sliceofpy
```

## Quickstart

Slice a `.obj` file in the current directory. Output G-code file is called `out.gcode`.

```sh
sliceofpy design.obj
```

For more info on any of the commands, type `sliceofpy -h`.

## Limitations

- The slicer does not generate supports for unsupported areas.
- The slicer cannot handle holes inside of an object.

I will gladly accept any contributions.

## Benefits

- The slicer is fairly easy to understand (~700 LOC)
- The slicer is pretty configurable both from the command line and if you imported it as a function.

## How it was made

[Read about it here](https://ttumiel.github.io/blog/slicer/)
