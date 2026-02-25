from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

def landing_page(request):
    if request.user.is_authenticated:
        return redirect("accounts:post_login_redirect")
    return render(request, "core/landing.html")