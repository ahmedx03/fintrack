from django.urls import path
from .views import SummaryView, ByCategoryView, OverTimeView

urlpatterns = [
    path('summary/',     SummaryView.as_view(),    name='analytics-summary'),
    path('by-category/', ByCategoryView.as_view(), name='analytics-by-category'),
    path('over-time/',   OverTimeView.as_view(),    name='analytics-over-time'),
]
