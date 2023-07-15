#!/bin/env python3

"""Generate a palette image from a base image and set of colors.

functions:
    * :func:`main`: run the program with CLI-based arguments
    * :func:`make_parser`: create the CLI parser

classes:
    * :class:`Palette`: visual palette created on an image base
"""


import argparse

import numpy as np
import pandas as pd
from wand.drawing import Drawing
from wand.image import Image

from .convert_colors import hex_to_rgb, rgb_to_hsv


# TODO: option for one-col vs two-col palette
def make_parser(
    parser: argparse.ArgumentParser = None,
) -> argparse.ArgumentParser:
    """Make a CLI-based argument parser.

    Args:
        parser (argparse.ArgumentParser): pre-existing parser to modify;
            default: `None`

    Returns:
        argparse.ArgumentParser:
    """
    descr = (
        "Given an image and a list of colors, generate a graphical "
        "representation of their palette."
    )
    if parser is None:
        parser = argparse.ArgumentParser(description=descr)
    else:
        parser.description = descr
    parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter
    parser.add_argument("img_path", help="The image to create the palette on.")
    parser.add_argument(
        "-cf", "--color-file", default="colors.json", help="The color file."
    )
    parser.add_argument(
        "-pf",
        "--palette-file",
        default="palette.png",
        help="The palette file.",
    )
    parser.add_argument(
        "-ff", "--font-family", default="Sarabun", help="Font family for text."
    )
    parser.add_argument(
        "-fs", "--font-size", type=int, default=28, help="Font size for text."
    )
    return parser


