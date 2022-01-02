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
`palette`
    img <-
    'colors.txt' <-
    # TODO:
        dark colors with light text
        keep colors in order
    # STRETCH
        can we pythonize this?
        text colors from theme
