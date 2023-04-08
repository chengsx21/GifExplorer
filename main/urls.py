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
    path('user/logout', views.user_logout),
    path('user/checklogin', views.check_user_login),
    path('image/upload', views.image_upload),
    # path('image/video', views.from_video_to_gif),
    path('image/detail/<gif_id>', views.image_detail),
    path('image/preview/<gif_id>', views.image_preview),
    path('image/download/<gif_id>', views.image_download),
    path('image/allgifs', views.image_allgifs),
]
