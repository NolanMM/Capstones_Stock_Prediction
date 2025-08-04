from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApiSignUp, ApiLogin, verify_email_mobile, get_recent_news_sentiment, get_historical_prices_mobile_by_stocks_and_start_date_and_end_date, get_stocks_available_api
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
    path('v2/signup/', ApiSignUp, name='api_v2_signup'),
    path('v2/login/', ApiLogin, name='api_v2_login'),
    path('v2/verify-email-mobile/', verify_email_mobile, name='api_v2_verify_email_mobile'),
    path('stock-news/<str:symbol>/', views.stock_news, name='stock_news'),
    path('get_recent_news/', get_recent_news_sentiment, name='get_recent_news'),
    path('contact-submit/', views.contact_submit, name='contact-submit'),
    path('get_historical_prices_mobile_by_stocks_and_start_date_and_end_date/', get_historical_prices_mobile_by_stocks_and_start_date_and_end_date, name='get_historical_prices_mobile_by_stocks_and_start_date_and_end_date'),
    path('get_stocks_available_api/', get_stocks_available_api, name='get_stocks_available_api'),
    path('', include(router.urls)),
]