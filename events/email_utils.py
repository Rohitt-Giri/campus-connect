from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django.utils import timezone


def _site_url(path: str) -> str:
    base = getattr(settings, "SITE_URL", "http://127.0.0.1:8000").rstrip("/")
    return f"{base}{path}"


def _user_email(user) -> str:
    return (getattr(user, "email", "") or "").strip()


def _user_name(user) -> str:
    try:
        n = (user.get_full_name() or "").strip()
    except Exception:
        n = ""
    return n or (getattr(user, "username", "") or "there")


def send_event_registration_email(reg) -> bool:
    """
    Email student after successful event registration.
    If event is paid -> includes Upload Payment Proof link.
    """
    user = reg.user
    event = reg.event

    email = _user_email(user)
    if not email:
        return False

    site = getattr(settings, "SITE_NAME", "Campus Connect")
    name = _user_name(user)

    event_url = _site_url(reverse("events:detail", kwargs={"pk": event.id}))

    # Nice readable date/time
    try:
        start_local = timezone.localtime(event.start_datetime).strftime("%b %d, %Y • %I:%M %p")
    except Exception:
        start_local = ""

    location = (getattr(event, "location", "") or "").strip()

    # Paid link (only if paid)
    payment_url = ""
    if getattr(event, "is_paid", False):
        try:
            payment_url = _site_url(reverse("payments:submit", kwargs={"registration_id": reg.id}))
        except Exception:
            payment_url = ""

    subject = f"{site}: Registration confirmed ✅"

    paid_text_block = ""
    if getattr(event, "is_paid", False):
        paid_text_block = f"""
This is a PAID event.
Amount: {getattr(event, "price", 0)}

Upload payment proof:
{payment_url}
"""

    text_body = f"""Hi {name},

You are successfully registered for:
{event.title}

When: {start_local}
Location: {location or "—"}

View event:
{event_url}
{paid_text_block}
— {site}
"""

    paid_html_block = ""
    if getattr(event, "is_paid", False):
        paid_html_block = f"""
        <div style="margin-top:14px;padding:12px;border-radius:14px;background:#fff7ed;border:1px solid #fed7aa;">
          <div style="font-weight:900;color:#9a3412;margin-bottom:6px;">This is a paid event</div>
          <div style="color:#7c2d12;font-size:14px;line-height:1.6;">
            Amount: <b>{getattr(event, "price", 0)}</b><br>
            Please upload your payment proof to confirm your spot.
          </div>
          <div style="margin-top:10px;">
            <a href="{payment_url}" style="display:inline-block;background:#f97316;color:#111827;text-decoration:none;
              padding:10px 14px;border-radius:999px;font-weight:900;">Upload payment proof</a>
          </div>
        </div>
        """

    html_body = f"""
<!doctype html><html><body style="margin:0;background:#f6f8fb;font-family:Arial;color:#0f172a;">
<div style="max-width:600px;margin:0 auto;padding:24px 14px;">
  <div style="background:#fff;border:1px solid rgba(15,23,42,.10);border-radius:16px;padding:18px;">
    <div style="font-size:18px;font-weight:900;margin-bottom:8px;">Registration confirmed ✅</div>
    <div style="font-size:14px;line-height:1.6;color:#334155;">
      Hi <b>{name}</b>,<br><br>
      You are successfully registered for:<br>
      <b>{event.title}</b><br><br>

      <b>When:</b> {start_local or "—"}<br>
      <b>Location:</b> {location or "—"}<br><br>

      <a href="{event_url}" style="display:inline-block;background:#16a34a;color:#06120a;text-decoration:none;
        padding:10px 14px;border-radius:999px;font-weight:900;">View event</a>

      {paid_html_block}
    </div>
  </div>

  <div style="text-align:center;margin-top:10px;font-size:12px;color:#94a3b8;">© {site}</div>
</div>
</body></html>
"""

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", "")
    msg = EmailMultiAlternatives(subject, text_body, from_email, [email])
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)
    return True

def send_event_reminder_email(registration) -> bool:
    """
    Sends reminder email to the registered student ~24 hours before event start.
    Returns True if sent, False if no email.
    """
    user = registration.user
    email = (getattr(user, "email", "") or "").strip()
    if not email:
        return False

    site = getattr(settings, "SITE_NAME", "Campus Connect")
    event = registration.event
    name = _user_name(user)

    event_url = _site_url(reverse("events:detail", kwargs={"pk": event.id}))
    start_local = timezone.localtime(event.start_datetime).strftime("%b %d, %Y %I:%M %p")

    is_paid = bool(getattr(event, "is_paid", False))
    price = getattr(event, "price", 0)

    subject = f"{site}: Reminder — {event.title} starts soon ⏰"
    headline = "Event reminder ⏰"
    accent = "#16a34a"

    payment_line_text = ""
    payment_line_html = ""
    if is_paid:
        payment_line_text = f"\nPayment: This is a PAID event (Amount: {price}).\n"
        payment_line_html = f"<div style='margin-top:10px;'><b>Payment:</b> Paid event (Amount: {price})</div>"

    text_body = f"""Hi {name},

This is a reminder that you're registered for:

Event: {event.title}
Starts: {start_local}
Location: {getattr(event, "location", "") or "—"}{payment_line_text}

View details:
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
      You’re registered for the following event and it starts soon:<br><br>
      <b>Event:</b> {event.title}<br>
      <b>Starts:</b> {start_local}<br>
      <b>Location:</b> {getattr(event, "location", "") or "—"}<br>
      {payment_line_html}
      <div style="margin-top:16px;">
        <a href="{event_url}" style="display:inline-block;background:{accent};color:#06120a;text-decoration:none;
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