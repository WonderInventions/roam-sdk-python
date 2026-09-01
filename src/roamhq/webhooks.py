"""Standard Webhooks signature verification for Roam webhook deliveries.

HAND-WRITTEN. Listed in .fernignore — regenerate-sdks.yml replaces the rest
of this package with rsync --delete.

Why this exists rather than the generated helper: Fern's webhook signature
model has no way to describe how a signing secret is encoded. Roam issues
secrets as ``whsec_<base64>`` and keys the HMAC with the decoded bytes. The
generated helper keys with the UTF-8 bytes of the string, so it rejects
every genuine delivery.

See https://www.standardwebhooks.com/
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Mapping, Optional

DEFAULT_TOLERANCE_SECONDS = 300
SECRET_PREFIX = "whsec_"
SUPPORTED_VERSION = "v1"


class WebhookVerificationError(Exception):
    """Raised when a delivery cannot be verified. Treat as a 401."""


def verify_webhook(
    payload: bytes | str,
    headers: Mapping[str, str],
    secret: str,
    *,
    tolerance_in_seconds: int = DEFAULT_TOLERANCE_SECONDS,
    now: Optional[float] = None,
) -> Any:
    """Verify a delivery and return its parsed JSON body.

    ``payload`` must be the raw request body. Treat any exception as a 401.
    """
    verify_webhook_signature(
        payload, headers, secret, tolerance_in_seconds=tolerance_in_seconds, now=now
    )
    if isinstance(payload, bytes):
        text = payload.decode("utf-8")
    else:
        text = payload
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise WebhookVerificationError(
            f"signature is valid but the body is not JSON: {exc}"
        ) from exc


def verify_webhook_signature(
    payload: bytes | str,
    headers: Mapping[str, str],
    secret: str,
    *,
    tolerance_in_seconds: int = DEFAULT_TOLERANCE_SECONDS,
    now: Optional[float] = None,
) -> None:
    """Verify a delivery without parsing the body."""
    if isinstance(payload, str):
        payload_bytes = payload.encode("utf-8")
        payload_text = payload
    else:
        payload_bytes = payload
        payload_text = payload.decode("utf-8")

    message_id = _require_header(headers, "webhook-id")
    timestamp = _require_header(headers, "webhook-timestamp")
    signature_header = _require_header(headers, "webhook-signature")

    _assert_timestamp_is_fresh(timestamp, tolerance_in_seconds, now)

    key = _decode_secret(secret)
    expected = base64.b64encode(
        hmac.new(
            key,
            f"{message_id}.{timestamp}.{payload_text}".encode("utf-8"),
            hashlib.sha256,
        ).digest()
    ).decode("ascii")

    candidates = []
    for part in signature_header.split():
        if not part:
            continue
        if "," in part:
            version, sig = part.split(",", 1)
        else:
            version, sig = SUPPORTED_VERSION, part
        if version == SUPPORTED_VERSION:
            candidates.append(sig)

    if not candidates:
        raise WebhookVerificationError(
            f"no {SUPPORTED_VERSION} signature found in the webhook-signature header"
        )

    matched = False
    for sig in candidates:
        if hmac.compare_digest(sig, expected):
            matched = True
    if not matched:
        raise WebhookVerificationError(
            "webhook signature does not match the computed signature"
        )


def _decode_secret(secret: str) -> bytes:
    if not secret:
        raise WebhookVerificationError("signing secret is empty")
    encoded = secret[len(SECRET_PREFIX) :] if secret.startswith(SECRET_PREFIX) else secret
    try:
        key = base64.b64decode(encoded, validate=False)
    except Exception as exc:
        raise WebhookVerificationError(
            "signing secret did not base64-decode to any bytes; expected the "
            "whsec_… value from Roam Administration → Developer"
        ) from exc
    if not key:
        raise WebhookVerificationError(
            "signing secret did not base64-decode to any bytes; expected the "
            "whsec_… value from Roam Administration → Developer"
        )
    return key


def _assert_timestamp_is_fresh(
    timestamp: str, tolerance_in_seconds: int, now: Optional[float]
) -> None:
    try:
        sent = float(timestamp)
    except ValueError as exc:
        raise WebhookVerificationError(
            f"webhook-timestamp is not a number: {timestamp}"
        ) from exc
    current = time.time() if now is None else now
    skew = abs(current - sent)
    if skew > tolerance_in_seconds:
        raise WebhookVerificationError(
            f"webhook-timestamp is {round(skew)}s away from now, outside the "
            f"{tolerance_in_seconds}s tolerance"
        )


def _require_header(headers: Mapping[str, str], name: str) -> str:
    lower = name.lower()
    for key, value in headers.items():
        if key.lower() == lower:
            if value:
                return value
            break
    raise WebhookVerificationError(f"missing {name} header")
