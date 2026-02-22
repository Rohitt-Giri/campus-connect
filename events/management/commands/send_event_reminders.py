from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from audit.utils import log_action
from events.models import EventRegistration
from events.email_utils import send_event_reminder_email


class Command(BaseCommand):
    help = "Send reminder emails for events starting within the next 24 hours (once per registration)."

    def add_arguments(self, parser):
        parser.add_argument("--hours", type=int, default=24, help="Reminder window in hours (default 24)")
        parser.add_argument("--dry-run", action="store_true", help="Show what would be sent, but do not send")

    def handle(self, *args, **options):
        hours = options["hours"]
        dry_run = options["dry_run"]

        now = timezone.now()
        window_end = now + timedelta(hours=hours)

        qs = (
            EventRegistration.objects
            .select_related("event", "user")
            .filter(
                reminder_sent_at__isnull=True,
                event__status="published",
                event__start_datetime__gte=now,
                event__start_datetime__lte=window_end,
            )
            .order_by("event__start_datetime")
        )

        total = qs.count()
        self.stdout.write(self.style.SUCCESS(f"Found {total} registration(s) needing reminders."))

        sent_count = 0
        for reg in qs:
            event = reg.event
            user = reg.user

            if dry_run:
                self.stdout.write(f"[DRY RUN] Would email {user.email} for event '{event.title}'")
                continue

            email_sent = send_event_reminder_email(reg)
            reg.reminder_sent_at = timezone.now()
            reg.save(update_fields=["reminder_sent_at"])

            # ✅ Audit log (optional but nice)
            try:
                # No request object in management command; pass request=None if your log_action supports it
                log_action(
                    request=None,
                    actor=None,
                    action="EVENT_REMINDER_SENT",
                    message=f"Reminder sent for event: {event.title} -> {getattr(user, 'username', '')}",
                    target=reg,
                    metadata={
                        "event_id": event.id,
                        "event_title": event.title,
                        "user": getattr(user, "username", ""),
                        "email_sent": email_sent,
                        "window_hours": hours,
                    },
                )
            except Exception:
                pass

            sent_count += 1

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run complete. No emails were sent."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Done. Processed {sent_count} reminder(s)."))