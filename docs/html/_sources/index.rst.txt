
palette_generator
=================

.. toctree::
   :maxdepth: 1
   :caption: Contents:

`palette_generator` is here to turn your images into beautiful palettes.

About
-----

There are three pieces to `palette_generator`:
    * `extract_colors` finds the N (default 512) best colors which represent
      the image, and writes them to a color histogram file.
    * `make_theme` takes a color histogram file and tweaks it slightly into a
      12-color palette. This is intended for theming an operating system to
      match a wallpaper (so the color names are things like "cyan" and
      "magenta"), but in general does a bit better job at creating a diverse
      palette than `extract_colors` with N=12, so you can easily use it to
      tweak `extract_colors` for your own purposes.
    * Finally, `gen_palette` takes a color theme and puts swatches on a
      background image. This can be used for a generated theme from
      `make_theme`, or it can be a hand-curated list of hexadecimal codes.

All together, you put an image in, and get a palette automatically curated
and displayed nicely for you.

.. image:: images/bird.jpg
   :width: 350

.. image:: images/palette.png
   :width: 350

Installation
------------

.. code-block:: sh

    pip install .

Usage
-----

.. argparse::
   :module: palette_generator._make_parser
   :func: make_parser
   :prog: python -m palette_generator

Developer Documentation
=======================

.. autosummary::
   palette_generator.convert_colors
   palette_generator.extract_colors
   palette_generator.make_theme
   palette_generator.gen_palette


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
