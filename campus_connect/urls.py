from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Landing page
    path("", include(("core.urls", "core"), namespace="core")),

    # Admin
    path("admin/logs/", include(("audit.urls", "audit"), namespace="audit")),
    path("admin/", admin.site.urls),

    # Auth / profiles
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),

    # Role dashboards
    path("student/", include(("student.urls", "student"), namespace="student")),
    path("staff/", include(("staff.urls", "staff"), namespace="staff")),

    # Modules
    path("notices/", include(("notices.urls", "notices"), namespace="notices")),
    path("events/", include(("events.urls", "events"), namespace="events")),
    path("payments/", include(("payments.urls", "payments"), namespace="payments")),
    path("lostfound/", include(("lostfound.urls", "lostfound"), namespace="lostfound")),
    path("notifications/", include(("notifications.urls", "notifications"), namespace="notifications")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)