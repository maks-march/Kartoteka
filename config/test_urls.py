from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path("test/", TemplateView.as_view(template_name="core/test_index.html"), name="test-index"),

    path("test/system/", TemplateView.as_view(template_name="system/system_list_test.html"), name="system-list-test"),

    path("test/system/create/", TemplateView.as_view(template_name="system/system_form_test.html"), name="system-create-test"),
    path("test/system/<int:pk>/", TemplateView.as_view(template_name="system/system_detail_test.html"), name="system-detail-test"),

    path("test/system-wide/", TemplateView.as_view(template_name="system/system_list_wide_test.html"), name="system-list-wide-test"),
    path("test/system-wide/create/", TemplateView.as_view(template_name="system/system_form_wide_test.html"), name="system-create-wide-test"),
    path("test/system-wide/<int:pk>/", TemplateView.as_view(template_name="system/system_detail_wide_test.html"), name="system-detail-wide-test"),
]
