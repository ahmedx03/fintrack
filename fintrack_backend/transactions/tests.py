from rest_framework.test import APITestCase
from rest_framework import status
from users.models import User
from .models import Category, Transaction
import datetime


def make_user(username='pookii', password='StrongPass123!', email='p@example.com'):
    return User.objects.create_user(username=username, password=password, email=email)


def get_token(client, username='pookii', password='StrongPass123!'):
    res = client.post('/api/auth/login/', {'username': username, 'password': password})
    return res.data['access']


class CategoryTests(APITestCase):
    def setUp(self):
        self.user = make_user()
        self.token = get_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_create_category(self):
        res = self.client.post('/api/categories/', {'name': 'Salary', 'type': 'income'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_list_categories_scoped_to_user(self):
        other = make_user('other', email='other@example.com')
        Category.objects.create(name='OtherCat', type='expense', user=other)
        Category.objects.create(name='MyCat', type='expense', user=self.user)
        res = self.client.get('/api/categories/')
        names = [c['name'] for c in res.data]
        self.assertIn('MyCat', names)
        self.assertNotIn('OtherCat', names)

    def test_cannot_delete_other_users_category(self):
        other = make_user('other', email='other@example.com')
        cat = Category.objects.create(name='Food', type='expense', user=other)
        res = self.client.delete(f'/api/categories/{cat.id}/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


class TransactionTests(APITestCase):
    def setUp(self):
        self.user = make_user()
        self.token = get_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.cat_expense = Category.objects.create(name='Food', type='expense', user=self.user)
        self.cat_income = Category.objects.create(name='Salary', type='income', user=self.user)

    def _create_tx(self, **kwargs):
        defaults = {'type': 'expense', 'amount': '50.00', 'date': '2024-05-01', 'category': self.cat_expense.id, 'note': ''}
        defaults.update(kwargs)
        return self.client.post('/api/transactions/', defaults)

    def test_create_transaction(self):
        res = self._create_tx(amount='99.99', note='Groceries')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_filter_by_type(self):
        self._create_tx(type='expense', category=self.cat_expense.id)
        self._create_tx(type='income', category=self.cat_income.id, amount='500.00')
        res = self.client.get('/api/transactions/?type=expense')
        self.assertEqual(len(res.data), 1)

    def test_filter_by_date_range(self):
        self._create_tx(date='2024-03-01')
        self._create_tx(date='2024-05-15')
        self._create_tx(date='2024-07-01')
        res = self.client.get('/api/transactions/?from=2024-04-01&to=2024-06-30')
        self.assertEqual(len(res.data), 1)

    def test_cannot_access_other_users_transactions(self):
        other = make_user('other', email='other@example.com')
        tx = Transaction.objects.create(user=other, type='expense', amount='10.00', date=datetime.date.today())
        res = self.client.get(f'/api/transactions/{tx.id}/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_blocked(self):
        self.client.credentials()
        res = self.client.get('/api/transactions/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
