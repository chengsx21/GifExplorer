'''
    views.py in django frame work
'''

import json
from wsgiref.util import FileWrapper
from PIL import Image
from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from utils.utils_request import NOT_FOUND, UNAUTHORIZED, INTERNAL_ERROR, request_failed, request_success
from . import helpers
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
        "password": "Happy-Day1"
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
        body = json.loads(req.body.decode("utf-8"))
        user_name = body["user_name"]
        password = body["password"]
        if not helpers.user_username_checker(user_name):
            return request_failed(2, "INVALID_USER_NAME_FORMAT", data={"data": {}})
        if not isinstance(password, str):
            return request_failed(3, "INVALID_PASSWORD_FORMAT", data={"data": {}})

        user = UserInfo.objects.filter(user_name=user_name).first()
        if not user:
            user = UserInfo(user_name=user_name, password=helpers.hash_password(password))
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
    return NOT_FOUND


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
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        user_name = body["user_name"]
        password = body["password"]
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
    return NOT_FOUND

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
    if req.method == "POST":
        encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
        token = helpers.decode_token(encoded_token)
        if not helpers.is_token_valid(token=encoded_token):
            return UNAUTHORIZED

        body = json.loads(req.body.decode("utf-8"))
        user_name = body["user_name"]
        old_password = body["old_password"]
        new_password = body["new_password"]
        if not helpers.user_username_checker(user_name):
            return request_failed(2, "INVALID_USER_NAME_FORMAT", data={"data": {}})
        if not (isinstance(old_password, str) and isinstance(new_password, str)):
            return request_failed(3, "INVALID_PASSWORD_FORMAT", data={"data": {}})

        if not user_name == token["user_name"]:
            return UNAUTHORIZED

        user = UserInfo.objects.filter(user_name=user_name).first()
        if not user:  # user name not existed yet.
            return request_failed(4, "USER_NAME_NOT_EXISTS_OR_WRONG_PASSWORD", data={"data": {}})
        if not helpers.check_password(old_password, user.password):
            return request_failed(4, "USER_NAME_NOT_EXISTS_OR_WRONG_PASSWORD", data={"data": {}})
        user.password = helpers.hash_password(new_password)
        user.save()
        return request_success(data={"data": {}})
    return INTERNAL_ERROR

@csrf_exempt
def user_logout(req: HttpRequest):
    '''
    request:
        token in 'HTTP_AUTHORIZATION'.
    response:
        nothing
    '''
    if req.method == "POST":
        encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
        if helpers.is_token_valid(token=encoded_token):
            helpers.delete_token_from_white_list(token=encoded_token)
            if not helpers.is_token_valid(token=encoded_token):
                return request_success(data={"data": {}})
            return INTERNAL_ERROR
        return UNAUTHORIZED
    return INTERNAL_ERROR

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
    if req.method == "POST":
        encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
        token = helpers.decode_token(encoded_token)
        if not helpers.is_token_valid(token=encoded_token):
            return UNAUTHORIZED
        json_data_str = req.POST.get("file_data")
        body = json.loads(json_data_str)
        body = json.loads(body)
        title = body["title"]
        category = body["category"]
        tags = body["tags"]
        if not (isinstance(title, str) and isinstance(category, str) and isinstance(tags, list)):
            return request_failed(5, "INVALID_DATA_FORMAT", data={"data": {}})
        for tag in tags:
            if not isinstance(tag, str):
                return request_failed(5, "INVALID_DATA_FORMAT", data={"data": {}})

        user = UserInfo.objects.filter(id=token["id"]).first()
        if not user:
            return UNAUTHORIZED

        gif = GifMetadata.objects.create(title=title, uploader=user.id, category=category, tags=tags)
        gif_file = GifFile.objects.create(metadata=gif, file=req.FILES.get("file"))
        gif_file.save()

        with Image.open(gif_file.file) as image:
            duration = image.info['duration'] * image.n_frames
        gif.duration = duration / 1000.0
        gif.save()
        gif.width = gif_file.file.width
        gif.height = gif_file.file.height
        gif.name = gif_file.file.name
        gif.save()
        # with Image.open(gif_file.file) as image:
        #     duration = image.info['duration'] * image.n_frames
        # gif.duration = duration / 1000.0
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
    return INTERNAL_ERROR

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
                "pub_time": gif.pub_time,
                "like": gif.likes
            }
        return request_success(return_data)
    elif req.method == "DELETE":
        encoded_token = str(req.META.get("HTTP_AUTHORIZATION"))
        token = helpers.decode_token(encoded_token)
        if not helpers.is_token_valid(token=encoded_token):
            return UNAUTHORIZED

        if not isinstance(gif_id, str) or not gif_id.isdecimal():
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})

        gif = GifMetadata.objects.filter(id=gif_id).first()
        if not gif:
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})
        if gif.uploader != token["id"]:
            return UNAUTHORIZED
        gif.delete()
        return request_success(data={"data": {}})
    return NOT_FOUND

@csrf_exempt
def image_preview(req: HttpRequest, gif_id: any):
    '''
    request:
        None
    response:
        Return a HttpResponse including the gif for preview
    '''
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
    return NOT_FOUND

@csrf_exempt
def image_download(req: HttpRequest, gif_id: any):
    '''
    request:
        None
    response:
        Return a HttpResponse including the gif for download
    '''
    if req.method == "GET":
        if not isinstance(gif_id, str) or not gif_id.isdecimal():
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})

        gif = GifMetadata.objects.filter(id=gif_id).first()
        if not gif:
            return request_failed(9, "GIFS_NOT_FOUND", data={"data": {}})
        gif_file = open(gif.giffile.file.path, 'rb')
        file_wrapper = FileWrapper(gif_file)
        response = HttpResponse(file_wrapper, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{gif.name}"'
        return response
    return NOT_FOUND
