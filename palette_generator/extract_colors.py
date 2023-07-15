#!/bin/env python3


"""Extract a finite number of representative colors from an image.

Functions:
    * :func:`main`: extract colors from an image using CLI-style args
    * :func:`make_parser`: create the CLI parser
"""


import argparse

import pandas as pd
from wand.image import Image

from .convert_colors import rgb_to_hex


def make_parser(
    parser: argparse.ArgumentParser = None,
) -> argparse.ArgumentParser:
    """Create a CLI parser.

    Args:
        parser (argparse.ArgumentParser): pre-existing parser to modify;
            default: `None`

    Returns:
        argparse.ArgumentParser: argument parser
    """
    descr = "Extract a pre-computed palette from an image."
    if parser is None:
        parser = argparse.ArgumentParser(description=descr)
    else:
        parser.description = descr
    parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter
    if "img_path" not in parser.format_usage():
        parser.add_argument(
            "img_path",
            help="The image file from which the palette is extracted.",
        )
    parser.add_argument(
        "-nc",
        "--n-colors",
        default=512,
        type=int,
        help="The number of colors to extract from the raw image. ",
    )
    parser.add_argument(
        "-hf",
        "--hist-file",
        default="color_hist.txt",
        help="The color histogram output.",
    )
    return parser


def main(
    img_path: str, n_colors: int = 512, hist_file: str = "color_hist.txt", **kwargs
):
    """Extract colors from an image.

    Args:
        img_path (str): image file
        n_colors (int): number of colors to extract; default: 512
        hist_file (str): save counts and hex codes to this file;
            default: 'color_hist.txt'

    Gobbles additional kwargs.
    """
    # Load the image.
    img = Image(filename=img_path)
    # Convert the image into `n_colors` palette space.
    # `dither` is important for generating counts that are more representative
    #   of human vision.
    img.quantize(n_colors, dither=True)
    colors = pd.DataFrame(img.histogram.items(), columns=["color_object", "count"])
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
    colors.to_csv(hist_file, index=False)


if __name__ == "__main__":
    PARSER = make_parser()
    ARGS = PARSER.parse_args()
    main(**vars(ARGS))
