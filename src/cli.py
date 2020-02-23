import argparse

from slicer import generate_gcode

def cli():
    p = argparse.ArgumentParser(
        description="A command line object slicer for .obj files."
    )
    p.add_argument("filename", type=str, help="The name of the .obj file")
    p.add_argument(
        "--output",
        "-o",
        type=str,
        default="out.gcode",
        help="The name of the output file",
    )
    p.add_argument(
        "--layer_height",
        "-l",
        type=float,
        default=1.0,
        help="The height of the slices in mm",
    )
    p.add_argument(
        "--scale",
        "-s",
        type=float,
        default=1.0,
        help="Scale all object values by this number",
    )
    p.add_argument(
        "--save_image",
        action="store_true",
        help="Save an image of the final extrusion path to out.jpg",
    )

    args = p.parse_args()

    generate_gcode(
        args.filename,
        outfile=args.output,
        slice_height=args.slice_height,
        scale=args.scale,
        save_image=args.save_image,
    )


if __name__ == "__main__":
    cli()
