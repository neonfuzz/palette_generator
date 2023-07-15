"""Tools for converting between color spaces.

Functions:
    * :func:`hex_to_rgb`: hexadecimal to rgb
    * :func:`rgb_to_hex`: rgb to hexadecimal
    * :func:`rgb_to_hsv`: rgb to hsv
    * :func:`rgb_to_xyz`: rgb to xyz
    * :func:`xyz_to_rgb`: xyz to rgb
    * :func:`xyz_to_cieluv`: xyz to cie-luv
    * :func:`cieluv_to_xyz`: cie-luv to xyz
    * :func:`cieluv_to_hex`: cie-luv to hexadecimal
    * :func:`hex_to_everything`: hexadecimal to, well, everything
"""

from typing import Tuple

import pandas as pd


# pylint: disable=invalid-name
# Though short, the names are well-understood.


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """Convert hexadecimal code to RGB space.

    Args:
        hex_code (str): hexadecimal

    Returns:
        Tuple[int, int, int]: RGB
    """
    hex_code = hex_code.strip("#")
    r = int(hex_code[:2], 16)
    g = int(hex_code[2:4], 16)
    b = int(hex_code[4:], 16)
    return r, g, b


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert RGB space to hexadecimal code.

    Args:
        rgb (Tuple[int, int, int]): RGB space

    Returns:
        str: hexadecimal code
    """
    return "#" + "".join([hex(c)[2:].upper().zfill(2) for c in rgb])


def rgb_to_hsv(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
    """Convert RGB space to HSV space.

    Args:
        rgb (Tuple[int, int, int]): RGB space

    Returns:
        Tuple[float, float, float]: HSV space
    """

    def delt_channel(vchannel):
        return (((vmax - vchannel) / 6) + (delt / 2)) / delt

    vr, vg, vb = [c / 255 for c in rgb]
    vmin, vmax = min(vr, vg, vb), max(vr, vg, vb)
    delt = vmax - vmin
    #  v = vmax
    if delt == 0:  # This is gray; no chroma.
        return 0, 0, vmax
    s = delt / vmax
    dr, dg, db = [delt_channel(c) for c in [vr, vg, vb]]
    if vr == vmax:
        h = db - dg
    elif vg == vmax:
        h = 1 / 3 + dr - db
    else:
        h = 2 / 3 + dg - dr

    h = h + 1 if h < 0 else h - 1
    return h, s, vmax


def _var_rgb(channel: int) -> float:
    """Help function for rgb->xyz."""
    channel_float = channel / 255
    if channel_float > 0.04045:
        return ((channel_float + 0.055) / 1.055) ** 2.4 * 100
    return channel_float / 12.92 * 100


def rgb_to_xyz(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
    """Convert RGB space to XYZ space.

    Args:
        rgb (Tuple[int, int, int]): RGB space

    Returns:
        Tuple[float, float, float]: XYZ space
    """
    vr, vg, vb = [_var_rgb(c) for c in rgb]
    x = vr * 0.4124 + vg * 0.3576 + vb * 0.1805
    y = vr * 0.2126 + vg * 0.7152 + vb * 0.0722
    z = vr * 0.0193 + vg * 0.1192 + vb * 0.9505
    return x, y, z


def _var_rgb_prime(var: float) -> int:
    """Help function for xyz->rgb."""
    if var > 0.0031308:
        out = round((1.055 * (var ** (1 / 2.4)) - 0.055) * 255)
    else:
        out = round(12.92 * var * 255)
    return min(out, 255)


def xyz_to_rgb(xyz: Tuple[float, float, float]) -> Tuple[int, int, int]:
    """Convert XYZ space to RGB space.

    Args:
        xyz (Tuple[float, float, float]): XYZ space

    Returns:
        Tuple[int, int, int]: RGB space
    """
    vx, vy, vz = [c / 100 for c in xyz]
    vr = 3.2406 * vx - 1.5372 * vy - 0.4986 * vz
    vg = -0.9689 * vx + 1.8758 * vy + 0.0415 * vz
    vb = 0.0557 * vx - 0.2040 * vy + 1.0570 * vz
    return _var_rgb_prime(vr), _var_rgb_prime(vg), _var_rgb_prime(vb)


def xyz_to_cieluv(xyz: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Convert XYZ space to CIE-LUV space.

    Args:
        xyz (Tuple[float, float, float]): XYZ space

    Returns:
        Tuple[float, float, float]: CIE-LUV space
    """
    x, y, z = xyz
    try:
        vu = (4 * x) / (x + (15 * y) + (3 * z))
    except ZeroDivisionError:
        vu = 0
    try:
        vv = (9 * y) / (x + (15 * y) + (3 * z))
    except ZeroDivisionError:
        vv = 0
    vy = (
        (y / 100) ** (1 / 3)
        if (y / 100) > 0.008856
        else (7.787 * (y / 100)) + (16 / 116)
    )
    cie_l = (116 * vy) - 16
    cie_u = 13 * cie_l * vu
    cie_v = 13 * cie_l * vv
    return cie_l, cie_u, cie_v


def cieluv_to_xyz(luv: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Convert CIE-LUV space to XYZ space.

    Args:
        luv (Tuple[float, float, float]): CIE-LUV space

    Returns:
        Tuple[float, float, float]: XYZ space
    """
    l, u, v = luv
    vy = (l + 16) / 116
    vy = vy**3 if vy**3 > 0.008856 else (vy - 16 / 116) / 7.787
    vu = 0 if l == 0 else u / (13 * l)
    vv = 0 if l == 0 else v / (13 * l)

    y = vy * 100
    x = 0.0 if vv == 0 else -(9 * y * vu) / ((vu - 4) * vv - vu * vv)
    z = 0.0 if vv == 0 else (9 * y - (15 * vv * y) - (vv * x)) / (3 * vv)
    return x, y, z


def cieluv_to_hex(luv: Tuple[float, float, float]) -> str:
    """Convert CIE-LUV space to hexadecimal code.

    Args:
        luv (Tuple[float, float, float]): CIE-LUV space

    Returns:
        str: hexadecimal code
    """
    xyz = cieluv_to_xyz(luv)
    rgb = xyz_to_rgb(xyz)
    return rgb_to_hex(rgb)


def hex_to_everything(hex_series: pd.Series) -> pd.DataFrame:
    """Convert many hexadecimal codes to all available color spaces.

    Args:
        hex_series (pd.Series): many hexadecimal codes

    Returns:
        pd.DataFrame: all color spaces in columns,
            with same index as `hex_series`
    """
    output = hex_series.copy()
    output.name = "hex"

    rgb = output.apply(hex_to_rgb).apply(pd.Series)
    rgb.columns = list("RGB")
    output = pd.merge(output, rgb, left_index=True, right_index=True)

    hsv = rgb.apply(rgb_to_hsv, axis=1).apply(pd.Series)
    hsv.columns = ["hue", "sat", "val"]
    output = pd.merge(output, hsv, left_index=True, right_index=True)

    xyz = rgb.apply(rgb_to_xyz, axis=1).apply(pd.Series)
    xyz.columns = list("XYZ")
    output = pd.merge(output, xyz, left_index=True, right_index=True)

    luv = xyz.apply(xyz_to_cieluv, axis=1).apply(pd.Series)
    luv.columns = list("LUV")
    output = pd.merge(output, luv, left_index=True, right_index=True)

    return output
