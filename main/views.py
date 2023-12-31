'''
    views.py in django frame work
'''
import zipfile
import os
import uuid
import math
import json
from wsgiref.util import FileWrapper
import io
import time
import datetime
import imghdr
import imageio
import imagehash
from jwt import DecodeError
from PIL import Image, ImageDraw, ImageFont, ImageSequence
from celery import shared_task
from django.core.files.base import ContentFile
from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.core.files import File
from django.utils.html import format_html
from django.db.models import Q
from django.http import HttpResponseRedirect
from utils.utils_request import not_found_error, unauthorized_error, format_error, request_failed, request_success
from GifExplorer import settings
from . import helpers
from .helpers import handle_errors
from . import config
from .models import UserInfo, UserVerification, GifMetadata, GifFile, GifComment, Message, GifShare, TaskInfo

# Create your views here.
@csrf_exempt
@handle_errors
def startup(req: HttpRequest):
    '''
        test deployment
    '''
    if req.method == "GET":
        return HttpResponse("Congratulations! Go ahead!")

@csrf_exempt
@handle_errors
def user_register(req: HttpRequest):
    '''
    request:
        {
            "user_name": "Alice",
            "password": "Happy-Day1",
            "salt": "secret_salt",
            "mail": "test@example.com"
        }
    response:
        {
            "code": 0,
            "message": "SUCCESS",
            "data": {
                "id": 1,
                "user_name": "Alice",
                "token": "SECRET_TOKEN"
            }
        }
    '''
    if req.method == "POST":
        try:
            body = json.loads(req.body.decode("utf-8"))
            user_name = body["user_name"]
            password = body["password"]
            salt = body["salt"]
            mail = body["mail"]
        except (TypeError, KeyError) as error:
            print(error)
            return format_error(str(error))

        if not helpers.user_username_checker(user_name):
            return request_failed(2, "INVALID_USER_NAME_FORMAT", data={"data": {}})
        if not isinstance(password, str):
            return request_failed(3, "INVALID_PASSWORD_FORMAT", data={"data": {}})

        user = UserVerification.objects.filter(user_name=user_name).first()
        if user:
            if user.is_verified is True:
                return request_failed(1, "USER_NAME_CONFLICT", data={"data": {}})
            created_at = user.created_at.timestamp()
            current_time = datetime.datetime.now().timestamp()
            if current_time - created_at <= config.USER_VERIFICATION_MAX_TIME and user.is_verified is False:
                return request_failed(1, "USER_NAME_CONFLICT", data={"data": {}})
            user.delete()

        verification_token = str(uuid.uuid4())
        print(verification_token)
        verification_link = f'https://gifexplorer-frontend-nullptr.app.secoder.net/signup/verify?token={verification_token}'
        vertificated_user = UserVerification.objects.create(user_name=user_name,
                                                            token=verification_token,
                                                            mail=mail,
                                                            password=helpers.hash_password(password),
                                                            salt=salt,
                                                            created_at=datetime.datetime.now())
        vertificated_user.save()

        subject = 'GifExplorer 注册'
        message = format_html('欢迎注册 GifExplorer!\
            请点击<a href="{}" style="display: block; text-align: center; font-weight: bold">{}</a>验证您的账户。\
            验证链接有效时长为五分钟。\
            若您没有进行注册操作，请忽略这封邮件。', verification_link, '这里')
        recipient = [mail]
        send_mail(subject=subject, message='', html_message=message, from_email=settings.EMAIL_HOST_USER, recipient_list=recipient)

        return request_success(data={"data": {}})
    return not_found_error()

@csrf_exempt
@handle_errors
def user_mail_verify(req: HttpRequest, token: str):
    '''
    request:
        verify user's email.
    '''
    if req.method == "GET":
        user = UserVerification.objects.filter(token=token).first()
        if not user:
            return request_failed(15, "INVALID_TOKEN", data={"data": {}})
        if user.is_verified is True:
            return request_failed(16, "ALREADY_VERIFIED", data={"data": {}})
        created_at = user.created_at.timestamp()
        current_time = datetime.datetime.now().timestamp()
        if current_time - created_at > config.USER_VERIFICATION_MAX_TIME and user.is_verified is False:
            return request_failed(17, "TOO_LONG_TIME", data={"data": {}})
        user.is_verified = True
        user.save()
        new_user = UserInfo(user_name=user.user_name, password=user.password, salt=user.salt, mail=user.mail)
        new_user.save()
        user_token = helpers.create_token(user_id=new_user.id, user_name=new_user.user_name)
        return_data = {
            "data": {
                "id": new_user.id,
                "user_name": new_user.user_name,
                "token": user_token
            }
        }
        helpers.add_token_to_white_list(user_token)
        return request_success(return_data)
    return not_found_error()

@csrf_exempt
@handle_errors
def user_salt(req: HttpRequest):
    '''
    request:
        {
            "user_name": "FirstUser",
        }
    response:
        {
            "code": 0,
            "info": "SUCCESS",
            "data": {
                "salt": "SECRET_SALT"
            }
        }
    '''
    if req.method == "POST":
        try:
            body = json.loads(req.body.decode("utf-8"))
            user_name = body["user_name"]
        except (TypeError, KeyError) as error:
            print(error)
            return format_error(str(error))

        user = UserInfo.objects.filter(user_name=user_name).first()
        if not user:
            return request_failed(4, "USER_NAME_NOT_EXISTS_OR_WRONG_PASSWORD", data={"data": {}})
        return_data = {
            "data": {
                "salt": user.salt
            }
        }
        return request_success(return_data)
    return not_found_error()

@csrf_exempt
@handle_errors
def user_password(req: HttpRequest, user_id: any):
    '''
    request:
        None
    response:
        {
            "code": 0,
            "info": "SUCCESS",
            "data": {
                "salt": "SECRET_SALT"
            }
        }
    '''
    if req.method == "POST":
        user = UserInfo.objects.filter(id=user_id).first()
        if not user:
            return request_failed(4, "USER_NAME_NOT_EXISTS_OR_WRONG_PASSWORD", data={"data": {}})
        return_data = {
            "data": {
                "password": user.password
            }
        }
        return request_success(return_data)
    return not_found_error()

@csrf_exempt
@handle_errors
def user_login(req: HttpRequest):
    '''
    request:
        {
            "user_name": "FirstUser",
            "password": "Hashed-Word"
        }
    response:
        {
            "code": 0,
            "info": "SUCCESS",
            "data": {
                "id": 1,
                "user_name": "FirstUser",
                "token": "SECRET_TOKEN"
            }
        }
    '''
    if req.method == "POST":
        try:
            body = json.loads(req.body.decode("utf-8"))
            user_name = body["user_name"]
            password = body["password"]
        except (TypeError, KeyError) as error:
            print(error)
            return format_error(str(error))
        if not helpers.user_username_checker(user_name):
            return request_failed(2, "INVALID_USER_NAME_FORMAT", data={"data": {}})
        if not isinstance(password, str):
            return request_failed(3, "INVALID_PASSWORD_FORMAT", data={"data": {}})

        user = UserInfo.objects.filter(user_name=user_name).first()
        if not user:  # user name not existed yet.
            return request_failed(4, "USER_NAME_NOT_EXISTS_OR_WRONG_PASSWORD", data={"data": {}})
        if helpers.check_password(password, user.password):
            user_token = helpers.create_token(user_id=user.id, user_name=user.user_name)
            return_data = {
                "data": {
                    "id": user.id,
                    "user_name": user_name,
                    "token": user_token
                }
            }
            helpers.add_token_to_white_list(user_token)
            return request_success(return_data)
        return request_failed(4, "USER_NAME_NOT_EXISTS_OR_WRONG_PASSWORD", data={"data": {}})
    return not_found_error()

@csrf_exempt
@handle_errors
def user_modify_password(req: HttpRequest):
    '''
    request:
        {
            "user_name": "Alice",
            "old_password": "Bob19937",
            "new_password": "Carol48271"
        }
    response:
        {
            "code": 0,
            "info": "SUCCESS",
            "data": {}
        }
    '''
    if req.method == "POST":
        try:
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
        except DecodeError as error:
            print(error)
            return unauthorized_error(str(error))
        try:
            body = json.loads(req.body.decode("utf-8"))
            user_name = body["user_name"]
            old_password = body["old_password"]
            new_password = body["new_password"]
        except (TypeError, KeyError) as error:
            print(error)
            return format_error(str(error))

        if not user_name == token["user_name"]:
            return unauthorized_error()

        user = UserInfo.objects.filter(user_name=user_name).first()
        if not user:  # user name not existed yet.
            return request_failed(4, "USER_NAME_NOT_EXISTS_OR_WRONG_PASSWORD", data={"data": {}})
        if not helpers.check_password(old_password, user.password):
            return request_failed(4, "USER_NAME_NOT_EXISTS_OR_WRONG_PASSWORD", data={"data": {}})
        user.password = helpers.hash_password(new_password)
        user.save()
        return request_success(data={"data": {}})
    return not_found_error()

@csrf_exempt
@handle_errors
def user_avatar(req: HttpRequest):
    '''
    request:
        - user token
        - avatar file
    '''
    try:
        encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
        token = helpers.decode_token(encoded_token)
        if not helpers.is_token_valid(token=encoded_token):
            return unauthorized_error()
    except DecodeError as error:
        print(error)
        return unauthorized_error(str(error))
    user_name = token["user_name"]
    user = UserInfo.objects.filter(user_name=user_name).first()
    if not user:
        return unauthorized_error()
    if req.method == "POST":
        file = req.FILES.get("file")
        if not file:
            return request_failed(18, "AVATAR_NOT_FOUND", data={"data": {}})
        img_format = imghdr.what(file.file)
        if img_format not in ["jpeg", "png"]:
            return request_failed(18, "AVATAR_NOT_FOUND", data={"data": {}})
        resized_image = helpers.image_resize(file.file)
        user.avatar = "data:image/png;base64," + helpers.image_to_base64(resized_image)
        user.save()

        return_data = {
            "data": {
                "id": user.id,
                "user_name": user.user_name,
                "avatar": user.avatar
            }
        }
        return request_success(return_data)
    if req.method == "GET":
        return_data = {
            "data": {
                "id": user.id,
                "user_name": user.user_name,
                "avatar": user.avatar
            }
        }
        return request_success(return_data)
    return not_found_error()

