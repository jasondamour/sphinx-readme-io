"""
Tests for sphinx-readme-io builder.
"""

import pytest
from docutils import nodes
from docutils.parsers.rst import Parser
from docutils.utils import new_document
from docutils.frontend import OptionParser

from sphinx_readme_io.transforms import (
    extract_title,
    generate_slug,
    extract_excerpt,
    generate_frontmatter,
    format_yaml_value,
    build_frontmatter_fields,
    extract_document_metadata,
    strip_md_extension_from_links,
    transform_content,
    _parse_metadata_value,
)


class TestExtractTitle:
    """Tests for extract_title function."""

    def test_fallback_to_docname(self):
        """Test that docname is used when no title in document."""
        parser = Parser()
        settings = OptionParser(components=(Parser,)).get_default_values()
        doc = new_document("test", settings)
        
        result = extract_title(doc, "my-document")
        assert result == "My Document"

    def test_fallback_with_path(self):
        """Test that path separators are handled in docname fallback."""
        parser = Parser()
        settings = OptionParser(components=(Parser,)).get_default_values()
        doc = new_document("test", settings)
        
        result = extract_title(doc, "api/index")
        assert result == "Api Index"


class TestGenerateSlug:
    """Tests for generate_slug function."""

    def test_simple_name(self):
        """Test simple document name."""
        assert generate_slug("getting-started") == "getting-started"

    def test_with_path(self):
        """Test document name with path."""
        assert generate_slug("api/index") == "api-index"

    def test_with_underscores(self):
        """Test document name with underscores."""
        assert generate_slug("my_document") == "my-document"

    def test_uppercase(self):
        """Test uppercase is converted to lowercase."""
        assert generate_slug("MyDocument") == "mydocument"

    def test_nested_path(self):
        """Test deeply nested path."""
        assert generate_slug("docs/api/v2/reference") == "docs-api-v2-reference"


class TestExtractExcerpt:
    """Tests for extract_excerpt function."""

    def test_simple_paragraph(self):
        """Test extracting simple paragraph."""
        content = "# Title\n\nThis is the first paragraph.\n\nSecond paragraph."
        result = extract_excerpt(content)
        assert result == "This is the first paragraph."

    def test_skips_headers(self):
        """Test that headers are skipped."""
        content = "# Header\n## Subheader\n\nActual content here."
        result = extract_excerpt(content)
        assert result == "Actual content here."

    def test_skips_code_blocks(self):
        """Test that code blocks are skipped."""
        content = "```python\ncode here\n```\n\nActual paragraph."
        result = extract_excerpt(content)
        assert result == "Actual paragraph."

    def test_truncates_long_content(self):
        """Test that long content is truncated."""
        long_text = "This is a very long paragraph. " * 20
        content = f"# Title\n\n{long_text}"
        result = extract_excerpt(content, max_length=50)
        assert len(result) <= 53  # 50 + "..."
        assert result.endswith("...")

    def test_empty_content(self):
        """Test empty content returns None."""
        assert extract_excerpt("") is None
        assert extract_excerpt("# Just a header") is None


class TestParseMetadataValue:
    """Tests for _parse_metadata_value function."""

    def test_parses_true(self):
        """Test parsing 'true' string."""
        assert _parse_metadata_value("true") is True
        assert _parse_metadata_value("True") is True
        assert _parse_metadata_value("TRUE") is True

    def test_parses_false(self):
        """Test parsing 'false' string."""
        assert _parse_metadata_value("false") is False
        assert _parse_metadata_value("False") is False

    def test_parses_integers(self):
        """Test parsing integer strings."""
        assert _parse_metadata_value("42") == 42
        assert _parse_metadata_value("0") == 0

    def test_parses_floats(self):
        """Test parsing float strings."""
        assert _parse_metadata_value("3.14") == 3.14

    def test_keeps_strings(self):
        """Test that regular strings are kept as-is."""
        assert _parse_metadata_value("hello") == "hello"
        assert _parse_metadata_value("my-category") == "my-category"


