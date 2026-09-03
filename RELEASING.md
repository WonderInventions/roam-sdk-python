# Releasing `roamhq`

Python packages publish to PyPI. Merging a regeneration PR does not publish.
Bump the version in `pyproject.toml`, merge, tag `vX.Y.Z`, and let
`.github/workflows/publish.yml` upload the wheel.

Do not `twine upload` from a laptop. Publishing uses [trusted
publishing](https://docs.pypi.org/trusted-publishers/): GitHub Actions
proves its identity to PyPI. There is no API token in this repo.

## One-time setup

These steps are in the GitHub and PyPI UIs, not in git.

1. Create a [pypi.org](https://pypi.org/account/register/) account (work
   email) and turn on two-factor authentication. Prefer the Wonder
   Inventions org if it already exists.
2. In this GitHub repo: **Settings → Environments → New environment**,
   name it `pypi`. Optional: add yourself as a required reviewer so a
   tag push cannot publish without a click.
3. On PyPI, open
   [pending publishers](https://pypi.org/manage/account/publishing/)
   and add:

   | Field | Value |
   | --- | --- |
   | PyPI project name | `roamhq` |
   | Owner | `WonderInventions` |
   | Repository | `roam-sdk-python` |
   | Workflow name | `publish.yml` |
   | Environment name | `pypi` |

   The names must match this workflow and the GitHub environment exactly.
   The first successful upload creates the PyPI project.

`roamhq` was free on PyPI as of the first generation (`roam-sdk` is taken).

## Cutting a release

1. Merge the "Regenerate SDK from OpenAPI spec" PR after setting the
   version in `pyproject.toml`.
2. Tag `vX.Y.Z` to match (`git tag vX.Y.Z && git push origin vX.Y.Z`).
   That runs **Publish**.
3. If the environment requires a reviewer, approve the deployment.

The first `v0.1.0` tag already exists, so it will not retrigger on its
own. After this workflow is on `master`, publish that version with
**Actions → Publish → Run workflow**.

When it succeeds: https://pypi.org/project/roamhq/ and `pip install roamhq`.
