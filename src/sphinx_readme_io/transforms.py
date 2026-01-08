"""
Transformations for readme.io-compatible markdown output.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from docutils import nodes


def extract_title(doctree: nodes.document, docname: str) -> str:
    """
    Extract the page title from the document tree.
    
    Falls back to the document name if no title is found.
    """
    # Try to find a title node
    for node in doctree.findall():
        if node.tagname == "title":
            return node.astext()
    
    # Fall back to document name
    return docname.replace("/", " ").replace("-", " ").replace("_", " ").title()


def generate_slug(docname: str) -> str:
    """
    Generate a readme.io-compatible slug from the document name.
    
    readme.io slugs are lowercase with hyphens, no slashes.
    """
    # Replace path separators and underscores with hyphens
    slug = docname.replace("/", "-").replace("_", "-")
    # Convert to lowercase
    slug = slug.lower()
    # Remove any double hyphens
    slug = re.sub(r"-+", "-", slug)
    # Remove leading/trailing hyphens
    slug = slug.strip("-")
    return slug


def extract_excerpt(content: str, max_length: int = 200) -> str | None:
    """
    Extract the first paragraph as an excerpt.
    
    Skips any YAML frontmatter, headers, and empty lines.
    """
    lines = content.split("\n")
    in_code_block = False
    paragraph_lines = []
    
    for line in lines:
        # Skip code blocks
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        
        # Skip headers
        if line.strip().startswith("#"):
            # If we already have paragraph content, stop here
            if paragraph_lines:
                break
            continue
        
        # Skip empty lines
        if not line.strip():
            # If we already have paragraph content, this ends the paragraph
            if paragraph_lines:
                break
            continue
        
        # Skip markdown links that are on their own line (like badges)
        if re.match(r"^\s*\[.*\]\(.*\)\s*$", line):
            continue
        
        paragraph_lines.append(line.strip())
    
    if not paragraph_lines:
        return None
    
    excerpt = " ".join(paragraph_lines)
    
    # Truncate if too long
    if len(excerpt) > max_length:
        excerpt = excerpt[:max_length].rsplit(" ", 1)[0] + "..."
    
    return excerpt


def extract_document_metadata(
    doctree: nodes.document,
    passthrough_fields: set[str] | None = None,
) -> dict[str, Any]:
    """
    Extract metadata from document for frontmatter overrides.
    
    Supports two patterns:
    
    1. RST field lists with `readmeio-` prefix:
        :readmeio-hidden: true
        :readmeio-category: guides
    
    2. MyST Parser YAML frontmatter (passthrough fields):
        ---
        title: Custom Title
        hidden: true
        category: guides
        ---
    
    Args:
        doctree: The document tree
        passthrough_fields: Set of field names to pass through directly from
            document metadata (for MyST frontmatter support). If None, uses
            a default set of common readme.io fields.
    
    Returns:
        Dictionary of metadata fields to use as frontmatter overrides
    """
    if passthrough_fields is None:
        # Default fields that are commonly used in readme.io frontmatter
        # These will be passed through directly if found in document metadata
        passthrough_fields = {
            "title", "slug", "excerpt", "category", "hidden", "order",
            "parentDoc", "parentDocSlug", "type", "api", "next", "previous",
        }
    
    metadata = {}
    
    # Check document settings for metadata
    if hasattr(doctree, "settings") and hasattr(doctree.settings, "env"):
        env = doctree.settings.env
        if hasattr(env, "metadata") and env.docname in env.metadata:
            doc_metadata = env.metadata[env.docname]
            for key, value in doc_metadata.items():
                # Pattern 1: readmeio- prefixed fields (RST field lists)
                if key.startswith("readmeio-"):
                    field_name = key[9:]  # Remove 'readmeio-' prefix
                    metadata[field_name] = _parse_metadata_value(value)
                # Pattern 2: Direct passthrough fields (MyST frontmatter)
                elif key in passthrough_fields:
                    # MyST Parser may already have parsed the value to proper type
                    if isinstance(value, str):
                        metadata[key] = _parse_metadata_value(value)
                    else:
                        metadata[key] = value
    
    return metadata


def _parse_metadata_value(value: str) -> Any:
    """Parse a metadata string value into appropriate Python type."""
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.isdigit():
        return int(value)
    try:
        return float(value)
    except ValueError:
        pass
    return value


def format_yaml_value(value: Any) -> str:
    """Format a Python value for YAML output."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        # Escape quotes and wrap in quotes
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    # For other types, convert to string and quote
    return f'"{value}"'


