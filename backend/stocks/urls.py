from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'stocks', views.StockPriceViewSet, basename='stockprice')

urlpatterns = [
    path('test-connection/', views.test_connection, name='test_connection'),
    path('available-stocks/', views.available_stocks, name='available_stocks'),
    path('stock-history/<str:symbol>/', views.stock_history, name='stock_history'),
    path('', include(router.urls)),
]