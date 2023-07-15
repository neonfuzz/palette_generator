import argparse

from . import extract_colors
from . import gen_palette
from . import make_theme


def make_parser() -> argparse.ArgumentParser:
    """Make CLI parser which can call submodule parsers.

    Returns:
        argparse.ArgumentParser: said parser
    """
    parser = argparse.ArgumentParser(prog="python -m palette_generator")
    parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter
    subparsers = parser.add_subparsers(dest="mode")
    # extract_colors
    extract_sub = subparsers.add_parser("extract_colors")
    extract_colors.make_parser(extract_sub)
    # make_theme
    theme_sub = subparsers.add_parser("make_theme")
    make_theme.make_parser(theme_sub)
    # gen_palette
    gen_sub = subparsers.add_parser("gen_palette")
    gen_palette.make_parser(gen_sub)
    # all
    all_sub = subparsers.add_parser("all", conflict_handler="resolve")
    gen_palette.make_parser(all_sub)
    make_theme.make_parser(all_sub)
    extract_colors.make_parser(all_sub)
    all_sub.description = (
        "Run all three sub-programs [extract, theme, palette]"
    )
    return parser
