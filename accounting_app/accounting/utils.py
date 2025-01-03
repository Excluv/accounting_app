from django.db.models import Sum, Q, QuerySet

from .models import Transaction, Account

from typing import Dict, Optional
import numpy as np


def get_trial_balance() -> Dict[str, QuerySet]:
    account_balance = (
        Transaction.objects
        .values("account__name")
        .annotate(
            debit=Sum("amount", filter=Q(amount__gt=0)),
            credit=Sum("amount", filter=Q(amount__lt=0))
        )
        .order_by("account__name")
    )
    trial_balance = {
        "account_balance": account_balance,
        "total_debit": sum(row["debit"] or 0 for row in account_balance),
        "total_credit": sum(abs(row["credit"] or 0) for row in account_balance),
    }
    return trial_balance


def get_account_transactions(account_name: str) -> QuerySet:
    transactions = Transaction.objects.filter(account__name=account_name)
    return transactions


def get_account_balance(account_name: str) -> QuerySet:
    transactions = get_account_transactions(account_name)
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
        credit = np.abs(np.cumsum([float(transaction.amount) for transaction in transactions]))
    
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
