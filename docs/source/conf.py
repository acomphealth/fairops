import os
import subprocess
import sys
sys.path.insert(0, os.path.abspath("../.."))  # Ensure your package is found


# Auto-generate API documentation using sphinx-apidoc
def run_apidoc():
    """Automatically generate .rst files for API documentation"""
    module_path = os.path.abspath("../../fairops")
    output_path = os.path.abspath("./")
    ignore_paths = ["tests", "setup.py"]
    command = ["sphinx-apidoc", "-o", output_path, module_path] + ignore_paths
    subprocess.call(command)


run_apidoc()

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
