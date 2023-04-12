'''
    This helpers.py file contains tools used in views.py - Created by csx
'''
import hashlib
import re
import math
# import imagehash
# from PIL import Image
import jwt
from .config import MAX_GIFS_PER_PAGE, USER_WHITE_LIST, SECRET_KEY
from .models import UserInfo, GifMetadata, GifFingerprint

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
    if not GifFingerprint.objects.filter(fingerprint=fingerprint).exists():
        gif_fingerprint = GifFingerprint(fingerprint=fingerprint)
        gif_fingerprint.save()
        return True
    return False

def delete_gif_fingerprint_from_list(fingerprint):
    '''
        Delete gif fingerprint
    '''
    if GifFingerprint.objects.filter(fingerprint=fingerprint).exists():
        gif_fingerprint = GifFingerprint.objects.get(fingerprint=fingerprint)
        gif_fingerprint.delete()

def get_user_read_history(user: UserInfo):
    """
        get read history list from a user
    """
    if not user.read_history:
        user.read_history = {}
    read_history_dict = {}
    for key in user.read_history:
        gif = GifMetadata.objects.filter(id=int(key)).first()
        if gif:
            read_history_dict[key] = user.read_history[key]
    read_history_list = list(read_history_dict.items())

    read_history_list = sorted(read_history_list, key=lambda x: x[1], reverse=True)
    return read_history_list

def show_user_read_history_pages(user: UserInfo, page: int):
    '''
        Show user read history pages
    '''
    if not user.read_history:
        return [], 0
    begin = page * MAX_GIFS_PER_PAGE
    end = (page + 1) * MAX_GIFS_PER_PAGE
    read_history_list = get_user_read_history(user)
    read_history_page = read_history_list[begin:end]

    gif_list = []
    for gif_id, read_time in read_history_page:
        gif = GifMetadata.objects.filter(id=int(gif_id)).first()
        user = UserInfo.objects.filter(id=gif.uploader).first()
        if gif:
            gif_list.append({
                "id": gif.id,
                "title": gif.title,
                "uploader": user.user_name,
                "pub_time": gif.pub_time.strftime('%Y-%m-%d_%H-%M-%S'),
                "like": gif.likes,
                "visit_time": read_time
            })
    return gif_list, math.ceil(len(read_history_list) / MAX_GIFS_PER_PAGE)
