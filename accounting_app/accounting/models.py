from django.db import models
from django.contrib.auth.models import User


class ChangeLog(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        abstract = True


class Account(ChangeLog):
    ACCOUNT_TYPES = [
        ("Asset", "Asset"),
        ("Liability", "Liability"),
        ("Equity", "Equity"),
        ("Contra Equity", "Contra Equity"),
        ("Revenue", "Revenue"),
        ("Expense", "Expense"),
    ]
    NORMAL_BALANCE = [
        ("Debit", "Debit"),
        ("Credit", "Credit"),
    ]
    name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    normal_balance = models.CharField(max_length=10, choices=NORMAL_BALANCE, blank=True)
    reference_code = models.IntegerField()

    def save(self, *args, **kwargs):
        if not self.normal_balance:
            if self.account_type in ["Asset", "Expenses"]:
                self.normal_balance = "Debit"
            else:
                self.normal_balance = "Credit"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"({self.account_type}) {self.reference_code} {self.name}"


class JournalEntry(ChangeLog):
    description = models.CharField(max_length=255)
    date = models.DateField()

    def __str__(self):
        return f"{self.description}"
    
    class Meta:
        verbose_name_plural = "Journal entries"


class Transaction(ChangeLog):
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE)
    description = models.CharField(max_length=1000, blank=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.description and self.journal_entry:
            self.description = self.journal_entry.description
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.account} {self.description} {self.amount:,.2f}"


class TaxRate(ChangeLog):
    name = models.CharField(max_length=255)
    rate = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.name} {self.rate}%"
