from django.urls import path, include
import main.views as views

urlpatterns = [
    path('startup', views.startup),
    path('register', views.user_register),
    # path('login', views.user_login),
    # path('user/<userName>', views.user_board),
]
