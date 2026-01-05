from django.contrib import admin
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.custom_login, name='login'),
    path('index', views.index, name ='index'),
    path('register/', views.register, name = 'register'),
    path('logout/', views.custom_logout, name='logout'),
    path('history/', views.search_history, name='search_history'),
    path('history/delete/<int:history_id>/', views.delete_history, name='delete_history'),
    path('history/clear/', views.clear_all_history, name='clear_all_history'),
]