@csrf_exempt
@handle_errors
def user_signature(req: HttpRequest):
    '''
    request:
        - user token
        - user signature
    '''
    if req.method == "POST":
        try:
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
        except DecodeError as error:
            print(error)
            return unauthorized_error(str(error))
        user_name = token["user_name"]
        user = UserInfo.objects.filter(user_name=user_name).first()
        if not user:
            return unauthorized_error()
        try:
            body = json.loads(req.body.decode("utf-8"))
            signature = body["signature"]
        except (TypeError, KeyError) as error:
            print(error)
            return format_error(str(error))
        user.signature = signature
        user.save()

        return_data = {
            "data": {
                "id": user.id,
                "user_name": user.user_name,
                "signature": user.signature
            }
        }
        return request_success(return_data)
    return not_found_error()

@csrf_exempt
@handle_errors
def user_logout(req: HttpRequest):
    '''
    request:
        token in 'HTTP_AUTHORIZATION'.
    response:
        nothing
    '''
    if req.method == "POST":
        try:
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            if helpers.is_token_valid(token=encoded_token):
                helpers.delete_token_from_white_list(token=encoded_token)
                if not helpers.is_token_valid(token=encoded_token):
                    return request_success(data={"data": {}})
        except DecodeError as error:
            print(error)
            return unauthorized_error(str(error))
        return unauthorized_error()
    return not_found_error()

@csrf_exempt
@handle_errors
def check_user_login(req: HttpRequest):
    '''
    request:
        None
    response:
        Return if user is logged in
    '''
    if req.method == "POST":
        try:
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            if helpers.is_token_valid(token=encoded_token):
                return request_success(data={"data": {}})
            return unauthorized_error()
        except DecodeError as error:
            print(error)
            return unauthorized_error(str(error))
    return not_found_error()

@csrf_exempt
@handle_errors
def user_profile(req: HttpRequest, user_id: any):
    '''
    request:
        - None
    response:
        - status
    '''
    if req.method == "GET":
        if not isinstance(user_id, str) or not user_id.isdigit():
            return format_error()

        user = UserInfo.objects.filter(id=int(user_id)).first()
        if not user:
            return request_failed(12, "USER_NOT_FOUND", data={"data": {}})
        profile_gifs = GifMetadata.objects.filter(uploader=int(user_id))
        profile_gifs = profile_gifs.order_by('-pub_time')
        gifs = []
        for gif in profile_gifs:
            gifs.append({
                "id": gif.id,
                "title": gif.title,
                "width": gif.width,
                "height": gif.height,
                "category": gif.category,
                "tags": gif.tags,
                "duration": gif.duration,
                "pub_time": gif.pub_time,
                "like": gif.likes,
            })

        is_followed = False
        if req.META.get("HTTP_AUTHORIZATION"):
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
            current_user = UserInfo.objects.filter(id=token["id"]).first()
            if str(user.id) in current_user.followings:
                is_followed = True

        return_data = {
            "data": {
                "id": user.id,
                "user_name": user.user_name,
                "signature": user.signature,
                "mail": user.mail,
                "avatar": user.avatar,
                "followers": len(user.followers),
                "following": len(user.followings),
                "register_time": user.register_time,
                "data": gifs,
                "is_followed": is_followed
            }
        }
        return request_success(return_data)
    return not_found_error()

@csrf_exempt
@handle_errors
def user_follow(req: HttpRequest, user_id: any):
    '''
    request:
        - user token is needed
    response:
        - status
    '''
    if req.method == "POST":
        try:
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
        except DecodeError as error:
            print(error)
            return unauthorized_error(str(error))

        user_name = token["user_name"]
        user = UserInfo.objects.filter(user_name=user_name).first()
        if not user:
            return unauthorized_error()
        if not isinstance(user_id, str) or not user_id.isdigit():
            return format_error()

        follow_user = UserInfo.objects.filter(id=int(user_id)).first()
        if not follow_user:
            return request_failed(12, "USER_NOT_FOUND", data={"data": {}})
        if follow_user == user:
            return request_failed(13, "CANNOT_FOLLOW_SELF", data={"data": {}})
        if str(follow_user.id) not in user.followings:
            if not user.followings:
                user.followings = {}
            if not follow_user.followers:
                follow_user.followers = {}
            user.followings[str(follow_user.id)] = str(datetime.datetime.now())
            user.save()
            follow_user.followers[str(user.id)] = str(datetime.datetime.now())
            follow_user.save()
            return request_success(data={"data": {}})
        else:
            return request_failed(14, "INVALID_FOLLOWS", data={"data": {}})
    return not_found_error()

@csrf_exempt
@handle_errors
def user_unfollow(req: HttpRequest, user_id: any):
    '''
    request:
        - user token is needed
    response:
        - status
    '''
    if req.method == "POST":
        try:
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
        except DecodeError as error:
            print(error)
            return unauthorized_error(str(error))

        user_name = token["user_name"]
        user = UserInfo.objects.filter(user_name=user_name).first()
        if not user:
            return unauthorized_error()
        if not isinstance(user_id, str) or not user_id.isdigit():
            return format_error()

        follow_user = UserInfo.objects.filter(id=int(user_id)).first()
        if not follow_user:
            return request_failed(12, "USER_NOT_FOUND", data={"data": {}})
        if follow_user == user:
            return request_failed(13, "CANNOT_FOLLOW_SELF", data={"data": {}})
        if str(follow_user.id) in user.followings:
            user.followings.pop(str(follow_user.id))
            user.save()
            follow_user.followers.pop(str(user.id))
            follow_user.save()
            return request_success(data={"data": {}})
        else:
            return request_failed(14, "INVALID_FOLLOWS", data={"data": {}})
    return not_found_error()

@csrf_exempt
@handle_errors
def user_get_followers(req: HttpRequest, user_id: any):
    '''
    request:
        - None
    response:
        - List of followers of user
    '''
    if req.method == "GET":
        if not isinstance(user_id, str) or not user_id.isdigit():
            return format_error()
        user = UserInfo.objects.filter(id=int(user_id)).first()
        if not user:
            return request_failed(12, "USER_NOT_FOUND", data={"data": {}})
        try:
            page = int(req.GET.get("page"))
        except (TypeError, ValueError) as error:
            print(error)
            return request_failed(6, "INVALID_PAGES", data={"data": {"error": str(error)}})
        user_followers_list, pages = helpers.show_user_followers(user, page - 1)
        return request_success(data={
            "data": {
                "page_count": pages,
                "page_data": user_followers_list
            }
        })
    return not_found_error()

@csrf_exempt
@handle_errors
def user_get_followings(req: HttpRequest, user_id: any):
    '''
    request:
        - None
    response:
        - List of followings of user
    '''
    if req.method == "GET":
        if not isinstance(user_id, str) or not user_id.isdigit():
            return format_error()
        user = UserInfo.objects.filter(id=int(user_id)).first()
        if not user:
            return request_failed(12, "USER_NOT_FOUND", data={"data": {}})
        try:
            page = int(req.GET.get("page"))
        except (TypeError, ValueError) as error:
            print(error)
            return request_failed(6, "INVALID_PAGES", data={"data": {"error": str(error)}})
        user_followings_list, pages = helpers.show_user_followings(user, page - 1)
        return request_success(data={
            "data": {
                "page_count": pages,
                "page_data": user_followings_list
            }
        })
    return not_found_error()

@csrf_exempt
@handle_errors
def user_message_list(req: HttpRequest):
    '''
    request:
        - User token is needed.
    response:
        - List of user messages
    '''
    if req.method == "GET":
        try:
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
        except DecodeError as error:
            print(error)
            return unauthorized_error(str(error))
        user_name = token["user_name"]
        user = UserInfo.objects.filter(user_name=user_name).first()
        if not user:
            return unauthorized_error()
        try:
            page = int(req.GET.get("page"))
        except (TypeError, ValueError) as error:
            print(error)
            return request_failed(6, "INVALID_PAGES", data={"data": {"error": str(error)}})
        user_messages_list, pages = helpers.get_user_message_list(user, page - 1)
        return_data = {
            "data": {
                "page_count": pages,
                "page_data": user_messages_list
            }
        }
        return request_success(return_data)
    return not_found_error()

@csrf_exempt
@handle_errors
def user_post_message(req: HttpRequest):
    '''
    request:
        {
            "user_id": 2,
            "message": "Test Message"
        }
        User token is needed.
    response:
        {
            "code": 0,
            "info": "Succeed",
            "data": {
                "2": [
                    {
                        "sender": 2,
                        "receiver": 1,
                        "message": "Test",
                        "pub_time": "2023-05-04T16:15:01.718Z"
                    },
                    {
                        "sender": 1,
                        "receiver": 2,
                        "message": "Test Again",
                        "pub_time": "2023-05-04T15:56:53.066Z"
                    }
                ]
            }
        }
    '''
    if req.method == "POST":
        try:
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
        except DecodeError as error:
            print(error)
            return unauthorized_error(str(error))

        user_name = token["user_name"]
        sender = UserInfo.objects.filter(user_name=user_name).first()
        if not sender:
            return unauthorized_error()

        try:
            body = json.loads(req.body.decode("utf-8"))
            user_id = body["user_id"]
            message = body["message"]
        except (TypeError, KeyError) as error:
            print(error)
            return format_error(str(error))
        if not (user_id and message and isinstance(user_id, int) and isinstance(message, str)):
            return format_error()

        receiver = UserInfo.objects.filter(id=user_id).first()
        if not receiver:
            return request_failed(12, "USER_NOT_FOUND", data={"data": {}})
        if receiver == sender:
            return request_failed(22, "CANNOT_MESSAGE_SELF", data={"data": {}})
        new_message = Message.objects.create(sender=sender, receiver=receiver, message=message)
        return_data = {
            "data": {
                "sender": sender.id,
                "receiver": receiver.id,
                "message": message,
                "pub_time": new_message.pub_time
            }
        }
        return request_success(data=return_data)
    return not_found_error()

