'''
    urls.py in django frame work
'''

from django.urls import path
import main.views as views

urlpatterns = [
    path('startup', views.startup),
    path('user/register', views.user_register),
    # path('login', views.user_login),
    # path('user/<userName>', views.user_board),
]
