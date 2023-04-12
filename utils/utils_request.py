'''
    This utils_request.py file contains tools to generate http response
'''
from django.http import JsonResponse


def request_failed(code, info, status_code=400, data={}):
    '''
        Return a http failure response
    '''
    return JsonResponse(
        {
            "code": code,
            "info": info,
            **data
        },
        status=status_code,
        headers={'Access-Control-Allow-Origin': '*'}
    )


def request_success(data={}):
    '''
        Return a http success response
    '''
    return JsonResponse(
        {
            "code": 0,
            "info": "Succeed",
            **data
        },
        headers={'Access-Control-Allow-Origin': '*'}
    )


def return_field(obj_dict, field_list):
    '''
        Return specific key-value pairs
    '''
    for field in field_list:
        assert field in obj_dict, f"Field `{field}` not found in object."

    return {
        k: v for k, v in obj_dict.items()
        if k in field_list
    }

def not_found_error(error="not found error"):
    '''
        define not found error response
    '''
    return request_failed(1000, "NOT_FOUND", 404, {"data": {"error": error}})

def unauthorized_error(error="unauthorized error"):
    '''
        define unauthorized error response
    '''
    return request_failed(1001, "UNAUTHORIZED", 401, {"data": {"error": error}})

def internal_error(error="internal error"):
    '''
        define internal error response
    '''
    return request_failed(1003, "INTERNAL_ERROR", 500, {"data": {"error": error}})

def format_error(error="format error"):
    '''
        define format error response
    '''
    return request_failed(1005, "INVALID_FORMAT", 400, {"data": {"error": error}})
