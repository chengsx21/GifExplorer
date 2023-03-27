'''
    views.py in django frame work
'''

import json
from django.http import HttpRequest, HttpResponse
# from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from utils.utils_request import NOT_FOUND, UNAUTHORIZED, INTERNAL_ERROR, request_failed, request_success
from utils.utils_require import CheckRequire, require
from . import helpers
from .models import UserInfo


# Create your views here.
@csrf_exempt
@CheckRequire
def startup(req: HttpRequest):
    '''
        test deployment
    '''
    if req.method == "GET":
        return HttpResponse("Congratulations! Go ahead!")


@csrf_exempt
@CheckRequire
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
        user_name = require(body, "user_name", "string", err_msg="Error type of [user_name]")
        password = require(body, "password", "string", err_msg="Error type of [password]")

        if not helpers.user_username_checker(user_name):
            return request_failed(2, "INVALID_USER_NAME_FORMAT", data={"data": {}})
        # elif not helpers.user_password_checker(password):
        #     return request_failed(3, "INVALID_PASSWORD_FORMAT", data={"data": {}})

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
            # TODO！ helpers.add_token_to_white_list(user_token)
            return request_success(return_data)
        return request_failed(1, "USER_NAME_CONFLICT", data={"data": {}})
    return NOT_FOUND


@csrf_exempt
@CheckRequire
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
        user_name = require(body, "user_name", "string", err_msg="Error type of [user_name]")
        password = require(body, "password", "string", err_msg="Error type of [password]")
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
            # TODO! helpers.add_token_to_white_list(user_token)
            return request_success(return_data)
        return request_failed(4, "WRONG_PASSWORD", data={"data": {}})
    return NOT_FOUND

@csrf_exempt
@CheckRequire
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
        print(encoded_token)
        token = helpers.decode_token(encoded_token)
        # TODO! if not helpers.check_token_in_white_list(encoded_token=encoded_token):
        # TODO!    return UNAUTHORIZED

        body = json.loads(req.body.decode("utf-8"))
        user_name = require(body, "user_name", "string", err_msg="Error type of [user_name]")
        old_password = require(body, "old_password", "string", err_msg="Error type of [old_password]")
        new_password = require(body, "new_password", "string", err_msg="Error type of [new_password]")

        if not user_name == token["user_name"]:
            return UNAUTHORIZED

        user = UserInfo.objects.filter(user_name=user_name).first()
        if not user:  # user name not existed yet.
            return request_failed(4, "WRONG_PASSWORD", data={"data": {}})
        if not helpers.check_password(old_password, user.password):
            return request_failed(4, "WRONG_PASSWORD", data={"data": {}})
        # elif not helpers.user_password_checker(new_password):
        #     status_code = 400
        #     response_msg = {
        #         "code": 3,
        #         "message": "INVALID_PASSWORD_FORMAT",
        #         "data": {}
        #     }
        user.password = helpers.hash_password(new_password)
        user.save()
        return request_success(data={"data": {}})
    return INTERNAL_ERROR
