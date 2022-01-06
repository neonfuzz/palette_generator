#!/bin/env python3

import argparse

import pandas as pd
from wand.image import Image

from convert_colors import rgb_to_hex


# TODO: Describe how this is different from `make_palette`.
PARSER = argparse.ArgumentParser(
    description="Extract a pre-computed palette from an image."
)
PARSER.add_argument(
    "img", help="The image file from which the palette is extracted."
)
PARSER.add_argument(
    "--n-colors",
    "-n",
    default=512,
    type=int,
    help="The number of colors to extract. Default: 512",
)
PARSER.add_argument(
    "--outfile",
    "-o",
    default="color_hist.txt",
    help="The output of the script. Default: 'color_hist.txt'",
)


FNAME = "nordic.png"
NCOLORS = 512
OUTFILE = "color_hist.txt"


def main(fname, ncolors=512, outfile="color_hist.txt"):
    img = Image(filename=fname)
    img.quantize(ncolors, dither=True)
    colors = pd.DataFrame(
        img.histogram.items(), columns=["color_object", "count"]
    )
    colors["hex"] = (
        colors["color_object"]
        .apply(lambda c: (c.red_int8, c.green_int8, c.blue_int8))
        .apply(rgb_to_hex)
    )
    colors = (
        colors.sort_values("count", ascending=False)
        .drop("color_object", axis=1)
        .reset_index(drop=True)
    )

    colors.to_csv(outfile, index=False)


if __name__ == "__main__":
    args = PARSER.parse_args()
    main(
        fname=args.img,
        ncolors=args.n_colors,
        outfile=args.outfile,
    )
