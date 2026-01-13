# Configuration file for the Sphinx documentation builder.
import os
import sys

# Add the src directory to the path so we can import our extension
sys.path.insert(0, os.path.abspath("../../src"))

# -- Project information -----------------------------------------------------
project = "Test Project"
copyright = "2024, Test Author"
author = "Test Author"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx_rdme",
]

# Templates path
templates_path = ["_templates"]

# Patterns to exclude
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for sphinx-rdme --------------------------------------------
rdme_frontmatter = True
rdme_strip_md_links = True
rdme_default_frontmatter = {
    "category": "documentation",
    "hidden": False,
    "type": "basic",
}

# -- Options for sphinx-markdown-builder (inherited) -------------------------
markdown_http_base = ""
markdown_uri_doc_suffix = ".md"
