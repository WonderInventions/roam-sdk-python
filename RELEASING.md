# Releasing `roamhq`

Python packages publish to PyPI. Merging a regeneration PR does not publish.
Bump the version in `pyproject.toml`, merge, then publish.

## One-time setup

The PyPI name `roamhq` was free as of the first generation. Create the
project on pypi.org under the Wonder Inventions account, then either:

- configure trusted publishing (OIDC) for `WonderInventions/roam-sdk-python`
  and workflow `publish.yml`, or
- store a PyPI token as a repo secret and add a publish workflow.

## Cutting a release

1. Merge the "Regenerate SDK from OpenAPI spec" PR after setting the version
   in `pyproject.toml`.
2. Tag `vX.Y.Z` to match.
3. Publish the wheel (`python -m build && twine upload dist/*`, or the
   GitHub Action).
