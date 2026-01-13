"""
Transformations for rdme-compatible markdown output.
"""

from __future__ import annotations

import json
import re
from typing import Any

from docutils import nodes


def extract_title(doctree: nodes.document, docname: str) -> str:
    """
    Extract the page title from the document tree.

    Falls back to the document name if no title is found.
    """
    # Try to find a title node
    for node in doctree.findall(nodes.title):
        return node.astext()

    # Fall back to document name
    return docname.replace("/", " ").replace("-", " ").replace("_", " ").title()


def generate_slug(docname: str) -> str:
    """
    Generate a rdme-compatible slug from the document name.

    rdme slugs are lowercase with hyphens, no slashes.
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
    paragraph_lines: list[str] = []

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

    1. RST field lists with `rdme-` prefix:
        :rdme-hidden: true
        :rdme-category: guides

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
            a default set of common rdme fields.

    Returns:
        Dictionary of metadata fields to use as frontmatter overrides
    """
    if passthrough_fields is None:
        # Fields that match the ReadMe API for guides/docs
        # See: https://docs.readme.com/main/reference/createguide
        passthrough_fields = {
            # Required fields
            "title",  # string, required
            "category",  # object with uri
            # Optional fields
            "slug",  # string, URL slug for the page
            "content",  # object with body, excerpt
            "type",  # enum: api_config, basic, endpoint, link, webhook
            "state",  # enum: current, deprecated
            "position",  # number, ordering
            "order",  # number, alias for position
            "hidden",  # boolean, hide from sidebar
            "parent",  # object with uri
            "next",  # object
            "link",  # object for redirect pages
            "metadata",  # object
            "privacy",  # object
            "appearance",  # object
            "allow_crawlers",  # enum: enabled, disabled
        }

    metadata: dict[str, Any] = {}

    # Check document settings for metadata
    if hasattr(doctree, "settings") and hasattr(doctree.settings, "env"):
        env = doctree.settings.env
        if hasattr(env, "metadata") and env.docname in env.metadata:
            doc_metadata = env.metadata[env.docname]
            for key, value in doc_metadata.items():
                # Pattern 1: rdme- prefixed fields (RST field lists)
                if key.startswith("rdme-"):
                    field_name: str = key[5:]  # Remove 'rdme-' prefix (5 chars)
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
    # Try to parse as JSON (for nested dicts/lists serialized as strings)
    if value.startswith(("{", "[")):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
    return value


