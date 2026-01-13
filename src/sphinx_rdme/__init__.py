"""
sphinx-rdme: A Sphinx extension to build documentation compatible with rdme.

This extension generates Markdown files with YAML frontmatter and rdme-compatible
links by extending sphinx-markdown-builder.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sphinx.application import Sphinx

__version__ = "0.1.0"


def setup(app: Sphinx) -> dict[str, Any]:
    """Set up the sphinx-rdme extension."""
    from sphinx_rdme.builder import rdmeBuilder

    app.add_builder(rdmeBuilder)

    # Configuration options for sphinx-rdme
    app.add_config_value("rdme_frontmatter", True, "env")
    app.add_config_value("rdme_strip_md_links", True, "env")
    # Default frontmatter fields - can include any key/value pairs
    # Example: {"category": "guides", "hidden": False, "order": 1}
    app.add_config_value("rdme_default_frontmatter", {}, "env")
    # Fields to pass through from document metadata (MyST frontmatter support)
    # Set to None to use defaults, or provide a custom set of field names
    app.add_config_value("rdme_passthrough_fields", None, "env")

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