class Palette:
    """Visual palette created on an image base.

    Overlay color samples on image across the left and right of the image. If
    the input is provided in '.json' format, also label the hex codes with the
    names provided by the '.json'. If 'fg' and/or 'bg' are provided, they will
    be used as the text color for the labels.

    Args:
        img_path (str): path to image
        color_file (str): path to color file; default: 'colors.json'
        palette_file (str): path to saved image; default: 'palette.png'
        cheight (int): height (in pixels) of a color swatch; default: 90
        cwidth (int): width (in pixels) of a color swatch; default: 180
        cwidth (int): margin (in pixels) between color swatches, also used for
            corner radius; default: 10
        font_family (str): font to use; default: 'Sarabun' else system default
        font_size (int): font size for text; default: 28
    """

    def __init__(self, img_path: str, **kwargs):
        """Initialize :class:`Palette`."""
        #: path to saved image
        self.palette_file = kwargs.pop("palette_file", "palette.png")
        #: height (in pixels) of a color swatch
        self.cheight = kwargs.pop("cheight", 90)
        #: width (in pixels) of a color swatch
        self.cwidth = kwargs.pop("cwidth", 180)
        #: margin (in pixels) between color swatches, also used for radius
        self.cmargin = kwargs.pop("cmargin", 10)

        self._read_colors(kwargs.pop("color_file", "colors.json"))
        self._make_font_colors()

        self.image = Image(filename=img_path)
        self._scale_image()
        self._draw = Drawing()
        self._draw.font_family = kwargs.pop("font_family", "Sarabun")
        self._draw.font_size = kwargs.pop("font_size", 28)

        self._colors_drawn = 0
        while self._colors_drawn < len(self.colors):
            self._add_color()
        self._draw(self.image)

    def _read_colors(self, color_path):
        """Read colors from `color_path`."""
        if color_path.endswith(".json"):
            #: colors loaded from `colorfile`
            self.colors = pd.read_json(color_path, typ="series")
        else:
            self.colors = pd.read_csv(color_path, header=None)[0]

    def show(self):
        """Not Implemented."""
        raise NotImplementedError
        #  self.image.show()

    def save(self, fname: str = None):
        """Save the palette to image file.

        Args:
            fname (str): path to save; default: :const:`palette_file`
        """
        fname = fname or self.palette_file
        self.image.save(filename=fname)

    def _scale_image(self):
        """Scale image, in place, to palette size."""
        n_colors_per_col = int(np.ceil(len(self.colors) / 2))
        width, height = self.image.size
        new_height = n_colors_per_col * (self.cheight + self.cmargin) + self.cmargin
        scale = new_height / height
        new_width = int(scale * width)
        self.image.resize(new_width, new_height)

    def _add_color(self):
        """Add the next color to the palette."""
        # Calc constants.
        n_colors_per_col = int(np.ceil(len(self.colors) / 2))
        x_pos = self._colors_drawn // n_colors_per_col
        y_pos = self._colors_drawn % n_colors_per_col
        width, _ = self.image.size

        left = self.cmargin if x_pos == 0 else width - self.cmargin - self.cwidth
        top = self.cmargin + y_pos * (self.cheight + self.cmargin)
        label = (  # If colors have names, include them.
            None
            if self.colors.index.dtype == int
            else self.colors.index[self._colors_drawn]
        )

        # Draw on the image.
        self._draw_rect(left, top, color=self.colors.iloc[self._colors_drawn])
        self._draw_text(
            left + self.cwidth // 2,
            top + self.cheight // 2,
            self.colors.iloc[self._colors_drawn],
            label=label,
        )
        self._colors_drawn += 1

    def _draw_rect(self, left: int, top: int, color: str):
        """Draw a color swatch on the palette image.

        Args:
            left (int): left position, in pixels
            top (int): top position, in pixels
            color (str): color of swatch
        """
        self._draw.fill_color = color
        self._draw.rectangle(
            left=left,
            top=top,
            width=self.cwidth,
            height=self.cheight,
            radius=self.cmargin,
        )

    def _make_font_colors(self):
        """Define light and dark font colors, and threshold for choosing."""
        # Choose "fg" if it exists, else "white".
        if self.colors.index.isin(["fg"]).any():
            _, _, fg_thresh = rgb_to_hsv(hex_to_rgb(self.colors.loc["fg"]))
            self._fg = self.colors.loc["fg"]
        else:
            fg_thresh = 1
            self._fg = "white"

        # Choose "bg" if it exists, else "black".
        if self.colors.index.isin(["bg"]).any():
            _, _, bg_thresh = rgb_to_hsv(hex_to_rgb(self.colors.loc["bg"]))
            self._bg = self.colors.loc["bg"]
        else:
            bg_thresh = 0
            self._bg = "black"

        if fg_thresh < bg_thresh:
            self._fg, self._bg = self._bg, self._fg

        # Define the value threshold as between the two.
        self._color_thresh = np.mean([fg_thresh, bg_thresh])

    def _get_font_color(self, color: str) -> str:
        """Find the best font color to label a color swatch.

        Args:
            color (str): the hexadecimal background of the swatch

        Returns:
            str: chosen font color
        """
        _, _, val = rgb_to_hsv(hex_to_rgb(color))
        if val < self._color_thresh:
            return self._fg
        return self._bg

    def _draw_text(self, text_x: int, text_y: int, color: str, label: str = None):
        """Overlay text on a color swatch.

        Args:
            text_x (int): x-position of text center, in pixels
            text_y (int): y-position of text center, in pixels
            color (str): the hexadecimal color to write
            label (str): name of the color; default: None
        """
        font_size = int(self._draw.font_size)
        # Determine literal text and its vertical offset.
        if label:
            text = f"{label}:\n{color}"
            v_offset = -font_size // 4  # T/B alignment.
        else:
            text = color
            v_offset = font_size // 3  # T/B alignment.
        # Set some drawing defaults.
        self._draw.text_alignment = "center"  # L/R alignment.
        self._draw.gravity = "north"
        self._draw.text_interline_spacing = -font_size // 6
        # Draw the text in the correct color.
        self._draw.fill_color = self._get_font_color(color)
        self._draw.text(text_x, text_y + v_offset, text)


def main(args: argparse.Namespace):
    """Generate a visual palette from CLI-like arguments.

    Args:
        args (argparse.Namespace): arguments from CLI
    """
    palette = Palette(**vars(args))
    palette.save()


if __name__ == "__main__":
    PARSER = make_parser()
    ARGS = PARSER.parse_args()
    main(ARGS)
