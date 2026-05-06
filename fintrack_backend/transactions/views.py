from rest_framework import generics, permissions
from .models import Category, Transaction
from .serializers import CategorySerializer, TransactionSerializer
from .utils import parse_date_param


class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        # IDOR protection: always scope to the authenticated user
        return Category.objects.filter(user=self.request.user)


class CategoryDestroyView(generics.DestroyAPIView):
    serializer_class = CategorySerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        # IDOR protection: a user can only delete their own categories
        return Category.objects.filter(user=self.request.user)


class TransactionListCreateView(generics.ListCreateAPIView):
    serializer_class = TransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        # IDOR protection: always scope to the authenticated user
        qs = Transaction.objects.filter(user=self.request.user)

        type_filter = self.request.query_params.get('type')
        if type_filter in ('income', 'expense'):
            qs = qs.filter(type=type_filter)

        # Validate category_id is a digit before hitting the DB
        category_id = self.request.query_params.get('category')
        if category_id and category_id.isdigit():
            qs = qs.filter(category_id=int(category_id))

        # Safely parse dates — malformed values are silently ignored (no 500)
        from_date = parse_date_param(self.request.query_params.get('from'))
        if from_date:
            qs = qs.filter(date__gte=from_date)

        to_date = parse_date_param(self.request.query_params.get('to'))
        if to_date:
            qs = qs.filter(date__lte=to_date)

        return qs


class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        # IDOR protection: User A cannot access User B's transaction by ID
        return Transaction.objects.filter(user=self.request.user)
