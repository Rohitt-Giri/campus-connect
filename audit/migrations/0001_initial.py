from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[
                    ("USER_APPROVE", "User Approved"),
                    ("USER_DEACTIVATE", "User Deactivated"),
                    ("USER_ACTIVATE", "User Activated"),
                    ("USER_ROLE_CHANGE", "User Role Changed"),
                    ("PAYMENT_APPROVE", "Payment Approved"),
                    ("PAYMENT_REJECT", "Payment Rejected"),
                    ("CLAIM_APPROVE", "Claim Approved"),
                    ("CLAIM_REJECT", "Claim Rejected"),
                    ("ITEM_RETURNED", "Item Marked Returned"),
                    ("NOTICE_CREATE", "Notice Created"),
                    ("NOTICE_UPDATE", "Notice Updated"),
                    ("EVENT_CREATE", "Event Created"),
                    ("EVENT_UPDATE", "Event Updated"),
                ], max_length=40)),
                ("message", models.CharField(blank=True, default="", max_length=255)),
                ("target_model", models.CharField(blank=True, default="", max_length=80)),
                ("target_id", models.CharField(blank=True, default="", max_length=64)),
                ("target_label", models.CharField(blank=True, default="", max_length=255)),
                ("ip_address", models.CharField(blank=True, default="", max_length=45)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "audit_auditlog",
                "ordering": ["-created_at"],
            },
        ),
    ]