from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard_status, name='dashboard_status'),
    path('dashboard/messages/delete/<id>', views.delete_message, name='delete_message'),
    path('dashboard/<id>', views.dashboard, name='dashboard'),
    path('send_message', views.send_message, name='send_message'),
    path('reply_message/<id>', views.reply_message, name='reply_message'),
    path('forward_message/<id>', views.forward_message, name='forward_message'),
    path('get_new_messages/<user_id>', views.get_new_messages, name='get_new_messages'),
]