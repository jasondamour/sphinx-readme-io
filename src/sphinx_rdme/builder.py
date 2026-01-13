"""
Custom Sphinx builder for rdme-compatible markdown output.
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING, Callable, ClassVar, TypeVar

_F = TypeVar("_F", bound=Callable[..., object])

if sys.version_info >= (3, 12):
    from typing import override
else:

    def override(func: _F) -> _F:  # noqa: D103
        return func


from docutils import nodes
from docutils.io import StringOutput
from sphinx.locale import __
from sphinx.util import logging
from sphinx.util.osutil import ensuredir, os_path

from sphinx_markdown_builder.builder import MarkdownBuilder, io_handler  # pyright: ignore[reportMissingTypeStubs]
from sphinx_markdown_builder.writer import MarkdownWriter  # pyright: ignore[reportMissingTypeStubs]

from sphinx_rdme.transforms import generate_slug, transform_content

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment

logger = logging.getLogger(__name__)


class rdmeBuilder(MarkdownBuilder):
    """
    Sphinx builder that generates rdme-compatible markdown files.

    Extends sphinx-markdown-builder to add:
    - YAML frontmatter with title, slug, excerpt
    - Stripped .md extensions from relative links
    """

    name: ClassVar[str] = "rdme"
    format: ClassVar[str] = "markdown"
    epilog: ClassVar[str] = __("The rdme-compatible markdown files are in %(outdir)s.")

    # Instance attributes
    out_suffix: str
    writer: MarkdownWriter
    slug_map: dict[str, str]
    current_doc_name: str
    sec_numbers: dict[str, tuple[int, ...]]

    def __init__(self, app: Sphinx, env: BuildEnvironment | None = None) -> None:
        self.slug_map = {}
        super().__init__(app, env)  # pyright: ignore[reportArgumentType]

    @override
    def init(self) -> None:
        """Initialize the builder."""
        super().init()
        # Ensure we use .md suffix for output files
        self.out_suffix = ".md"

    @override
    def prepare_writing(self, docnames: set[str]) -> None:
        """Prepare for writing documents."""
        self.writer = MarkdownWriter(self)
        # Build a mapping of docname -> slug for link rewriting
        self.slug_map = self._build_slug_map(docnames)

    def _build_slug_map(self, docnames: set[str]) -> dict[str, str]:
        """
        Build a mapping from docname to final slug for all documents.

        This checks document metadata for explicit slug overrides,
        falling back to auto-generated slugs.
        """
        slug_map: dict[str, str] = {}
        for docname in docnames:
            # Check for explicit slug in document metadata
            explicit_slug: str | None = None
            if hasattr(self.env, "metadata") and docname in self.env.metadata:
                doc_metadata = self.env.metadata[docname]
                # Check for rdme-slug first (RST field list)
                if "rdme-slug" in doc_metadata:
                    explicit_slug = str(doc_metadata["rdme-slug"])
                # Then check for direct slug field (MyST frontmatter)
                elif "slug" in doc_metadata:
                    explicit_slug = str(doc_metadata["slug"])

            # Use explicit slug or generate one
            slug_map[docname] = (
                explicit_slug if explicit_slug else generate_slug(docname)
            )

        return slug_map

    @override
    def write_doc(self, docname: str, doctree: nodes.document) -> None:
        """
        Write a single document to a markdown file with rdme compatibility.

        This overrides the parent method to add post-processing for:
        - YAML frontmatter
        - Link transformation
        """
        self.current_doc_name = docname
        self.sec_numbers = self.env.toc_secnumbers.get(docname, {})

        # Set docname in temp_data so it's accessible during writing
        self.env.temp_data["docname"] = docname

        # Generate markdown content using the parent writer
        destination = StringOutput(encoding="utf-8")
        _ = self.writer.write(doctree, destination)

        # Get the raw markdown output (cast to str since output type is untyped)
        output = self.writer.output
        raw_content: str = str(output) if output else ""

        # Get passthrough fields config (convert list to set if needed)
        passthrough_fields: set[str] | None
        config_fields = self.config.rdme_passthrough_fields
        if config_fields is None:
            passthrough_fields = None
        elif isinstance(config_fields, set):
            passthrough_fields = config_fields
        else:
            passthrough_fields = set(config_fields)

        # Transform content for rdme compatibility
        transformed_content = transform_content(
            content=raw_content,
            doctree=doctree,
            docname=docname,
            add_frontmatter=self.config.rdme_frontmatter,
            strip_md_links=self.config.rdme_strip_md_links,
            default_frontmatter=self.config.rdme_default_frontmatter,
            passthrough_fields=passthrough_fields,
            slug_map=self.slug_map,
        )

        # Write to output file
        # Rename index.md to 00_index.md so it's created first when rdme runs alphabetically
        output_docname = os_path(docname)
        dirname, basename = os.path.split(output_docname)
        if basename == "index":
            output_docname = (
                os.path.join(dirname, "00_index") if dirname else "00_index"
            )
        out_filename = os.path.join(self.outdir, f"{output_docname}{self.out_suffix}")
        ensuredir(os.path.dirname(out_filename))

        with io_handler(out_filename):
            with open(out_filename, "w", encoding="utf-8") as file:
                _ = file.write(transformed_content)

        logger.debug("Wrote rdme-compatible markdown: %s", out_filename)
