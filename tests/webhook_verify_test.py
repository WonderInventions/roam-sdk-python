"""Standard Webhooks signature verification as a consumer of roamhq.webhooks."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import sys
import time

import pytest

# Seed checkout has no generated package yet; regen installs roamhq.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from roamhq.webhooks import (  # noqa: E402
    WebhookVerificationError,
    verify_webhook,
    verify_webhook_signature,
)

MESSAGE_ID = "b0d9f6d2-1c3c-4a7e-9c1b-2d5e8f0a1b2c"
BODY = json.dumps({"eventId": MESSAGE_ID, "type": "chat.message"})


def mint_secret() -> tuple[str, bytes]:
    key = secrets.token_bytes(32)
    return "whsec_" + base64.b64encode(key).decode("ascii"), key


def sign(key: bytes, message_id: str, timestamp: str, body: str) -> str:
    digest = hmac.new(
        key, f"{message_id}.{timestamp}.{body}".encode("utf-8"), hashlib.sha256
    ).digest()
    return "v1," + base64.b64encode(digest).decode("ascii")


def now() -> str:
    return str(int(time.time()))


def headers_for(key: bytes, *, message_id: str = MESSAGE_ID, ts: str | None = None, body: str = BODY) -> dict[str, str]:
    ts = ts or now()
    return {
        "webhook-id": message_id,
        "webhook-timestamp": ts,
        "webhook-signature": sign(key, message_id, ts, body),
    }


def test_accepts_genuine_whsec_delivery() -> None:
    secret, key = mint_secret()
    verify_webhook_signature(BODY, headers_for(key), secret)


def test_accepts_secret_without_prefix() -> None:
    secret, key = mint_secret()
    verify_webhook_signature(BODY, headers_for(key), secret.removeprefix("whsec_"))


def test_rejects_tampered_body() -> None:
    secret, key = mint_secret()
    with pytest.raises(WebhookVerificationError):
        verify_webhook_signature(BODY + " ", headers_for(key), secret)


def test_accepts_second_of_two_signatures() -> None:
    secret, key = mint_secret()
    _, stale = mint_secret()
    ts = now()
    headers = {
        "webhook-id": MESSAGE_ID,
        "webhook-timestamp": ts,
        "webhook-signature": f"{sign(stale, MESSAGE_ID, ts, BODY)} {sign(key, MESSAGE_ID, ts, BODY)}",
    }
    verify_webhook_signature(BODY, headers, secret)


def test_replay_window() -> None:
    secret, key = mint_secret()
    current = time.time()
    ts = str(int(current))
    headers = headers_for(key, ts=ts)
    with pytest.raises(WebhookVerificationError, match="outside the 300s"):
        verify_webhook_signature(BODY, headers, secret, now=current + 400)
    verify_webhook_signature(BODY, headers, secret, now=current + 250)
    verify_webhook_signature(
        BODY, headers, secret, tolerance_in_seconds=600, now=current + 400
    )


def test_verify_returns_parsed_body() -> None:
    secret, key = mint_secret()
    event = verify_webhook(BODY, headers_for(key), secret)
    assert event["type"] == "chat.message"