@csrf_exempt
@handle_errors
def user_read_message(req: HttpRequest, user_id: any):
    '''
    request:
        - User token is needed.
    response:
        - User messages list
    '''
    if req.method == "GET":
        try:
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
        except DecodeError as error:
            print(error)
            return unauthorized_error(str(error))

        try:
            page = int(req.GET.get("page"))
        except (TypeError, ValueError) as error:
            print(error)
            return request_failed(6, "INVALID_PAGES", data={"data": {"error": str(error)}})

        user_name = token["user_name"]
        user = UserInfo.objects.filter(user_name=user_name).first()
        if not user:
            return unauthorized_error()
        if not isinstance(user_id, str) or not user_id.isdigit():
            return format_error()

        user_id = int(user_id)
        other_user = UserInfo.objects.filter(id=user_id).first()
        if not other_user:
            return request_failed(12, "USER_NOT_FOUND", data={"data": {}})
        if other_user == user:
            return request_failed(22, "CANNOT_MESSAGE_SELF", data={"data": {}})

        messages = Message.objects.filter(sender=other_user, receiver=user)
        for single_message in messages:
            single_message.is_read = True
            single_message.save()

        user_messages_list, pages = helpers.show_user_message_page(user, other_user, page - 1)
        return_data = {
            "data": {
                "page_count": pages,
                "page_data": user_messages_list
            }
        }
        return request_success(return_data)

    return not_found_error()

@csrf_exempt
@handle_errors
def user_info(req: HttpRequest, user_id: any):
    '''
    request:
        - None
    response:
        - status
    '''
    if req.method == "GET":
        if not isinstance(user_id, str) or not user_id.isdigit():
            return format_error()

        user = UserInfo.objects.filter(id=int(user_id)).first()
        if not user:
            return request_failed(12, "USER_NOT_FOUND", data={"data": {}})

        is_followed = False
        if req.META.get("HTTP_AUTHORIZATION"):
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
            current_user = UserInfo.objects.filter(id=token["id"]).first()
            if str(user.id) in current_user.followings:
                is_followed = True

        return_data = {
            "data": {
                "id": user.id,
                "user_name": user.user_name,
                "signature": user.signature,
                "avatar": user.avatar,
                "is_followed": is_followed
            }
        }
        return request_success(return_data)
    return not_found_error()

@csrf_exempt
@handle_errors
def user_read_history(req: HttpRequest):
    '''
    request:
        - gif_id
        - user token is needed
    response:
        - status
    '''
    try:
        encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
        token = helpers.decode_token(encoded_token)
        if not helpers.is_token_valid(token=encoded_token):
            return unauthorized_error()
    except DecodeError as error:
        print(error)
        return unauthorized_error(str(error))

    user_name = token["user_name"]
    user = UserInfo.objects.filter(user_name=user_name).first()
    if not user:
        return unauthorized_error()

    if req.method == "POST":
        try:
            gif_id = int(req.GET.get("id"))
        except (TypeError, ValueError) as error:
            print(error)
            return format_error(str(error))
        gif = GifMetadata.objects.filter(id=gif_id).first()
        if not gif:
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})

        if not user.read_history:
            user.read_history = {}
        user.read_history[str(gif_id)] = str(datetime.datetime.now())
        user.save()
        tags = gif.tags
        helpers.update_user_tags(user, tags)
        return request_success(data={"data": {}})

    if req.method == "GET":
        try:
            page = int(req.GET.get("page"))
        except (TypeError, ValueError) as error:
            print(error)
            return request_failed(6, "INVALID_PAGES", data={"data": {"error": str(error)}})
        read_history_list, pages = helpers.show_user_read_history_pages(user, page - 1)
        return request_success(data=
            {
                "data": {
                    "page_count": pages,
                    "page_data": read_history_list
                }
            })
    return not_found_error()


@csrf_exempt
@handle_errors
def user_search_history(req: HttpRequest):
    '''
    request:
        - user token is needed
    response:
        - search_history
    '''
    try:
        encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
        token = helpers.decode_token(encoded_token)
        if not helpers.is_token_valid(token=encoded_token):
            return unauthorized_error()
    except DecodeError as error:
        print(error)
        return unauthorized_error(str(error))

    user_name = token["user_name"]
    user = UserInfo.objects.filter(user_name=user_name).first()
    if not user:
        return unauthorized_error()

    if req.method == "GET":
        search_history = helpers.get_user_search_history(user)
        all_search_history = []
        for search_content, search_time in search_history:
            all_search_history.append({
                "keyword": search_content,
                "search_time": search_time
            })
        return_data = {
            "data": {
                "search_data": all_search_history
            }
        }
        return request_success(return_data)

    if req.method == "DELETE":
        search_content = req.GET.get("history")
        helpers.delete_user_search_history(user, search_content)
        return request_success(data={"data": {}})
    return not_found_error()

@csrf_exempt
@handle_errors
def user_personalize(req: HttpRequest):
    '''
    request:
        - user token is needed
    response:
        - recommended gif id list
    '''
    if req.method == "GET":
        try:
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
        except DecodeError as error:
            print(error)
            return unauthorized_error(str(error))

        user_name = token["user_name"]
        user = UserInfo.objects.filter(user_name=user_name).first()
        if not user:
            return unauthorized_error()
        search_engine = config.SEARCH_ENGINE
        tags = helpers.get_user_tags(user)
        suggest_gif_list = search_engine.personalization_search(tags)
        gifs = []
        for gif_id in suggest_gif_list:
            gif = GifMetadata.objects.filter(id=gif_id).first()
            if gif:
                gif_user = UserInfo.objects.filter(id=gif.uploader).first()
                gifs.append({
                    "id": gif.id,
                    "title": gif.title,
                    "width": gif.width,
                    "height": gif.height,
                    "category": gif.category,
                    "tags": gif.tags,
                    "duration": gif.duration,
                    "pub_time": gif.pub_time,
                    "like": gif.likes,
                    "uploader_id": gif.uploader,
                    "uploader": gif_user.user_name,
                })
            if len(gifs) >= 10:
                break

        return_data = {"data": gifs}
        return request_success(return_data)
    return not_found_error()

@csrf_exempt
@handle_errors
def image_upload(req: HttpRequest):
    '''
    request:
        {
            "title": "Wonderful Gif",
            "category": "animals"
            "tags": ["funny", "cat"]
        }
        Tip: The gif file is sent within the request!
    response:
        {
            "code": 0,
            "info": "SUCCESS",
            "data": {
                "id": 1,
                "width": 640,
                "height": 480,
                "duration": 5.2,
                "uploader": 3, 
                "pub_time": "2023-03-21T19:02:16.305Z",
                }
        }
    '''
    if req.method == "POST":
        try:
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
        except DecodeError as error:
            print(error)
            return unauthorized_error(str(error))

        try:
            title = req.POST.get("title")
            category = req.POST.get("category")
            tags = req.POST.getlist("tags")[0]
            tags = [tag.strip() for tag in tags.split(",")]
        except (TypeError, KeyError) as error:
            print(error)
            return format_error(str(error))

        if not (title and category and tags and isinstance(title, str) and isinstance(category, str) and isinstance(tags, list)):
            return format_error()
        for tag in tags:
            if not isinstance(tag, str):
                return format_error()

        user = UserInfo.objects.filter(id=token["id"]).first()
        if not user:
            return unauthorized_error()

        file_contents = req.FILES.get("file").read()
        name = req.FILES.get("file").name
        if file_contents[0:6] != b'GIF89a' and file_contents[0:6] != b'GIF87a':
            return request_failed(10, "INVALID_GIF", data={"data": {}})

        file_obj = io.BytesIO(file_contents)
        image = Image.open(file_obj)
        gif_fingerprint = imagehash.average_hash(image, hash_size=16)
        fingerprint = helpers.add_gif_fingerprint_to_list(gif_fingerprint)
        if fingerprint.gif_id != 0:
            return_data = {
                "data": {
                    "id": fingerprint.gif_id,
                    "duplication": True                    
                }
            }
            return request_success(return_data)

        gif = GifMetadata.objects.create(title=title, uploader=user.id, category=category, tags=tags)
        gif_file = GifFile.objects.create(metadata=gif, file=req.FILES.get("file"))
        gif_file.save()
        fingerprint.gif_id = gif.id
        fingerprint.save()

        with Image.open(gif_file.file) as image:
            durations = [image.info.get("duration")] * image.n_frames
            if not durations[0]:
                durations = [100] * image.n_frames
            total_time = sum(durations) / 1000.0
        width = gif_file.file.width
        height = gif_file.file.height
        path = gif_file.file.path
        gif.duration = total_time
        gif.width = width
        gif.height = height
        gif.name = name
        gif.save()

        resize_path = path.rsplit("/", 1)[0] + "/resize_" + path.rsplit("/", 1)[1]
        max_size = min(width, height, 150)
        ratio = width / height
        new_width = int(max_size * math.sqrt(ratio))
        new_height = int(max_size / math.sqrt(ratio))
        resize_size = (new_width, new_height)
        with Image.open(path) as img:
            frames = []
            for frame in ImageSequence.Iterator(img):
                resized_frame = frame.resize(resize_size, Image.ANTIALIAS)
                frames.append(resized_frame)
            frames[0].save(resize_path, save_all=True, append_images=frames[1:], disposal=2)

        if os.getenv('DEPLOY') is not None:
            helpers.post_search_metadata(user, gif)

        if user.user_name != "spider":
            helpers.post_message_to_fans(user, gif.id)

        return_data = {
            "data": {
                "id": gif.id,
                "duplication": False
            }
        }
        return request_success(return_data)
    return not_found_error()

