# Publishing to PyPI

This project publishes the `aws-cloud-utilities` package to PyPI through the
GitHub Actions workflow at `.github/workflows/publish.yml`.

The current package name is already present on PyPI:

- Package: `aws-cloud-utilities`
- Import package: `aws_cloud_utilities`
- Console scripts: `aws-cloud-utilities`, `awscu`
- Production project URL: <https://pypi.org/project/aws-cloud-utilities/>

PyPI does not allow replacing files for an existing version. If a release fails
after upload, keep the existing version immutable and publish the next patch
version instead.

## One-Time PyPI Setup

Production publishing uses PyPI trusted publishing. Configure the PyPI project
with a trusted publisher that matches this repository:

- PyPI project: `aws-cloud-utilities`
- GitHub owner: `jon-the-dev`
- GitHub repository: `aws-cloud-tools`
- Workflow filename: `publish.yml`
- Environment name: `pypi`

Optional TestPyPI dry runs use the same workflow with the `testpypi`
environment. Configure TestPyPI similarly if you want to verify publishing before
a production release.

No PyPI API token is needed when trusted publishing is configured correctly. The
workflow uses GitHub OIDC through `id-token: write`.

## Release Checklist

1. Confirm the version is not already on PyPI:

   ```bash
   python -m pip index versions aws-cloud-utilities
   ```

2. Update the version in:

   ```text
   pyproject.toml
   aws_cloud_utilities/__init__.py
   ```

3. Add a dated entry to `CHANGELOG.md`.

4. Validate locally:

   ```bash
   python -m pytest
   rm -rf dist build *.egg-info
   python -m build
   python -m twine check dist/*
   ```

5. Commit and push the release prep:

   ```bash
   git add pyproject.toml aws_cloud_utilities/__init__.py CHANGELOG.md docs/development/publishing.md mkdocs.yml README.md
   git commit -m "chore(release): prepare vX.Y.Z"
   git push origin main
   ```

6. Optional: publish to TestPyPI:

   ```bash
   gh workflow run publish.yml -f test_pypi=true
   gh run list --workflow publish.yml --limit 5
   ```

7. Create the production GitHub release. This creates the tag and triggers the
   PyPI publish workflow:

   ```bash
   gh release create vX.Y.Z \
     --target main \
     --title "vX.Y.Z" \
     --notes "See CHANGELOG.md for release notes."
   ```

8. Watch the publish workflow:

   ```bash
   gh run list --workflow publish.yml --limit 5
   gh run watch <run-id>
   gh run view <run-id> --log-failed
   ```

9. Verify PyPI:

   ```bash
   python -m pip index versions aws-cloud-utilities
   python -m pip install --upgrade aws-cloud-utilities
   aws-cloud-utilities --version
   ```

## Common Failures

- `Trusted publishing exchange failure`: the PyPI trusted publisher does not
  exactly match the GitHub owner, repository, workflow filename, and environment.
- `File already exists`: the version has already been uploaded. Bump to the next
  patch version and release again.
- GitHub environment approval required: approve the `pypi` environment in the
  Actions run, then let the job continue.
