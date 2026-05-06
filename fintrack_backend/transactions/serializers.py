from rest_framework import serializers
from .models import Category, Transaction


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
