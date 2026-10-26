from django.urls import path
from . import views

urlpatterns = [
    path("", views.ticket_list, name="ticket_list"),
    path("import/", views.ticket_import, name="ticket_import"),
    path("import/template/", views.ticket_import_template, name="ticket_import_template"),
    path("<int:ticket_id>/export/", views.ticket_export, name="ticket_export"),
    path("<int:ticket_id>/attachments/download/", views.attachment_download, name="attachment_download"),
    path("new/", views.ticket_create, name="ticket_create"),
    path("<int:ticket_id>/", views.ticket_detail, name="ticket_detail"),
]
