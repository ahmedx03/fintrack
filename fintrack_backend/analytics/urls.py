from django.urls import path
from .views import SummaryView, ByCategoryView, OverTimeView, BudgetStatusView

urlpatterns = [
    path('summary/',        SummaryView.as_view(),     name='analytics-summary'),
    path('by-category/',    ByCategoryView.as_view(),  name='analytics-by-category'),
    path('over-time/',      OverTimeView.as_view(),     name='analytics-over-time'),
    path('budget-status/',  BudgetStatusView.as_view(), name='analytics-budget-status'),
]
