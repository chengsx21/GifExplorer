'''
    This helpers.py file contains tools used in views.py - Created by csx
'''
import hashlib
import re
import imagehash
from PIL import Image
import jwt

SECRET_KEY = "Welcome to the god damned SE world!"

USER_WHITE_LIST = {}

GIF_HASH_LIST = []

def is_english(char: str):
    '''
        Test if char is english
    '''
    if re.search('[a-z]', char) or re.search('[A-Z]', char):
        return True
    return False

def is_chinese(char: str):
    '''
        Test if char is chinese
    '''
    return re.match(".*[\u3400-\u4DB5\u4E00-\u9FCB\uF900-\uFA6A].*", char)

def user_username_checker(user_name: str):
    '''
        Check user's username
    '''
    if not isinstance(user_name, str):
        return False
    if len(user_name) > 14:
        return False
    if not (is_english(user_name[0]) or is_chinese(user_name[0])):
        return False
    return True

def hash_password(password):
    '''
        Encrypts password using MD5 hash function
    '''
    # perform 1000 iterations of MD5 hash function on the password
    password = password.encode('utf-8')
    for _ in range(1000):
        password = hashlib.md5(password).hexdigest().encode('utf-8')
    return password.decode('utf-8')

def check_password(password, hashed_password):
    '''
        Checks whether a password matches its hashed representation
    '''
    password = hash_password(password)
    return password == hashed_password

def create_token(user_name, user_id):
    '''
        Create a jwt token for user
    '''
    payload = {
        "id": user_id,
        "user_name": user_name
    }
    encoded_token = "Bearer " + jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return encoded_token

def decode_token(token):
    '''
        Decode a jwt token for user
    '''
    encoded_token = token.replace("Bearer ", "")
    return jwt.decode(encoded_token, SECRET_KEY, algorithms="HS256")

def add_token_to_white_list(token):
    '''
        Add token to white list
    '''
    decoded_token = decode_token(token)
    user_id = decoded_token["id"]
    if user_id not in USER_WHITE_LIST:
        USER_WHITE_LIST[user_id] = []
    if token not in USER_WHITE_LIST[user_id]:
        USER_WHITE_LIST[user_id].append(token)

def is_token_valid(token):
    '''
        Check user's token in white list
    '''
    decoded_token = decode_token(token)
    user_id = decoded_token["id"]
    if user_id not in USER_WHITE_LIST:
        return False
    if token in USER_WHITE_LIST[user_id]:
        return True
    return False

def delete_token_from_white_list(token):
    '''
        Delete token from white list
    '''
    decoded_token = decode_token(token)
    user_id = decoded_token["id"]
    if user_id not in USER_WHITE_LIST:
        return False
    if token in USER_WHITE_LIST[user_id]:
        while token in USER_WHITE_LIST[user_id]:
            USER_WHITE_LIST[user_id].remove(token)
        return True
    return False

def add_gif_fingerprint_to_list(fingerprint):
    '''
        Calculate gif fingerprint
    '''
    if str(fingerprint) not in GIF_HASH_LIST:
        GIF_HASH_LIST.append(str(fingerprint))
        return True
    return False

def delete_gif_fingerprint_from_list(fingerprint):
    '''
        Delete gif fingerprint
    '''
    if str(fingerprint) in GIF_HASH_LIST:
        GIF_HASH_LIST.remove(str(fingerprint))
