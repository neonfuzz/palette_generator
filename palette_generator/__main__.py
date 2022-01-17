import argparse

from . import extract_colors
from . import gen_palette
from . import make_theme


def make_parser() -> argparse.ArgumentParser:
    """
    Make CLI parser which can call submodule parsers.

    Returns:
        argparse.ArgumentParser: said parser
    """
    parser = argparse.ArgumentParser()
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


# Run the module.
PARSER = make_parser()
ARGS = PARSER.parse_args()
if ARGS.mode in ["extract_colors", "all"]:
    extract_colors.main(**vars(ARGS))
if ARGS.mode in ["make_theme", "all"]:
    make_theme.main(ARGS)
if ARGS.mode in ["gen_palette", "all"]:
    gen_palette.main(ARGS)
