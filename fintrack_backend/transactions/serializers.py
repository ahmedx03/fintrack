from rest_framework import serializers
from .models import Category, Transaction, Budget, RecurringTransaction


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'type')
        read_only_fields = ('id',)

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Transaction
        fields = ('id', 'type', 'amount', 'date', 'note', 'category', 'category_name', 'created_at')
        read_only_fields = ('id', 'created_at', 'category_name')

    def validate_category(self, category):
        user = self.context['request'].user
        if category and category.user != user:
            raise serializers.ValidationError("Invalid category.")
        return category

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class BudgetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model  = Budget
        fields = ('id', 'category', 'category_name', 'monthly_limit')
        read_only_fields = ('id', 'category_name')

    def validate_category(self, category):
        if category.user != self.context['request'].user:
            raise serializers.ValidationError("Invalid category.")
        return category

    def validate(self, attrs):
        user = self.context['request'].user
        category = attrs.get('category')
        if category and Budget.objects.filter(user=user, category=category).exists():
            raise serializers.ValidationError(
                {'category': 'You already have a budget for this category.'}
            )
        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class RecurringTransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model  = RecurringTransaction
        fields = (
            'id', 'type', 'amount', 'note',
            'category', 'category_name',
            'interval', 'next_occurrence', 'is_active', 'created_at',
        )
        read_only_fields = ('id', 'category_name', 'created_at')

    def validate_category(self, category):
        if category and category.user != self.context['request'].user:
            raise serializers.ValidationError("Invalid category.")
        return category

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
