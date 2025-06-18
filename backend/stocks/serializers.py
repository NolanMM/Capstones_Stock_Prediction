from rest_framework import serializers
from .models import StockPrice, Article

class StockPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockPrice
        fields = ['Date', 'Close', 'High', 'Low', 'Open', 'Volume', 'Stock_Symbol']

class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = 'all'