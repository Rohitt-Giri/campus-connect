from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", include("core.urls")),
    path("admin/logs/", include("audit.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("student/", include("student.urls")),
    path("staff/", include("staff.urls")),
    path("notices/", include(("notices.urls", "notices"), namespace="notices")),
    path("events/", include("events.urls")),
    path("payments/", include(("payments.urls", "payments"), namespace="payments")),
    path("lostfound/", include("lostfound.urls")),
    path("notifications/", include(("notifications.urls", "notifications"), namespace="notifications")),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
