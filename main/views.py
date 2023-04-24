'''
    views.py in django frame work
'''
import zipfile
import os
import uuid
import json
from wsgiref.util import FileWrapper
import io
# import time
import datetime
import imghdr
import imageio
import imagehash
from jwt import DecodeError
from PIL import Image
from celery import shared_task
from celery.result import AsyncResult
from django.core.files.base import ContentFile
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.utils.html import format_html
from utils.utils_request import not_found_error, unauthorized_error, internal_error, format_error, request_failed, request_success
from GifExplorer import settings
from . import helpers
from . import config
from .models import UserInfo, GifMetadata, GifFile, GifComment, UserVerification

# Create your views here.
@csrf_exempt
def startup(req: HttpRequest):
    '''
        test deployment
    '''
    if req.method == "GET":
        return HttpResponse("Congratulations! Go ahead!")

@csrf_exempt
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
    try:
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
            # print(verification_token)
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
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
def user_mail_verify(req: HttpRequest, token: str):
    '''
    request:
        verify user's email.
    '''
    try:
        if req.method == "GET":
            try:
                user = UserVerification.objects.filter(token=token).first()
            except (TypeError, KeyError) as error:
                print(error)
                return format_error(str(error))

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
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
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
    try:
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
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
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
    try:
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
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
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
    try:
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
            except (TypeError, ValueError) as error:
                print(error)
                return format_error(str(error))

            if not helpers.user_username_checker(user_name):
                return request_failed(2, "INVALID_USER_NAME_FORMAT", data={"data": {}})
            if not (isinstance(old_password, str) and isinstance(new_password, str)):
                return request_failed(3, "INVALID_PASSWORD_FORMAT", data={"data": {}})
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
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
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
    try:
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
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
def user_logout(req: HttpRequest):
    '''
    request:
        token in 'HTTP_AUTHORIZATION'.
    response:
        nothing
    '''
    try:
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
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
def check_user_login(req: HttpRequest):
    '''
    request:
        None
    response:
        Return if user is logged in
    '''
    try:
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
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
def user_profile(req: HttpRequest, user_id: any):
    '''
    request:
        - None
    response:
        - status
    '''
    try:
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
                    "data": gifs
                }
            }
            return request_success(return_data)
        return not_found_error()
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
def user_follow(req: HttpRequest, user_id: any):
    '''
    request:
        - user token is needed
    response:
        - status
    '''
    try:
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

            follow_user = UserInfo.objects.filter(id=user_id).first()
            if not follow_user:
                return request_failed(12, "USER_NOT_FOUND", data={"data": {}})
            if follow_user == user:
                return request_failed(13, "CANNOT_FOLLOW_SELF", data={"data": {}})
            if str(follow_user.id) not in user.followings:
                if not user.followings:
                    user.followings = {}
                if not follow_user.followers:
                    follow_user.followers = {}
                user.followings[str(follow_user.id)] = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                user.save()
                follow_user.followers[str(user.id)] = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                follow_user.save()
                return request_success(data={"data": {}})
            else:
                return request_failed(14, "INVALID_FOLLOWS", data={"data": {}})
        return not_found_error()
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
def user_unfollow(req: HttpRequest, user_id: any):
    '''
    request:
        - user token is needed
    response:
        - status
    '''
    try:
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

            follow_user = UserInfo.objects.filter(id=user_id).first()
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
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
def user_read_history(req: HttpRequest):
    '''
    request:
        - gif_id
        - user token is needed
    response:
        - status
    '''
    try:
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
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
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
    try:
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
                return request_success(data={"data": {"id": fingerprint.id}})

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
            gif.duration = total_time
            gif.width = gif_file.file.width
            gif.height = gif_file.file.height
            gif.name = name
            gif.save()

            return_data = {
                "data": {
                    "id": gif.id,
                    "width": gif.width,
                    "height": gif.height,
                    "duration": gif.duration,
                    "category": gif.category,
                    "tags": gif.tags,
                    "uploader": user.id,
                    "pub_time": gif.pub_time
                }
            }
            return request_success(return_data)
        return not_found_error()
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
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
    try:
        if req.method == "GET":
            if not isinstance(gif_id, str) or not gif_id.isdecimal():
                return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})

            gif = GifMetadata.objects.filter(id=gif_id).first()
            if not gif:
                return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})
            user = UserInfo.objects.filter(id=gif.uploader).first()

            is_liked = False
            if req.META.get("HTTP_AUTHORIZATION"):
                encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
                token = helpers.decode_token(encoded_token)
                if not helpers.is_token_valid(token=encoded_token):
                    return unauthorized_error()
                current_user = UserInfo.objects.filter(id=token["id"]).first()
                if str(gif.id) in current_user.favorites:
                    is_liked = True

            return_data = {
                "data": {
                        "id": gif.id,
                        "title": gif.title,
                        "uploader": user.user_name,
                        "uploader_id": user.id,
                        "avatar": user.avatar,
                        "width": gif.width,
                        "height": gif.height,
                        "category": gif.category,
                        "tags": gif.tags,
                        "duration": gif.duration,
                        "pub_time": gif.pub_time,
                        "like": gif.likes,
                        "is_liked": is_liked
                    }
                }
            return request_success(return_data)
        elif req.method == "DELETE":
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
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
def image_preview(req: HttpRequest, gif_id: any):
    '''
    request:
        None
    response:
        Return a HttpResponse including the gif for preview
    '''
    try:
        if req.method == "GET":
            if not isinstance(gif_id, str) or not gif_id.isdecimal():
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
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
def image_download(req: HttpRequest, gif_id: any):
    '''
    request:
        None
    response:
        Return a HttpResponse including the gif for download
    '''
    try:
        if req.method == "GET":
            if not isinstance(gif_id, str) or not gif_id.isdecimal():
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
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
def image_download_zip(req: HttpRequest):
    '''
    request:
        - gif_ids: a comma-separated list of GIF ids
    response:
        Return a HttpResponse including a zip file containing the requested gifs for download
    '''
    try:
        if req.method == "POST":
            body = json.loads(req.body.decode("utf-8"))
            gif_ids = body["gif_ids"]
            if not gif_ids:
                return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})

            gifs = GifMetadata.objects.filter(id__in=gif_ids)

            if len(gifs) != len(gif_ids):
                return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, mode='w') as zip_file:
                for gif in gifs:
                    gif_file = open(gif.giffile.file.path, 'rb')
                    zip_file.writestr(f"{gif.title}.gif", gif_file.read())
                    gif_file.close()

            response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip', headers={'Access-Control-Allow-Origin': '*'})
            cur_time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            response['Content-Disposition'] = f'attachment; filename="{cur_time}.zip"'
            return response
        return not_found_error()
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
def image_like(req: HttpRequest, gif_id: any):
    '''
    request:
        - gif_id
        - user token is needed
    response:
        - status
    '''
    try:
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
                user.favorites[str(gif_id)] = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                user.save()
                gif.likes += 1
                gif.save()
                return request_success(data={"data": {}})
            else:
                return request_failed(5, "INVALID_LIKES", data={"data": {}})
        return not_found_error()
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
def image_cancel_like(req: HttpRequest, gif_id: any):
    '''
    request:
        - user token is needed
    response:
        - status
    '''
    try:
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
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
def from_video_to_gif(req: HttpRequest):
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
    try:
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

            task = from_video_to_gif_task.delay(title=title, category=category, tags=tags, user=user.id, hashed_name=hashed_name)
            return_data = {
                "data": {
                    "task_id": task.id,
                    "task_status": task.status
                }
            }
            return request_success(data=return_data)
        return not_found_error()
    except Exception as error:
        print(error)
        return internal_error(str(error))