@csrf_exempt
@handle_errors
def image_update_metadata(req, gif_id):
    '''
    request:
        {
            "category": "animals",
            "tags": ["funny", "cat"]
        }
    response:
        {
            "code": 0,
            "info": "SUCCESS",
            "data": {
                "id": 1
        }
    '''
    if req.method == "POST":
        try:
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
        except DecodeError as error:
            print(error)
            return unauthorized_error(str(error))

        try:
            body = json.loads(req.body.decode("utf-8"))
            category = body["category"]
            tags = body["tags"]
        except (TypeError, ValueError) as error:
            print(error)
            return format_error(str(error))

        if not (category and tags and isinstance(category, str) and isinstance(tags, list)):
            return format_error()
        for tag in tags:
            if not isinstance(tag, str):
                return format_error()
        user = UserInfo.objects.filter(id=token["id"]).first()
        if not user:
            return unauthorized_error()
        gif = GifMetadata.objects.filter(id=gif_id).first()
        if not gif:
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})

        gif.category = category
        gif.tags = tags
        gif.save()

        if os.getenv('DEPLOY') is not None:
            helpers.post_search_metadata(user, gif)

        return_data = {
            "data": {
                "id": gif.id
            }
        }
        return request_success(return_data)
    return not_found_error()

@csrf_exempt
@handle_errors
def image_upload_resize(req: HttpRequest):
    '''
    request:
        same as image_upload except that the resize parameter is added
    response:
        {
            "code": 0,
            "info": "SUCCESS",
            "data": {
                "id": 1,
                "width": 640,
                "height": 480,
                "duration": 5.2,
                "uploader": 3, 
                "pub_time": "2023-03-21T19:02:16.305Z",
                }
        }
    '''
    if req.method == "POST":
        try:
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
        except DecodeError as error:
            print(error)
            return unauthorized_error(str(error))

        try:
            title = req.POST.get("title")
            category = req.POST.get("category")
            tags = req.POST.getlist("tags")[0]
            tags = [tag.strip() for tag in tags.split(",")]
            ratio = req.POST.get("ratio")
        except (TypeError, KeyError) as error:
            print(error)
            return format_error(str(error))

        if not helpers.is_float_string(ratio):
            return request_failed(21, "INVALID_RATIO", data={"data": {}})
        if not (title and category and tags and isinstance(title, str) and isinstance(category, str) and isinstance(tags, list)):
            return format_error()
        for tag in tags:
            if not isinstance(tag, str):
                return format_error()

        user = UserInfo.objects.filter(id=token["id"]).first()
        if not user:
            return unauthorized_error()

        file_contents = req.FILES.get("file").read()
        file = req.FILES.get("file")
        name = file.name
        img = Image.open(io.BytesIO(file_contents))
        width, height = img.size
        if file_contents[0:6] != b'GIF89a' and file_contents[0:6] != b'GIF87a':
            return request_failed(10, "INVALID_GIF", data={"data": {}})

        with open(name, 'wb') as temp_gif:
            for chunk in file.chunks():
                temp_gif.write(chunk)
        task_info = TaskInfo.objects.create(task_type="resize", task_status="STARTED")
        task = image_upload_resize_task.delay(title=title, category=category, tags=tags, user=user.id, name=name, ratio=ratio, width=width, height=height, task_id=task_info.id)
        if not user.task_history:
            user.task_history = {}
        user.task_history[str(task.id)] = str(datetime.datetime.now())
        user.save()
        task_info.task_id = task.id
        task_info.save()
        return_data = {
            "data": {
                "task_id": task.id,
                "task_status": task.status
            }
        }
        return request_success(return_data)
    return not_found_error()

@shared_task
def image_upload_resize_task(*, title: str, category: str, tags: list, user: int, name: str, ratio: float, width: int, height: int, task_id: int):
    '''
        resize a gif
    '''
    try:
        resize_size = (int(width * float(ratio)), int(height * float(ratio)))
        with Image.open(name) as img:
            frames = []
            for frame in ImageSequence.Iterator(img):
                resized_frame = frame.resize(resize_size, Image.ANTIALIAS)
                frames.append(resized_frame)
            output_file = io.BytesIO()
            frames[0].save(output_file, format='GIF', save_all=True, append_images=frames[1:], disposal=2)

        image = Image.open(output_file)
        gif_fingerprint = imagehash.average_hash(image, hash_size=16)
        fingerprint = helpers.add_gif_fingerprint_to_list(gif_fingerprint)
        if fingerprint.gif_id != 0:
            os.remove(name)
            return_data = {
                "id": fingerprint.gif_id,
                "duplication": True
            }
            task = TaskInfo.objects.filter(id=task_id).first()
            task.task_status = "SUCCESS"
            task.task_result = return_data
            task.save()
            return return_data

        gif = GifMetadata.objects.create(title=title, uploader=user, category=category, tags=tags)
        gif_file = GifFile.objects.create(metadata=gif)
        gif_file.file.save(name, File(output_file))
        gif_file.save()
        fingerprint.gif_id = gif.id
        fingerprint.save()

        with Image.open(gif_file.file) as image:
            durations = [image.info.get("duration")] * image.n_frames
            if not durations[0]:
                durations = [100] * image.n_frames
            total_time = sum(durations) / 1000.0
        width = gif_file.file.width
        height = gif_file.file.height
        path = gif_file.file.path
        gif.duration = total_time
        gif.width = width
        gif.height = height
        gif.name = name
        gif.save()

        resize_path = path.rsplit("/", 1)[0] + "/resize_" + path.rsplit("/", 1)[1]
        max_size = min(width, height, 150)
        ratio = width / height
        new_width = int(max_size * math.sqrt(ratio))
        new_height = int(max_size / math.sqrt(ratio))
        resize_size = (new_width, new_height)
        with Image.open(path) as img:
            frames = []
            for frame in ImageSequence.Iterator(img):
                resized_frame = frame.resize(resize_size, Image.ANTIALIAS)
                frames.append(resized_frame)
            frames[0].save(resize_path, save_all=True, append_images=frames[1:], disposal=2)

        os.remove(name)
        upload_user = UserInfo.objects.filter(id=user).first()
        if os.getenv('DEPLOY') is not None:
            helpers.post_search_metadata(upload_user, gif)

        if upload_user.user_name != "spider":
            helpers.post_message_to_fans(upload_user, gif.id)

        return_data = {
            "id": gif.id,
            "duplication": False
        }
        task = TaskInfo.objects.filter(id=task_id).first()
        task.task_status = "SUCCESS"
        task.task_result = return_data
        task.save()
        return return_data
    except Exception as error:
        print(error)
        task = TaskInfo.objects.filter(id=task_id).first()
        task.task_status = "FAILURE"
        task.save()
        return_data = {
            "error": str(error)
        }
        return return_data

@csrf_exempt
@handle_errors
def image_detail(req: HttpRequest, gif_id: any):
    '''
    GET:
    request:
        None
    response:
        {
            "code": 0,
            "info": "SUCCESS",
            "data": {
                "id": 514,
                "title": "Wonderful Gif",
                "uploader": "AliceBurn", 
                "width": gif.width,
                "height": gif.height,
                "category": "animals",
                "tags": ["funny", "cat"],
                "duration": gif.duration,
                "pub_time": "2023-03-21T19:02:16.305Z",
                "like": 114514,
                "isliked": True
            }
        }
    DELETE:
    request:
        None
    response:
        {
            "code": 0,
            "info": "SUCCESS",
            "data": {}
        }
        {
            "code": 9,
            "info": "GIFS_NOT_FOUND",
            "data": {}
        }
        {
            "code": 1,
            "info": "USER_NAME_CONFLICT",
            "data": {}
        }
    '''
    if req.method == "GET":
        if not isinstance(gif_id, str) or not gif_id.isdecimal():
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})

        gif = GifMetadata.objects.filter(id=gif_id).first()
        if not gif:
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})
        user = UserInfo.objects.filter(id=gif.uploader).first()

        is_liked = False
        is_followed = False
        if req.META.get("HTTP_AUTHORIZATION"):
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
            current_user = UserInfo.objects.filter(id=token["id"]).first()
            if str(gif.id) in current_user.favorites:
                is_liked = True
            if str(user.id) in current_user.followings:
                is_followed = True

        return_data = {
            "data": {
                "gif_data": {
                    "id": gif.id,
                    "title": gif.title,
                    "uploader": user.user_name,
                    "width": gif.width,
                    "height": gif.height,
                    "category": gif.category,
                    "tags": gif.tags,
                    "duration": gif.duration,
                    "pub_time": gif.pub_time,
                    "like": gif.likes,
                    "is_liked": is_liked,
                },
                "user_data": {
                    "id": user.id,
                    "user_name": user.user_name,
                    "signature": user.signature,
                    "mail": user.mail,
                    "avatar": user.avatar,
                    "followers": len(user.followers),
                    "following": len(user.followings),
                    "register_time": user.register_time,
                    "is_followed": is_followed
                }
            }
        }
        return request_success(return_data)
    if req.method == "DELETE":
        try:
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
        except DecodeError as error:
            print(error)
            return unauthorized_error(str(error))
        if not isinstance(gif_id, str) or not gif_id.isdecimal():
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})

        gif = GifMetadata.objects.filter(id=gif_id).first()
        if not gif:
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})
        if gif.uploader != token["id"]:
            return unauthorized_error()

        helpers.delete_gif_fingerprint_from_list(gif_id)
        os.remove(gif.giffile.file.path)
        gif.delete()
        return request_success(data={"data": {}})
    return not_found_error()

@csrf_exempt
@handle_errors
def image_preview_low_resolution(req: HttpRequest, gif_id: any):
    '''
    request:
        None
    response:
        Return a HttpResponse including the gif for preview
    '''
    if req.method == "GET":
        if not isinstance(gif_id, str) or not gif_id.isdecimal():
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})

        gif = GifMetadata.objects.filter(id=int(gif_id)).first()
        if not gif:
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})
        path = gif.giffile.file.path
        resize_path = path.rsplit("/", 1)[0] + "/resize_" + path.rsplit("/", 1)[1]
        try:
            gif_file = open(resize_path, 'rb')
        except FileNotFoundError:
            gif_file = open(path, 'rb')
        file_wrapper = FileWrapper(gif_file)
        response = HttpResponse(file_wrapper, content_type='image/gif', headers={'Access-Control-Allow-Origin': '*'})
        response['Content-Disposition'] = f'inline; filename="{gif.name}"'
        return response
    return not_found_error()

