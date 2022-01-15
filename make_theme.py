#!/bin/env python3


import argparse
from pprint import pp
from typing import Callable, Tuple

import matplotlib.pyplot as plt
import pandas as pd
from scipy.spatial.distance import euclidean

from convert_colors import cieluv_to_hex, hex_to_everything


PARSER = argparse.ArgumentParser(
    description="Read a palette of colors, and turn it into a cohesive color "
    "scheme. Prints suggested theme to screen and saves HEX codes to file."
)
PARSER.add_argument(
    "-i",
    "--infile",
    default="color_hist.txt",
    help="each line is '{N}: {C}' where {N} in the number of counts of color "
    "{C}, which is provided as a HEX code. Default: 'color_hist.txt'",
)
PARSER.add_argument(
    "-o",
    "--outfile",
    default="colors.txt",
    help="Each line is a unique theme color, provided as a HEX code. "
    "Default: 'colors.txt'",
)
PARSER.add_argument(
    "-p",
    "--p_mix",
    default=0.25,
    type=float,
    help="Percent to mix pure color in with image colors to get 'red', "
    "'yellow', 'green', 'cyan', 'blue', and 'magenta'. Recommend higher values"
    " for homogeneous images and lower values for heterogeneous images. "
    "Best results between 0.0 and 0.5. Default: 0.25",
)

_RGB = ["R", "G", "B"]
_HSV = ["hue", "sat", "val"]
_XYZ = ["X", "Y", "Z"]
_LUV = ["L", "U", "V"]


class Themer:
    _ref = hex_to_everything(
        pd.Series(
            {
                # Based on xkcd color survey results.
                "red": "#E50000",
                "yellow": "#FFFF14",
                "green": "#15B01A",
                "cyan": "#13EAC9",  # xkcd "aqua"
                "blue": "#0343DF",
                "magenta": "#FF028D",  # xkcd "hot pink"
                "white": "#FFFFFF",
                "black": "#000000",
            }
        )
    )
    ALL = 0
    BRIGHT = 1
    MUTED = 2

    def __init__(self, fname="color_hist.txt", p_mix=0.25):
        colors = pd.read_csv(fname)
        colors = colors.sort_values("count", ascending=False).reset_index(
            drop=True
        )
        self.colors = pd.merge(
            colors,
            hex_to_everything(colors["hex"]),
            left_on="hex",
            right_on="hex",
        )

        self._theme = pd.DataFrame()
        self.p_mix = p_mix

    def _get_subset(self, bright_mode: int = 1):
        # 0 = all, 1 = bright only, 2 = muted
        if bright_mode == self.ALL:
            return self.colors
        if bright_mode == self.BRIGHT:
            return self.colors[
                (self.colors["sat"] > self.colors["sat"].quantile(0.5))
                & (self.colors["val"] > self.colors["val"].quantile(0.5))
            ]
        if bright_mode == self.MUTED:
            return self.colors[
                (self.colors["sat"] < self.colors["sat"].quantile(0.5))
                | (self.colors["val"] < self.colors["val"].quantile(0.5))
            ]
        raise ValueError(f"Unexpected value for `bright_mode`: {bright_mode}")

    def _measure(
        self,
        luv: Tuple[float, float, float],
        mode: Callable = euclidean,
        bright_mode: int = 1,  # 0 = all, 1 = bright only, 2 = muted
        nearest: bool = True,
    ):
        colors = self._get_subset(bright_mode)
        dist = colors[_LUV].apply(mode, v=luv, axis=1)
        if nearest:
            return colors.loc[dist.idxmin()]
        return colors.loc[dist.idxmax()]

    def _get_mixed(self, ref, **kwargs):
        # All in LUV space.
        pure = self._ref.loc[ref][_LUV]
        base = self._measure(pure, **kwargs)[_LUV]
        mixed_luv = (1 - self.p_mix) * base + self.p_mix * pure

        # Now to everything.
        hex_code = cieluv_to_hex(mixed_luv)
        mixed = hex_to_everything(pd.Series([hex_code])).iloc[0]
        mixed.name = ref
        return mixed

    def _get_special(self, mode):
        if mode == "common":
            color = self.colors.iloc[0]
        elif mode == "mean":
            color = self._measure(
                self.colors[_LUV].mean(), bright_mode=self.ALL
            )
        elif mode == "fg":
            color = self._measure(
                self.colors.iloc[0][_LUV],
                bright_mode=self.MUTED,
                nearest=False,
            )
        elif mode == "bg":
            color = self.colors.iloc[0]
        elif mode == "accent":
            color = self.colors.loc[
                self._get_subset(self.BRIGHT)["sat"].idxmax()
            ]
        elif mode == "secondary":
            try:
                color = self._measure(
                    self._theme.loc["accent", _LUV],
                    bright_mode=self.BRIGHT,
                    nearest=False,
                )
            except KeyError:
                # We should never get here, but just in case...
                raise ValueError("Must calculate 'accent' before 'secondary'.")
        else:
            raise NotImplementedError(f"Mode '{mode}' not implemented.")
        color.name = mode
        return color

    @property
    def red(self) -> str:
        return self.theme.loc["red"]

    @property
    def yellow(self) -> str:
        return self.theme.loc["yellow"]

    @property
    def green(self) -> str:
        return self.theme.loc["green"]

    @property
    def cyan(self) -> str:
        return self.theme.loc["cyan"]

    @property
    def blue(self) -> str:
        return self.theme.loc["blue"]

    @property
    def magenta(self) -> str:
        return self.theme.loc["magenta"]

    @property
    def white(self) -> str:
        return self.theme.loc["white"]

    @property
    def black(self) -> str:
        return self.theme.loc["black"]

    @property
    def common(self) -> str:
        return self.theme.loc["common"]

    @property
    def mean(self) -> str:
        return self.theme.loc["mean"]

    @property
    def fg(self) -> str:
        return self.theme.loc["fg"]

    @property
    def bg(self) -> str:
        return self.theme.loc["bg"]

    @property
    def accent(self) -> str:
        return self.theme.loc["accent"]

    @property
    def secondary(self) -> str:
        return self.theme.loc["secondary"]

    @property
    def theme(self):
        if self._theme.empty:
            muted = ["white", "black"]
            for ref in self._ref.index:
                mode = self.MUTED if ref in muted else self.BRIGHT
                color = self._get_mixed(ref, bright_mode=mode)
                self._theme = self._theme.append(color)
            for special in [
                "common",
                "mean",
                "fg",
                "bg",
                "accent",
                "secondary",
            ]:
                self._theme = self._theme.append(self._get_special(special))
        return self._theme["hex"]

    def plot(self, mode="LUV", scale=30):
        x, y, z = list(mode)
        size = self.colors["count"] / self.colors["count"].mean() * scale
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        ax.scatter(
            self.colors[x],
            self.colors[y],
            self.colors[z],
            c=self.colors["hex"],
            s=size,
        )
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        ax.set_zlabel(z)

        plt.show()

    def save(self, fname="colors.txt"):
        with open(fname, "wt") as outfile:
            for color in self.theme.unique():
                outfile.write(color)
                outfile.write("\n")


def main(args: argparse.Namespace):
    theme = Themer(args.infile, p_mix=args.p_mix)
    pp(theme.theme)
    theme.save(args.outfile)


if __name__ == "__main__":
    ARGS = PARSER.parse_args()
    main(ARGS)
