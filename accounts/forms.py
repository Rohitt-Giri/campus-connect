from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, UserProfile

from django.forms.widgets import ClearableFileInput

class NoClearableFileInput(ClearableFileInput):
    template_name = "accounts/widgets/file_input.html"
    
class RegisterForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=[(User.Role.STUDENT, "Student"), (User.Role.STAFF, "Staff")],
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = User
        fields = ["username", "email", "role", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_approved = False
        user.is_active = True
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            "photo",
            "full_name", "phone", "bio",
            "program", "semester", "student_id",
            "department", "designation",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Full name"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone number"}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Short bio"}),
            "photo": NoClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),

            "program": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. BSc IT"}),
            "semester": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 6th"}),
            "student_id": forms.TextInput(attrs={"class": "form-control", "placeholder": "Your Student ID"}),

            "department": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. IT Department"}),
            "designation": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Lecturer"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user

        # ✅ Make file input look good and stop showing "Currently / Clear / Change"
        self.fields["photo"].widget = forms.ClearableFileInput(attrs={
            "class": "form-control",
            "accept": "image/*",
        })

        # ✅ Role-based hide
        role = getattr(user, "role", None)

        if role == "STUDENT":
            self.fields["department"].widget = forms.HiddenInput()
            self.fields["designation"].widget = forms.HiddenInput()
        elif role == "STAFF":
            self.fields["program"].widget = forms.HiddenInput()
            self.fields["semester"].widget = forms.HiddenInput()
            self.fields["student_id"].widget = forms.HiddenInput()