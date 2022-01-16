#!/bin/env python3


"""
Extract a finite number of representative colors from an image.

Functions:
    * :func:`main`: extract colors from an image using CLI-style args
"""


import argparse

import pandas as pd
from wand.image import Image

from .convert_colors import rgb_to_hex


def _make_parser() -> argparse.ArgumentParser:
    """
    Create a CLI parser.

    Returns:
        argparse.ArgumentParser: argument parser
    """
    parser = argparse.ArgumentParser(
        description="Extract a pre-computed palette from an image."
    )
    parser.add_argument(
        "fname", help="The image file from which the palette is extracted."
    )
    parser.add_argument(
        "--n-colors",
        "-n",
        default=512,
        type=int,
        help="The number of colors to extract. Default: 512",
    )
    parser.add_argument(
        "--outfile",
        "-o",
        default="color_hist.txt",
        help="The output of the script. Default: 'color_hist.txt'",
    )
    return parser


FNAME = "nordic.png"
N_COLORS = 512
OUTFILE = "color_hist.txt"


def main(fname: str, n_colors: int = 512, outfile: str = "color_hist.txt"):
    """
    Extract colors from an image.

    Args:
        fname (str): image file
        n_colors (int): number of colors to extract; default: 512
        outfile (str): save counts and hex codes to this file;
            default: 'color_hist.txt'
    """
    # Load the image.
    img = Image(filename=fname)
    # Convert the image into `n_colors` palette space.
    # `dither` is important for generating counts that are more representative
    #   of human vision.
    img.quantize(n_colors, dither=True)
    colors = pd.DataFrame(
        img.histogram.items(), columns=["color_object", "count"]
    )
    # Calculate hexadecimal codes from wand color objects.
    colors["hex"] = (
        colors["color_object"]
        .apply(lambda c: (c.red_int8, c.green_int8, c.blue_int8))
        .apply(rgb_to_hex)
    )
    # Sort by count.
    colors = (
        colors.sort_values("count", ascending=False)
        .drop("color_object", axis=1)
        .reset_index(drop=True)
    )
    # Save to file.
    colors.to_csv(outfile, index=False)


if __name__ == "__main__":
    PARSER = _make_parser()
    ARGS = PARSER.parse_args()
    main(**vars(ARGS))
