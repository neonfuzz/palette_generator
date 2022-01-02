#!/bin/env python3


from pprint import pp
from typing import Tuple

import matplotlib.pyplot as plt
import pandas as pd
from scipy.spatial.distance import cosine, euclidean

from convert_colors import cieluv_to_hex, hex_to_everything


_RGB = ["R", "G", "B"]
_HSV = ["hue", "sat", "val"]
_XYZ = ["X", "Y", "Z"]
_LUV = ["L", "U", "V"]


# TODO: fg, bg, accent, secondary
class Themer:
    _ref = hex_to_everything(
        pd.Series(
            {
                "red": "#FF0000",
                "yellow": "#FFFF00",
                "green": "#00FF00",
                "cyan": "#00FFFF",
                "blue": "#0000FF",
                "magenta": "#FF00FF",
                "white": "#FFFFFF",
                "black": "#000000",
            }
        )
    )
    ALL = 0
    BRIGHT = 1
    MUTED = 2

    def __init__(self, fname="color_hist.txt"):
        colors = pd.read_csv(
            fname, names=["count", "hex"], sep=": ", engine="python"
        )
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

    # TODO: allow for use of cosine
    def _measure(
        self,
        luv: Tuple[float, float, float],
        bright_mode: int = 1,  # 0 = all, 1 = bright only, 2 = muted
        nearest: bool = True,
    ):
        if bright_mode == self.ALL:
            colors = self.colors
        elif bright_mode == self.BRIGHT:
            colors = self.colors[
                (self.colors["sat"] > self.colors["sat"].quantile(0.5))
                & (self.colors["val"] > self.colors["val"].quantile(0.5))
            ]
        elif bright_mode == self.MUTED:
            colors = self.colors[
                (self.colors["sat"] < self.colors["sat"].quantile(0.5))
                | (self.colors["val"] < self.colors["val"].quantile(0.5))
            ]
        else:
            raise ValueError(
                f"Unexpected value for `bright_mode`: {bright_mode}"
            )
        dist = ((colors[_LUV] - luv) ** 2).sum(axis=1).pow(0.5)
        if nearest:
            return colors.loc[dist.idxmin()]
        return colors.loc[dist.idxmax()]

    def _get_mixed(self, ref, p=0.2, **kwargs):
        # All in LUV space.
        pure = self._ref.loc[ref][_LUV]
        base = self._measure(pure, **kwargs)[_LUV]
        mixed_luv = (1 - p) * base + p * pure

        # Now to everything.
        hex_code = cieluv_to_hex(mixed_luv)
        mixed = hex_to_everything(pd.Series([hex_code])).iloc[0]
        mixed.name = ref
        return mixed

    def _get_special(self, mode):
        if mode == "common":
            color = self.colors.iloc[0]
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
    def theme(self):
        if self._theme.empty:
            muted = ["white", "black"]
            for ref in self._ref.index:
                mode = self.MUTED if ref in muted else self.BRIGHT
                color = self._get_mixed(ref, bright_mode=mode)
                self._theme = self._theme.append(color)
            self._theme = self._theme.append(self._get_special("common"))
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


# TODO: command line args
def main():
    theme = Themer()
    pp(theme.theme)
    theme.save()
    theme.save("colors.txt")


if __name__ == "__main__":
    main()
