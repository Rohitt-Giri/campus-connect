from django import forms
from decimal import Decimal
from .models import Event, EventRegistration


class EventForm(forms.ModelForm):
    price = forms.DecimalField(required=False, min_value=0, decimal_places=2)

    class Meta:
        model = Event
        fields = [
            "title",
            "location",
            "start_datetime",
            "end_datetime",
            "description",
            "status",
            "is_paid",
            "price",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Event title"}),
            "location": forms.TextInput(attrs={"class": "form-control", "placeholder": "Location"}),
            "start_datetime": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "end_datetime": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 6, "placeholder": "Describe the event..."}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "is_paid": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "0.00"}),
        }

    def clean(self):
        cleaned = super().clean()
        is_paid = cleaned.get("is_paid")
        price = cleaned.get("price")

        if not is_paid:
            cleaned["price"] = 0
            return cleaned

        if price is None or price <= 0:
            self.add_error("price", "Price is required for a paid event and must be greater than 0.")

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