class TestFormatYamlValue:
    """Tests for format_yaml_value function."""

    def test_formats_booleans(self):
        """Test formatting boolean values."""
        assert format_yaml_value(True) == "true"
        assert format_yaml_value(False) == "false"

    def test_formats_integers(self):
        """Test formatting integer values."""
        assert format_yaml_value(42) == "42"
        assert format_yaml_value(0) == "0"

    def test_formats_floats(self):
        """Test formatting float values."""
        assert format_yaml_value(3.14) == "3.14"

    def test_formats_strings(self):
        """Test formatting string values."""
        assert format_yaml_value("hello") == '"hello"'

    def test_escapes_quotes_in_strings(self):
        """Test that quotes in strings are escaped."""
        assert format_yaml_value('Say "hello"') == '"Say \\"hello\\""'


class TestGenerateFrontmatter:
    """Tests for generate_frontmatter function."""

    def test_basic_frontmatter(self):
        """Test basic frontmatter generation."""
        result = generate_frontmatter({"title": "My Title", "slug": "my-slug"})
        assert '---' in result
        assert 'title: "My Title"' in result
        assert 'slug: "my-slug"' in result

    def test_with_excerpt(self):
        """Test frontmatter with excerpt."""
        result = generate_frontmatter({
            "title": "Title",
            "slug": "slug",
            "excerpt": "Some description"
        })
        assert 'excerpt: "Some description"' in result

    def test_with_category(self):
        """Test frontmatter with category."""
        result = generate_frontmatter({
            "title": "Title",
            "slug": "slug",
            "category": "guides"
        })
        assert 'category: "guides"' in result

    def test_hidden_flag(self):
        """Test frontmatter with hidden flag."""
        result = generate_frontmatter({
            "title": "Title",
            "slug": "slug",
            "hidden": True
        })
        assert "hidden: true" in result

    def test_escapes_quotes(self):
        """Test that quotes in values are escaped."""
        result = generate_frontmatter({
            "title": "Title",
            "slug": "slug",
            "excerpt": 'Say "hello"'
        })
        assert 'excerpt: "Say \\"hello\\""' in result

    def test_skips_none_values(self):
        """Test that None values are skipped."""
        result = generate_frontmatter({
            "title": "Title",
            "slug": "slug",
            "excerpt": None,
            "category": None
        })
        assert "excerpt" not in result
        assert "category" not in result

    def test_arbitrary_fields(self):
        """Test that arbitrary fields are included."""
        result = generate_frontmatter({
            "title": "Title",
            "slug": "slug",
            "custom_field": "custom_value",
            "order": 5,
            "featured": True
        })
        assert 'custom_field: "custom_value"' in result
        assert "order: 5" in result
        assert "featured: true" in result


class MockEnv:
    """Mock Sphinx environment for testing document metadata extraction."""
    
    def __init__(self, docname: str, metadata: dict):
        self.docname = docname
        self.metadata = {docname: metadata}


class MockSettings:
    """Mock document settings with environment."""
    
    def __init__(self, env: MockEnv):
        self.env = env


def create_doc_with_metadata(docname: str, metadata: dict):
    """Create a document with mock metadata (simulating MyST frontmatter)."""
    parser = Parser()
    settings = OptionParser(components=(Parser,)).get_default_values()
    doc = new_document("test", settings)
    # Attach mock environment with metadata
    doc.settings.env = MockEnv(docname, metadata)
    return doc


