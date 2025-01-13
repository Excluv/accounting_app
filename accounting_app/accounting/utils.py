from django.db.models import Sum, Q, QuerySet

from .models import Transaction, Account

from typing import Optional, Union
import numpy as np


def get_account_transactions(account_name: str, 
                             start_date: Optional[str]=None, 
                             end_date: Optional[str]=None) -> QuerySet:
    transactions = Transaction.objects.filter(account__name=account_name)
    if start_date and end_date:
        transactions = transactions.filter(journal_entry__date__range=(start_date, end_date))

    return transactions


def get_account_cumulative_balance(account_name: str,
                                   start_date: Optional[str]=None, 
                                   end_date: Optional[str]=None) -> QuerySet:
    transactions = get_account_transactions(account_name, start_date, end_date)
    account_balance = calc_cumulative_balance(transactions)
    return account_balance


def get_account_info(by: str="name", 
                     qty: Optional[str]=None,
                     account_name: Optional[str]=None,
                     account_type: Optional[str]=None) -> QuerySet:
    if by == "name":   
        if qty == "all":
            info = Account.objects.all()
        elif qty == "single":
            info = Account.objects.filter(name__exact=account_name)
    elif by == "type":
        info = Account.objects.filter(account_type__exact=account_type)

    return info


def calc_cumulative_balance(transactions: QuerySet) -> dict:
    if len(transactions) == 0:
        return {
            "debit_balance": [], 
            "credit_balance": []
        }

    debit = [""] * len(transactions)
    credit = [""] * len(transactions)

    normal_balance = transactions.first().account.normal_balance
    if normal_balance == "Debit":
        debit = np.cumsum([float(transaction.amount) for transaction in transactions])
    elif normal_balance == "Credit":
        credit = np.cumsum([float(transaction.amount) for transaction in transactions])
    
    cumulative_balance = {
        "debit_balance": debit,
        "credit_balance": credit,
    }
    return cumulative_balance


def create_custom_app(label: str, url: str, models: list=None) -> dict:
    custom_app = {
        "app_label": label,
        "name": label,
        "app_url": url,
        "models": models if models else []
    }
    return custom_app


def create_custom_model(label: str, url: str, perms: Optional[dict]=None) -> dict:
    custom_model = {
        "object_name": label,
        "name": label,
        "admin_url": url,
        "perms": perms if perms else {"add": False, "change": False, "delete": False, "view": False}
    }
    return custom_model


def calc_account_balance(account_name: Union[str, list], 
                         start_date: Optional[str]=None, 
                         end_date: Optional[str]=None) -> float:
    if isinstance(account_name, str):
        tx = get_account_transactions(account_name, start_date, end_date)
        account_balance = calc_tx_total(tx)
    else:
        tx = [get_account_transactions(account.name, start_date, end_date) for account in account_name]
        account_balance = sum([calc_tx_total(t) for t in tx])

    return account_balance


def calc_tx_total(transactions: QuerySet) -> float:
    total = sum([float(transaction.amount) for transaction in transactions])
    return total


def calc_total_revenue_expense(start_date: Optional[str]=None, 
                               end_date: Optional[str]=None) -> float:
    revenue_accounts = get_account_info("type", account_type="Revenue")
    expense_accounts = get_account_info("type", account_type="Expense")
    total_revenue = sum([calc_account_balance(account.name, start_date, end_date) for account in revenue_accounts])
    total_expense = sum([calc_account_balance(account.name, start_date, end_date) for account in expense_accounts])
    return total_revenue, total_expense


def calc_net_income(total_revenue: float=None, 
                    total_expense: float=None,
                    start_date: Optional[str]=None, 
                    end_date: Optional[str]=None) -> float:
    if total_revenue and total_expense:
        net_income = abs(total_revenue) - abs(total_expense)
    else:
        total_revenue, total_expense = calc_total_revenue_expense(start_date, end_date)
        net_income = abs(total_revenue) - abs(total_expense)

    return net_income
