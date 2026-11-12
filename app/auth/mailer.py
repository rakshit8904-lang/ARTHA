
"""
Email delivery for verification messages using Brevo HTTP API.
Verification happens only when the user opens the signed link.
"""

import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from flask import current_app
from app.errors import ServiceUnavailable


BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def is_configured():
    cfg = current_app.config
    api_key = cfg.get("BREVO_API_KEY") or os.environ.get("BREVO_API_KEY")
    sender = cfg.get("SMTP_FROM") or os.environ.get("SMTP_FROM")
    return bool(api_key and sender)


def send_email(to_address, subject, body):
    cfg = current_app.config

    api_key = cfg.get("BREVO_API_KEY") or os.environ.get("BREVO_API_KEY")
    sender = cfg.get("SMTP_FROM") or os.environ.get("SMTP_FROM")

    if not api_key or not sender:
        raise ServiceUnavailable("Brevo API email delivery is not configured")

    payload = {
        "sender": {
            "name": "Artha AI",
            "email": sender
        },
        "to": [
            {"email": to_address}
        ],
        "subject": subject,
        "textContent": body
    }

    request = Request(
        BREVO_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json"
        },
        method="POST"
    )

    try:
        with urlopen(request, timeout=20) as response:
            if response.status not in (200, 201, 202):
                raise ServiceUnavailable(
                    f"Brevo API returned unexpected status: {response.status}"
                )

    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        current_app.logger.exception("Brevo API email delivery failed")
        raise ServiceUnavailable("Email delivery failed") from exc
