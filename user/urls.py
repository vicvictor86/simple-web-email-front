from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard_status, name='dashboard_status'),
    path('dashboard/<id>', views.dashboard, name='dashboard'),
    path('send_message', views.send_message, name='send_message')
]