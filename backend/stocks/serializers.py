from rest_framework import serializers
from .models import StockPrice, Article

class StockPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockPrice
        fields = ['Date', 'Close_Prices', 'High_Prices', 'Low_Prices', 
                 'Open_Prices', 'Volume', 'Symbol', 'Market_Index']

class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = '__all__'