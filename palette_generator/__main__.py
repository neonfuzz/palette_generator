from . import extract_colors
from . import gen_palette
from . import make_theme
from ._make_parser import make_parser


# Run the module.
PARSER = make_parser()
ARGS = PARSER.parse_args()
if ARGS.mode in ["extract_colors", "all"]:
    extract_colors.main(**vars(ARGS))
if ARGS.mode in ["make_theme", "all"]:
    make_theme.main(ARGS)
if ARGS.mode in ["gen_palette", "all"]:
    gen_palette.main(ARGS)
