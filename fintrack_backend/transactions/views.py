import csv
from django.http import StreamingHttpResponse
from rest_framework import generics, permissions
from rest_framework.pagination import CursorPagination
from rest_framework.views import APIView

from .models import Category, Transaction, Budget, RecurringTransaction
from .serializers import (
    CategorySerializer, TransactionSerializer,
    BudgetSerializer, RecurringTransactionSerializer,
)
from .utils import parse_date_param, process_recurring_for_user


# ── Cursor pagination for transactions ───────────────────────────────────────────
class TransactionCursorPagination(CursorPagination):
    """
    Stable, tamper-proof pagination suitable for infinite-scroll UIs.
    Clients pass ?cursor=<opaque_value> to advance; the response includes
    'next' and 'previous' cursor URLs.
    """
    page_size             = 25
    ordering              = ['-date', '-created_at']
    cursor_query_param    = 'cursor'
    page_size_query_param = 'page_size'
    max_page_size         = 100


# ── Categories ───────────────────────────────────────────────────────────────────
class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class   = CategorySerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)


class CategoryDestroyView(generics.DestroyAPIView):
    serializer_class   = CategorySerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)


# ── Transactions ─────────────────────────────────────────────────────────────────
def _apply_transaction_filters(qs, query_params):
    """Shared filter logic used by both list and export views."""
    type_filter = query_params.get('type')
    if type_filter in ('income', 'expense'):
        qs = qs.filter(type=type_filter)

    category_id = query_params.get('category')
    if category_id and category_id.isdigit():
        qs = qs.filter(category_id=int(category_id))

    from_date = parse_date_param(query_params.get('from'))
    if from_date:
        qs = qs.filter(date__gte=from_date)

    to_date = parse_date_param(query_params.get('to'))
    if to_date:
        qs = qs.filter(date__lte=to_date)

    return qs


class TransactionListCreateView(generics.ListCreateAPIView):
    serializer_class   = TransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class   = TransactionCursorPagination

    def list(self, request, *args, **kwargs):
        # Lazily fire any due recurring transactions before returning results.
        # This replaces the need for a cron job — schedules are processed the
        # first time the user opens their transactions on or after the due date.
        process_recurring_for_user(request.user)
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        qs = Transaction.objects.filter(user=self.request.user)
        return _apply_transaction_filters(qs, self.request.query_params)


class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = TransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)


# ── CSV export ───────────────────────────────────────────────────────────────────
class _Echo:
    """Minimal write buffer for StreamingHttpResponse."""
    def write(self, value):
        return value


class TransactionExportView(APIView):
    """
    GET /api/transactions/export/

    Streams the authenticated user's transactions as a CSV file.
    Accepts the same ?type, ?category, ?from, ?to filters as the list endpoint.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        qs = Transaction.objects.filter(user=request.user).select_related('category')
        qs = _apply_transaction_filters(qs, request.query_params)

        def rows():
            yield ['date', 'type', 'amount', 'category', 'note']
            for tx in qs:
                yield [
                    tx.date.isoformat(),
                    tx.type,
                    str(tx.amount),
                    tx.category.name if tx.category else '',
                    tx.note,
                ]

        writer   = csv.writer(_Echo())
        response = StreamingHttpResponse(
            (writer.writerow(row) for row in rows()),
            content_type='text/csv',
        )
        response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
        return response


# ── Budgets ──────────────────────────────────────────────────────────────────────
class BudgetListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/budgets/  — list the user's budgets
    POST /api/budgets/  — create a budget (one per category)
    """
    serializer_class   = BudgetSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user).select_related('category')


class BudgetDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/budgets/<id>/
    PATCH  /api/budgets/<id>/  — update monthly_limit
    DELETE /api/budgets/<id>/
    """
    serializer_class   = BudgetSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names  = ['get', 'patch', 'delete']

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)


# ── Recurring transactions ───────────────────────────────────────────────────────
class RecurringTransactionListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/recurring/  — list recurring schedules
    POST /api/recurring/  — create a new schedule
    """
    serializer_class   = RecurringTransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return RecurringTransaction.objects.filter(
            user=self.request.user
        ).select_related('category')


class RecurringTransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/recurring/<id>/
    PATCH  /api/recurring/<id>/  — e.g. pause (is_active=False) or change amount
    DELETE /api/recurring/<id>/
    """
    serializer_class   = RecurringTransactionSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names  = ['get', 'patch', 'delete']

    def get_queryset(self):
        return RecurringTransaction.objects.filter(user=self.request.user)
