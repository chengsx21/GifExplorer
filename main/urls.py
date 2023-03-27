'''
    urls.py in django frame work
'''

from django.urls import path
import main.views as views

urlpatterns = [
    path('startup', views.startup),
    path('user/register', views.user_register),
    path('user/login', views.user_login),
    path('user/modifypassword', views.user_modify_password),
    path('user/logout', views.user_logout)
]
