# sphinx-readme-io

A Sphinx extension to build documentation compatible with [readme.io](https://readme.com/).

## Features

- Generates Markdown files with YAML frontmatter
- Strips `.md` extensions from relative links (readme.io resolves links without extensions)
- Extracts page titles and slugs automatically
- Flexible frontmatter with configurable defaults and per-document overrides
- Supports [MyST Parser](https://myst-parser.readthedocs.io/) YAML frontmatter
- Built on top of [sphinx-markdown-builder](https://github.com/liran-funaro/sphinx-markdown-builder)

## Installation

```bash
pip install sphinx-readme-io
```

Or with uv:

```bash
uv add sphinx-readme-io
```

## Usage

Add the extension to your `conf.py`:

```python
extensions = [
    # ... other extensions ...
    "sphinx_readme_io",
]
```

Build your documentation:

```bash
sphinx-build -M readmeio ./docs ./build
```

Or using the builder directly:

```bash
sphinx-build -b readmeio ./docs ./build/readmeio
```

## Configuration

Add these options to your `conf.py`:

| Option | Default | Description |
|--------|---------|-------------|
| `readmeio_frontmatter` | `True` | Enable/disable YAML frontmatter generation |
| `readmeio_strip_md_links` | `True` | Strip `.md` extension from relative links |
| `readmeio_default_frontmatter` | `{}` | Default frontmatter fields (dict) |
| `readmeio_passthrough_fields` | `None` | Fields to pass through from document metadata |

### Default Frontmatter

You can set default frontmatter fields that apply to all documents:

```python
# conf.py
readmeio_default_frontmatter = {
    "category": "guides",
    "hidden": False,
    "order": 1,
    "author": "Documentation Team",
}
```

This can include **any key/value pairs** - not just readme.io standard fields. The defaults can also override auto-generated fields like `title`, `slug`, and `excerpt`:

```python
# Override auto-generated excerpt for all pages
readmeio_default_frontmatter = {
    "excerpt": "Official documentation",
}
```

### Per-Document Overrides

#### Option 1: RST Field Lists

For RST sources, use field lists with the `readmeio-` prefix:

```rst
:readmeio-hidden: true
:readmeio-category: advanced
:readmeio-custom-field: custom-value

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
readmeio_passthrough_fields = {
    "title", "slug", "hidden", "category", "my_custom_field"
}
```

### Precedence

Frontmatter values are resolved in this order (highest to lowest priority):

1. **Per-document metadata** (RST `:readmeio-*:` fields or MyST frontmatter)
2. **Default frontmatter** (`readmeio_default_frontmatter` config)
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
