"""
URL configuration for almanac project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from stocks import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('stocks.urls')),
    path('api/', include('djoser.urls')),
    path('api/', include('djoser.urls.authtoken')),
    
    path('', views.index, name='index'),
    path('portfolio.html', views.portfolio, name='portfolio'),
    path('account.html', views.account, name='account'),
    path('marketprediction.html', views.marketprediction, name='marketprediction'),
    path('register.html', views.register, name='register'),
    path('verify-email-page/', views.verify_email_page, name='verify-email-page'),

    
    # Generic handler 
    path('<str:page_name>/', views.page_handler, name='page_handler'),

    # JSON 
    path('json/chartdata.json', views.chart_data_json, name='chart_data_json'),
    path('json/stocknames.json', views.stock_names_json, name='stock_names_json'),
    path('json/stockdetails.json', views.stock_details_json, name='stock_details_json'),
    path('json/newsarticles.json', views.news_articles_json, name='news_articles_json'),
]
