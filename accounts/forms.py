from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


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
        user.is_active = True  # important for showing "waiting approval"
        if commit:
            user.save()
        return user