def format_yaml_value(value: Any) -> str | None:
    """Format a Python value for YAML output.
    
    Returns None for dicts and lists to signal they need block formatting.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        # Escape quotes and wrap in quotes
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(value, dict):
        # Return None to signal this needs block formatting
        return None
    if isinstance(value, list):
        # Return None to signal this needs block formatting
        return None
    # For other types, convert to string and quote
    return f'"{value}"'


def _format_yaml_nested(value: dict[str, Any] | list[Any], indent: int) -> list[str]:
    """Format nested YAML structures (dicts and lists) as lines."""
    lines: list[str] = []
    indent_str = "  " * indent

    if isinstance(value, dict):
        for k, v in value.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{indent_str}{k}:")
                lines.extend(_format_yaml_nested(v, indent + 1))
            else:
                formatted = format_yaml_value(v)
                lines.append(f"{indent_str}{k}: {formatted}")
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{indent_str}-")
                lines.extend(_format_yaml_nested(item, indent + 1))
            else:
                formatted = format_yaml_value(item)
                lines.append(f"{indent_str}- {formatted}")

    return lines


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

        if isinstance(value, (dict, list)):
            # Handle nested structures
            lines.append(f"{key}:")
            lines.extend(_format_yaml_nested(value, 1))
        else:
            formatted_value = format_yaml_value(value)
            lines.append(f"{key}: {formatted_value}")

    lines.append("---")
    lines.append("")  # Empty line after frontmatter

    return "\n".join(lines)


def strip_md_extension_from_links(content: str) -> str:
    """
    Remove .md extension from relative markdown links.

    rdme resolves links without extensions, so we need to strip them.

    Transforms:
        [Link](./path/to/file.md) -> [Link](./path/to/file)
        [Link](path/to/file.md#anchor) -> [Link](path/to/file#anchor)

    Does not transform:
        [Link](https://example.com/file.md) - external URLs
        [Link](mailto:test@example.md) - non-http schemes
    """

    # Pattern to match markdown links: [text](url)
    # We want to strip .md from relative URLs only
    def replace_link(match: re.Match[str]) -> str:
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


def rewrite_relative_links_with_slugs(
    content: str,
    current_docname: str,
    slug_map: dict[str, str],
) -> str:
    """
    Rewrite relative markdown links to use the target document's slug.

    This resolves links based on the slug defined in each target document's
    frontmatter, enabling custom URL slugs to work correctly in rdme.

    Transforms:
        [Link](auth.md) -> [Link](cli-auth)  (if auth.md has slug: cli-auth)
        [Link](./api/ref.md#section) -> [Link](api-reference#section)

    Does not transform:
        [Link](https://example.com/file.md) - external URLs
        [Link](mailto:test@example.md) - non-http schemes

    Args:
        content: The markdown content to transform
        current_docname: The docname of the current document (for resolving relative paths)
        slug_map: Mapping of docname -> slug for all documents

    Returns:
        Transformed content with links rewritten to use slugs
    """
    import os.path

    def replace_link(match: re.Match[str]) -> str:
        text = match.group(1)
        url = match.group(2)

        # Skip external URLs (http://, https://, mailto:, etc.)
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", url):
            return match.group(0)

        # Skip non-.md links (images, etc.)
        if not re.search(r"\.md(#|$)", url):
            return match.group(0)

        # Parse the URL to extract path and anchor
        anchor = ""
        if "#" in url:
            url_path, anchor = url.split("#", 1)
            anchor = "#" + anchor
        else:
            url_path = url

        # Remove .md extension
        if url_path.endswith(".md"):
            url_path = url_path[:-3]

        # Resolve the target docname relative to current document
        if url_path.startswith("./"):
            url_path = url_path[2:]

        # Get the directory of the current document
        current_dir = os.path.dirname(current_docname)

        # Resolve the target path relative to current document's directory
        if current_dir:
            target_docname = os.path.normpath(os.path.join(current_dir, url_path))
        else:
            target_docname = os.path.normpath(url_path)

        # Normalize path separators (Windows compatibility)
        target_docname = target_docname.replace("\\", "/")

        # Look up the slug for the target document
        if target_docname in slug_map:
            slug = slug_map[target_docname]
            return f"[{text}]({slug}{anchor})"

        # Fallback: just strip .md extension if target not in slug map
        return f"[{text}]({url_path}{anchor})"

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
       - RST field lists with :rdme-*: prefix
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
        # ReadMe API expects excerpt inside content object
        excerpt = extract_excerpt(content)
        if excerpt:
            fields["content"] = {"excerpt": excerpt}

    # Layer 2: Default frontmatter from config
    if default_frontmatter:
        _deep_merge(fields, default_frontmatter)

    # Layer 3: Per-document metadata (highest precedence)
    doc_metadata = extract_document_metadata(doctree, passthrough_fields)
    _deep_merge(fields, doc_metadata)

    return fields


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
    """
    Deep merge override dict into base dict.

    For nested dicts, merges recursively instead of replacing.
    This allows content.excerpt from doc to override auto-generated content.excerpt
    while preserving other content fields.
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            # Both are dicts, merge recursively
            base_dict: dict[str, Any] = base[key]
            override_dict: dict[str, Any] = value
            _deep_merge(base_dict, override_dict)
        else:
            base[key] = value


def transform_content(
    content: str,
    doctree: nodes.document,
    docname: str,
    add_frontmatter: bool = True,
    strip_md_links: bool = True,
    default_frontmatter: dict[str, Any] | None = None,
    passthrough_fields: set[str] | None = None,
    slug_map: dict[str, str] | None = None,
) -> str:
    """
    Transform markdown content for rdme compatibility.

    Args:
        content: The raw markdown content
        doctree: The document tree (for extracting title and metadata)
        docname: The document name (for generating slug)
        add_frontmatter: Whether to add YAML frontmatter
        strip_md_links: Whether to strip .md from links
        default_frontmatter: Default frontmatter fields (can be overridden per-document)
        passthrough_fields: Set of field names to pass through from document
            metadata (for MyST frontmatter support)
        slug_map: Mapping of docname -> slug for link rewriting. If provided,
            links will be rewritten to use the target document's slug.

    Returns:
        Transformed markdown content
    """
    result = content

    # Rewrite links: use slug map if provided, otherwise just strip .md
    if strip_md_links:
        if slug_map is not None:
            result = rewrite_relative_links_with_slugs(result, docname, slug_map)
        else:
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
