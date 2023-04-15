'''
    urls.py in django frame work
'''

from django.urls import path
import main.views as views

urlpatterns = [
    path('startup', views.startup),
    path('user/register', views.user_register),
    path('user/salt', views.user_salt),
    path('user/login', views.user_login),
    path('user/modifypassword', views.user_modify_password),
    path('user/logout', views.user_logout),
    path('user/checklogin', views.check_user_login),
    path('user/read_history', views.user_read_history),
    path('image/upload', views.image_upload),
    # path('image/video', views.from_video_to_gif),
    path('image/detail/<gif_id>', views.image_detail),
    path('image/preview/<gif_id>', views.image_preview),
    path('image/download/<gif_id>', views.image_download),
    path('image/download_zip', views.image_download_zip),
    path('image/like', views.image_like),
    path('image/cancel-like', views.image_cancel_like),
    # path('image/comment/<gif_id>', views.image_comment),
    # path('image/comment', views.image_comment),
    path('image/allgifs', views.image_allgifs),
]
