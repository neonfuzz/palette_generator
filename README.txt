`extract_colors`
    img <-
    ncolors <-
    -> 'colors.txt'
    -> 'color_hist.txt'
    # TODO:
        probably just return hist, not 'colors.txt'
        can we pythonize this? it seems to work best with ncolors >= 512,
            but PIL can't handle that.
`make_theme.py`
    'color_hist.txt' <-
    -> 'colors.txt'
    # TODO:
        documentation
        output the hex column as a json (as well as? instead of?) unique hex codes
`gen_palette.py`
    img <-
    'colors.txt' <-
    -> 'palette.png'
    # TODO:
        documentation
        remove hard-coded path to font
        option to read in json and put color names in output
    # STRETCH
        text colors from theme
        option for one- vs two-column palette