def generate_frontmatter(fields: dict[str, Any]) -> str:
    """
    Generate YAML frontmatter from a dictionary of fields.
    
    Args:
        fields: Dictionary of frontmatter fields and values.
                Values of None are skipped.
    
    Returns:
        YAML frontmatter string including --- delimiters.
    """
    lines = ["---"]
    
    for key, value in fields.items():
        if value is None:
            continue
        formatted_value = format_yaml_value(value)
        lines.append(f"{key}: {formatted_value}")
    
    lines.append("---")
    lines.append("")  # Empty line after frontmatter
    
    return "\n".join(lines)


def strip_md_extension_from_links(content: str) -> str:
    """
    Remove .md extension from relative markdown links.
    
    readme.io resolves links without extensions, so we need to strip them.
    
    Transforms:
        [Link](./path/to/file.md) -> [Link](./path/to/file)
        [Link](path/to/file.md#anchor) -> [Link](path/to/file#anchor)
    
    Does not transform:
        [Link](https://example.com/file.md) - external URLs
        [Link](mailto:test@example.md) - non-http schemes
    """
    # Pattern to match markdown links: [text](url)
    # We want to strip .md from relative URLs only
    def replace_link(match: re.Match) -> str:
        text = match.group(1)
        url = match.group(2)
        
        # Skip external URLs (http://, https://, mailto:, etc.)
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", url):
            return match.group(0)
        
        # Strip .md extension (but preserve anchors)
        url = re.sub(r"\.md(#|$)", r"\1", url)
        
        return f"[{text}]({url})"
    
    # Match markdown links
    pattern = r"\[([^\]]*)\]\(([^)]+)\)"
    return re.sub(pattern, replace_link, content)


def build_frontmatter_fields(
    doctree: nodes.document,
    docname: str,
    content: str,
    default_frontmatter: dict[str, Any] | None = None,
    passthrough_fields: set[str] | None = None,
    auto_title: bool = True,
    auto_slug: bool = True,
    auto_excerpt: bool = True,
) -> dict[str, Any]:
    """
    Build the frontmatter fields dictionary with proper precedence.
    
    Precedence (highest to lowest):
    1. Per-document metadata:
       - RST field lists with :readmeio-*: prefix
       - MyST YAML frontmatter (passthrough fields)
    2. Default frontmatter from config
    3. Auto-generated values (title, slug, excerpt)
    
    Args:
        doctree: The document tree
        docname: The document name
        content: The markdown content (for excerpt extraction)
        default_frontmatter: Default frontmatter fields from config
        passthrough_fields: Set of field names to pass through from document
            metadata (for MyST frontmatter support)
        auto_title: Whether to auto-generate title
        auto_slug: Whether to auto-generate slug
        auto_excerpt: Whether to auto-generate excerpt
    
    Returns:
        Dictionary of frontmatter fields
    """
    fields: dict[str, Any] = {}
    
    # Layer 1: Auto-generated values (lowest precedence)
    if auto_title:
        fields["title"] = extract_title(doctree, docname)
    if auto_slug:
        fields["slug"] = generate_slug(docname)
    if auto_excerpt:
        fields["excerpt"] = extract_excerpt(content)
    
    # Layer 2: Default frontmatter from config
    if default_frontmatter:
        fields.update(default_frontmatter)
    
    # Layer 3: Per-document metadata (highest precedence)
    doc_metadata = extract_document_metadata(doctree, passthrough_fields)
    fields.update(doc_metadata)
    
    return fields


def transform_content(
    content: str,
    doctree: nodes.document,
    docname: str,
    add_frontmatter: bool = True,
    strip_md_links: bool = True,
    default_frontmatter: dict[str, Any] | None = None,
    passthrough_fields: set[str] | None = None,
) -> str:
    """
    Transform markdown content for readme.io compatibility.
    
    Args:
        content: The raw markdown content
        doctree: The document tree (for extracting title and metadata)
        docname: The document name (for generating slug)
        add_frontmatter: Whether to add YAML frontmatter
        strip_md_links: Whether to strip .md from links
        default_frontmatter: Default frontmatter fields (can be overridden per-document)
        passthrough_fields: Set of field names to pass through from document
            metadata (for MyST frontmatter support)
    
    Returns:
        Transformed markdown content
    """
    result = content
    
    # Strip .md from links
    if strip_md_links:
        result = strip_md_extension_from_links(result)
    
    # Add frontmatter
    if add_frontmatter:
        fields = build_frontmatter_fields(
            doctree=doctree,
            docname=docname,
            content=result,
            default_frontmatter=default_frontmatter,
            passthrough_fields=passthrough_fields,
        )
        frontmatter = generate_frontmatter(fields)
        result = frontmatter + result
    
    return result
