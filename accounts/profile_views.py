# accounts/profile_views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import ProfileForm
from .models import UserProfile

@login_required
def my_profile_view(request):
    profile, _created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "created_at": timezone.now(),
            "updated_at": timezone.now(),
            "full_name": "",
            "phone": "",
            "bio": "",
        }
    )

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.updated_at = timezone.now()
            obj.save()
            messages.success(request, "Profile updated ✅")
            return redirect("accounts:my_profile")
        messages.error(request, "Please fix the errors below.")
    else:
        form = ProfileForm(instance=profile, user=request.user)

    return render(request, "accounts/my_profile.html", {
        "form": form,
        "profile": profile,
    })