from django import forms
from .models import Item, Claim


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["item_type", "title", "description", "location", "date_happened", "image"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "date_happened": forms.DateInput(attrs={"type": "date"}),
        }


class ClaimForm(forms.ModelForm):
    class Meta:
        model = Claim
        fields = ["full_name", "phone", "email", "proof_message"]
        widgets = {
            "proof_message": forms.Textarea(attrs={"rows": 4, "placeholder": "Explain why this item belongs to you (color, marks, where you lost it, etc.)"}),
        }
