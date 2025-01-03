from django.urls import path

from .admin import accounting_admin_site


urlpatterns = [
    path("trial-balance/", accounting_admin_site.trial_balance_view, name="trial_balance"),
    path("account-balance/<str:account_name>/", accounting_admin_site.account_balance_view, name="account_balance"),
    path("report/<str:report_name>/", accounting_admin_site.report_view, name="report_view"),
]
