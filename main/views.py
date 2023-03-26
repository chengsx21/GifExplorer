'''
    views.py in django frame work
'''

import json
from django.http import HttpRequest, HttpResponse
# from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from utils.utils_request import NOT_FOUND, request_failed, request_success
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
        elif not helpers.user_password_checker(password):
            return request_failed(3, "INVALID_PASSWORD_FORMAT", data={"data": {}})
        else:
            user = UserInfo.objects.filter(user_name=user_name).first()
            if not user:
                user = UserInfo(user_name=user_name, password=helpers.md5(password))
                user.save()
                user_token = helpers.create_token(user_name=user.user_name, user_id=user.id)
                return_data = {
                    "data": {
                        "id": user.id,
                        "user_name": user_name,
                        "token": user_token
                    }
                }
                # TODO！ helpers.enable_token(user_token)
                return request_success(return_data)
            else:
                return request_failed(1, "USER_NAME_CONFLICT", data={"data": {}})
    else:
        return NOT_FOUND
