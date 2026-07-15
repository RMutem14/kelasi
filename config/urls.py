"""
Configuration racine des URLs du projet Huduma.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.dashboard.views import LandingPageView

urlpatterns = [
    path("admin/", admin.site.urls),
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
