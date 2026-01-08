"""
sphinx-readme-io: A Sphinx extension to build documentation compatible with readme.io.

This extension generates Markdown files with YAML frontmatter and readme.io-compatible
links by extending sphinx-markdown-builder.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sphinx.application import Sphinx

__version__ = "0.1.0"


def setup(app: Sphinx) -> dict:
    """Set up the sphinx-readme-io extension."""
    from sphinx_readme_io.builder import ReadmeIOBuilder

    app.add_builder(ReadmeIOBuilder)

    # Configuration options for sphinx-readme-io
    app.add_config_value("readmeio_frontmatter", True, "env")
    app.add_config_value("readmeio_strip_md_links", True, "env")
    # Default frontmatter fields - can include any key/value pairs
    # Example: {"category": "guides", "hidden": False, "order": 1}
    app.add_config_value("readmeio_default_frontmatter", {}, "env")
    # Fields to pass through from document metadata (MyST frontmatter support)
    # Set to None to use defaults, or provide a custom set of field names
    app.add_config_value("readmeio_passthrough_fields", None, "env")

    # Configuration options inherited from sphinx-markdown-builder
    # These are needed because we extend MarkdownBuilder
    app.add_config_value("markdown_http_base", "", "html", str)
    app.add_config_value("markdown_uri_doc_suffix", ".md", "html", str)
    app.add_config_value("markdown_file_suffix", ".md", "html", str)
    app.add_config_value("markdown_anchor_sections", False, "html", bool)
    app.add_config_value("markdown_anchor_signatures", False, "html", bool)
    app.add_config_value("markdown_docinfo", False, "html", bool)
    app.add_config_value("markdown_bullet", "*", "html", str)
    app.add_config_value("markdown_flavor", "", "html", str)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
