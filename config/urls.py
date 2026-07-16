"""
Configuration racine des URLs du projet Huduma.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from apps.dashboard.views import LandingPageView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("offline/", TemplateView.as_view(template_name="pages/offline.html"), name="offline"),
    path("i18n/", include("django.conf.urls.i18n")),
    # Landing page (publique) à la racine
    path("", LandingPageView.as_view(), name="landing"),
    # Dashboard (préfixe /dashboard/)
    path("dashboard/", include("apps.dashboard.urls")),
    # Apps métier
    path("accounts/", include("apps.accounts.urls")),
    path("academic/", include("apps.academic.urls")),
    path("pedagogy/", include("apps.pedagogy.urls")),
    path("validation/", include("apps.validation.urls")),
    path("marketplace/", include("apps.marketplace.urls")),
    path("students/", include("apps.students.urls")),
    path("parents/", include("apps.parents.urls")),
    path("finance/", include("apps.finance.urls")),
    path("attendance/", include("apps.attendance.urls")),
    path("schedule/", include("apps.schedule.urls")),
    path("forum/", include("apps.forum.urls")),
    path("notifications/", include("apps.notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    try:
        import debug_toolbar
        urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
    except ImportError:
        pass

handler403 = "apps.core.views.error_403"
handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"