@shared_task
def from_video_to_gif_task(*, title: str, category: str, tags: list, user: int, hashed_name: str):
    '''
        mp4/mkv -> gif
    '''
    video = imageio.get_reader(hashed_name + ".mp4")
    fps = video.get_meta_data()['fps']
    gif_frames = []
    for frame in video:
        gif_frames.append(frame[:, :, :3])
    imageio.mimsave(hashed_name + ".gif", gif_frames, fps=fps)

    gif = GifMetadata.objects.create(title=title, uploader=user, category=category, tags=tags)
    gif_file = GifFile.objects.create(metadata=gif, file=hashed_name + ".gif")

    with open(hashed_name + ".gif", 'rb') as temp_gif:
        gif_file.file.save(hashed_name + ".gif", ContentFile(temp_gif.read()))
    gif_file.save()

    with Image.open(gif_file.file) as image:
        duration = image.info['duration'] * image.n_frames
    gif.duration = duration / 1000.0
    gif.width = gif_file.file.width
    gif.height = gif_file.file.height
    gif.name = gif_file.file.name
    gif.save()
    os.remove(hashed_name + ".mp4")
    os.remove(hashed_name + ".gif")

    return_data = {
        "data": {
            "id": gif.id,
            "width": gif.width,
            "height": gif.height,
            "duration": gif.duration,
            "uploader": user,
            "pub_time": gif.pub_time
        }
    }
    return return_data

@csrf_exempt
def check_from_video_to_gif_task_status(req: HttpRequest, task_id):
    '''
    request:
        None
    response:
        {
            "task_id": "ec1e476d-4f95-4d5e-94f3-b094de82c500",
            "task_status": "PENDING"
        }
        {
            "task_id": "ec1e476d-4f95-4d5e-94f3-b094de82c500",
            "task_status": "STARTED"
        }
        {
            "task_id": "efe4811e-bdbf-49e0-80ad-a93749159cd0",
            "task_status": "SUCCESS",
            "task_result": {
                "data": {
                    "id": 6,
                    "width": 1280,
                    "height": 720,
                    "duration": 5.2,
                    "uploader": 1,
                    "pub_time": "2023-04-24T01:22:07.326363Z"
                }
            }
        }
    '''
    try:
        if req.method == "GET":
            task_result = AsyncResult(task_id)
            response_data = {
                "task_id": task_id,
                "task_status": task_result.status,
            }

            if task_result.status == 'SUCCESS':
                response_data['task_result'] = task_result.result

            return JsonResponse(response_data)
        return not_found_error()
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
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
    try:
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
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
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
    try:
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
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
def image_comment_like(req: HttpRequest, comment_id: any):
    '''
    request:
        - user token is needed
    response:
        - status
    '''
    try:
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
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
def image_comment_cancel_like(req: HttpRequest, comment_id: any):
    '''
    request:
        - user token is needed
    response:
        - status
    '''
    try:
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
    except Exception as error:
        print(error)
        return internal_error(str(error))

@csrf_exempt
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
                    "gif_url": "https://wonderful-gif/apple.gif",
                    "uploader": "AliceBurn", 
                    "pub_time": "2023-03-21T19:02:16.305Z",
                },
                {
                    "id": 519,
                    "title": "Strong Man",
                    "category": "sports",
                    "gif_url": "https://wonderful-gif/strong-man.gif",
                    "uploader": "AliceBurn", 
                    "pub_time": "2023-03-21T19:02:16.305Z",
                }
            ]
        }
    '''
    try:
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
    except Exception as error:
        print(error)
        return internal_error(str(error))
