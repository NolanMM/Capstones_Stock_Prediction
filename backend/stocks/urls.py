from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'stocks', views.StockPriceViewSet, basename='stockprice')

urlpatterns = [
    path('test-connection/', views.test_connection, name='test_connection'),
    path('available-stocks/', views.available_stocks, name='available_stocks'),
    path('stock-history/<str:symbol>/', views.stock_history, name='stock_history'),
    path('predict-stock/', views.predict_stock, name='predict-stock'),
    path('account/', views.AccountDetail.as_view(), name='account-detail'),
    path('portfolio/', views.PortfolioListCreate.as_view(), name='portfolio-list-create'),
    path('portfolio/<str:stock_symbol>/', views.PortfolioDestroy.as_view(), name='portfolio-destroy'),
    path('login/', views.custom_login, name='custom-login'),
    path('logout/', views.custom_logout, name='custom-logout'),
    path('register/', views.create_user, name='create_user'),
    path('verify-email/', views.verify_email, name='verify-email'),
    path('verify-email-page/', views.verify_email_page, name='verify-email-page'),
    path('stock-news/<str:symbol>/', views.stock_news, name='stock_news'),
    path('contact-submit/', views.contact_submit, name='contact-submit'),
    path('', include(router.urls)),
]