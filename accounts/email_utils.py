from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django.utils import timezone


def _site_url(path: str) -> str:
    base = getattr(settings, "SITE_URL", "http://127.0.0.1:8000").rstrip("/")
    return f"{base}{path}"


def _display_name(user) -> str:
    try:
        name = (user.get_full_name() or "").strip()
    except Exception:
        name = ""
    if not name:
        name = (getattr(user, "username", "") or "there").strip()
    return name or "there"


def _send_html_email(*, to_email: str, subject: str, title: str, body_html: str, body_text: str) -> None:
    site_name = getattr(settings, "SITE_NAME", "Campus Connect")
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", "")
    msg = EmailMultiAlternatives(subject, body_text, from_email, [to_email])
    msg.attach_alternative(body_html, "text/html")
    msg.send(fail_silently=False)


def send_user_approved_email(user) -> bool:
    email = (getattr(user, "email", "") or "").strip()
    if not email:
        return False

    site_name = getattr(settings, "SITE_NAME", "Campus Connect")
    login_url = _site_url(reverse("accounts:login"))
    name = _display_name(user)

    approved_time = timezone.localtime(timezone.now()).strftime("%b %d, %Y %I:%M %p")
    preheader = "You can now log in — your account has been approved."

    subject = f"{site_name}: Your account is approved ✅"

    text_body = f"""Hi {name},

Good news — your {site_name} account has been approved. You can now log in.

Log in:
{login_url}

Approved at: {approved_time}

— {site_name}
"""

    html_body = f"""
<!doctype html><html><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{site_name} — Approved</title></head>
<body style="margin:0;padding:0;background:#f6f8fb;font-family:Arial,Helvetica,sans-serif;color:#0f172a;">
<div style="display:none;font-size:1px;color:#f6f8fb;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;">{preheader}</div>
<div style="max-width:600px;margin:0 auto;padding:28px 16px;">
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:18px;">
    <div style="width:44px;height:44px;border-radius:14px;background:linear-gradient(135deg,#16a34a,#22c55e);
      display:flex;align-items:center;justify-content:center;font-weight:900;color:#06120a;">CC</div>
    <div>
      <div style="font-size:16px;font-weight:900;line-height:1;">{site_name}</div>
      <div style="font-size:13px;color:#64748b;font-weight:600;margin-top:3px;">Account notification</div>
    </div>
  </div>

  <div style="background:#fff;border:1px solid rgba(15,23,42,0.10);border-radius:18px;box-shadow:0 12px 30px rgba(15,23,42,0.06);padding:22px;">
    <div style="font-size:20px;font-weight:900;margin:0 0 8px;">Approved ✅</div>
    <div style="font-size:14px;color:#334155;line-height:1.65;">
      Hi <b>{name}</b>,<br><br>
      Your <b>{site_name}</b> account has been approved. You can now log in and continue using the platform.
    </div>

    <div style="margin-top:18px;">
      <a href="{login_url}" style="display:inline-block;background:linear-gradient(135deg,#16a34a,#22c55e);
        color:#06120a;text-decoration:none;font-weight:900;border-radius:999px;padding:12px 18px;">Log in</a>
    </div>

    <div style="margin-top:14px;font-size:12.5px;color:#64748b;line-height:1.55;">
      If the button doesn’t work, copy and paste this link:<br>
      <a href="{login_url}" style="color:#16a34a;font-weight:800;text-decoration:none;">{login_url}</a>
    </div>

    <div style="margin-top:14px;font-size:12px;color:#94a3b8;line-height:1.6;">Approved at: {approved_time}</div>
  </div>

  <div style="margin-top:14px;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">
    This is an automated email. If you didn’t request this, you can ignore it.<br>© {site_name}
  </div>
</div>
</body></html>
"""
    _send_html_email(to_email=email, subject=subject, title="Approved", body_html=html_body, body_text=text_body)
    return True


