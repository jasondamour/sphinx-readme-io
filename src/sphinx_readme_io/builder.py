"""
Custom Sphinx builder for readme.io-compatible markdown output.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Set

from docutils import nodes
from docutils.io import StringOutput
from sphinx.locale import __
from sphinx.util import logging
from sphinx.util.osutil import ensuredir, os_path

from sphinx_markdown_builder.builder import MarkdownBuilder, io_handler
from sphinx_markdown_builder.writer import MarkdownWriter

from sphinx_readme_io.transforms import transform_content

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment

logger = logging.getLogger(__name__)


class ReadmeIOBuilder(MarkdownBuilder):
    """
    Sphinx builder that generates readme.io-compatible markdown files.
    
    Extends sphinx-markdown-builder to add:
    - YAML frontmatter with title, slug, excerpt
    - Stripped .md extensions from relative links
    """
    
    name = "readmeio"
    format = "markdown"
    epilog = __("The readme.io-compatible markdown files are in %(outdir)s.")
    
    def __init__(self, app: Sphinx, env: BuildEnvironment = None):
        super().__init__(app, env)
    
    def init(self):
        """Initialize the builder."""
        super().init()
        # Ensure we use .md suffix for output files
        self.out_suffix = ".md"
    
    def prepare_writing(self, docnames: Set[str]):
        """Prepare for writing documents."""
        self.writer = MarkdownWriter(self)
    
    def write_doc(self, docname: str, doctree: nodes.document):
        """
        Write a single document to a markdown file with readme.io compatibility.
        
        This overrides the parent method to add post-processing for:
        - YAML frontmatter
        - Link transformation
        """
        self.current_doc_name = docname
        self.sec_numbers = self.env.toc_secnumbers.get(docname, {})
        
        # Generate markdown content using the parent writer
        destination = StringOutput(encoding="utf-8")
        self.writer.write(doctree, destination)
        
        # Get the raw markdown output
        raw_content = self.writer.output
        
        # Get passthrough fields config (convert list to set if needed)
        passthrough_fields = self.config.readmeio_passthrough_fields
        if passthrough_fields is not None and not isinstance(passthrough_fields, set):
            passthrough_fields = set(passthrough_fields)
        
        # Transform content for readme.io compatibility
        transformed_content = transform_content(
            content=raw_content,
            doctree=doctree,
            docname=docname,
            add_frontmatter=self.config.readmeio_frontmatter,
            strip_md_links=self.config.readmeio_strip_md_links,
            default_frontmatter=self.config.readmeio_default_frontmatter,
            passthrough_fields=passthrough_fields,
        )
        
        # Write to output file
        out_filename = os.path.join(self.outdir, f"{os_path(docname)}{self.out_suffix}")
        ensuredir(os.path.dirname(out_filename))
        
        with io_handler(out_filename):
            with open(out_filename, "w", encoding="utf-8") as file:
                file.write(transformed_content)
        
        logger.debug("Wrote readme.io-compatible markdown: %s", out_filename)