class TestExtractDocumentMetadata:
    """Tests for extract_document_metadata function (passthrough frontmatter)."""

    def test_extracts_readmeio_prefixed_fields(self):
        """Test that readmeio- prefixed fields are extracted."""
        doc = create_doc_with_metadata("test-doc", {
            "readmeio-hidden": "true",
            "readmeio-category": "guides",
            "readmeio-order": "5",
        })
        
        result = extract_document_metadata(doc)
        
        assert result["hidden"] is True
        assert result["category"] == "guides"
        assert result["order"] == 5

    def test_extracts_passthrough_fields(self):
        """Test that default passthrough fields are extracted (MyST frontmatter)."""
        doc = create_doc_with_metadata("test-doc", {
            "title": "Custom Title",
            "hidden": True,
            "category": "advanced",
            "order": 10,
        })
        
        result = extract_document_metadata(doc)
        
        assert result["title"] == "Custom Title"
        assert result["hidden"] is True
        assert result["category"] == "advanced"
        assert result["order"] == 10

    def test_custom_passthrough_fields(self):
        """Test that custom passthrough fields can be specified."""
        doc = create_doc_with_metadata("test-doc", {
            "my_custom_field": "custom_value",
            "another_field": "another_value",
            "ignored_field": "should not appear",
        })
        
        # Only pass through specific fields
        result = extract_document_metadata(
            doc, 
            passthrough_fields={"my_custom_field", "another_field"}
        )
        
        assert result["my_custom_field"] == "custom_value"
        assert result["another_field"] == "another_value"
        assert "ignored_field" not in result

    def test_passthrough_parses_string_booleans(self):
        """Test that string boolean values are parsed correctly."""
        doc = create_doc_with_metadata("test-doc", {
            "hidden": "true",
            # Use a custom passthrough set to test the "featured" field
        })
        
        result = extract_document_metadata(doc)
        assert result["hidden"] is True
        
        # Test with custom passthrough to verify string parsing
        doc2 = create_doc_with_metadata("test-doc", {
            "featured": "false",
        })
        result2 = extract_document_metadata(doc2, passthrough_fields={"featured"})
        assert result2["featured"] is False

    def test_passthrough_preserves_native_types(self):
        """Test that native Python types are preserved (MyST Parser behavior)."""
        doc = create_doc_with_metadata("test-doc", {
            "hidden": True,  # Native bool, not string
            "order": 5,      # Native int, not string
        })
        
        result = extract_document_metadata(doc)
        
        assert result["hidden"] is True
        assert isinstance(result["hidden"], bool)
        assert result["order"] == 5
        assert isinstance(result["order"], int)

    def test_readmeio_prefix_takes_precedence(self):
        """Test that readmeio- prefixed fields override passthrough fields."""
        doc = create_doc_with_metadata("test-doc", {
            "category": "from-passthrough",
            "readmeio-category": "from-prefix",
        })
        
        result = extract_document_metadata(doc)
        
        # readmeio- prefix should override since it's processed after
        assert result["category"] == "from-prefix"

    def test_empty_passthrough_fields_set(self):
        """Test that empty passthrough set only extracts readmeio- prefixed fields."""
        doc = create_doc_with_metadata("test-doc", {
            "title": "Should be ignored",
            "category": "Also ignored",
            "readmeio-hidden": "true",
        })
        
        result = extract_document_metadata(doc, passthrough_fields=set())
        
        assert "title" not in result
        assert "category" not in result
        assert result["hidden"] is True

    def test_no_metadata_returns_empty_dict(self):
        """Test that missing metadata returns empty dict."""
        parser = Parser()
        settings = OptionParser(components=(Parser,)).get_default_values()
        doc = new_document("test", settings)
        # No env attached
        
        result = extract_document_metadata(doc)
        
        assert result == {}


