'''
    views.py in django frame work
'''
import os
import json
from wsgiref.util import FileWrapper
import io
import imageio
import imagehash
from jwt import DecodeError
from PIL import Image
# from celery import shared_task
from django.core.files.base import ContentFile
from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from utils.utils_request import not_found_error, unauthorized_error, internal_error, format_error, request_failed, request_success
from . import helpers
from . import config
from .models import UserInfo, GifMetadata, GifFile

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
            "salt": "secret_salt"
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
            except (TypeError, KeyError) as error:
                print(error)
                return format_error(str(error))

            if not helpers.user_username_checker(user_name):
                return request_failed(2, "INVALID_USER_NAME_FORMAT", data={"data": {}})
            if not isinstance(password, str):
                return request_failed(3, "INVALID_PASSWORD_FORMAT", data={"data": {}})

            user = UserInfo.objects.filter(user_name=user_name).first()
            if not user:
                user = UserInfo(user_name=user_name, password=helpers.hash_password(password), salt=salt)
                user.save()
                user_token = helpers.create_token(user_name=user.user_name, user_id=user.id)
                return_data = {
                    "data": {
                        "id": user.id,
                        "user_name": user_name,
                        "token": user_token
                    }
                }
                helpers.add_token_to_white_list(user_token)
                return request_success(return_data)
            return request_failed(1, "USER_NAME_CONFLICT", data={"data": {}})
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
    # try:
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
    # except Exception as error:
    #     print(error)
    #     return internal_error(str(error))

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
                tags = req.POST.getlist("tags")
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

            file_contents = req.FILES.get("file").read()
            file_obj = io.BytesIO(file_contents)
            image = Image.open(file_obj)
            gif_fingerprint = imagehash.average_hash(image, hash_size=16)
            if not helpers.add_gif_fingerprint_to_list(gif_fingerprint):
                return request_success(data={"data": {}})

            # gif not empty is needed
            gif = GifMetadata.objects.create(title=title, uploader=user.id, category=category, tags=tags)
            gif_file = GifFile.objects.create(metadata=gif, file=req.FILES.get("file"))
            gif_file.save()

            with Image.open(gif_file.file) as image:
                duration = image.info['duration'] * image.n_frames
            gif.duration = duration / 1000.0
            gif.width = gif_file.file.width
            gif.height = gif_file.file.height
            gif.name = gif_file.file.name
            gif.save()

            return_data = {
                "data": {
                    "id": gif.id,
                    "width": gif.width,
                    "height": gif.height,
                    "duration": gif.duration,
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
        Node
    response:
        {
            "code": 0,
            "info": "SUCCESS",
            "data": {
                "id": 514,
                "title": "Wonderful Gif",
                "url": "https://wonderful-gif/apple.gif",
                "uploader": "AliceBurn", 
                "width": gif.width,
                "height": gif.height,
                "duration": gif.duration,
                "pub_time": "2023-03-21T19:02:16.305Z",
                "like": 114514
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

            return_data = {
                    "id": gif.id,
                    "title": gif.title,
                    # "url": gif.gif_file.url,
                    "uploader": user.user_name,
                    "width": gif.width,
                    "height": gif.height,
                    "duration": gif.duration,
                    "pub_time": gif.pub_time,
                    "like": gif.likes
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

            file_contents = gif.giffile.file.read()
            file_obj = io.BytesIO(file_contents)
            image = Image.open(file_obj)
            gif_fingerprint = imagehash.average_hash(image, hash_size=16)
            helpers.delete_gif_fingerprint_from_list(gif_fingerprint)

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

            gif = GifMetadata.objects.filter(id=gif_id).first()
            if not gif:
                return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})
            gif_file = open(gif.giffile.file.path, 'rb')
            file_wrapper = FileWrapper(gif_file)
            response = HttpResponse(file_wrapper, content_type='image/gif')
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

            gif = GifMetadata.objects.filter(id=gif_id).first()
            if not gif:
                return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})
            gif_file = open(gif.giffile.file.path, 'rb')
            file_wrapper = FileWrapper(gif_file)
            response = HttpResponse(file_wrapper, content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{gif.title}.gif"'
            return response
        return not_found_error()
    except Exception as error:
        print(error)
        return internal_error(str(error))

# @csrf_exempt
# def from_video_to_gif(req: HttpRequest):
#     '''
#         支持mp4/mkv格式视频上传后在线转换为 GIF 处理过程不能阻塞操作
#     '''
#     try:
#         if req.method == "POST":
#             try:
#                 encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
#                 token = helpers.decode_token(encoded_token)
#                 if not helpers.is_token_valid(token=encoded_token):
#                     return unauthorized_error()
#             except DecodeError as error:
#                 print(error)
#                 return unauthorized_error(str(error))

#             try:
#                 title = req.POST.get("title")
#                 category = req.POST.get("category")
#                 tags = req.POST.getlist("tags")
#                 name = req.FILES.get("file").name.rsplit(".", 1)[0]
#             except (TypeError, KeyError) as error:
#                 print(error)
#                 return format_error(str(error))

#             if not (isinstance(title, str) and isinstance(category, str) and isinstance(tags, list)):
#                 return format_error()
#             for tag in tags:
#                 if not isinstance(tag, str):
#                     return format_error()

#             user = UserInfo.objects.filter(id=token["id"]).first()
#             if not user:
#                 return unauthorized_error()

#             video_file = req.FILES.get("file")
#             if not video_file:
#                 return format_error()
#             with open('TEMP_VIDEO.mp4', 'wb') as temp_video:
#                 for chunk in video_file.chunks():
#                     temp_video.write(chunk)
#             # from_video_to_gif_task.delay()

#             video = imageio.get_reader('TEMP_VIDEO.mp4')
#             fps = video.get_meta_data()['fps']
#             gif_frames = []
#             for frame in video:
#                 gif_frames.append(frame[:, :, :3])
#             imageio.mimsave('TEMP_GIF.gif', gif_frames, fps=fps)

#             gif = GifMetadata.objects.create(title=title, uploader=user.id, category=category, tags=tags)
#             gif_file = GifFile.objects.create(metadata=gif, file='TEMP_GIF.gif')

#             with open('TEMP_GIF.gif', 'rb') as temp_gif:
#                 gif_file.file.save(name+'.gif', ContentFile(temp_gif.read()))
#             gif_file.save()

#             with Image.open(gif_file.file) as image:
#                 duration = image.info['duration'] * image.n_frames
#             gif.duration = duration / 1000.0
#             gif.width = gif_file.file.width
#             gif.height = gif_file.file.height
#             gif.name = gif_file.file.name
#             gif.save()

#             os.remove('TEMP_VIDEO.mp4')
#             os.remove('TEMP_GIF.gif')

#             return_data = {
#                 "data": {
#                     "id": gif.id,
#                     "width": gif.width,
#                     "height": gif.height,
#                     "duration": gif.duration,
#                     "uploader": user.id,
#                     "pub_time": gif.pub_time
#                 }
#             }
#             return request_success(return_data)
#         return not_found_error()
#     except Exception as error:
#         print(error)
#         return internal_error(str(error))

# @shared_task
# def from_video_to_gif_task():
#     video = imageio.get_reader('TEMP_VIDEO.mp4')
#     fps = video.get_meta_data()['fps']
#     gif_frames = []
#     for frame in video:
#         gif_frames.append(frame[:, :, :3])
#     gif = imageio.mimsave('TEMP_GIF.gif', gif_frames, fps=fps)
#     return None

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
        if req.method == "GET":
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
                    # "gif_url": gif.file.url,
                    "uploader": user.user_name,
                    "pub_time": gif.pub_time
                }
                gifs_list.append(gif_dict)
            return request_success({"data": gifs_list})
        return not_found_error()
    except Exception as error:
        print(error)
        return internal_error(str(error))
