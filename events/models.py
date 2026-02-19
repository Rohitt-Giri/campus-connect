from django.conf import settings
from django.db import models

class Event(models.Model):
    STATUS_CHOICES = (("draft","Draft"),("published","Published"))

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="events_created")
    created_at = models.DateTimeField(auto_now_add=True)

    # keep these now (for later payments)
    is_paid = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ["start_datetime"]

    def __str__(self):
        return self.title

class EventRegistration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="event_registrations")

    full_name = models.CharField(max_length=150, default="", blank=True)
    phone = models.CharField(max_length=30, default="", blank=True)
    email = models.EmailField(default="", blank=True)
    notes = models.CharField(max_length=255, default="", blank=True)

    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("event","user")
        ordering = ["-registered_at"]

    def __str__(self):
        return f"{self.user} -> {self.event}"
    
payment_qr = models.ImageField(upload_to="events/payment_qr/", null=True, blank=True)

