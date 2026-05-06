from django.urls import path
from .views import CategoryListCreateView, CategoryDestroyView, TransactionListCreateView, TransactionDetailView

urlpatterns = [
    path('categories/',           CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/',  CategoryDestroyView.as_view(),    name='category-destroy'),
    path('transactions/',          TransactionListCreateView.as_view(), name='transaction-list-create'),
    path('transactions/<int:pk>/', TransactionDetailView.as_view(),    name='transaction-detail'),
]
