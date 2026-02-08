from django import forms
from .models import PaymentProof


class PaymentProofForm(forms.ModelForm):
    class Meta:
        model = PaymentProof
        fields = ["proof_image", "remarks"]

        widgets = {
            "remarks": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Optional note (e.g., paid via eSewa, Ref ID...)"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["proof_image"].widget.attrs.update({
            "class": "form-control"
        })