@csrf_exempt
@handle_errors
def image_preview(req: HttpRequest, gif_id: any):
    '''
    request:
        None
    response:
        Return a HttpResponse including the gif for preview
    '''
    if req.method == "GET":
        if not isinstance(gif_id, str):
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})
        if len(gif_id) == 12:
            gif_share = GifShare.objects.filter(token=gif_id).first()
            if not gif_share:
                return HttpResponseRedirect('https://gifexplorer-frontend-nullptr.app.secoder.net/image/not-found')
            pub_time = gif_share.pub_time.timestamp()
            current_time = datetime.datetime.now().timestamp()
            if current_time - pub_time > config.GIF_EXTERNAL_LINK_MAX_TIME:
                gif_share.delete()
                return HttpResponseRedirect('https://gifexplorer-frontend-nullptr.app.secoder.net/image/not-found')
            gif_id = gif_share.gif_ids[0]
        if not gif_id.isdecimal():
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})

        gif = GifMetadata.objects.filter(id=int(gif_id)).first()
        if not gif:
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})
        gif_file = open(gif.giffile.file.path, 'rb')
        file_wrapper = FileWrapper(gif_file)
        response = HttpResponse(file_wrapper, content_type='image/gif', headers={'Access-Control-Allow-Origin': '*'})
        response['Content-Disposition'] = f'inline; filename="{gif.name}"'
        return response
    return not_found_error()

@csrf_exempt
@handle_errors
def image_download(req: HttpRequest, gif_id: any):
    '''
    request:
        None
    response:
        Return a HttpResponse including the gif for download
    '''
    if req.method == "GET":
        if not isinstance(gif_id, str):
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})
        if len(gif_id) == 12:
            gif_share = GifShare.objects.filter(token=gif_id).first()
            if not gif_share:
                return HttpResponseRedirect('https://gifexplorer-frontend-nullptr.app.secoder.net/image/not-found')
            pub_time = gif_share.pub_time.timestamp()
            current_time = datetime.datetime.now().timestamp()
            if current_time - pub_time > config.GIF_EXTERNAL_LINK_MAX_TIME:
                gif_share.delete()
                return HttpResponseRedirect('https://gifexplorer-frontend-nullptr.app.secoder.net/image/not-found')
            gif_id = gif_share.gif_ids[0]
        if not gif_id.isdecimal():
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})

        gif = GifMetadata.objects.filter(id=int(gif_id)).first()
        if not gif:
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})
        gif_file = open(gif.giffile.file.path, 'rb')
        file_wrapper = FileWrapper(gif_file)
        response = HttpResponse(file_wrapper, content_type='application/octet-stream', headers={'Access-Control-Allow-Origin': '*'})
        response['Content-Disposition'] = f'attachment; filename="{gif.name}"'
        return response
    return not_found_error()

@csrf_exempt
@handle_errors
def image_create_link(req: HttpRequest, gif_id: any):
    '''
    request:
        - gif_id: the id of the gif
    response:
        - return the preview and download link of the gif
    '''
    if req.method == "GET":
        if not isinstance(gif_id, str) or not gif_id.isdecimal():
            return format_error()

        gif = GifMetadata.objects.filter(id=int(gif_id)).first()
        if not gif:
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})
        token = helpers.generate_token()
        GifShare.objects.create(token=token, gif_ids=[gif_id])
        if os.getenv('DEPLOY') is None:
            preview_url = "http://127.0.0.1:8000/image/preview/" + token
            download_url = "http://127.0.0.1:8000/image/download/" + token
        else:
            preview_url = "https://gifexplorer-backend-nullptr.app.secoder.net/image/preview/" + token
            download_url = "https://gifexplorer-backend-nullptr.app.secoder.net/image/download/" + token
        return_data = {
            "data": {
                "preview_link": preview_url,
                "download_link": download_url
            }
        }
        return request_success(return_data)
    return not_found_error()

@csrf_exempt
@handle_errors
def image_download_zip(req: HttpRequest):
    '''
    request:
        - gif_ids: a comma-separated list of GIF ids
    response:
        Return a HttpResponse including a zip file containing the requested gifs for download
    '''
    if req.method == "GET":
        token = req.GET.get("token")
        gif_share = GifShare.objects.filter(token=token).first()
        if not gif_share:
            return HttpResponseRedirect('https://gifexplorer-frontend-nullptr.app.secoder.net/image/not-found')
        pub_time = gif_share.pub_time.timestamp()
        current_time = datetime.datetime.now().timestamp()
        if current_time - pub_time > config.GIF_EXTERNAL_LINK_MAX_TIME:
            gif_share.delete()
            return HttpResponseRedirect('https://gifexplorer-frontend-nullptr.app.secoder.net/image/not-found')
        gif_ids = gif_share.gif_ids
        gifs = GifMetadata.objects.filter(id__in=gif_ids)

        if len(gifs) != len(gif_ids):
            return HttpResponseRedirect('https://gifexplorer-frontend-nullptr.app.secoder.net/image/not-found')
    elif req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        gif_ids = body["gif_ids"]
        if not gif_ids:
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})

        gifs = GifMetadata.objects.filter(id__in=gif_ids)

        if len(gifs) != len(gif_ids):
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})
    else:
        return not_found_error()
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode='w') as zip_file:
        for gif in gifs:
            hashed_title = str(uuid.uuid4())[0:6] + '_' + gif.title
            gif_file = open(gif.giffile.file.path, 'rb')
            zip_file.writestr(f"{hashed_title}.gif", gif_file.read())
            gif_file.close()

    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip', headers={'Access-Control-Allow-Origin': '*'})
    cur_time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    response['Content-Disposition'] = f'attachment; filename="{cur_time}.zip"'
    return response

@csrf_exempt
@handle_errors
def image_create_zip_link(req: HttpRequest):
    '''
    request:
        - gif_id: the id of the gif
    response:
        - return the preview and download link of the gif
    '''
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        gif_ids = body["gif_ids"]
        if not gif_ids or not isinstance(gif_ids, list):
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})
        gifs = GifMetadata.objects.filter(id__in=gif_ids)
        if len(gifs) != len(gif_ids):
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})

        token = helpers.generate_token()
        GifShare.objects.create(token=token, gif_ids=gif_ids)
        if os.getenv('DEPLOY') is None:
            downloadzip_url = "http://127.0.0.1:8000/image/downloadzip?token=" + token
        else:
            downloadzip_url = "https://gifexplorer-backend-nullptr.app.secoder.net/image/downloadzip?token=" + token
        return_data = {
            "data": {
                "downloadzip_link": downloadzip_url
            }
        }
        return request_success(return_data)
    return not_found_error()

@csrf_exempt
@handle_errors
def image_like(req: HttpRequest, gif_id: any):
    '''
    request:
        - gif_id
        - user token is needed
    response:
        - status
    '''
    if req.method == "POST":
        try:
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
        except DecodeError as error:
            print(error)
            return unauthorized_error(str(error))

        if not isinstance(gif_id, str) or not gif_id.isdigit():
            return format_error()
        gif_id = int(gif_id)

        gif = GifMetadata.objects.filter(id=gif_id).first()
        if not gif:
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})

        user = UserInfo.objects.filter(id=token["id"]).first()
        if not user:
            return unauthorized_error()
        if str(gif_id) not in user.favorites:
            user.favorites[str(gif_id)] = str(datetime.datetime.now())
            tags = gif.tags
            helpers.update_user_tags(user, tags)
            user.save()
            gif.likes += 1
            gif.save()
            return request_success(data={"data": {}})
        else:
            return request_failed(5, "INVALID_LIKES", data={"data": {}})
    return not_found_error()

@csrf_exempt
@handle_errors
def image_cancel_like(req: HttpRequest, gif_id: any):
    '''
    request:
        - user token is needed
    response:
        - status
    '''
    if req.method == "POST":
        try:
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
        except DecodeError as error:
            print(error)
            return unauthorized_error(str(error))

        if not isinstance(gif_id, str) or not gif_id.isdigit():
            return format_error()
        gif_id = int(gif_id)

        gif = GifMetadata.objects.filter(id=gif_id).first()
        if not gif:
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})

        user = UserInfo.objects.filter(id=token["id"]).first()
        if not user:
            return unauthorized_error()
        if str(gif_id) in user.favorites:
            user.favorites.pop(str(gif_id))
            user.save()
            gif.likes -= 1
            gif.save()
            return request_success(data={"data": {}})
        else:
            return request_failed(5, "INVALID_LIKES", data={"data": {}})
    return not_found_error()

