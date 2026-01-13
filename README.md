# sphinx-rdme

A Sphinx extension to build documentation compatible with [readme.io](https://readme.io/) via the [rdme cli](https://github.com/readmeio/rdme/).

## Features

- Generates Markdown files with YAML frontmatter
- Strips `.md` extensions from relative links (rdme resolves links without extensions)
- Extracts page titles and slugs automatically
- Flexible frontmatter with configurable defaults and per-document overrides
- Supports [MyST Parser](https://myst-parser.readthedocs.io/) YAML frontmatter
- Built on top of [sphinx-markdown-builder](https://github.com/liran-funaro/sphinx-markdown-builder)

## Installation

```bash
pip install sphinx-rdme
```

Or with uv:

```bash
uv add sphinx-rdme
```

## Usage

Add the extension to your `conf.py`:

```python
extensions = [
    # ... other extensions ...
    "sphinx_rdme",
]
```

Build your documentation:

```bash
sphinx-build -M rdme ./docs ./build
```

Or using the builder directly:

```bash
sphinx-build -b rdme ./docs ./build/rdme
```

## Configuration

Add these options to your `conf.py`:

| Option | Default | Description |
|--------|---------|-------------|
| `rdme_frontmatter` | `True` | Enable/disable YAML frontmatter generation |
| `rdme_strip_md_links` | `True` | Strip `.md` extension from relative links |
| `rdme_default_frontmatter` | `{}` | Default frontmatter fields (dict) |
| `rdme_passthrough_fields` | `None` | Fields to pass through from document metadata |

### Default Frontmatter

You can set default frontmatter fields that apply to all documents:

```python
# conf.py
rdme_default_frontmatter = {
    "category": "guides",
    "hidden": False,
    "order": 1,
    "author": "Documentation Team",
}
```

This can include **any key/value pairs** - not just rdme standard fields. The defaults can also override auto-generated fields like `title`, `slug`, and `excerpt`:

```python
# Override auto-generated excerpt for all pages
rdme_default_frontmatter = {
    "excerpt": "Official documentation",
}
```

### Per-Document Overrides

#### Option 1: RST Field Lists

For RST sources, use field lists with the `rdme-` prefix:

```rst
:rdme-hidden: true
:rdme-category: advanced
:rdme-custom-field: custom-value

My Document Title
=================

Content here...
```

#### Option 2: MyST Parser YAML Frontmatter

If you're using [MyST Parser](https://myst-parser.readthedocs.io/) for Markdown sources, you can use YAML frontmatter directly in your `.md` files:

```markdown
---
title: Custom Title
hidden: true
category: advanced
order: 5
---

# My Document

Content here...
```

By default, the following fields are passed through from MyST frontmatter:
- `title`, `slug`, `excerpt`, `category`, `hidden`, `order`
- `parentDoc`, `parentDocSlug`, `type`, `api`, `next`, `previous`

To customize which fields are passed through:

```python
# conf.py
rdme_passthrough_fields = {
    "title", "slug", "hidden", "category", "my_custom_field"
}
```

### Precedence

Frontmatter values are resolved in this order (highest to lowest priority):

1. **Per-document metadata** (RST `:rdme-*:` fields or MyST frontmatter)
2. **Default frontmatter** (`rdme_default_frontmatter` config)
3. **Auto-generated values** (title, slug, excerpt)

## Output Format

Generated Markdown files include YAML frontmatter:

```yaml
---
title: "Page Title"
slug: "page-slug"
excerpt: "First paragraph of the page"
category: "guides"
hidden: false
---

# Page Title

Content here...
```

## License

MIT License - see [LICENSE](LICENSE) for details.
