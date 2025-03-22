from django.shortcuts import render
from django.http import JsonResponse
from .models import StockPrice, Article
from .serializers import StockPriceSerializer, ArticleSerializer
from rest_framework import viewsets

# Create your views here.
def index(request):
    return render(request, 'index.html')

def test_connection(request):
    stocks = list(StockPrice.objects.all()[:5].values())
    return JsonResponse({"stocks": stocks, "method": "django_orm"})

class StockPriceViewSet(viewsets.ModelViewSet):
    queryset = StockPrice.objects.all()
    serializer_class = StockPriceSerializer
    
    def get_queryset(self):
        queryset = StockPrice.objects.all()
        stock_name = self.request.query_params.get('name', None)
        if stock_name:
            queryset = queryset.filter(name=stock_name)
        return queryset

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    
    def get_queryset(self):
        queryset = Article.objects.all()
        stock_name = self.request.query_params.get('stock_name', None)
        if stock_name:
            queryset = queryset.filter(stock_name=stock_name)
        return queryset