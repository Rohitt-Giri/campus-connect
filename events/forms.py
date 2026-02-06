from django import forms
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
        ]
        widgets = {
            "start_datetime": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "end_datetime": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Tech Talk 2026"}),
            "location": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Hall A"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Describe the event..."}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }


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
