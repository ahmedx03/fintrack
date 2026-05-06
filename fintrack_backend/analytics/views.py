from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum, Q
from django.db.models.functions import TruncDay, TruncMonth
from transactions.models import Transaction
from transactions.utils import parse_date_param


class SummaryView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        # IDOR: user-scoped query
        qs = Transaction.objects.filter(user=request.user)

        from_date = parse_date_param(request.query_params.get('from'))
        to_date   = parse_date_param(request.query_params.get('to'))
        if from_date:
            qs = qs.filter(date__gte=from_date)
        if to_date:
            qs = qs.filter(date__lte=to_date)

        totals = qs.aggregate(
            total_income=Sum('amount', filter=Q(type='income')),
            total_expenses=Sum('amount', filter=Q(type='expense')),
        )
        income   = totals['total_income']   or 0
        expenses = totals['total_expenses'] or 0
        return Response({'total_income': income, 'total_expenses': expenses, 'balance': income - expenses})


class ByCategoryView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        qs = Transaction.objects.filter(user=request.user)

        tx_type = request.query_params.get('type', 'expense')
        if tx_type in ('income', 'expense'):
            qs = qs.filter(type=tx_type)

        from_date = parse_date_param(request.query_params.get('from'))
        to_date   = parse_date_param(request.query_params.get('to'))
        if from_date:
            qs = qs.filter(date__gte=from_date)
        if to_date:
            qs = qs.filter(date__lte=to_date)

        rows = qs.values('category__name').annotate(total=Sum('amount')).order_by('-total')
        data = [
            {'category': row['category__name'] or 'Uncategorised', 'total': row['total']}
            for row in rows
        ]
        return Response(data)


class OverTimeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        qs = Transaction.objects.filter(user=request.user)

        from_date = parse_date_param(request.query_params.get('from'))
        to_date   = parse_date_param(request.query_params.get('to'))
        if from_date:
            qs = qs.filter(date__gte=from_date)
        if to_date:
            qs = qs.filter(date__lte=to_date)

        period   = request.query_params.get('period', 'month')
        trunc_fn = TruncDay if period == 'day' else TruncMonth

        rows = (
            qs.annotate(period=trunc_fn('date'))
            .values('period')
            .annotate(
                income=Sum('amount', filter=Q(type='income')),
                expenses=Sum('amount', filter=Q(type='expense')),
            )
            .order_by('period')
        )
        data = [
            {
                'date':     row['period'].strftime('%Y-%m-%d'),
                'income':   row['income']   or 0,
                'expenses': row['expenses'] or 0,
                'balance':  (row['income'] or 0) - (row['expenses'] or 0),
            }
            for row in rows
        ]
        return Response(data)
