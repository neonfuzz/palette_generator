from datetime import date
import os
import sys
import toml


# Path setup.
sys.path.insert(0, os.path.abspath(".."))


# Read info from toml.
with open("../pyproject.toml", "rt", encoding="utf-8") as infile:
    config = toml.load(infile)


# Project information.
project = config["tool"]["poetry"]["name"]
author = config["tool"]["poetry"]["authors"][0]
copyright = f"{date.today().year}, {author}"
release = config["tool"]["poetry"]["version"]


# General configuration.
extensions = config["tool"]["sphinx"]["extensions"]
templates_path = config["tool"]["sphinx"]["templates_path"]
exclude_patterns = config["tool"]["sphinx"]["exclude_patterns"]


# Options for HTML output.
html_theme = config["tool"]["sphinx"]["html_theme"]
html_static_path = config["tool"]["sphinx"]["html_static_path"]
html_theme_options = config["tool"]["sphinx"]["html_theme_options"]
default_dark_mode = config["tool"]["sphinx"]["default_dark_mode"]
