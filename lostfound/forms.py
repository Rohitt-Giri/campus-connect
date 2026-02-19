from django import forms
from .models import ClaimRequest, LostFoundItem


class LostFoundItemForm(forms.ModelForm):
    class Meta:
        model = LostFoundItem
        fields = ["item_type", "title", "description", "location", "date_happened", "image"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "date_happened": forms.DateInput(attrs={"type": "date"}),
        }


class ClaimRequestForm(forms.ModelForm):
    class Meta:
        model = ClaimRequest
        fields = ["full_name", "phone", "email", "proof_message"]
        widgets = {
            "proof_message": forms.Textarea(attrs={"rows": 4, "placeholder": "Explain proof/unique details (serial no, marks, etc.)"}),
        }
