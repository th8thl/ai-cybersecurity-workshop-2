from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="/tickets/", permanent=False)),
    path("accounts/", include("django.contrib.auth.urls")),
    path("tickets/", include("tickets.urls")),
    path("chatbot/", include("chatbot.urls")),
    path("admin/", admin.site.urls),
]
