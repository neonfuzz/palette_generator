#!/bin/env python3


import argparse

import numpy as np
import pandas as pd
from wand.drawing import Drawing
from wand.image import Image

from convert_colors import hex_to_rgb, rgb_to_hsv


# TODO: option for one-col vs two-col palette
def _make_parser():
    parser = argparse.ArgumentParser(
        description="Given an image and a list of colors, generate a "
        "graphical representation of their palette."
    )
    parser.add_argument("img_path", help="The image.")
    parser.add_argument(
        "-c",
        "--color_file",
        default="colors.json",
        help="The palette colors. Can read .json or a plain list of color "
        "hex codes. Default: 'colors.json'",
    )
    parser.add_argument(
        "-o",
        "--outfile",
        default="palette.png",
        help="The outfile. Default: 'palette.png'",
    )
    parser.add_argument(
        "-ff",
        "--font-family",
        default="Sarabun",
        help="Font family for text. Default: 'Sarabun'",
    )
    parser.add_argument(
        "-fs",
        "--font-size",
        type=int,
        default=28,
        help="Font size for text. Default: 28",
    )
    return parser


class Palette:
    def __init__(self, img_path, **kwargs):
        self.outfile = kwargs.pop("outfile", "palette.png")
        self.cheight = kwargs.pop("cheight", 90)
        self.cwidth = kwargs.pop("cwidth", 180)
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
        if color_path.endswith(".json"):
            self.colors = pd.read_json(color_path, typ="series")
        else:
            self.colors = pd.read_csv(color_path, header=None)[0]

    def show(self):
        raise NotImplementedError
        #  self.image.show()

    def save(self, fname=None):
        fname = fname or self.outfile
        self.image.save(filename=fname)

    def _scale_image(self):
        n_colors_per_col = int(np.ceil(len(self.colors) / 2))
        width, height = self.image.size
        new_height = (
            n_colors_per_col * (self.cheight + self.cmargin) + self.cmargin
        )
        scale = new_height / height
        new_width = int(scale * width)
        self.image.resize(new_width, new_height)

    def _add_color(self):
        n_colors_per_col = int(np.ceil(len(self.colors) / 2))
        x_pos = self._colors_drawn // n_colors_per_col
        y_pos = self._colors_drawn % n_colors_per_col
        width, _ = self.image.size

        left = (
            self.cmargin if x_pos == 0 else width - self.cmargin - self.cwidth
        )
        top = self.cmargin + y_pos * (self.cheight + self.cmargin)
        label = (
            None
            if self.colors.index.dtype == int
            else self.colors.index[self._colors_drawn]
        )

        self._draw_rect(left, top, color=self.colors.iloc[self._colors_drawn])
        self._draw_text(
            left + self.cwidth // 2,
            top + self.cheight // 2,
            self.colors.iloc[self._colors_drawn],
            label=label,
        )
        self._colors_drawn += 1

    def _draw_rect(self, left, top, color):
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

        # Define the value threshold as between the two.
        self._color_thresh = np.mean([fg_thresh, bg_thresh])

    def _get_font_color(self, color: str) -> str:
        """
        Find the best font color to label a color swatch.

        Args:
            color (str): the hexadecimal background of the swatch

        Returns:
            str: chosen font color
        """
        _, _, val = rgb_to_hsv(hex_to_rgb(color))
        if val < self._color_thresh:
            return self._fg
        return self._bg

    def _draw_text(
        self, text_x: int, text_y: int, color: str, label: str = None
    ):
        """
        Overlay text on a color swatch.

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


if __name__ == "__main__":
    PARSER = _make_parser()
    ARGS = PARSER.parse_args()
    PALETTE = Palette(**vars(ARGS))
    PALETTE.save()
