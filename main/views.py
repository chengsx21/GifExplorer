import json
from . import helpers
from .models import User
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from utils.utils_request import NOT_FOUND, BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp


# Create your views here.
@csrf_exempt
@CheckRequire
def startup(req: HttpRequest):
    return HttpResponse("Congratulations! You have successfully installed the requirements. Go ahead!")

@csrf_exempt
@CheckRequire
def user_register(req: HttpRequest):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        user_name = require(body, "user_name", "string", err_msg="Missing or error type of [user_name]")
        password = require(body, "password", "string", err_msg="Missing or error type of [password]")
        
        if not helpers.user_username_checker(user_name):
            return request_failed(2, "INVALID_USER_NAME_FORMAT", None, {"data": {}})    
        elif not helpers.user_password_checker(password):
            return request_failed(3, "INVALID_PASSWORD_FORMAT", None, {"data": {}})   
        else:    
            user = User.objects.filter(user_name=user_name).first()
            if not user:
                user = User(user_name=user_name, password=helpers.md5(password))
                user.save()
                user_token = helpers.create_token(user_name=user.user_name, id=user.id)
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
                return request_failed(1, "USER_NAME_CONFLICT", None, {"data": {}})       
    else:
        return NOT_FOUND