@csrf_exempt
@handle_errors
def image_upload_video(req: HttpRequest):
    '''
    request:
        {
            "title": "Wonderful Gif",
            "category": "animals"
            "tags": ["funny", "cat"]
        }
        Tip: The video file is sent within the request!
    response:
        {
            "code": 0,
            "info": "SUCCESS",
            "data": {
                "task_id": "ec1e476d-4f95-4d5e-94f3-b094de82c500",
                "task_status": "PENDING"
            }
        }
    '''
    if req.method == "POST":
        try:
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
        except DecodeError as error:
            print(error)
            return unauthorized_error(str(error))

        try:
            title = req.POST.get("title")
            category = req.POST.get("category")
            tags = req.POST.getlist("tags")[0]
            tags = [tag.strip() for tag in tags.split(",")]
            name = req.FILES.get("file").name.rsplit(".", 1)[0]
            hashed_name = name + str(uuid.uuid4())[0:8]
        except (TypeError, KeyError) as error:
            print(error)
            return format_error(str(error))

        if not (isinstance(title, str) and isinstance(category, str) and isinstance(tags, list)):
            return format_error()
        for tag in tags:
            if not isinstance(tag, str):
                return format_error()

        user = UserInfo.objects.filter(id=token["id"]).first()
        if not user:
            return unauthorized_error()

        video_file = req.FILES.get("file")
        if not helpers.is_valid_video(video_file):
            return request_failed(19, "INVALID_VIDEO", data={"data": {}})
        if not video_file:
            return format_error()
        with open(hashed_name + ".mp4", 'wb') as temp_video:
            for chunk in video_file.chunks():
                temp_video.write(chunk)
        task_info = TaskInfo.objects.create(task_type="video", task_status="STARTED")
        task = image_upload_video_task.delay(title=title, category=category, tags=tags, user=user.id, hashed_name=hashed_name, task_id=task_info.id)
        if not user.task_history:
            user.task_history = {}
        user.task_history[str(task.id)] = str(datetime.datetime.now())
        user.save()
        task_info.task_id = task.id
        task_info.save()
        return_data = {
            "data": {
                "task_id": task.id,
                "task_status": task.status
            }
        }
        return request_success(data=return_data)
    return not_found_error()

@shared_task
def image_upload_video_task(*, title: str, category: str, tags: list, user: int, hashed_name: str, task_id: int):
    '''
        mp4/mkv -> gif
    '''
    try:
        video = imageio.get_reader(hashed_name + ".mp4")
        fps = video.get_meta_data()['fps']
        gif_frames = []
        for i, frame in enumerate(video):
            height = frame.shape[0]
            width = frame.shape[1]
            if i % 3 == 0:
                gif_frames.append(frame[:, :, :3])
        imageio.mimsave(hashed_name + ".gif", gif_frames, duration=1000/fps, loop=0)

        path = hashed_name + ".gif"
        new_path = "_" + hashed_name + ".gif"
        max_size = min(width, height, 300)
        ratio = width / height
        new_width = int(max_size * math.sqrt(ratio))
        new_height = int(max_size / math.sqrt(ratio))
        resize_size = (new_width, new_height)
        with Image.open(path) as img:
            frames = []
            for frame in ImageSequence.Iterator(img):
                resized_frame = frame.resize(resize_size, Image.ANTIALIAS)
                frames.append(resized_frame)
            frames[0].save(new_path, save_all=True, append_images=frames[1:], disposal=2)

        gif = GifMetadata.objects.create(title=title, uploader=user, category=category, tags=tags)
        gif_file = GifFile.objects.create(metadata=gif, file=new_path)

        with open(new_path, 'rb') as temp_gif:
            gif_file.file.save(new_path, ContentFile(temp_gif.read()))
        gif_file.save()

        with Image.open(gif_file.file) as image:
            duration = image.info['duration'] * image.n_frames
        gif.duration = duration / 1000.0
        gif.width = gif_file.file.width
        gif.height = gif_file.file.height
        gif.name = gif_file.file.name
        gif.save()
        os.remove(hashed_name + ".mp4")
        os.remove(path)
        os.remove(new_path)

        path = gif_file.file.path
        resize_path = path.rsplit("/", 1)[0] + "/resize_" + path.rsplit("/", 1)[1]
        max_size = min(width, height, 150)
        ratio = width / height
        new_width = int(max_size * math.sqrt(ratio))
        new_height = int(max_size / math.sqrt(ratio))
        resize_size = (new_width, new_height)
        with Image.open(path) as img:
            frames = []
            for frame in ImageSequence.Iterator(img):
                resized_frame = frame.resize(resize_size, Image.ANTIALIAS)
                frames.append(resized_frame)
            frames[0].save(resize_path, save_all=True, append_images=frames[1:], disposal=2)

        upload_user = UserInfo.objects.filter(id=user).first()
        if os.getenv('DEPLOY') is not None:
            helpers.post_search_metadata(upload_user, gif)

        if upload_user.user_name != "spider":
            helpers.post_message_to_fans(upload_user, gif.id)

        return_data = {
            "id": gif.id,
            "duplication": False
        }
        task = TaskInfo.objects.filter(id=task_id).first()
        task.task_status = "SUCCESS"
        task.task_result = return_data
        task.save()
        return return_data
    except Exception as error:
        print(error)
        task = TaskInfo.objects.filter(id=task_id).first()
        task.task_status = "FAILURE"
        task.save()
        return_data = {
            "error": str(error)
        }
        return return_data

@csrf_exempt
@handle_errors
def image_watermark(req: HttpRequest, gif_id: any):
    '''
    request:
        user token
    '''
    if req.method == "POST":
        try:
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
        except DecodeError as error:
            print(error)
            return unauthorized_error(str(error))

        gif = GifMetadata.objects.filter(id=gif_id).first()
        if not gif:
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})

        user = UserInfo.objects.filter(user_name=token["user_name"]).first()
        if not user or user.id != gif.uploader:
            return unauthorized_error()

        task_info = TaskInfo.objects.create(task_type="watermark", task_status="STARTED")
        task = image_watermark_task.delay(gif_id=gif_id, user_name=user.user_name, task_id=task_info.id)
        if not user.task_history:
            user.task_history = {}
        user.task_history[str(task.id)] = str(datetime.datetime.now())
        user.save()
        task_info.task_id = task.id
        task_info.save()
        return_data = {
            "data": {
                "task_id": task.id,
                "task_status": task.status
            }
        }
        return request_success(data=return_data)
    return not_found_error()

@shared_task
def image_watermark_task(gif_id: int, user_name: str, task_id: int):
    '''
        add watermark to a gif in the database
    '''
    try:
        gif = GifMetadata.objects.filter(id=gif_id).first()
        text = '@' + user_name
        font_path = "files/tests/Songti.ttf"
        font_size = 16
        with Image.open(gif.giffile.file.path) as img:
            frames = []
            for frame in ImageSequence.Iterator(img):
                watermark_image = Image.new('RGBA', frame.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(watermark_image, 'RGBA')
                font = ImageFont.truetype(font_path, font_size, encoding="unic")
                text_width, text_height = draw.textsize(text=text, font=font)
                x_axis = frame.width - text_width - 10
                y_axis = frame.height - text_height - 10
                if x_axis < 0 or y_axis < 0:
                    return_data = {
                        "id": gif.id,
                        "code": 20,
                        "info": "GIF_TOO_SMALL",
                    }
                    task = TaskInfo.objects.filter(id=task_id).first()
                    task.task_status = "FAILURE"
                    task.task_result = return_data
                    task.save()
                    return return_data
                draw.text((x_axis, y_axis), text, font=font, fill=(0, 0, 0, 255))
                frame = Image.alpha_composite(frame.convert('RGBA'), watermark_image)
                frames.append(frame)
            frames[0].save(gif.giffile.file.path, save_all=True, append_images=frames[1:], disposal=2)
        return_data = {"id": gif.id}
        task = TaskInfo.objects.filter(id=task_id).first()
        task.task_status = "SUCCESS"
        task.task_result = return_data
        task.save()
        return return_data
    except Exception as error:
        print(error)
        task = TaskInfo.objects.filter(id=task_id).first()
        task.task_status = "FAILURE"
        task.save()
        return_data = {
            "error": str(error)
        }
        return return_data

@csrf_exempt
@handle_errors
def image_task_check(req: HttpRequest):
    '''
    request:
        User token
    response:
        {
            "code": 0,
            "info": "SUCCESS",
            "data": [
                {
                    "task_id": "ec1e476d-4f95-4d5e-94f3-b094de82c500",
                    "task_type": "watermark",
                    "task_status": "PENDING",
                    "task_time": "2023-04-15T13:56:38.484Z"
                },
                {
                    "task_id": "efe4811e-bdbf-49e0-80ad-a93749159cd0",
                    "task_type": "video"
                    "task_status": "SUCCESS",
                    "task_result": {
                        "id": 6
                    }
                }
            ]
        }
    '''
    if req.method == "GET":
        try:
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
        except DecodeError as error:
            print(error)
            return unauthorized_error(str(error))

        user = UserInfo.objects.filter(id=token["id"]).first()
        task_ids = user.task_history
        user_task_list = []

        task_ids = dict(sorted(list(task_ids.items()), key=lambda x: x[1], reverse=True))
        for task_id, _ in task_ids.items():
            task = TaskInfo.objects.filter(task_id=task_id).first()
            if task.task_status == "STARTED":
                created_at = task.task_time.timestamp()
                current_time = datetime.datetime.now().timestamp()
                if current_time - created_at >= config.TASK_HANDLING_MAX_TIME:
                    return_data = {
                        "code": 23,
                        "info": "TOO_LONG_TIME"
                    }
                    task.task_status = "FAILURE"
                    task.task_result = return_data
                    task.save()
            data = {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "task_status": task.task_status,
                "task_time": task.task_time
            }
            if task.task_result:
                data['task_result'] = task.task_result
            user_task_list.append(data)

        return_data = {
            "data": {
                "task_count": len(task_ids),
                "task_data": user_task_list
            }
        }
        return request_success(return_data)
    return not_found_error()

@csrf_exempt
@handle_errors
def image_comment(req: HttpRequest, gif_id: any):
    '''
    GET:
    request:
        None
    response:
        {
            "code": 0,
            "info": "SUCCESS",
            "data": [
                {
                    "id": 2,
                    "user": "Test1",
                    "content": "这是一条测试评论",
                    "pub_time": "2023-04-15T13:56:39.518Z",
                    "like": 1919,
                    "replies": []
                },
                {
                    "id": 1,
                    "user": "Test1",
                    "content": "测试评论",
                    "pub_time": "2023-04-15T13:56:38.484Z",
                    "like": 810,
                    "replies": [
                        {
                            "id": 3,
                            "user": "Test2",
                            "content": "评论",
                            "pub_time": "2023-04-15T13:56:43.351Z",
                            "like": 123
                        }
                    ]
                }
            ]
            
        }
    POST:
    request:
        User Token
        {
            "content": "这是一条测试评论",
            "parent_id": 10
        }
    response:
        {
            "code": 0,
            "info": "Succeed",
            "data": {
                "id": 5,
                "user": "Test",
                "content": "这是一条测试评论",
                "pub_time": "2023-04-15T14:41:21.525Z"
            }
        }
        {
            "code": 9,
            "info": "GIFS_NOT_FOUND",
            "data": {}
        }
        {
            "code": 11,
            "info": "COMMENTS_NOT_FOUND",
            "data": {}
        }
    '''
    if req.method == "POST":
        try:
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
        except DecodeError as error:
            print(error)
            return unauthorized_error(str(error))
        try:
            body = json.loads(req.body)
            content = body["content"]
            parent_id = body.get("parent_id")
        except (TypeError, KeyError) as error:
            print(error)
            return format_error(str(error))

        if not (isinstance(gif_id, str) and isinstance(content, str) and gif_id.isdigit()):
            return format_error()

        user = UserInfo.objects.filter(id=token["id"]).first()
        if not user:
            return unauthorized_error()

        gif = GifMetadata.objects.filter(id=int(gif_id)).first()
        if not gif:
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})

        if parent_id:
            parent = GifComment.objects.filter(parent__isnull=True, id=parent_id).first()
            if not parent:
                return request_failed(11, "COMMENTS_NOT_FOUND", data={"data": {}})
            comment = GifComment.objects.create(metadata=gif, user=user, content=content, parent=parent)
        else:
            comment = GifComment.objects.create(metadata=gif, user=user, content=content)
        comment.save()
        return_data = {
            "data": {
                "id": comment.id,
                "user": user.user_name,
                "content": comment.content,
                "pub_time": comment.pub_time
            }
        }
        return request_success(return_data)
    if req.method == "GET":
        if not isinstance(gif_id, str) or not gif_id.isdigit():
            return format_error()
        gif = GifMetadata.objects.filter(id=int(gif_id)).first()
        if not gif:
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})

        login = False
        if req.META.get("HTTP_AUTHORIZATION"):
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
            user = UserInfo.objects.filter(id=token["id"]).first()
            if not user:
                return unauthorized_error()
            login = True

        comments = gif.comments.all().filter(parent__isnull=True)
        comments = comments.order_by('-pub_time')
        comments_data = []
        for comment in comments:
            is_liked = False
            if login and str(comment.id) in user.comment_favorites:
                is_liked = True
            comment_data = {
                "id": comment.id,
                "user": comment.user.user_name,
                "avatar": comment.user.avatar,
                "content": comment.content,
                "pub_time": comment.pub_time,
                "like": comment.likes,
                "is_liked": is_liked
            }
            replies_data = []
            replies = comment.replies.all().order_by('-pub_time')
            for reply in replies:
                is_liked = False
                if login and str(reply.id) in user.comment_favorites:
                    is_liked = True
                reply_data = {
                    "id": reply.id,
                    "user": reply.user.user_name,
                    "avatar": reply.user.avatar,
                    "content": reply.content,
                    "pub_time": reply.pub_time,
                    "like": reply.likes,
                    "is_liked": is_liked
                }
                replies_data.append(reply_data)
            comment_data["replies"] = replies_data
            comments_data.append(comment_data)
        return_data = {
            "data": comments_data
        }
        return request_success(return_data)
    return not_found_error()

