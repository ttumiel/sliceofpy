import argparse
import logging

from slicer import generate_gcode

logger = logging.getLogger(__name__)
logging.basicConfig()


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
        default=0.2,
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
    p.add_argument(
        "--feedrate",
        "-f",
        type=float,
        default=3600,
        help="The speed at which the printer head moves in mm/min. (Default: 3600mm/min)",
    )
    p.add_argument(
        "--feedrate_writing",
        type=float,
        default=None,
        help="The speed at which the printer head moves while printing in mm/min. (Default: 0.5*feedrate)",
    )
    p.add_argument(
        "--filament_diameter",
        "-d",
        type=float,
        default=1.75,
        help="The diameter of FDM filament you are using",
    )
    p.add_argument(
        "--extrusion_width",
        "-w",
        type=float,
        default=0.4,
        help="Total width of the capsule shaped cross section of a squashed filament.",
    )
    p.add_argument(
        "--extrusion_multiplier",
        type=float,
        default=1,
        help="The length of extrusion filament to be pushed through on a move"
        "command will be multiplied by this number before being applied.",
    )
    p.add_argument(
        "--units",
        type=str,
        default="mm",
        choices=["in", "mm"],
        help="The units to operate in. Either mm or in.",
    )

    # TODO: wall_speed, infill_speed

    args = p.parse_args()

    generate_gcode(
        args.filename,
        outfile=args.output,
        layer_height=args.layer_height,
        scale=args.scale,
        save_image=args.save_image,
        feedrate=args.feedrate,
        feedrate_writing=args.feedrate_writing,
        filament_diameter=args.filament_diameter,
        extrusion_width=args.extrusion_width,
        extrusion_multiplier=args.extrusion_multiplier,
        units=args.units,
    )


if __name__ == "__main__":
    cli()