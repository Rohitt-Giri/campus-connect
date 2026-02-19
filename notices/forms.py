from django import forms
from .models import Notice


class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ["title", "category", "content"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Notice title"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 6, "placeholder": "Write notice content..."}),
        }
