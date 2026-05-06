from rest_framework.test import APITestCase
from rest_framework import status
from users.models import User
from transactions.models import Category, Transaction
import datetime


def make_user(username='pookii', password='StrongPass123!', email='p@example.com'):
    return User.objects.create_user(username=username, password=password, email=email)


class AnalyticsTests(APITestCase):
    def setUp(self):
        self.user = make_user()
        login = self.client.post('/api/auth/login/', {'username': 'pookii', 'password': 'StrongPass123!'})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
        self.food = Category.objects.create(name='Food', type='expense', user=self.user)
        self.salary = Category.objects.create(name='Salary', type='income', user=self.user)
        Transaction.objects.create(user=self.user, type='income', amount=3000, date=datetime.date(2024, 5, 1), category=self.salary)
        Transaction.objects.create(user=self.user, type='expense', amount=200, date=datetime.date(2024, 5, 10), category=self.food)
        Transaction.objects.create(user=self.user, type='expense', amount=50, date=datetime.date(2024, 5, 20), category=self.food)

    def test_summary(self):
        res = self.client.get('/api/analytics/summary/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(float(res.data['total_income']), 3000)
        self.assertEqual(float(res.data['total_expenses']), 250)
        self.assertEqual(float(res.data['balance']), 2750)

    def test_by_category(self):
        res = self.client.get('/api/analytics/by-category/?type=expense')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]['category'], 'Food')
        self.assertEqual(float(res.data[0]['total']), 250)

    def test_over_time_monthly(self):
        res = self.client.get('/api/analytics/over-time/?period=month')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(float(res.data[0]['balance']), 2750)
