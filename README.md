# roamhq

Official Python SDK for the [Roam API](https://developer.ro.am).

```bash
pip install roamhq
```

Requires **Python 3.10+**.

```python
import os
from roamhq import RoamClient

client = RoamClient(token=os.environ["ROAM_TOKEN"])

result = client.chat.post(
    group_id="88bebce7-6cbb-4666-96f9-5c02d73e6661",
    text="Build completed successfully!",
)
```

Full usage — pagination, retries, error handling, version pinning — is in the
[SDK guide](https://developer.ro.am/docs/guides/sdks). The
[API reference](https://developer.ro.am/docs/api/api) documents every endpoint.

## Verifying webhooks

```python
from roamhq.webhooks import verify_webhook

event = verify_webhook(body, request.headers, os.environ["ROAM_WEBHOOK_SECRET"])
```

`body` must be the **raw request bytes**. Treat any exception as a `401`. Pass
the signing secret exactly as Roam issued it, `whsec_` prefix included.

This is the one part of the SDK that is hand-written rather than generated. See
[`src/roamhq/webhooks.py`](src/roamhq/webhooks.py) for why.

## This repository is mostly generated

The client and types are generated from the Roam OpenAPI specification by
[Fern](https://buildwithfern.com). **Do not edit them by hand** — the next
regeneration will overwrite them.

A change to the spec opens or updates a single long-lived pull request here
titled "Regenerate SDK from OpenAPI spec". A human reviews the diff, picks the
semantic-version bump in `pyproject.toml`, and merges. Merging does not
publish to PyPI.

Everything listed in [`.fernignore`](.fernignore) is hand-maintained.
