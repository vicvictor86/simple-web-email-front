from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/<id>', views.dashboard, name='dashboard'),
]