class TestBuildFrontmatterFields:
    """Tests for build_frontmatter_fields function."""

    def test_auto_generates_fields(self):
        """Test that fields are auto-generated."""
        parser = Parser()
        settings = OptionParser(components=(Parser,)).get_default_values()
        doc = new_document("test", settings)
        
        content = "# My Title\n\nSome content here."
        result = build_frontmatter_fields(
            doctree=doc,
            docname="my-doc",
            content=content,
        )
        
        assert result["title"] == "My Doc"  # Falls back to docname
        assert result["slug"] == "my-doc"
        assert result["excerpt"] == "Some content here."

    def test_default_frontmatter_overrides_auto(self):
        """Test that default frontmatter overrides auto-generated values."""
        parser = Parser()
        settings = OptionParser(components=(Parser,)).get_default_values()
        doc = new_document("test", settings)
        
        content = "# My Title\n\nSome content."
        result = build_frontmatter_fields(
            doctree=doc,
            docname="my-doc",
            content=content,
            default_frontmatter={
                "title": "Custom Title",
                "category": "guides",
                "hidden": False,
            }
        )
        
        assert result["title"] == "Custom Title"  # Overridden
        assert result["slug"] == "my-doc"  # Auto-generated
        assert result["category"] == "guides"  # From defaults
        assert result["hidden"] is False  # From defaults

    def test_can_disable_auto_fields(self):
        """Test that auto-generation can be disabled."""
        parser = Parser()
        settings = OptionParser(components=(Parser,)).get_default_values()
        doc = new_document("test", settings)
        
        content = "# My Title\n\nSome content."
        result = build_frontmatter_fields(
            doctree=doc,
            docname="my-doc",
            content=content,
            auto_title=False,
            auto_excerpt=False,
        )
        
        assert "title" not in result
        assert result["slug"] == "my-doc"
        assert "excerpt" not in result


class TestStripMdExtension:
    """Tests for strip_md_extension_from_links function."""

    def test_simple_md_link(self):
        """Test stripping .md from simple link."""
        content = "[Link](file.md)"
        result = strip_md_extension_from_links(content)
        assert result == "[Link](file)"

    def test_md_link_with_anchor(self):
        """Test stripping .md from link with anchor."""
        content = "[Link](file.md#section)"
        result = strip_md_extension_from_links(content)
        assert result == "[Link](file#section)"

    def test_relative_path_link(self):
        """Test stripping .md from relative path link."""
        content = "[Link](../docs/file.md)"
        result = strip_md_extension_from_links(content)
        assert result == "[Link](../docs/file)"

    def test_preserves_external_urls(self):
        """Test that external URLs are not modified."""
        content = "[Link](https://example.com/file.md)"
        result = strip_md_extension_from_links(content)
        assert result == "[Link](https://example.com/file.md)"

    def test_preserves_http_urls(self):
        """Test that http URLs are not modified."""
        content = "[Link](http://example.com/file.md)"
        result = strip_md_extension_from_links(content)
        assert result == "[Link](http://example.com/file.md)"

    def test_multiple_links(self):
        """Test multiple links in same content."""
        content = "See [doc1](doc1.md) and [doc2](doc2.md#anchor)."
        result = strip_md_extension_from_links(content)
        assert result == "See [doc1](doc1) and [doc2](doc2#anchor)."

    def test_preserves_non_md_links(self):
        """Test that non-.md links are not modified."""
        content = "[Image](image.png)"
        result = strip_md_extension_from_links(content)
        assert result == "[Image](image.png)"


