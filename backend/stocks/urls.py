from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'stocks', views.StockPriceViewSet)
router.register(r'articles', views.ArticleViewSet)

urlpatterns = [
    path('test-connection/', views.test_connection, name='test_connection'),
    path('', include(router.urls)),
]