@csrf_exempt
@handle_errors
def image_comment_delete(req: HttpRequest, comment_id: any):
    '''
    request:
        user token
    response:
        {
            "code": 0,
            "info": "Succeed",
            "data": {}
        }
        {
            "code": 11,
            "info": "COMMENTS_NOT_FOUND",
            "data": {}
        }
        {
            "code": 1001,
            "info": "UNAUTHORIZED",
            "data": {}
        }
    '''
    if req.method == "DELETE":
        try:
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
        except DecodeError as error:
            print(error)
            return unauthorized_error(str(error))

        if not isinstance(comment_id, str) or not comment_id.isdigit():
            return format_error()

        comment = GifComment.objects.filter(id=int(comment_id)).first()
        if not comment:
            return request_failed(11, "COMMENTS_NOT_FOUND", data={"data": {}})
        user = UserInfo.objects.filter(id=token["id"]).first()
        if not (user and comment.user == user):
            return unauthorized_error()

        comment.delete()
        return request_success(data={"data": {}})
    return not_found_error()

@csrf_exempt
@handle_errors
def image_comment_like(req: HttpRequest, comment_id: any):
    '''
    request:
        - user token is needed
    response:
        - status
    '''
    if req.method == "POST":
        try:
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
        except DecodeError as error:
            print(error)
            return unauthorized_error(str(error))

        if not isinstance(comment_id, str) or not comment_id.isdigit():
            return format_error()

        comment = GifComment.objects.filter(id=int(comment_id)).first()
        if not comment:
            return request_failed(11, "COMMENTS_NOT_FOUND", data={"data": {}})
        user = UserInfo.objects.filter(id=token["id"]).first()
        if not user:
            return unauthorized_error()

        if not user.comment_favorites:
            user.comment_favorites = []
        if comment_id not in user.comment_favorites:
            user.comment_favorites.append(comment_id)
            user.save()
            comment.likes += 1
            comment.save()
            return request_success(data={"data": {}})
        else:
            return request_failed(5, "INVALID_LIKES", data={"data": {}})
    return not_found_error()