class TestTransformContent:
    """Tests for transform_content function."""

    def test_full_transform(self):
        """Test full content transformation."""
        parser = Parser()
        settings = OptionParser(components=(Parser,)).get_default_values()
        doc = new_document("test", settings)
        
        content = "# My Doc\n\nSome content with [link](other.md)."
        result = transform_content(
            content=content,
            doctree=doc,
            docname="my-doc",
            add_frontmatter=True,
            strip_md_links=True,
        )
        
        assert result.startswith("---")
        assert 'title: "My Doc"' in result
        assert 'slug: "my-doc"' in result
        assert "[link](other)" in result
        assert "[link](other.md)" not in result

    def test_without_frontmatter(self):
        """Test transformation without frontmatter."""
        parser = Parser()
        settings = OptionParser(components=(Parser,)).get_default_values()
        doc = new_document("test", settings)
        
        content = "# My Doc\n\nContent."
        result = transform_content(
            content=content,
            doctree=doc,
            docname="my-doc",
            add_frontmatter=False,
            strip_md_links=True,
        )
        
        assert not result.startswith("---")
        assert "# My Doc" in result

    def test_without_link_stripping(self):
        """Test transformation without link stripping."""
        parser = Parser()
        settings = OptionParser(components=(Parser,)).get_default_values()
        doc = new_document("test", settings)
        
        content = "# My Doc\n\nSee [link](other.md)."
        result = transform_content(
            content=content,
            doctree=doc,
            docname="my-doc",
            add_frontmatter=False,
            strip_md_links=False,
        )
        
        assert "[link](other.md)" in result

    def test_with_default_frontmatter(self):
        """Test transformation with default frontmatter."""
        parser = Parser()
        settings = OptionParser(components=(Parser,)).get_default_values()
        doc = new_document("test", settings)
        
        content = "# My Doc\n\nSome content."
        result = transform_content(
            content=content,
            doctree=doc,
            docname="my-doc",
            add_frontmatter=True,
            strip_md_links=True,
            default_frontmatter={
                "category": "guides",
                "hidden": False,
                "order": 1,
            }
        )
        
        assert result.startswith("---")
        assert 'category: "guides"' in result
        assert "hidden: false" in result
        assert "order: 1" in result

    def test_default_frontmatter_can_override_auto(self):
        """Test that default frontmatter can override auto-generated values."""
        parser = Parser()
        settings = OptionParser(components=(Parser,)).get_default_values()
        doc = new_document("test", settings)
        
        content = "# My Doc\n\nSome content."
        result = transform_content(
            content=content,
            doctree=doc,
            docname="my-doc",
            add_frontmatter=True,
            strip_md_links=True,
            default_frontmatter={
                "title": "Overridden Title",
                "slug": "custom-slug",
            }
        )
        
        assert 'title: "Overridden Title"' in result
        assert 'slug: "custom-slug"' in result

    def test_with_myst_style_frontmatter(self):
        """Test transformation with MyST-style YAML frontmatter passthrough."""
        # Simulate a document with MyST frontmatter metadata
        doc = create_doc_with_metadata("my-doc", {
            "title": "MyST Custom Title",
            "hidden": True,
            "category": "tutorials",
            "order": 3,
        })
        
        content = "# My Doc\n\nSome content."
        result = transform_content(
            content=content,
            doctree=doc,
            docname="my-doc",
            add_frontmatter=True,
            strip_md_links=True,
        )
        
        assert result.startswith("---")
        # Document metadata should override auto-generated title
        assert 'title: "MyST Custom Title"' in result
        assert "hidden: true" in result
        assert 'category: "tutorials"' in result
        assert "order: 3" in result

    def test_myst_frontmatter_overrides_defaults(self):
        """Test that per-document MyST frontmatter overrides config defaults."""
        doc = create_doc_with_metadata("my-doc", {
            "category": "from-document",
            "hidden": True,
        })
        
        content = "# My Doc\n\nSome content."
        result = transform_content(
            content=content,
            doctree=doc,
            docname="my-doc",
            add_frontmatter=True,
            strip_md_links=True,
            default_frontmatter={
                "category": "from-defaults",
                "hidden": False,
                "author": "Default Author",
            }
        )
        
        # Document metadata takes precedence over defaults
        assert 'category: "from-document"' in result
        assert "hidden: true" in result
        # Default values still apply for fields not in document metadata
        assert 'author: "Default Author"' in result

    def test_custom_passthrough_fields_in_transform(self):
        """Test custom passthrough fields in full transformation."""
        doc = create_doc_with_metadata("my-doc", {
            "my_custom": "value",
            "title": "Should Be Ignored",  # Not in custom passthrough
        })
        
        content = "# My Doc\n\nSome content."
        result = transform_content(
            content=content,
            doctree=doc,
            docname="my-doc",
            add_frontmatter=True,
            strip_md_links=True,
            passthrough_fields={"my_custom"},  # Only pass through this field
        )
        
        assert 'my_custom: "value"' in result
        # Title should be auto-generated since it's not in passthrough
        assert 'title: "My Doc"' in result
