"""Transactional email via Resend, isolated so the provider can be swapped
without touching auth code.

Behaviour:
- With RESEND_API_KEY set: sends real email. The raw content (which may carry
  a reset token inside a link) is never logged; only recipient domain and the
  provider message id are.
- Without a key, in development only: logs the reset link so local dev works
  without a Resend account. Never enabled outside dev.
"""
from __future__ import annotations

import logging

from app.core.config import settings

log = logging.getLogger("musper.email")

BRAND_GREEN = "#1F4E3D"
BRAND_ORANGE = "#E07B1F"
BRAND_CREAM = "#F5F2EA"


class EmailNotConfigured(Exception):
    """Raised when no provider key is set and we are not in dev."""


def send_email(to: str, subject: str, html: str, text: str) -> str | None:
    """Send one email. Returns the provider message id, or None in dev fallback.

    Raises EmailNotConfigured outside development when no key is set. Any
    provider error is logged by type only and re-raised for the caller to
    decide; callers in enumeration-sensitive paths must swallow it.
    """
    if not settings.resend_api_key:
        if settings.is_dev:
            return None  # caller may use its own dev fallback
        raise EmailNotConfigured("RESEND_API_KEY is not set")

    import resend  # local import keeps the SDK out of test collection paths

    resend.api_key = settings.resend_api_key
    try:
        result = resend.Emails.send({
            "from": settings.email_from,
            "to": [to],
            "subject": subject,
            "html": html,
            "text": text,
        })
    except Exception as exc:
        # Log the failure class only; never the message content or the address
        # beyond its domain (content can contain tokens).
        domain = to.split("@")[-1] if "@" in to else "?"
        log.error("Email send failed (%s) to *@%s", type(exc).__name__, domain)
        raise
    message_id = (result or {}).get("id")
    log.info("Email sent to *@%s (id=%s)", to.split("@")[-1], message_id)
    return message_id


def _reset_html(first_name: str, reset_link: str, expiry_minutes: int) -> str:
    return f"""\
<div style="background:{BRAND_CREAM};padding:32px 16px;font-family:Georgia,'Times New Roman',serif;">
  <div style="max-width:520px;margin:0 auto;background:#ffffff;border-radius:16px;overflow:hidden;border:1px solid rgba(22,22,22,0.08);">
    <div style="background:{BRAND_GREEN};padding:20px 28px;">
      <span style="color:{BRAND_CREAM};font-size:18px;font-weight:600;">MusperSolutions</span>
    </div>
    <div style="padding:28px;color:#1a1a1a;font-size:15px;line-height:1.6;">
      <p style="margin:0 0 14px;">Hello {first_name},</p>
      <p style="margin:0 0 18px;">We received a request to reset the password on your MusperSolutions account. Click the button below to choose a new one.</p>
      <p style="margin:0 0 22px;text-align:center;">
        <a href="{reset_link}" style="background:{BRAND_ORANGE};color:#ffffff;text-decoration:none;padding:12px 28px;border-radius:999px;font-weight:600;display:inline-block;">Reset my password</a>
      </p>
      <p style="margin:0 0 8px;color:#6b6b6b;font-size:13px;">This link expires in {expiry_minutes} minutes and can be used once.</p>
      <p style="margin:0;color:#6b6b6b;font-size:13px;">If you did not request this, you can ignore this email. Your password will not change.</p>
    </div>
    <div style="padding:16px 28px;border-top:1px solid rgba(22,22,22,0.08);color:#9a9591;font-size:12px;">
      MusperSolutions Ltd · KN 12, Nyarugenge, Kigali, Rwanda
    </div>
  </div>
</div>"""


def _reset_text(first_name: str, reset_link: str, expiry_minutes: int) -> str:
    return (
        f"Hello {first_name},\n\n"
        "We received a request to reset the password on your MusperSolutions account.\n"
        f"Open this link to choose a new one:\n\n{reset_link}\n\n"
        f"The link expires in {expiry_minutes} minutes and can be used once.\n"
        "If you did not request this, ignore this email. Your password will not change.\n\n"
        "MusperSolutions Ltd, Kigali, Rwanda"
    )


def send_password_reset(user, reset_link: str) -> str | None:
    """Send the branded reset email. Returns provider id or None (dev fallback)."""
    first_name = (user.full_name or "there").split(" ")[0]
    minutes = settings.reset_token_ttl_minutes
    return send_email(
        to=user.email,
        subject="Reset your MusperSolutions password",
        html=_reset_html(first_name, reset_link, minutes),
        text=_reset_text(first_name, reset_link, minutes),
    )
