import datetime
from django.db.models import Sum, Q
from django.db.models.functions import TruncDay, TruncMonth
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from transactions.models import Transaction, Budget
from transactions.utils import parse_date_param


class SummaryView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
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
        return Response({
            'total_income':   income,
            'total_expenses': expenses,
            'balance':        income - expenses,
        })


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


class BudgetStatusView(APIView):
    """
    GET /api/analytics/budget-status/

    Returns each of the user's budgets alongside how much has been spent
    in the current calendar month, giving the frontend everything it needs
    to render a progress bar.

    Response shape (per budget):
    {
        "category":      "Food",
        "monthly_limit": "500.00",
        "spent":         "320.00",
        "remaining":     "180.00",
        "percent_used":  64.0
    }
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        today           = datetime.date.today()
        first_of_month  = today.replace(day=1)

        budgets = (
            Budget.objects
            .filter(user=request.user)
            .select_related('category')
        )

        data = []
        for budget in budgets:
            spent = (
                Transaction.objects
                .filter(
                    user=request.user,
                    category=budget.category,
                    type='expense',
                    date__gte=first_of_month,
                    date__lte=today,
                )
                .aggregate(total=Sum('amount'))['total']
            ) or 0

            limit        = budget.monthly_limit
            remaining    = limit - spent
            percent_used = (
                round(float(spent) / float(limit) * 100, 1) if limit > 0 else 0
            )
            data.append({
                'category':      budget.category.name,
                'monthly_limit': limit,
                'spent':         spent,
                'remaining':     remaining,
                'percent_used':  percent_used,
            })

        return Response(data)
