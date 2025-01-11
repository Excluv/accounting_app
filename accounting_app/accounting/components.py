from django import forms
from django.db.models import Sum, Q
from .models import Transaction

from .utils import (calc_cumulative_balance,
                    calc_total_revenue_expense,
                    calc_net_income,
                    calc_account_balance,
                    calc_tx_total,
                    get_account_info,
                    get_account_transactions)
                    


class DateRangeForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={"class": "datepicker", "type": "date"}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={"class": "datepicker", "type": "date"}))
    

class ViewComponent:
    def get_trial_balance(self, start_date, end_date):
        accounts = (
            Transaction.objects
            .values("account__name")
            .annotate(
                debit=Sum("amount", filter=Q(amount__gt=0)),
                credit=Sum("amount", filter=Q(amount__lt=0))
            )
            .order_by("account__name")
        )
        if start_date and end_date:
            accounts = accounts.filter(journal_entry__date__range=(start_date, end_date))

        components = {
            "accounts": accounts,
            "total_debit": sum(row["debit"] or 0 for row in accounts),
            "total_credit": sum(abs(row["credit"] or 0) for row in accounts),
        }
        return components

    def get_account_balance(self, account_name, start_date, end_date):
        account_transactions = get_account_transactions(account_name, start_date, end_date)
        if len(account_transactions) == 0:
            components = {}
        else:
            account_balance = calc_cumulative_balance(account_transactions)
            components = {
                "transactions": account_transactions,
                "balance": account_balance,
                "total_debit": (account_balance["debit_balance"][-1] 
                                if account_balance["debit_balance"][0] != "" 
                                else ""),
                "total_credit": (account_balance["credit_balance"][-1]  
                                if account_balance["credit_balance"][0] != ""  
                                else ""),
            }
        
        return components

    def get_income_statement(self, start_date, end_date):
        total_revenue, total_expense = calc_total_revenue_expense(start_date, end_date)
        net_income = calc_net_income(total_revenue, total_expense)
        components = {
            "revenue_accounts": get_account_info("type", account_type="Revenue"),
            "expense_accounts": get_account_info("type", account_type="Expense"),
            "total_revenue": total_revenue,
            "total_expense": total_expense,
            "net_income": net_income,
        }
        return components

    def get_retained_earnings_statement(self, start_date, end_date):
        net_income = calc_net_income()
        cash_dividends = calc_tx_total(get_account_transactions("Cash Dividends"))
        increased_retained_earnings = net_income - cash_dividends

        retained_earnings_tx = get_account_transactions("Retained Earnings", start_date, end_date)
        beginning_retained_earnings = retained_earnings_tx[0].amount if retained_earnings_tx else 0
        ending_retained_earnings = beginning_retained_earnings + increased_retained_earnings

        components = {
            "beginning_retained_earnings": beginning_retained_earnings,
            "net_income": net_income,
            "cash_dividends": cash_dividends,
            "increased_retained_earnings": increased_retained_earnings,
            "ending_retained_earnings": ending_retained_earnings,
        }
        return components

    def get_balance_sheet(self, start_date, end_date):
        asset_accounts = get_account_info("type", account_type="Asset")
        liability_accounts = get_account_info("type", account_type="Liability")
        equity_accounts = get_account_info("type", account_type="Equity")

        total_assets = calc_account_balance(asset_accounts, start_date, end_date)
        total_liabilities = calc_account_balance(liability_accounts, start_date, end_date)
        total_equity = calc_account_balance(equity_accounts, start_date, end_date)
        total_liabilities_and_equity = total_liabilities + total_equity

        components = {
            "asset_accounts": asset_accounts,
            "liability_accounts": liability_accounts,
            "equity_accounts": equity_accounts,
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "total_equity": total_equity,
            "total_liabilities_and_equity": total_liabilities_and_equity,
        }
        return components
