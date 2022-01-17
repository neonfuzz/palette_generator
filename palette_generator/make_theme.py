#!/bin/env python3


"""
Create a 12-color theme from a pre-computed palette.

Classes:
    * :class:`Themer`: make a color theme from a palette

Functions:
    * :func:`main`: run the script
    * :func:`make_parser`: make the CLI parser
"""


import argparse
from typing import Tuple

import matplotlib.pyplot as plt
import pandas as pd
from scipy.spatial.distance import euclidean

from .convert_colors import cieluv_to_hex, hex_to_everything


def make_parser(
    parser: argparse.ArgumentParser = None,
) -> argparse.ArgumentParser:
    """
    Create a CLI parser.

    Args:
        parser (argparse.ArgumentParser): pre-existing parser to modify;
            default: `None`

    Returns:
        argparse.ArgumentParser: argument parser
    """
    descr = (
        "Read a palette of colors, and turn it into a cohesive  12-color "
        "scheme. Prints suggested theme to screen and saves HEX  codes to "
        "file."
    )
    if parser is None:
        parser = argparse.ArgumentParser(description=descr)
    else:
        parser.description = descr
    parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter
    parser.add_argument(
        "-hf",
        "--hist-file",
        default="color_hist.txt",
        help="each line is '{N}: {C}' where {N} in the number of counts of"
        " color {C}, which is provided as a HEX code. ",
    )
    parser.add_argument(
        "-cf",
        "--color-file",
        default="colors.json",
        help="Save curated color theme here. "
        "If extension is '.json', save as a one-line json with color "
        "names. OR each line is a unique theme color, provided as a HEX code. ",
    )
    parser.add_argument(
        "-p",
        "--p_mix",
        default=0.25,
        type=float,
        help="Percent to mix pure color in with image colors to get 'red', "
        "'yellow', 'green', 'cyan', 'blue', 'magenta', 'white', and 'black'. "
        "Recommend higher values for homogeneous images and lower values for "
        "heterogeneous images. Best results between 0.0 and 0.5. Use 0.0 for "
        "colors true only to image.",
    )
    return parser


_RGB = ["R", "G", "B"]
_HSV = ["hue", "sat", "val"]
_XYZ = ["X", "Y", "Z"]
_LUV = ["L", "U", "V"]


def _exclude(
    subset: pd.DataFrame,
    exclude: pd.Series,
    exclude_dist: float = 100.0,
) -> pd.DataFrame:
    """
    Exclude a color and its neighbors from a DataFrame.

    Args:
        subset (pd.DataFrame): DataFrame of colors
        exclude (pd.Series): color to exclude
        exclude_dist (float): colors within this distance of `exclude` will be
            excluded

    Returns:
        pd.DataFrame: `subset` with some colors excluded
    """
    dist = subset[_LUV].apply(euclidean, v=exclude[_LUV], axis=1)
    return subset[dist > exclude_dist]


