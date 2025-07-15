from django.contrib import admin
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name ='index'),
    path('login/', views.custom_login, name='login'),
    path('register/', views.register, name = 'register'),
    path('logout/', views.custom_logout, name='logout')
]
