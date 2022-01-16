#!/bin/env python3


import argparse

import numpy as np
from wand.drawing import Drawing
from wand.image import Image

from convert_colors import hex_to_rgb


# TODO: option for one-col vs two-col palette
PARSER = argparse.ArgumentParser(
    description="Given an image and a list of colors, generate a graphical "
    "representation of their palette."
)
PARSER.add_argument("img_path", help="The image.")
PARSER.add_argument(
    "-c",
    "--color_file",
    default="colors.txt",
    help="The list of colors. Default: 'colors.txt'",
)
PARSER.add_argument(
    "-o",
    "--outfile",
    default="palette.png",
    help="The outfile. Default: 'palette.png'",
)
PARSER.add_argument(
    "-ff",
    "--font-family",
    default="Sarabun",
    help="Font family for text. Default: 'Sarabun'",
)
PARSER.add_argument(
    "-fs",
    "--font-size",
    type=int,
    default=32,
    help="Font size for text. Default: 32",
)


def _get_font_color(color):
    rgb = hex_to_rgb(color)
    if np.mean(rgb) < 128:
        return "#FFFFFF"
    return "#000000"


class Palette:
    def __init__(self, img_path, **kwargs):
        self.outfile = kwargs.pop("outfile", "palette.png")
        self.cheight = kwargs.pop("cheight", 90)
        self.cwidth = kwargs.pop("cwidth", 180)
        self.cmargin = kwargs.pop("cmargin", 10)

        self.image = Image(filename=img_path)
        with open(
            kwargs.pop("color_file", "colors.txt"), "rt", encoding="utf-8"
        ) as infile:
            self.colors = [x.strip() for x in infile.readlines()]
        self._scale_image()
        self._draw = Drawing()
        self._draw.font_family = kwargs.pop("font_family", "Sarabun")
        self._draw.font_size = kwargs.pop("font_size", 32)

        self._colors_drawn = 0
        while self._colors_drawn < len(self.colors):
            self._add_color()
        self._draw(self.image)

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
        self._draw_rect(left, top, color=self.colors[self._colors_drawn])
        self._draw_text(
            left + self.cwidth // 2,
            top + self.cheight // 2,
            self.colors[self._colors_drawn],
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

    def _draw_text(self, text_x, text_y, color):
        v_offset = int(self._draw.font_size / 3)  # T/B alignment.
        self._draw.text_alignment = "center"  # L/R alignment.
        self._draw.gravity = "north"
        self._draw.fill_color = _get_font_color(color)
        self._draw.text(text_x, text_y + v_offset, color)


if __name__ == "__main__":
    args = PARSER.parse_args()
    palette = Palette(**vars(args))
    palette.save()
