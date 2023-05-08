'''
    urls.py in django frame work
'''

from django.urls import path
import main.views as views

urlpatterns = [
    path('startup', views.startup),
    path('user/register', views.user_register),
    path('user/verify/<token>', views.user_mail_verify),
    path('user/salt', views.user_salt),
    path('user/password/<user_id>', views.user_password),
    path('user/login', views.user_login),
    path('user/modifypassword', views.user_modify_password),
    path('user/avatar', views.user_avatar),
    path('user/logout', views.user_logout),
    path('user/checklogin', views.check_user_login),
    path('user/profile/<user_id>', views.user_profile),
    path('user/follow/<user_id>', views.user_follow),
    path('user/unfollow/<user_id>', views.user_unfollow),
    path('user/message', views.user_message),
    path('user/readmessage/<user_id>', views.user_read_message),
    path('user/readhistory', views.user_read_history),
    path('image/upload', views.image_upload),
    path('image/update/<gif_id>', views.image_update_metadata),
    path('image/resize', views.image_upload_resize),
    path('image/resizecheck/<task_id>', views.image_upload_resize_check),
    path('image/video', views.image_upload_video),
    path('image/videocheck/<task_id>', views.image_upload_video_check),
    path('image/watermark/<gif_id>', views.image_watermark),
    path('image/watermarkcheck/<task_id>', views.image_watermark_check),
    path('image/detail/<gif_id>', views.image_detail),
    path('image/preview/<gif_id>', views.image_preview),
    path('image/download/<gif_id>', views.image_download),
    path('image/createlink/<gif_id>', views.image_create_link),
    path('image/downloadzip', views.image_download_zip),
    path('image/createziplink', views.image_create_zip_link),
    path('image/like/<gif_id>', views.image_like),
    path('image/cancellike/<gif_id>', views.image_cancel_like),
    path('image/comment/<gif_id>', views.image_comment),
    path('image/comment/delete/<comment_id>', views.image_comment_delete),
    path('image/comment/like/<comment_id>', views.image_comment_like),
    path('image/comment/cancellike/<comment_id>', views.image_comment_cancel_like),
    path('image/allgifs', views.image_allgifs),
    path('image/search', views.image_search),
    path('image/search/suggest', views.search_suggest),
]
