'''
    This helpers.py file contains tools used in views.py - Created by csx
'''
import hashlib
import io
import re
import base64
import math
from functools import wraps
import magic
from PIL import Image
import jwt
from utils.utils_request import internal_error
from .config import MAX_GIFS_PER_PAGE, USER_WHITE_LIST, SECRET_KEY, SEARCH_ENGINE
from .models import UserInfo, UserToken, GifMetadata, GifFingerprint

def handle_errors(view_func):
    '''
        Handle errors
    '''
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            response = view_func(request, *args, **kwargs)
        except Exception as error:
            print(error)
            response = internal_error(str(error))
        return response
    return wrapper


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

def is_float_string(sentence):
    '''
        Test if sentence is float string
    '''
    try:
        float(sentence)
        return True
    except ValueError:
        return False

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
    user_token = UserToken.objects.filter(user_id=user_id).first()
    if not user_token:
        user_token = UserToken(user_id=user_id, token=token)
        user_token.save()

def is_token_valid(token):
    '''
        Check user's token in white list
    '''
    decoded_token = decode_token(token)
    user_id = decoded_token["id"]
    user_token = UserToken.objects.filter(user_id=user_id).first()
    if not user_token:
        return False
    return True

def delete_token_from_white_list(token):
    '''
        Delete token from white list
    '''
    decoded_token = decode_token(token)
    user_id = decoded_token["id"]
    user_tokens = UserToken.objects.filter(user_id=user_id)
    if not user_tokens.first():
        return False
    for user_token in user_tokens:
        user_token.delete()

def add_gif_fingerprint_to_list(fingerprint):
    '''
        Calculate gif fingerprint
    '''
    gif_fingerprint = GifFingerprint.objects.filter(fingerprint=fingerprint).first()
    if not gif_fingerprint:
        gif_fingerprint = GifFingerprint(fingerprint=fingerprint)
        gif_fingerprint.save()
    return gif_fingerprint

def delete_gif_fingerprint_from_list(gif_id):
    '''
        Delete gif fingerprint
    '''
    gif_fingerprint = GifFingerprint.objects.filter(gif_id=gif_id).first()
    if gif_fingerprint:
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
                "data": {
                    "id": gif.id,
                    "name": gif.name,
                    "title": gif.title,
                    "width": gif.width,
                    "height": gif.height,
                    "duration": gif.duration,
                    "uploader": user.user_name,
                    "uploader_id": user.id,
                    "category": gif.category,
                    "tags": gif.tags,
                    "like": gif.likes,
                    "pub_time": gif.pub_time
                },
                "visit_time": read_time
            })
    return gif_list, math.ceil(len(read_history_list) / MAX_GIFS_PER_PAGE)

def image_resize(image, size=(512, 512)):
    '''
        Resize a given image
    '''
    img = Image.open(image)
    resized_img = img.resize(size, Image.ANTIALIAS)
    return resized_img

def image_to_base64(image):
    '''
        Transfer image to base64 code
    '''
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    byte_data = buffer.getvalue()
    return base64.b64encode(byte_data).decode()

def is_valid_video(file):
    '''
        Check whether a file is a valid video
    '''
    mime = magic.from_buffer(file.read(1024), mime=True)
    return mime in ['video/x-matroska', 'video/mp4']

def show_search_page(gif_id_list, page: int):
    '''
        Show search page
    '''
    if not gif_id_list:
        return [], 0
    begin = page * MAX_GIFS_PER_PAGE
    end = (page + 1) * MAX_GIFS_PER_PAGE

    gif_list = []
    for gif_id in gif_id_list[begin:end]:
        gif = GifMetadata.objects.filter(id=int(gif_id)).first()
        if gif:
            user = UserInfo.objects.filter(id=gif.uploader).first()
            gif_list.append({
                "id": gif.id,
                "name": gif.name,
                "title": gif.title,
                "width": gif.width,
                "height": gif.height,
                "duration": gif.duration,
                "uploader": user.user_name,
                "uploader_id": user.id,
                "category": gif.category,
                "tags": gif.tags,
                "like": gif.likes,
                "pub_time": gif.pub_time
            })
    return gif_list, math.ceil(len(gif_id_list) / MAX_GIFS_PER_PAGE)

def post_search_metadata(user: UserInfo, gif: GifMetadata):
    '''
        Post search metadata to elasticsearch engine
    '''
    data = {
        "id": gif.id,
        "title": gif.title,
        "uploader": user.user_name,
        "width": gif.width,
        "height": gif.height,
        "category": gif.category,
        "tags": gif.tags,
        "duration": gif.duration,
        "pub_time": "2023-04-23T15:32:59.514Z",
        "like": 0,
        "is_liked": False
    }
    search_engine = SEARCH_ENGINE
    search_engine.post_metadata(data)

