import os
import sys
sys.path.insert(0, os.path.abspath("../.."))  # Ensure your package is found

# Enable autodoc
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",  # Enables Google-style docstrings
    "sphinx.ext.viewcode",  # Adds links to source code
    "sphinx_rtd_theme",  # Enables the ReadTheDocs theme
]

# Set the ReadTheDocs theme
html_theme = "sphinx_rtd_theme"

# Ensure docstrings are included for all members
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}
