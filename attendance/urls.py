from django.contrib import admin # 3Add commentMore actions
from django.urls import path, include
from attendance import views
from .views import check_in_out_view, check_in, check_out, dashboard  # Import the correct view

app_name = 'attendance'

urlpatterns = [
     path('dashboard/', views.dashboard, name='dashboard'),
    path('check-in-out/', views.check_in_out_view, name='check_in_out'),
    path('checkin/', views.check_in, name='check_in'),
    path('checkout/', views.check_out, name='check_out'),]