@csrf_exempt
@handle_errors
def image_comment_cancel_like(req: HttpRequest, comment_id: any):
    '''
    request:
        - user token is needed
    response:
        - status
    '''
    if req.method == "POST":
        try:
            encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
            token = helpers.decode_token(encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return unauthorized_error()
        except DecodeError as error:
            print(error)
            return unauthorized_error(str(error))

        if not isinstance(comment_id, str) or not comment_id.isdigit():
            return format_error()

        comment = GifComment.objects.filter(id=int(comment_id)).first()
        if not comment:
            return request_failed(11, "COMMENTS_NOT_FOUND", data={"data": {}})
        user = UserInfo.objects.filter(id=token["id"]).first()
        if not user:
            return unauthorized_error()

        if not user.comment_favorites:
            user.comment_favorites = []
        if comment_id in user.comment_favorites:
            user.comment_favorites.remove(comment_id)
            user.save()
            comment.likes -= 1
            comment.save()
            return request_success(data={"data": {}})
        else:
            return request_failed(5, "INVALID_LIKES", data={"data": {}})
    return not_found_error()

@csrf_exempt
@handle_errors
def image_allgifs(req: HttpRequest):
    '''
    request:
        {
            "category": "sports"
        }
    response:
        {
            "code": 0,
            "info": "SUCCESS",
            "data": [
                {
                    "id": 514,
                    "title": "Wonderful Gif",
                    "category": "sports",
                    "uploader": "AliceBurn", 
                    "pub_time": "2023-03-21T19:02:16.305Z",
                },
                {
                    "id": 519,
                    "title": "Strong Man",
                    "category": "sports",
                    "uploader": "AliceBurn", 
                    "pub_time": "2023-03-21T19:02:16.305Z",
                }
            ]
        }
    '''
    if req.method == "POST":
        try:
            body = json.loads(req.body.decode("utf-8"))
            req_category = body["category"]
        except (TypeError, KeyError) as error:
            print(error)
            return format_error()

        if not isinstance(req_category, str):
            return format_error()
        if req_category in config.CATEGORY_LIST:
            category = config.CATEGORY_LIST[req_category]
        else:
            category = config.CATEGORY_LIST[""]

        gifs = GifMetadata.objects.filter(category=category).order_by('-pub_time')[:200]
        if not gifs:
            return request_success(data={})
        gifs_list = []
        for gif in gifs:
            user = UserInfo.objects.filter(id=gif.uploader).first()
            gif_dict = {
                "id": gif.id,
                "title": gif.title,
                "category": gif.category,
                "uploader": user.user_name,
                "pub_time": gif.pub_time
            }
            gifs_list.append(gif_dict)
        return request_success({"data": gifs_list})
    return not_found_error()

@csrf_exempt
@handle_errors
def image_search(req: HttpRequest):
    '''
    request:
        {
            "target": "title",
            "keyword": "cat picture",
            "filter": [
                {"range": {"width": {"gte": 0, "lte": 100}}},
                {"range": {"height": {"gte": 0, "lte": 100}}},
                {"range": {"duration": {"gte": 0, "lte": 100}}}
            ],
            "category": "sports",
            "tags": ["animal", "cat"],
            "type": "perfect",
            "page": 2
        }
    response:
        {
            "code": 0,
            "info": "SUCCESS",
            "data": {
                "page_count": 15,
                "page_data": [
                    {
                        "id": 117,
                        "name": "pretty.gif",
                        "title": "Pretty Gif",
                        "width": 400,
                        "height": 250,
                        "duration": 5.2,
                        "uploader": "Bob",
                        "uploader_id": 4,
                        "category": "beauty",
                        "tags": ["beauty", "fun"],
                        "like": 412,
                        "pub_time": "2023-04-25T17:13:55.648217Z"
                    }
                ]
            }
        }
        格式错误：
        {
            "code": , 
            "info": "INVALID_FORMAT",
            "data": {}
        }
        页码非正整数：
         {
            "code": 5,
            "info": "INVALID_PAGE",
            "data": {}
        }
    '''

    if req.method == "POST":
        start_time = time.time()
        try:
            body = json.loads(req.body.decode("utf-8"))
        except (TypeError, KeyError) as error:
            print(error)
            return format_error()

        # target 默认为 "" ，表示没有本项限制。
        if "target" not in body:
            body["target"] = ""
        # target 必须为 "", "uploader", "title" 三者之一
        try:
            assert body["target"] in ["", "uploader", "title"]
        except Exception as error:
            print(error)
            return format_error()
        # keyword 默认为 "" ，表示没有本项限制。
        if "keyword" not in body:
            body["keyword"] = ""
        # filter 默认为 [] ，表示没有本项限制。
        if "filter" not in body:
            body["filter"] = []
        # category 默认为 "" ，表示没有本项限制。
        if "category" not in body:
            body["category"] = ""
        # tags 默认为 [] ，表示没有本项限制。
        if "tags" not in body:
            body["tags"] = []
        # 检查 filter 的类型
        try:
            assert isinstance(body["filter"], list)
            for each_filter in body["filter"]:
                assert isinstance(each_filter, dict)
                assert "range" in each_filter
        except Exception as error:
            print(error)
            return format_error()
        # 检查 keyword, category, tags 的类型
        try:
            assert isinstance(body["keyword"], str)
            assert isinstance(body["category"], str)
            assert isinstance(body["tags"], list)
            for tag in body["tags"]:
                assert isinstance(tag, str)
        except Exception as error:
            print(error)
            return format_error()

        # type 默认为 "perfect"
        if "type" not in body:
            body["type"] = "perfect"
        # type 必须为以下几个之一
        try:
            assert body["type"] in ["perfect", "partial", "fuzzy", "regex", "related"]
        except Exception as error:
            print(error)
            return format_error()
        # page 默认为 1
        if "page" not in body:
            body["page"] = 1
        # page 必须为正整数
        try:
            assert isinstance(body["page"], int)
            assert body["page"] > 0
        except Exception as error:
            print(error)
            return request_failed(5, "INVALID_PAGE", data={"data": {}})

        # 非正则表达式搜索的情形：target 和 keyword 必须都非空串（""），或者都为空串，才合法。
        if body["type"] != "regex":
            try:
                assert (body["target"] != "" and body["keyword"] != "") or (body["target"] == "" and body["keyword"] == "")
            except Exception as error:
                print(error)
                return format_error()
        # 正则表达式搜索的情形：target 必须属于 ["uploader", "title"] ，默认为 "title"
        else:
            if body["target"] not in ["uploader", "title"]:
                body["target"] = "title"
            # try:
            #     assert body["target"] in ["uploader", "title"]
            # except Exception as error:
            #     print(error)
            #     return format_error()

        search_start_time = time.time()
        # 通过正则表达式搜索
        id_list = []
        if body["type"] == "regex":
            query = Q()
            if body["filter"]:
                ranges = [filter["range"] for filter in body["filter"]]
                # ranges = [
                #     {"width": {"gte": 0, "lte": 100}},
                #     {"height": {"gte": 0, "lte": 100}},
                #     {"duration": {"gte": 0, "lte": 100}}
                # ]
                for each_range in ranges:
                    if "width" in each_range:
                        query &= Q(width__gte=each_range["width"]["gte"])
                        query &= Q(width__lte=each_range["width"]["lte"])
                    elif "height" in each_range:
                        query &= Q(height__gte=each_range["height"]["gte"])
                        query &= Q(height__lte=each_range["height"]["lte"])
                    elif "duration" in each_range:
                        query &= Q(duration__gte=each_range["duration"]["gte"])
                        query &= Q(duration__lte=each_range["duration"]["lte"])
            if body["category"]:
                query &= Q(category=body["category"])
            if body["tags"]:
                # query &= Q(tags__in=(body["tags"]))
                for tag in body["tags"]:
                    query &= Q(tags__contains=tag)  # sqlite 不支持 contains

            repred_keyword = repr(body['keyword'])[1:-1]
            if body["target"] == "uploader":
                # 如果 keyword 为 "" ，那么没有本项限制。
                if body["keyword"] == "":
                    uploaader_id_list = list(UserInfo.objects.all().values_list('id', flat=True))
                else:
                    uploaader_id_list = list(UserInfo.objects.filter(user_name__regex=repred_keyword).values_list('id', flat=True))
                # print(f'uploaader_id_list = {uploaader_id_list}')

                id_list = list(GifMetadata.objects.filter(Q(uploader__in=uploaader_id_list) & query).values_list('id', flat=True))
            elif body["target"] == "title":
                # 如果 keyword 为 "" ，那么没有本项限制。
                if body["keyword"] == "":
                    id_list = list(GifMetadata.objects.all().values_list('id', flat=True))
                else:
                    id_list = list(GifMetadata.objects.filter(Q(title__regex=repred_keyword) & query).values_list('id', flat=True))

        # 通过关键词搜索
        else:
            # 连接搜索模块
            if os.getenv('DEPLOY') is not None:
                cache_body = helpers.generate_cache_body(body)
                if cache_body in config.CACHE_HISTORY and (datetime.datetime.now().timestamp() - config.CACHE_HISTORY[cache_body][1] < config.CACHE_MAX_TIME) and (config.CACHE_HISTORY[cache_body][2] == body["tags"]):
                    id_list = config.CACHE_HISTORY[cache_body][0]
                    print("Cached!")

                else:
                    search_engine = config.SEARCH_ENGINE

                    # 如果用户已登录，将本次搜索记录到用户的搜索历史中
                    if req.META.get("HTTP_AUTHORIZATION"):
                        encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
                        token = helpers.decode_token(encoded_token)
                        if not helpers.is_token_valid(token=encoded_token):
                            return unauthorized_error()
                        user = UserInfo.objects.filter(id=token["id"]).first()
                        content = body["keyword"]
                        if content:
                            helpers.post_user_search_history(user=user, search_content=content)
                            helpers.update_user_tags(user, [content])

                    if body["type"] == "perfect":
                        id_list = search_engine.search_perfect(request=body)
                    elif body["type"] == "partial":
                        id_list = search_engine.search_partial(request=body)
                    elif body["type"] == "fuzzy":
                        id_list = search_engine.search_fuzzy(request=body)
                    elif body["type"] == "related":
                        id_list = search_engine.search_related(request=body)
                    else:
                        return format_error()

                    if os.getenv('DEPLOY') is not None:
                        config.CACHE_HISTORY[cache_body] = (id_list, datetime.datetime.now().timestamp(), body["tags"])
                        if len(config.CACHE_HISTORY) > config.MAX_CACHE_HISTORY:
                            cache_history = list(config.CACHE_HISTORY.items())
                            config.CACHE_HISTORY = dict(sorted(cache_history, key=lambda x: x[1], reverse=True)[: config.MAX_CACHE_HISTORY // 2])
                        print("Not cached!")
            else:
                search_engine = config.SEARCH_ENGINE

                # 如果用户已登录，将本次搜索记录到用户的搜索历史中
                if req.META.get("HTTP_AUTHORIZATION"):
                    encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
                    token = helpers.decode_token(encoded_token)
                    if not helpers.is_token_valid(token=encoded_token):
                        return unauthorized_error()
                    user = UserInfo.objects.filter(id=token["id"]).first()
                    content = body["keyword"]
                    if content:
                        helpers.post_user_search_history(user=user, search_content=content)
                        helpers.update_user_tags(user, [content])

                if body["type"] == "perfect":
                    id_list = search_engine.search_perfect(request=body)
                elif body["type"] == "partial":
                    id_list = search_engine.search_partial(request=body)
                elif body["type"] == "fuzzy":
                    id_list = search_engine.search_fuzzy(request=body)
                elif body["type"] == "related":
                    id_list = search_engine.search_related(request=body)
                else:
                    return format_error()
        search_finish_time = time.time()

        gifs = GifMetadata.objects.filter(id__in=id_list)
        id_list = [gif.id for gif in gifs]
        gif_list, pages = helpers.show_search_page(id_list, body["page"] - 1)

        finish_time = time.time()
        return request_success(data=
            {
                "data": {
                    "page_count": pages,
                    "page_data": gif_list,
                    "time": finish_time - start_time,
                    "search_time": search_finish_time - search_start_time
                }
            })
    return not_found_error()

@csrf_exempt
@handle_errors
def search_suggest(req: HttpRequest):
    """
    request:
        {
            "query": "Hello" (default = ""),
            "target": "title" (default = "title"),
            "correct": True (default = True)
        }
    response:
        {
            "code": 0,
            "message": "SUCCESS",
            "data": {
                "suggestions": [
                    "Hello world!",
                    "Hello world again!"
                ]
            }
        }
    """
    if req.method == "POST":
        try:
            body = json.loads(req.body)
        except Exception as error:
            print(error)
            return format_error()
        if "query" not in body:
            body["query"] = ""
        try:
            assert body["target"] in ["title", "uploader"]
        except Exception as _:
            body["target"] = "title"
        if "correct" not in body:
            body["correct"] = True

        # 连接搜索模块
        search_engine = config.SEARCH_ENGINE

        if body["target"] == "title":
            # 如果 body["target"] == "title" 先获取补全建议
            suggestion_list = search_engine.suggest_search(body["query"])
            # 如果建议结果较少且需要纠错
            if len(suggestion_list) < 4 and body["correct"]:
                # 获取纠错建议
                corrected_list = search_engine.correct_search(input=body["query"], target=body["target"])
                return request_success(data=
                    {
                        "data": {
                            "suggestions": helpers.deduplicate(suggestion_list + corrected_list)
                        }
                    })
            else:
                return request_success(data=
                    {
                        "data": {
                            "suggestions": suggestion_list
                        }
                    })
        else:
            # 如果 body["target"] == "uploader" ，直接纠错
            corrected_list = search_engine.correct_search(input=body["query"], target=body["target"])
            return request_success(data=
                {
                    "data": {
                        "suggestions": corrected_list
                    }
                })
    return not_found_error()

@csrf_exempt
@handle_errors
def image_gifs_count(req: HttpRequest):
    '''
    request:
        None
    response:
        number of gifs
    '''
    if req.method == "GET":
        count = GifMetadata.objects.count()
        return request_success(data={"data": count})
    return not_found_error()

@csrf_exempt
@handle_errors
def search_hotwords(req: HttpRequest):
    """
    request:
        None
    response:
        {
            "code": 0,
            "message": "SUCCESS",
            "data": {
                ['spider', 'dog', 'hello', 'large', 'still', 'word']
            }
        }
    """
    if req.method == "GET":
        search_engine = config.SEARCH_ENGINE
        hotwords_list = search_engine.hotwords_search()
        return request_success(data={
                "data": hotwords_list
            })
    return not_found_error()
