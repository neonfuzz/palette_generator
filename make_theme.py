#!/bin/env python3


from pprint import pp
from typing import Tuple

import matplotlib.pyplot as plt
import pandas as pd

from convert_colors import cieluv_to_hex, hex_to_everything


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

        self._theme = {
            "red": None,
            "yellow": None,
            "green": None,
            "cyan": None,
            "blue": None,
            "magenta": None,
            "white": None,
            "black": None,
            "common": None,
            "mean": None,
        }
        # TODO: refactor this as a DataFrame.
        self._mix = {}

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
        dist = ((colors[["L", "U", "V"]] - luv) ** 2).sum(axis=1).pow(0.5)
        if nearest:
            return colors.loc[dist.idxmin()]
        return colors.loc[dist.idxmax()]

    def _mix_color_with_ref(self, ref: str, p=0.2):
        if ref in self._mix:
            return self._mix[ref]["hex"]
        _ = self.theme
        color = self._theme[ref][["L", "U", "V"]]
        pure = self._ref.loc[ref][["L", "U", "V"]]
        mixed_luv = (1 - p) * color + p * pure
        hex_code = cieluv_to_hex(mixed_luv)
        mixed = hex_to_everything(pd.Series([hex_code])).iloc[0]
        self._mix[ref] = mixed
        return self._mix[ref]["hex"]

    def _get_from_ref(self, ref: str, **kwargs) -> str:
        if self._theme[ref] is not None:
            return self._theme[ref]["hex"]
        self._theme[ref] = self._measure(
            self._ref.loc[ref][["L", "U", "V"]], **kwargs
        )
        return self._theme[ref]["hex"]

    @property
    def red(self) -> str:
        return self._get_from_ref("red")

    @property
    def yellow(self) -> str:
        return self._get_from_ref("yellow")

    @property
    def green(self) -> str:
        return self._get_from_ref("green")

    @property
    def cyan(self) -> str:
        return self._get_from_ref("cyan")

    @property
    def blue(self) -> str:
        return self._get_from_ref("blue")

    @property
    def magenta(self) -> str:
        return self._get_from_ref("magenta")

    @property
    def white(self) -> str:
        return self._get_from_ref("white", bright_mode=self.ALL)

    @property
    def black(self) -> str:
        return self._get_from_ref("black", bright_mode=self.ALL)

    @property
    def common(self) -> str:
        if self._theme["common"] is not None:
            return self._theme["common"]["hex"]
        self._theme["common"] = self.colors.iloc[0]
        return self._theme["common"]["hex"]

    @property
    def mean(self) -> str:
        if self._theme["mean"] is not None:
            return self._theme["mean"]["hex"]
        com = (
            self.colors[["L", "U", "V"]]
            .mul(self.colors["count"], axis=0)
            .mean()
            / self.colors["count"].sum()
        )
        hex_code = cieluv_to_hex(com)
        color = hex_to_everything(pd.Series([hex_code])).iloc[0]
        self._theme["mean"] = color
        return self._theme["mean"]["hex"]

    # TODO: Maybe accent can be determined by looking at which theme color
    #       is furtherst from the mean of all the others? (leave one out)
    #   Can this^ be done with pairwise distance, and does that speed up
    #   the calculation?
    #   and/OR!!!: measure cosine distance from mean.
    #              scipy.spatial.distance.cosine
    #              foo[luv].apply(cosine, v=foo[luv].mean(), axis=1)
    @property
    def theme(self) -> dict:
        # Calculate all colors if they haven't been already.
        _ = self.red
        _ = self.yellow
        _ = self.green
        _ = self.cyan
        _ = self.blue
        _ = self.magenta
        _ = self.white
        _ = self.black
        _ = self.common
        _ = self.mean
        return {k: v.loc["hex"] for k, v in self._theme.items()}

    # TODO: Make this available through the api and hide `theme`.
    @property
    def mix(self) -> dict:
        # Mix pure colors with theme colors.
        if not self._mix:
            for ref in self._ref.index:
                _ = self._mix_color_with_ref(ref)
            self._mix['common'] = self._theme['common']
        return {k: v.loc['hex'] for k, v in self._mix.items()}

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

    def save(self, fname="colors.txt", mix=False):
        if mix:
            colors = set(self.mix.values())
        else:
            colors = set(self.theme.values())
        with open(fname, "wt") as outfile:
            for color in colors:
                outfile.write(color)
                outfile.write("\n")


# TODO: command line args
def main():
    theme = Themer()
    print('True colors:')
    pp(theme.theme)
    print('\nMixed colors:')
    pp(theme.mix)
    theme.save()
    theme.save('colors_mixed.txt', mix=True)


if __name__ == "__main__":
    main()
