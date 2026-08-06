# Claude AI Assistant Instructions

This document provides guidelines for Claude AI when working on this repository.

## Repository Overview

This is the AWS Cloud Utilities repository - a unified command-line toolkit for AWS operations. It includes various tools for cost optimization, inventory management, security auditing, and more.

## Documentation

The docs site is MkDocs Material, published to <https://jon-the-dev.github.io/aws-cloud-tools/>.

**The command reference is generated, not hand-written.** `docs/commands/*.md`, the services tables in
`docs/index.md` and `docs/commands/index.md`, and `docs/reference/cli.md` each contain regions marked
with `<!-- BEGIN GENERATED: ... -->` / `<!-- END GENERATED: ... -->`. Everything inside those markers
comes from `scripts/gen_docs.py`, which introspects the live Click tree. Edit the prose around them;
never edit inside them.

After changing any command, option, or help string:

```bash
make docs-gen     # regenerate the reference sections
make docs-check   # verify nothing drifted (also runs in CI)
```

`scripts/validate_docs.py` parses every `aws-cloud-utilities ...` example in `docs/` and fails if it
names a command group, subcommand, or option that does not exist. It also rejects global options
(`--profile`, `--region`, `--output`, `--verbose`, `--debug`, `--config`) written *after* the command
name, because Click rejects them there.

To show a deliberately-invalid example, put `validate-docs: ignore` on the line above it.

Both checks run in the `docs` job of `.github/workflows/ci.yml` and again before the Pages deploy.

## Git Workflow

1. Always work on feature branches (usually starting with `claude/`)
2. Commit with clear, descriptive messages
3. Push to the designated branch

## Code Standards

- Follow existing code style in the repository
- Add documentation for new scripts/features
- Update README.md when adding new functionality
- Include examples in documentation
- Docstrings on Click commands become user-facing `--help` text and flow into the generated docs.
  Write them accordingly, and keep the `Examples:` block in `aws_cloud_utilities/cli.py` valid.
