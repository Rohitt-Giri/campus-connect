from django import forms
from decimal import Decimal
from .models import Event, EventRegistration


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "location",
            "start_datetime",
            "end_datetime",
            "status",
            "is_paid",
            "price",
        ]
        widgets = {
            "start_datetime": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "end_datetime": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Tech Talk 2026"}),
            "location": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Hall A"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Describe the event..."}),
            "status": forms.Select(attrs={"class": "form-select"}),

            "is_paid": forms.CheckboxInput(attrs={"class": "form-check-input", "role": "switch"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
        }

    def clean(self):
        cleaned = super().clean()
        is_paid = cleaned.get("is_paid")
        price = cleaned.get("price")

        if price is None:
            price = Decimal("0.00")
            cleaned["price"] = price

        if is_paid and price <= 0:
            self.add_error("price", "Price must be greater than 0 for paid events.")
        if not is_paid:
            cleaned["price"] = Decimal("0.00")

        return cleaned


class EventRegistrationForm(forms.ModelForm):
    class Meta:
        model = EventRegistration
        fields = ["full_name", "phone", "email", "notes"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Your full name"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "98XXXXXXXX"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "your@email.com"}),
            "notes": forms.TextInput(attrs={"class": "form-control", "placeholder": "Optional message"}),
        }
