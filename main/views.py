'''
    views.py in django frame work
'''

import json
from django.http import HttpRequest, HttpResponse
# from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from utils.utils_request import NOT_FOUND, UNAUTHORIZED, INTERNAL_ERROR, request_failed, request_success
from . import helpers
from .models import UserInfo


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
        if not (isinstance(user_name, str) and helpers.user_username_checker(user_name)):
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
        if not (isinstance(user_name, str) and isinstance(password, str)):
            return request_failed(4, "WRONG_PASSWORD", data={"data": {}})

        user = UserInfo.objects.filter(user_name=user_name).first()
        if not user:  # user name not existed yet.
            return request_failed(4, "WRONG_PASSWORD", data={"data": {}})
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
        return request_failed(4, "WRONG_PASSWORD", data={"data": {}})
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
        if not (isinstance(user_name, str) and isinstance(old_password, str) and isinstance(new_password, str)):
            return request_failed(3, "INVALID_PASSWORD_FORMAT", data={"data": {}})

        if not user_name == token["user_name"]:
            return UNAUTHORIZED

        user = UserInfo.objects.filter(user_name=user_name).first()
        if not user:  # user name not existed yet.
            return request_failed(4, "WRONG_PASSWORD", data={"data": {}})
        if not helpers.check_password(old_password, user.password):
            return request_failed(4, "WRONG_PASSWORD", data={"data": {}})
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
