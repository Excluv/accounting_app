from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import render

from .models import Account, JournalEntry, Transaction, TaxRate
from .utils import (get_trial_balance,
                    get_account_info,
                    create_custom_app,
                    create_custom_model)
from .components import (DateRangeForm,
                         ViewComponent)


class ModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    can_delete = True

    class Media:
        js = ("custom_admin.js")


class AccountAdmin(ModelAdmin):
    list_display = ("name", "account_type", "normal_balance", "reference_code")
    search_fields = ("name", )
    list_filter = ("account_type", )
    

class JournalEntryAdmin(ModelAdmin):
    list_display = ("description", "date", "created_by")
    inlines = [TransactionInline]
    list_filter = ("date", )
    search_fields = ("description", )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        journal_entry = form.instance
        transactions = journal_entry.transaction_set.all()
        for transaction in transactions:
            if not transaction.account or transaction.amount == 0:
                transaction.delete()


class TaxRateAdmin(ModelAdmin):
    list_display = ("name", "rate")
    search_fields = ("name", )


class TransactionAdmin(ModelAdmin):
    list_display = ("journal_entry", "account", "formatted_amount")
    search_fields = ("journal_entry", )
    list_filter = ("account", )

    def formatted_amount(self, obj):
        return f"{obj.amount:,.2f}"


class AccountingAdminSite(admin.AdminSite):
    site_title = "Accounting App"
    site_header = "Accounting App"
    site_context = {
        "site_header": site_header,
        "is_nav_sidebar_enabled": True,
        "has_permission": True,
        "is_popup": False,
        "app_name": "Accounting App",
        "form": DateRangeForm(),
    }
    view_components = ViewComponent()

    @staticmethod
    def handle_date_request(request):
        start_date = None
        end_date = None
        if request.method == "POST":
            start_date = request.POST.get("start_date")
            end_date = request.POST.get("end_date")
        
        return start_date, end_date

    def trial_balance_view(self, request):
        start_date, end_date = self.handle_date_request(request)
        components = self.view_components.get_trial_balance(start_date, end_date)

        context = components.update({"available_apps": self.get_app_list(request)})
        context.update(self.site_context)

        return render(request, "admin/trial_balance.html", context)

    def account_balance_view(self, request, account_name):
        start_date, end_date = self.handle_date_request(request)
        components = self.view_components.get_account_balance(account_name, start_date, end_date)

        context = {
            "account_name": account_name,
            "available_apps": self.get_app_list(request),
        }
        context.update(self.site_context)
        context.update(components)

        return render(request, "admin/account_balance.html", context)

    def report_view(self, request, report_name):
        context = {
            "report_name": report_name,
            "available_apps": self.get_app_list(request),
        }
        urls_dict = {
            "Income Statement": "admin/income_statement.html",
            "Retained Earnings Statement": "admin/retained_earnings_statement.html",
            "Balance Sheet": "admin/balance_sheet.html",
        }
        
        start_date, end_date = self.handle_date_request(request)
        if report_name == "Income Statement":
            view_components = self.view_components.get_income_statement(start_date, end_date)
        elif report_name == "Retained Earnings Statement":
            view_components = self.view_components.get_retained_earnings_statement(start_date, end_date)
        elif report_name == "Balance Sheet":
            view_components = self.view_components.get_balance_sheet(start_date, end_date)
        else:
            view_components = {}
        
        context.update(view_components)
        context.update(self.site_context)
        
        return render(request, urls_dict.get(report_name, "admin/index.html"), context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("trial-balance/", 
                 self.admin_view(self.trial_balance_view), 
                 name="trial_balance"),
            path("account-balance/<str:account_name>/",
                 self.admin_view(self.account_balance_view),
                 name="account_balance"),
            path("report/<str:report_name>/",
                 self.admin_view(self.report_view),
                 name="report_view"),
        ]
        return custom_urls + urls

    def get_app_list(self, request):
        # Create Balance View app 
        balance_view_app = create_custom_app("Balance View", reverse("admin:index"))

        trial_balance_model = create_custom_model("Trial Balance", reverse("trial_balance"))
        balance_view_app["models"].append(trial_balance_model)

        accounts = get_account_info("name", "all")
        for account in accounts:
            balance_view_model = create_custom_model(account.name, reverse("account_balance", args=[account.name]))
            balance_view_app["models"].append(balance_view_model)

        # Create Report View app
        report_view_app = create_custom_app("Report View", reverse("admin:index"))

        reports = ["Income Statement", "Retained Earnings Statement", "Balance Sheet"]
        for report in reports:
            report_view_model = create_custom_model(report, reverse("report_view", args=[report]))
            report_view_app["models"].append(report_view_model)

        app_list = super().get_app_list(request)
        app_list[0]["app_url"] = reverse("admin:index")
        app_list.append(balance_view_app)
        app_list.append(report_view_app)
        
        return app_list


accounting_admin_site = AccountingAdminSite(name="accounting_admin")
for model in [(Account, AccountAdmin), 
              (JournalEntry, JournalEntryAdmin), 
              (Transaction, TransactionAdmin), 
              (TaxRate, TaxRateAdmin)]:
    accounting_admin_site.register(*model)
