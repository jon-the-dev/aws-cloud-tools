# AWS Cloud Utilities v2 Documentation

This directory contains the complete documentation for AWS Cloud Utilities v2, built with MkDocs and Material theme.

## Documentation Structure

```
docs/
├── index.md                    # Main documentation homepage
├── getting-started/           # Getting started guides
│   ├── installation.md       # Installation instructions
│   ├── quick-start.md        # Quick start guide
│   ├── configuration.md      # Configuration options
│   └── migration.md          # Migration from v1
├── commands/                  # Command documentation
│   ├── index.md              # Commands overview
│   ├── account.md            # Account commands
│   ├── costops.md            # Cost optimization commands
│   ├── security.md           # Security commands
│   ├── inventory.md          # Inventory commands
│   ├── logs.md               # Log management commands
│   ├── iam.md                # IAM commands
│   ├── support.md            # Support commands
│   └── ...                   # Other service commands
├── examples/                  # Usage examples
│   ├── common-use-cases.md   # Common usage patterns
│   ├── cost-optimization.md  # Cost optimization examples
│   ├── security-auditing.md  # Security audit examples
│   └── ...                   # Other examples
├── development/              # Development documentation
│   ├── contributing.md       # Contributing guide
│   ├── testing.md           # Testing guide
│   ├── architecture.md      # Architecture overview
│   └── api-reference.md     # API reference
└── reference/               # Reference documentation
    ├── cli.md               # Complete CLI reference
    ├── configuration.md     # Configuration reference
    ├── errors.md           # Error codes and handling
    └── changelog.md        # Version history
```

## Building Documentation

### Prerequisites

Install documentation dependencies:

```bash
pip install -r docs-requirements.txt
```

### Build and Serve

Use the provided script:

```bash
./docs-serve.sh
```

Or manually:

```bash
# Build documentation
mkdocs build

# Serve locally (with auto-reload)
mkdocs serve
```

The documentation will be available at: http://127.0.0.1:8000

### Build for Production

```bash
# Build static site
mkdocs build

# Output will be in site/ directory
ls site/
```

## Documentation Standards

### Writing Guidelines

1. **Clear and Concise**: Write in clear, simple language
2. **Examples**: Include practical examples for all commands
3. **Structure**: Use consistent heading structure
4. **Links**: Link between related documentation pages
5. **Code Blocks**: Use proper syntax highlighting

### Markdown Standards

- Use `#` for main headings, `##` for sections, `###` for subsections
- Use code blocks with language specification: ```bash
- Use tables for structured information
- Use admonitions for important notes: `!!! note`
- Use consistent formatting for commands and options

### Command Documentation Format

Each command should include:

```markdown
# Service Commands

Brief description of the service.

## Commands

### `command-name`

Brief command description.

```bash
aws-cloud-utilities service command-name [options]
```

**Options:**
- `--option` - Option description

**Examples:**
```bash
# Example usage
aws-cloud-utilities service command-name --option value
```

## Common Use Cases

### Use Case Name
```bash
# Example workflow
aws-cloud-utilities service command1
aws-cloud-utilities service command2
```
```

## Contributing to Documentation

### Adding New Documentation

1. **Create new file** in appropriate directory
2. **Follow naming convention**: lowercase with hyphens
3. **Update navigation** in `mkdocs.yml`
4. **Add cross-references** to related pages
5. **Test locally** before submitting

### Updating Existing Documentation

1. **Keep examples current** with latest CLI version
2. **Update screenshots** if UI changes
3. **Verify all links** work correctly
4. **Test code examples** to ensure they work

### Documentation Review Process

1. **Technical accuracy**: Ensure all commands and examples work
2. **Clarity**: Check that explanations are clear
3. **Completeness**: Verify all options and use cases are covered
4. **Consistency**: Maintain consistent style and format

## MkDocs Configuration

The site is configured in `mkdocs.yml`:

- **Theme**: Material Design theme
- **Plugins**: Search, mkdocstrings for API docs
- **Extensions**: Code highlighting, tables, admonitions
- **Navigation**: Hierarchical structure

### Key Features

- **Search**: Full-text search across all documentation
- **Dark/Light Mode**: Theme toggle
- **Mobile Responsive**: Works on all devices
- **Code Copying**: Click to copy code blocks
- **Navigation**: Expandable navigation tree

## Deployment

### GitHub Pages

The documentation can be deployed to GitHub Pages:

```bash
# Deploy to gh-pages branch
mkdocs gh-deploy
```

### Custom Domain

Configure custom domain in `mkdocs.yml`:

```yaml
site_url: https://your-domain.com/aws-cloud-tools/
```

## Maintenance

### Regular Updates

- **Keep examples current** with latest AWS services
- **Update screenshots** when UI changes
- **Review and update** getting started guides
- **Add new command documentation** as features are added

### Link Checking

Regularly check for broken links:

```bash
# Install link checker
pip install mkdocs-linkcheck

# Check links
mkdocs build --strict
```

## Troubleshooting

### Common Issues

1. **Build Errors**
   ```bash
   # Check for syntax errors
   mkdocs build --strict
   ```

2. **Missing Dependencies**
   ```bash
   # Reinstall requirements
   pip install -r docs-requirements.txt
   ```

3. **Navigation Issues**
   ```bash
   # Verify mkdocs.yml navigation structure
   mkdocs serve --verbose
   ```

### Getting Help

- Check MkDocs documentation: https://www.mkdocs.org/
- Material theme docs: https://squidfunk.github.io/mkdocs-material/
- Open issue in project repository

## Style Guide

### Voice and Tone

- **Professional but approachable**
- **Action-oriented** (use active voice)
- **User-focused** (address the reader directly)
- **Consistent terminology**

### Formatting

- **Commands**: Use `code` formatting
- **File paths**: Use `code` formatting
- **UI elements**: Use **bold** formatting
- **Emphasis**: Use *italic* sparingly
- **Important notes**: Use admonitions

### Code Examples

- **Complete examples**: Show full commands
- **Realistic data**: Use realistic (but fake) AWS resource names
- **Comments**: Explain complex examples
- **Output**: Show expected output when helpful

This documentation system provides comprehensive coverage of AWS Cloud Utilities v2 while maintaining high standards for clarity and usability.
