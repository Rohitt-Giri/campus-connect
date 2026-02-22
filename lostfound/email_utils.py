from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse

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
    # safe fallback
    try:
        name = (user.get_full_name() or "").strip()
    except Exception:
        name = ""
    return name or (getattr(user, "username", "") or "there")

def send_claim_status_email(claim) -> bool:
    """
    claim: ClaimRequest
    Emails the claimant (student) when approved/rejected.
    """
    student = getattr(claim, "student", None) or getattr(claim, "user", None)
    if not student:
        return False

    email = _user_email(student)
    if not email:
        return False

    site = getattr(settings, "SITE_NAME", "Campus Connect")

    status = (claim.status or "").lower()
    if status not in {"approved", "rejected"}:
        return False

    item = claim.item
    item_url = _site_url(reverse("lostfound:detail", kwargs={"pk": item.id}))

    if status == "approved":
        subject = f"{site}: Your claim was approved ✅"
        headline = "Claim approved ✅"
        color = "#16a34a"
        message = "Your claim has been approved. Please follow the collection instructions from staff (if provided)."
    else:
        subject = f"{site}: Your claim was rejected ❌"
        headline = "Claim rejected ❌"
        color = "#dc2626"
        message = "Your claim was rejected. If you think this is a mistake, contact staff."

    note = ""
    # If you have any staff note field later, you can include it here.

    name = _user_name(student)

    text_body = f"""Hi {name},

{message}

Item: {getattr(item, 'title', 'Item')} (ID: {item.id})
Status: {status.upper()}

View item:
{item_url}

— {site}
"""

    html_body = f"""
<!doctype html><html><body style="margin:0;background:#f6f8fb;font-family:Arial;color:#0f172a;">
<div style="max-width:600px;margin:0 auto;padding:24px 14px;">
  <div style="background:#fff;border:1px solid rgba(15,23,42,.10);border-radius:16px;padding:18px;">
    <div style="font-size:18px;font-weight:900;color:{color};margin-bottom:8px;">{headline}</div>
    <div style="font-size:14px;line-height:1.6;color:#334155;">
      Hi <b>{name}</b>,<br><br>
      {message}<br><br>
      <b>Item:</b> {getattr(item, 'title', 'Item')} (ID: {item.id})<br>
      <b>Status:</b> {status.upper()}<br>
      {f"<b>Note:</b> {note}<br>" if note else ""}
      <br>
      <a href="{item_url}" style="display:inline-block;background:{color};color:#fff;text-decoration:none;
        padding:10px 14px;border-radius:999px;font-weight:900;">View item</a>
    </div>
  </div>
  <div style="text-align:center;margin-top:10px;font-size:12px;color:#94a3b8;">© {site}</div>
</div>
</body></html>
"""
    _send(email, subject, text_body, html_body)
    return True


def send_item_returned_email(item, *, to_user) -> bool:
    """
    Emails the user (usually the original poster) when item is marked returned.
    """
    if not to_user:
        return False
    email = _user_email(to_user)
    if not email:
        return False

    site = getattr(settings, "SITE_NAME", "Campus Connect")
    item_url = _site_url(reverse("lostfound:detail", kwargs={"pk": item.id}))
    name = _user_name(to_user)

    subject = f"{site}: Item marked as returned ✅"
    headline = "Item returned ✅"
    color = "#16a34a"

    text_body = f"""Hi {name},

Your Lost & Found item has been marked as returned/resolved.

Item: {getattr(item, 'title', 'Item')} (ID: {item.id})

View item:
{item_url}

— {site}
"""

    html_body = f"""
<!doctype html><html><body style="margin:0;background:#f6f8fb;font-family:Arial;color:#0f172a;">
<div style="max-width:600px;margin:0 auto;padding:24px 14px;">
  <div style="background:#fff;border:1px solid rgba(15,23,42,.10);border-radius:16px;padding:18px;">
    <div style="font-size:18px;font-weight:900;color:{color};margin-bottom:8px;">{headline}</div>
    <div style="font-size:14px;line-height:1.6;color:#334155;">
      Hi <b>{name}</b>,<br><br>
      Your Lost &amp; Found item has been marked as returned/resolved.<br><br>
      <b>Item:</b> {getattr(item, 'title', 'Item')} (ID: {item.id})<br><br>
      <a href="{item_url}" style="display:inline-block;background:{color};color:#fff;text-decoration:none;
        padding:10px 14px;border-radius:999px;font-weight:900;">View item</a>
    </div>
  </div>
  <div style="text-align:center;margin-top:10px;font-size:12px;color:#94a3b8;">© {site}</div>
</div>
</body></html>
"""
    _send(email, subject, text_body, html_body)
    return True

def send_claim_received_email(claim) -> bool:
    site = getattr(settings, "SITE_NAME", "Campus Connect")

    student = getattr(claim, "student", None)
    # ✅ prefer claim.email (from form), fallback to student's account email
    to_email = (getattr(claim, "email", "") or "").strip()
    if not to_email and student:
        to_email = (getattr(student, "email", "") or "").strip()

    if not to_email:
        return False

    item = claim.item
    item_url = _site_url(reverse("lostfound:detail", kwargs={"pk": item.id}))
    name = _user_name(student) if student else "there"

    subject = f"{site}: Claim received 📨"

    text_body = f"""Hi {name},

We received your claim for:

Item: {getattr(item,'title','Item')} (ID: {item.id})
Status: PENDING REVIEW

Staff will review your claim soon.

View item:
{item_url}

— {site}
"""

    html_body = f"""
<!doctype html><html><body style="background:#f6f8fb;font-family:Arial;">
<div style="max-width:600px;margin:auto;padding:24px;">
  <div style="background:#fff;border-radius:16px;padding:18px;border:1px solid rgba(15,23,42,.10);">
    <div style="font-weight:900;font-size:18px;color:#16a34a;">Claim received 📨</div>
    <p>Hi <b>{name}</b>,</p>
    <p>Your claim has been submitted and is pending staff review.</p>
    <p><b>Item:</b> {getattr(item,'title','Item')} (ID: {item.id})</p>
    <a href="{item_url}" style="background:#16a34a;color:#fff;padding:10px 14px;border-radius:999px;text-decoration:none;font-weight:900;">View item</a>
  </div>
  <div style="text-align:center;margin-top:10px;font-size:12px;color:#94a3b8;">© {site}</div>
</div>
</body></html>
"""

    _send(to_email, subject, text_body, html_body)
    return True