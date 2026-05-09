from django.db import models
from django.conf import settings


class Category(models.Model):
    INCOME = 'income'
    EXPENSE = 'expense'
    TYPE_CHOICES = [(INCOME, 'Income'), (EXPENSE, 'Expense')]

    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='categories')

    class Meta:
        unique_together = ('name', 'user')
        ordering = ['type', 'name']

    def __str__(self):
        return f'{self.name} ({self.type})'


class Transaction(models.Model):
    INCOME = 'income'
    EXPENSE = 'expense'
    TYPE_CHOICES = [(INCOME, 'Income'), (EXPENSE, 'Expense')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    note = models.CharField(max_length=500, blank=True, default='')   # was TextField — length now enforced
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f'{self.type} ${self.amount} on {self.date}'


class Budget(models.Model):
    """Monthly spending cap for a category.  One budget per user+category."""
    user     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budgets'
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='budgets'
    )
    monthly_limit = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ('user', 'category')

    def __str__(self):
        return f'{self.category.name}: {self.monthly_limit}/month'


class RecurringTransaction(models.Model):
    """
    Template for automatically repeating income/expense entries.
    Run `python manage.py process_recurring` (e.g. via a daily cron) to
    materialise due entries as real Transaction rows.
    """
    WEEKLY  = 'weekly'
    MONTHLY = 'monthly'
    INTERVAL_CHOICES = [(WEEKLY, 'Weekly'), (MONTHLY, 'Monthly')]

    user     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='recurring_transactions'
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='recurring_transactions'
    )
    type            = models.CharField(max_length=10, choices=Transaction.TYPE_CHOICES)
    amount          = models.DecimalField(max_digits=12, decimal_places=2)
    note            = models.CharField(max_length=500, blank=True, default='')
    interval        = models.CharField(max_length=10, choices=INTERVAL_CHOICES)
    next_occurrence = models.DateField()
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['next_occurrence']

    def __str__(self):
        return f'{self.type} ${self.amount} every {self.interval}'
