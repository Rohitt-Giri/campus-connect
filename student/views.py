from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from notices.models import Notice

# lostfound optional safety
try:
    from lostfound.models import LostFoundItem, ClaimRequest
except Exception:
    LostFoundItem = None
    ClaimRequest = None


@login_required
def student_dashboard_view(request):
    recent_notices = Notice.objects.filter(is_active=True).order_by("-created_at")[:3]
    notices_count = Notice.objects.filter(is_active=True).count()

    my_posts_count = 0
    my_claims_count = 0
    if LostFoundItem and ClaimRequest:
        my_posts_count = LostFoundItem.objects.filter(created_by_id=request.user.id).count()
        my_claims_count = ClaimRequest.objects.filter(student_id=request.user.id).count()

    return render(request, "student/dashboard.html", {
        "recent_notices": recent_notices,
        "notices_count": notices_count,
        "my_posts_count": my_posts_count,
        "my_claims_count": my_claims_count,
    })