class Themer:
    """
    Make a color theme.

    Args:
        fname (str): color histogram file; default: 'color_hist.txt'
        p_mix (float): percent to mix pure colors in with histogram colors;
            default: 0.25
    """

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
    _ALL = 0
    _BRIGHT = 1
    _MUTED = 2

    def __init__(self, fname: str = "color_hist.txt", p_mix: float = 0.25):
        """Initialize :class:`Themer`."""
        colors = pd.read_csv(fname)
        colors = colors.sort_values("count", ascending=False).reset_index(
            drop=True
        )
        #: colors loaded from `fname`
        self.colors = pd.merge(
            colors,
            hex_to_everything(colors["hex"]),
            left_on="hex",
            right_on="hex",
        )

        self._theme = pd.DataFrame()
        #: amount to mix pure colors with image colors
        self.p_mix = p_mix

    def _get_subset(self, bright_mode: int = 1) -> pd.DataFrame:
        """
        Get a subset of :attr:`self.colors`.

        Args:
            bright_mode (int): one of :attr:`self._BRIGHT`,
                :attr:`self._MUTED`, or :attr:`self._ALL`.
                'bright' colors are those where saturation and value are in
                the top half of all colors; default: :attr:`self._BRIGHT`

        Returns:
            pd.DataFrame: subset of :attr:`self.colors`
        """
        # 0 = all, 1 = bright only, 2 = muted
        if bright_mode == self._ALL:
            return self.colors
        if bright_mode == self._BRIGHT:
            return self.colors[
                (self.colors["sat"] > self.colors["sat"].quantile(0.5))
                & (self.colors["val"] > self.colors["val"].quantile(0.5))
            ]
        if bright_mode == self._MUTED:
            return self.colors[
                (self.colors["sat"] < self.colors["sat"].quantile(0.5))
                | (self.colors["val"] < self.colors["val"].quantile(0.5))
            ]
        raise ValueError(f"Unexpected value for `bright_mode`: {bright_mode}")

    def _measure(self, luv: Tuple[float, float, float], **kwargs) -> pd.Series:
        """
        Find the closest (or farthest) color from given.

        Args:
            luv (Tuple[float, float, float]): given color, in CIE-LUV space
            mode (Callable): how to measure distance;
                default: :func:`euclidean`
            bright_mode (int): one of :attr:`self._BRIGHT`,
                :attr:`self._MUTED`, or :attr:`self._ALL`.
                'bright' colors are those where saturation and value are in
                the top half of all colors; default: :attr:`self._BRIGHT`
            nearest (bool): if `True`, return closest color,
                else return farthest; default: `True`
            exclude (pd.Series): exclude this color and its neighbors
            exclude_dist (float): what is considered a neighbor for `exclude`

        Returns:
            pd.Series: color best-matching :meth:`_measure` parameters
        """
        mode = kwargs.pop("mode", euclidean)
        bright_mode = kwargs.pop("bright_mode", self._BRIGHT)
        nearest = kwargs.pop("nearest", True)
        exclude = kwargs.pop("exclude", None)
        exclude_dist = kwargs.pop("exclude_dist", 100.0)

        colors = self._get_subset(bright_mode)
        if exclude is not None:
            colors = _exclude(colors, exclude, exclude_dist)
        dist = colors[_LUV].apply(mode, v=luv, axis=1)
        if nearest:
            return colors.loc[dist.idxmin()]
        return colors.loc[dist.idxmax()]

    def _get_mixed(self, ref: str, **kwargs) -> pd.Series:
        """
        Get best represention of a color.

        Find the in-palette color closest to `ref` and mix it with the pure
        color according to :attr:`p_mix` proportion.

        Args:
            ref (str): reference color e.g., "red"

        Additional kwargs are passed to :meth:`_measure`

        Returns:
            pd.Series: best color, mixed with pure color
        """
        # All in LUV space.
        pure = self._ref.loc[ref][_LUV]
        base = self._measure(pure, **kwargs)[_LUV]
        mixed_luv = (1 - self.p_mix) * base + self.p_mix * pure

        # Now to everything.
        hex_code = cieluv_to_hex(mixed_luv)
        mixed = hex_to_everything(pd.Series([hex_code])).iloc[0]
        mixed.name = ref
        return mixed

    def _get_special(self, mode: str) -> pd.Series:
        """
        Get a specific theme color from the palette space.

        Args:
            mode (str): one of
                'common' = most commonly-used color
                'mean' = color closest to the mean of all colors (un-weighted)
                'bg' = alias of 'common'
                'fg' = muted color furthest from the most commonly-used color
                'accent' = most saturated color, excluding colors too close
                    to the most common color
                'secondary' = bright color furthest from 'accent', excluding
                    colors too close to the most common color

        Returns:
            pd.Series: the queried color
        """
        if mode == "common" or mode == "bg":
            color = self.colors.iloc[0]
        elif mode == "mean":
            color = self._measure(
                self.colors[_LUV].mean(), bright_mode=self._ALL
            )
        elif mode == "fg":
            color = self._measure(
                self.colors.iloc[0][_LUV],
                bright_mode=self._MUTED,
                nearest=False,
            )
        elif mode == "accent":
            try:
                subset = self._get_subset(self._BRIGHT)
                subset = _exclude(subset, exclude=self._theme.loc["bg"])
                color = self.colors.loc[subset["sat"].idxmax()]
            except KeyError as exc:
                # We should never get here, but just in case...
                raise ValueError(
                    "Must calculate 'bg' before 'accent'."
                ) from exc
        elif mode == "secondary":
            try:
                color = self._measure(
                    self._theme.loc["accent", _LUV],
                    bright_mode=self._BRIGHT,
                    nearest=False,
                    exclude=self._theme.loc["bg"],
                )
            except KeyError as exc:
                # We should never get here, but just in case...
                raise ValueError(
                    "Must calculate 'accent' and 'bg' before 'secondary'."
                ) from exc
        else:
            raise NotImplementedError(f"Mode '{mode}' not implemented.")
        color.name = mode
        return color

    @property
    def theme(self) -> pd.Series:
        """
        Calculate and return the best-calculated theme for the palette.

        Returns:
            pd.Series: hex codes for each theme color
        """
        if self._theme.empty:
            muted = ["white", "black"]
            for ref in self._ref.index:
                mode = self._MUTED if ref in muted else self._BRIGHT
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
        return self._theme["hex"].drop(["common", "mean"])

    def plot(self, mode: str = "LUV", scale: float = 30.0):
        """
        Plot the palette's colors, weighted by size.

        Args:
            mode (3-len str or iterable): which color space to use;
                default: 'LUV'
            scale (float): Degree by which to scale point size; default: 30.
        """
        # pylint: disable=invalid-name
        # 'x', 'y', and 'z' are well-understood.
        # 'ax' is commonly-used for matplotlib antics.
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

    def save(self, fname: str = "colors.json"):
        """
        Save the theme to file.

        Can save in json format or text/csv format.

        Args:
            fname (str): save path; will save in json format if `fname` ends
                with '.json', else in csv format; default: 'colors.json'
        """
        if fname.endswith(".json"):
            self.theme.to_json(fname)
        else:
            self.theme.to_csv(fname, index=False, header=False)


def main(args: argparse.Namespace):
    """
    Execute the :mod:`palette_generator.make_theme` script.

    Creates theme and saves it to file.

    Args:
        args (argparse.Namespace): arguments from running script in CLI
    """
    theme = Themer(args.hist_file, p_mix=args.p_mix)
    theme.save(args.color_file)


if __name__ == "__main__":
    PARSER = make_parser()
    ARGS = PARSER.parse_args()
    main(ARGS)
