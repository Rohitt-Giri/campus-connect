# payments/email_utils.py
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django.utils import timezone


def _site_url(path: str) -> str:
    base = getattr(settings, "SITE_URL", "http://127.0.0.1:8000").rstrip("/")
    return f"{base}{path}"


def _send(to_email: str, subject: str, text_body: str, html_body: str) -> None:
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", "")
    msg = EmailMultiAlternatives(subject, text_body, from_email, [to_email])
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)


def _user_email(user) -> str:
    return (getattr(user, "email", "") or "").strip()


def _user_name(user) -> str:
    try:
        name = (user.get_full_name() or "").strip()
    except Exception:
        name = ""
    return name or (getattr(user, "username", "") or "there")


def send_payment_received_email(proof) -> bool:
    """
    When a student uploads proof -> email: "we received it, pending review"
    """
    reg = proof.registration
    user = reg.user
    email = _user_email(user)
    if not email:
        return False

    site = getattr(settings, "SITE_NAME", "Campus Connect")
    name = _user_name(user)
    event = reg.event

    event_url = _site_url(reverse("events:detail", kwargs={"pk": event.id}))
    time_str = ""
    if getattr(proof, "submitted_at", None):
        time_str = timezone.localtime(proof.submitted_at).strftime("%b %d, %Y %I:%M %p")

    subject = f"{site}: Payment proof received ✅ (Pending review)"
    headline = "Payment proof received ✅"
    accent = "#0ea5e9"
    msg = "We received your payment proof. Staff will review it soon."

    submitted_text = f"Submitted at: {time_str}" if time_str else ""
    submitted_html = f"<b>Submitted at:</b> {time_str}<br>" if time_str else ""

    text_body = f"""Hi {name},

{msg}

Event: {event.title}
Status: PENDING
{submitted_text}

View event:
{event_url}

— {site}
"""

    html_body = f"""
<!doctype html><html><body style="margin:0;background:#f6f8fb;font-family:Arial;color:#0f172a;">
<div style="max-width:600px;margin:0 auto;padding:24px 14px;">
  <div style="background:#fff;border:1px solid rgba(15,23,42,.10);border-radius:16px;padding:18px;">
    <div style="font-size:18px;font-weight:900;color:{accent};margin-bottom:8px;">{headline}</div>
    <div style="font-size:14px;line-height:1.65;color:#334155;">
      Hi <b>{name}</b>,<br><br>
      {msg}<br><br>
      <b>Event:</b> {event.title}<br>
      <b>Status:</b> PENDING<br>
      {submitted_html}
      <div style="margin-top:16px;">
        <a href="{event_url}" style="display:inline-block;background:{accent};color:#fff;text-decoration:none;
          padding:10px 14px;border-radius:999px;font-weight:900;">View event</a>
      </div>
    </div>
  </div>
  <div style="text-align:center;margin-top:10px;font-size:12px;color:#94a3b8;">© {site}</div>
</div>
</body></html>
"""
    _send(email, subject, text_body, html_body)
    return True


def send_payment_status_email(proof) -> bool:
    """
    When staff approves/rejects -> email student.
    proof.status should be approved/rejected
    """
    reg = proof.registration
    user = reg.user
    email = _user_email(user)
    if not email:
        return False

    status = (getattr(proof, "status", "") or "").lower()
    if status not in {"approved", "rejected"}:
        return False

    site = getattr(settings, "SITE_NAME", "Campus Connect")
    name = _user_name(user)
    event = reg.event
    event_url = _site_url(reverse("events:detail", kwargs={"pk": event.id}))

    if status == "approved":
        subject = f"{site}: Payment approved ✅"
        headline = "Payment approved ✅"
        accent = "#16a34a"
        msg = "Your payment has been approved. Your registration is now confirmed."
    else:
        subject = f"{site}: Payment rejected ❌"
        headline = "Payment rejected ❌"
        accent = "#dc2626"
        msg = "Your payment was rejected. Please re-upload a clear proof of payment."

    # If rejected, include the "re-upload" link
    pay_url = _site_url(reverse("payments:submit", kwargs={"registration_id": reg.id}))

    # staff note (safe)
    note = (getattr(proof, "staff_note", "") or "").strip()
    note_text = f"\nStaff note: {note}\n" if note else ""
    note_html = f"<b>Staff note:</b> {note}<br>" if note else ""

    reupload_text = f"\nRe-upload payment proof:\n{pay_url}\n" if status == "rejected" else ""
    reupload_btn_html = ""
    if status == "rejected":
        reupload_btn_html = f"""
        <a href="{pay_url}" style="display:inline-block;background:#0f172a;color:#fff;text-decoration:none;
          padding:10px 14px;border-radius:999px;font-weight:900;">Re-upload proof</a>
        """

    text_body = f"""Hi {name},

{msg}

Event: {event.title}
Status: {status.upper()}{note_text}

View event:
{event_url}{reupload_text}

— {site}
"""

    html_body = f"""
<!doctype html><html><body style="margin:0;background:#f6f8fb;font-family:Arial;color:#0f172a;">
<div style="max-width:600px;margin:0 auto;padding:24px 14px;">
  <div style="background:#fff;border:1px solid rgba(15,23,42,.10);border-radius:16px;padding:18px;">
    <div style="font-size:18px;font-weight:900;color:{accent};margin-bottom:8px;">{headline}</div>
    <div style="font-size:14px;line-height:1.65;color:#334155;">
      Hi <b>{name}</b>,<br><br>
      {msg}<br><br>
      <b>Event:</b> {event.title}<br>
      <b>Status:</b> {status.upper()}<br>
      {note_html}

      <div style="margin-top:16px;display:flex;gap:10px;flex-wrap:wrap;">
        <a href="{event_url}" style="display:inline-block;background:{accent};color:#fff;text-decoration:none;
          padding:10px 14px;border-radius:999px;font-weight:900;">View event</a>

        {reupload_btn_html}
      </div>
    </div>
  </div>
  <div style="text-align:center;margin-top:10px;font-size:12px;color:#94a3b8;">© {site}</div>
</div>
</body></html>
"""
    _send(email, subject, text_body, html_body)
    return True