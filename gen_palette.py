#!/bin/env python3


import argparse

import numpy as np
from PIL import Image
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype


# TODO: option for one-col vs two-col palette
PARSER = argparse.ArgumentParser(
    description="Given an image and a list of colors, generate a graphical "
    "representation of their palette."
)
PARSER.add_argument("img", help="The image.")
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


def _get_font_color(color):
    color = color.strip("#")
    rgb = color[:2], color[2:4], color[4:]
    rgb = tuple(int(c, 16) for c in rgb)
    if np.mean(rgb) < 85:
        return "#FFFFFF"
    return "#000000"


class Palette:
    def __init__(
        self,
        img_path,
        **kwargs
    ):
        self.outfile = kwargs.pop('outfile', 'palette.png')
        self.cheight = kwargs.pop('cheight', 90)
        self.cwidth = kwargs.pop('cwidth', 180)
        self.cmargin = kwargs.pop('cmargin', 10)

        # TODO: hard path
        self._font = truetype(
            "/home/addie/fonts/Sarabun/Sarabun-Regular.ttf", size=32
        )
        self.image = Image.open(img_path)
        with open(
            kwargs.pop("color_file", "colors.txt"), "rt", encoding="utf-8"
        ) as infile:
            self.colors = [x.strip() for x in infile.readlines()]
        self._scale_image()
        self.draw = Draw(self.image)

        self._colors_drawn = 0
        for color in self.colors:
            self._add_color(color)

    def show(self):
        self.image.show()

    def save(self, fname=None):
        fname = fname or self.outfile
        self.image.save(fname)

    def _scale_image(self):
        n_colors_per_col = int(np.ceil(len(self.colors) / 2))
        width, height = self.image.size
        out_height = (
            n_colors_per_col * (self.cheight + self.cmargin) + self.cmargin
        )
        scale = out_height / height
        new_width, new_height = int(scale * width), out_height
        self.image = self.image.resize((new_width, new_height))

    def _add_color(self, color):
        n_colors_per_col = int(np.ceil(len(self.colors) / 2))
        x_pos = self._colors_drawn // n_colors_per_col
        y_pos = self._colors_drawn % n_colors_per_col
        width, _ = self.image.size

        left = (
            self.cmargin if x_pos == 0 else width - self.cmargin - self.cwidth
        )
        right = left + self.cwidth
        top = self.cmargin + y_pos * (self.cheight + self.cmargin)
        bot = top + self.cheight

        self._draw_rect([left, top, right, bot], color=color)
        self._colors_drawn += 1

    def _draw_rect(self, box, color):
        text_xy = tuple(np.array(box).reshape((2, 2)).mean(axis=0).astype(int))

        self.draw.rounded_rectangle(box, fill=color, radius=self.cmargin)
        self.draw.text(
            text_xy,
            color,
            anchor="mm",
            align="center",
            font=self._font,
            fill=_get_font_color(color),
        )


if __name__ == "__main__":
    args = PARSER.parse_args()
    palette = Palette(
        img_path=args.img, color_file=args.color_file, outfile=args.outfile
    )
    palette.save()
