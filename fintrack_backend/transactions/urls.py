from django.urls import path
from .views import (
    CategoryListCreateView, CategoryDestroyView,
    TransactionListCreateView, TransactionDetailView,
    TransactionExportView,
    BudgetListCreateView, BudgetDetailView,
    RecurringTransactionListCreateView, RecurringTransactionDetailView,
)

urlpatterns = [
    # Categories
    path('categories/',           CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/',  CategoryDestroyView.as_view(),    name='category-destroy'),

    # Transactions — export must come before <int:pk> so the literal wins
    path('transactions/',          TransactionListCreateView.as_view(), name='transaction-list-create'),
    path('transactions/export/',   TransactionExportView.as_view(),    name='transaction-export'),
    path('transactions/<int:pk>/', TransactionDetailView.as_view(),    name='transaction-detail'),

    # Budgets
    path('budgets/',           BudgetListCreateView.as_view(), name='budget-list-create'),
    path('budgets/<int:pk>/',  BudgetDetailView.as_view(),    name='budget-detail'),

    # Recurring transactions
    path('recurring/',           RecurringTransactionListCreateView.as_view(), name='recurring-list-create'),
    path('recurring/<int:pk>/',  RecurringTransactionDetailView.as_view(),    name='recurring-detail'),
]