def send_user_rejected_email(user) -> bool:
    email = (getattr(user, "email", "") or "").strip()
    if not email:
        return False

    site_name = getattr(settings, "SITE_NAME", "Campus Connect")
    name = _display_name(user)
    support_email = getattr(settings, "SUPPORT_EMAIL", "")

    subject = f"{site_name}: Account not approved ❌"
    preheader = "Your account was not approved. Contact support if you think this is a mistake."
    time_str = timezone.localtime(timezone.now()).strftime("%b %d, %Y %I:%M %p")

    text_body = f"""Hi {name},

Your {site_name} account was not approved at this time.

If you believe this is a mistake, reply to this email{f" or contact {support_email}" if support_email else ""}.

— {site_name}
"""

    html_body = f"""
<!doctype html><html><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{site_name} — Not Approved</title></head>
<body style="margin:0;padding:0;background:#f6f8fb;font-family:Arial,Helvetica,sans-serif;color:#0f172a;">
<div style="display:none;font-size:1px;color:#f6f8fb;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;">{preheader}</div>
<div style="max-width:600px;margin:0 auto;padding:28px 16px;">
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:18px;">
    <div style="width:44px;height:44px;border-radius:14px;background:linear-gradient(135deg,#16a34a,#22c55e);
      display:flex;align-items:center;justify-content:center;font-weight:900;color:#06120a;">CC</div>
    <div>
      <div style="font-size:16px;font-weight:900;line-height:1;">{site_name}</div>
      <div style="font-size:13px;color:#64748b;font-weight:600;margin-top:3px;">Account notification</div>
    </div>
  </div>

  <div style="background:#fff;border:1px solid rgba(15,23,42,0.10);border-radius:18px;box-shadow:0 12px 30px rgba(15,23,42,0.06);padding:22px;">
    <div style="font-size:20px;font-weight:900;margin:0 0 8px;">Not approved ❌</div>
    <div style="font-size:14px;color:#334155;line-height:1.65;">
      Hi <b>{name}</b>,<br><br>
      Your <b>{site_name}</b> account was not approved at this time.
      If you believe this is a mistake, please reply to this email{f" or contact <b>{support_email}</b>" if support_email else ""}.
    </div>
    <div style="margin-top:14px;font-size:12px;color:#94a3b8;">Updated at: {time_str}</div>
  </div>

  <div style="margin-top:14px;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">© {site_name}</div>
</div>
</body></html>
"""
    _send_html_email(to_email=email, subject=subject, title="Not approved", body_html=html_body, body_text=text_body)
    return True


def send_user_activated_email(user, is_active: bool) -> bool:
    email = (getattr(user, "email", "") or "").strip()
    if not email:
        return False

    site_name = getattr(settings, "SITE_NAME", "Campus Connect")
    name = _display_name(user)
    login_url = _site_url(reverse("accounts:login"))

    state = "activated ✅" if is_active else "deactivated ❌"
    subject = f"{site_name}: Your account was {state}"

    text_body = f"""Hi {name},

Your {site_name} account was {state}.

Login:
{login_url}

— {site_name}
"""

    html_body = f"""
<!doctype html><html><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{site_name} — Account {state}</title></head>
<body style="margin:0;padding:0;background:#f6f8fb;font-family:Arial,Helvetica,sans-serif;color:#0f172a;">
<div style="max-width:600px;margin:0 auto;padding:28px 16px;">
  <div style="background:#fff;border:1px solid rgba(15,23,42,0.10);border-radius:18px;box-shadow:0 12px 30px rgba(15,23,42,0.06);padding:22px;">
    <div style="font-size:20px;font-weight:900;margin:0 0 8px;">Account {state}</div>
    <div style="font-size:14px;color:#334155;line-height:1.65;">
      Hi <b>{name}</b>,<br><br>
      Your <b>{site_name}</b> account was {state}.
    </div>
    <div style="margin-top:18px;">
      <a href="{login_url}" style="display:inline-block;background:linear-gradient(135deg,#16a34a,#22c55e);
        color:#06120a;text-decoration:none;font-weight:900;border-radius:999px;padding:12px 18px;">Log in</a>
    </div>
  </div>
  <div style="margin-top:14px;font-size:12px;color:#94a3b8;text-align:center;">© {site_name}</div>
</div>
</body></html>
"""
    _send_html_email(to_email=email, subject=subject, title="Account update", body_html=html_body, body_text=text_body)
    return True


def send_role_changed_email(user, old_role: str, new_role: str) -> bool:
    email = (getattr(user, "email", "") or "").strip()
    if not email:
        return False

    site_name = getattr(settings, "SITE_NAME", "Campus Connect")
    name = _display_name(user)

    subject = f"{site_name}: Your role has been updated"
    text_body = f"""Hi {name},

Your role on {site_name} has been updated:
{old_role} → {new_role}

— {site_name}
"""

    html_body = f"""
<!doctype html><html><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{site_name} — Role Updated</title></head>
<body style="margin:0;padding:0;background:#f6f8fb;font-family:Arial,Helvetica,sans-serif;color:#0f172a;">
<div style="max-width:600px;margin:0 auto;padding:28px 16px;">
  <div style="background:#fff;border:1px solid rgba(15,23,42,0.10);border-radius:18px;box-shadow:0 12px 30px rgba(15,23,42,0.06);padding:22px;">
    <div style="font-size:20px;font-weight:900;margin:0 0 8px;">Role updated</div>
    <div style="font-size:14px;color:#334155;line-height:1.65;">
      Hi <b>{name}</b>,<br><br>
      Your role on <b>{site_name}</b> has been updated:<br>
      <b>{old_role}</b> → <b>{new_role}</b>
    </div>
  </div>
  <div style="margin-top:14px;font-size:12px;color:#94a3b8;text-align:center;">© {site_name}</div>
</div>
</body></html>
"""
    _send_html_email(to_email=email, subject=subject, title="Role updated", body_html=html_body, body_text=text_body)
    return True