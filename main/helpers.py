'''
    This helpers.py file contains tools used in views.py - Created by csx
'''
import hashlib
import io
import re
import base64
import datetime
import math
from functools import wraps
import magic
from PIL import Image
import jwt
from django.db.models import Q
from django.utils.crypto import get_random_string
from utils.utils_request import internal_error
from .config import MAX_GIFS_PER_PAGE, MAX_USERS_PER_PAGE, MAX_MESSAGES_PER_PAGE, MAX_SEARCH_HISTORY, SECRET_KEY, SEARCH_ENGINE
from .models import UserInfo, UserToken, GifMetadata, GifFingerprint, Message

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

def get_user_followers(user: UserInfo):
    """
        get followers list from a user
    """
    if not user.followers:
        user.followers = {}
    read_followers_list = list(user.followers.items())
    read_followers_list = sorted(read_followers_list, key=lambda x: x[1], reverse=True)
    return read_followers_list

def show_user_followers(user: UserInfo, page: int):
    '''
        Show user followers pages
    '''
    if not user.followers:
        return [], 0
    begin = page * MAX_USERS_PER_PAGE
    end = (page + 1) * MAX_USERS_PER_PAGE
    followers_list = get_user_followers(user)
    followers_page = followers_list[begin:end]

    user_followers_list = []
    for user_id, _ in followers_page:
        user = UserInfo.objects.filter(id=int(user_id)).first()
        if user:
            user_followers_list.append({
                "id": user.id,
                "user_name": user.user_name,
                "signature": user.signature,
                "mail": user.mail,
                "avatar": user.avatar,
                "followers": len(user.followers),
                "following": len(user.followings),
                "register_time": user.register_time
            })
    return user_followers_list, math.ceil(len(followers_list) / MAX_USERS_PER_PAGE)

def get_user_followings(user: UserInfo):
    """
        get followings list from a user
    """
    if not user.followings:
        user.followings = {}
    read_followings_list = list(user.followings.items())
    read_followings_list = sorted(read_followings_list, key=lambda x: x[1], reverse=True)
    return read_followings_list

def show_user_followings(user: UserInfo, page: int):
    '''
        Show user followings pages
    '''
    if not user.followings:
        return [], 0
    begin = page * MAX_USERS_PER_PAGE
    end = (page + 1) * MAX_USERS_PER_PAGE
    followings_list = get_user_followings(user)
    followings_page = followings_list[begin:end]

    user_followings_list = []
    for user_id, _ in followings_page:
        user = UserInfo.objects.filter(id=int(user_id)).first()
        if user:
            user_followings_list.append({
                "id": user.id,
                "user_name": user.user_name,
                "signature": user.signature,
                "mail": user.mail,
                "avatar": user.avatar,
                "followers": len(user.followers),
                "following": len(user.followings),
                "register_time": user.register_time
            })
    return user_followings_list, math.ceil(len(followings_list) / MAX_USERS_PER_PAGE)

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

def generate_token():
    '''
        Generate a random token
    '''
    return get_random_string(length=12)

def update_user_tags(user: UserInfo, tags: list):
    '''
        Update user tags
    '''
    if not user.tags:
        user.tags = {}
    for tag in tags:
        if tag in user.tags:
            user.tags[tag] += 1
        else:
            user.tags[tag] = 1
    user.save()

def get_user_tags(user: UserInfo):
    '''
        Get user tags
    '''
    if not user.tags:
        return {}
    tags = list(user.tags.items())
    tags = dict(sorted(tags, key=lambda x: x[1], reverse=True)[:10])
    max_val = max(tags.values())
    normalized_tags = {}
    for key, value in tags.items():
        normalized_tags[key] = value / max_val
    return normalized_tags

def post_user_search_history(user: UserInfo, search_content: str):
    '''
        Post user search history
    '''
    if not user.search_history:
        user.search_history = {}
    user.search_history[search_content] = str(datetime.datetime.now())
    while len(user.search_history) > MAX_SEARCH_HISTORY:
        history = list(user.search_history.items())
        sorted_history = sorted(history, key=lambda x: x[1], reverse=True)
        removed_content = sorted_history[-1][0]
        user.search_history.pop(removed_content)
    user.save()

def get_user_search_history(user: UserInfo):
    '''
        Get user search history
    '''
    if not user.search_history:
        user.search_history = {}
    read_search_list = list(user.search_history.items())
    read_search_list = sorted(read_search_list, key=lambda x: x[1], reverse=True)
    return read_search_list

def delete_user_search_history(user: UserInfo, search_content: str):
    '''
        Delete user search history
    '''
    if not user.search_history:
        user.search_history = {}
    if search_content in user.search_history:
        user.search_history.pop(search_content)
    user.save()

def get_user_message_list(user: UserInfo, page: int):
    '''
        Get user message list
    '''
    user_messages = Message.objects.filter(Q(receiver=user)|Q(sender=user)).order_by("-pub_time")
    if not user_messages:
        return [], 0
    user_list = []
    messages_list = []
    for message in user_messages:
        other_user = message.sender if message.sender != user else message.receiver
        if other_user.id not in user_list:
            user_list.append(other_user.id)
            single_message = {}
            single_message["user"] = {
                "id": other_user.id,
                "user_name": other_user.user_name,
                "avatar": other_user.avatar,
                "signature": other_user.signature
            }
            last_message = Message.objects.filter(receiver=user, sender=other_user).order_by("-pub_time").first()
            is_read = True
            if last_message and not last_message.is_read:
                is_read = False
            single_message["message"] = {
                "message": message.message,
                "pub_time": message.pub_time,
                "is_read": is_read
            }
            messages_list.append(single_message)
    begin = page * MAX_USERS_PER_PAGE
    end = (page + 1) * MAX_USERS_PER_PAGE
    return messages_list[begin:end], math.ceil(len(messages_list) / MAX_USERS_PER_PAGE)

def show_user_message_page(user: UserInfo, other_user: UserInfo, page: int):
    '''
        Show user message page
    '''
    user_messages = Message.objects.filter(Q(receiver=user, sender=other_user)|Q(sender=user, receiver=other_user)).order_by("-pub_time")
    if not user_messages:
        return [], 0
    begin = page * MAX_MESSAGES_PER_PAGE
    end = (page + 1) * MAX_MESSAGES_PER_PAGE
    messages_list = []
    for single_message in user_messages[begin:end]:
        messages_list.append({
            "sender": single_message.sender.id,
            "receiver": single_message.receiver.id,
            "message": single_message.message,
            "pub_time": single_message.pub_time
        })
    return messages_list, math.ceil(len(user_messages) / MAX_MESSAGES_PER_PAGE)

def deduplicate(list_to_deduplicate):
    '''
        Deduplicate a list
    '''
    return [x for i, x in enumerate(list_to_deduplicate) if x not in list_to_deduplicate[:i]]

def post_message_to_fans(user: UserInfo, gif_id: int):
    '''
        Post message to fans
    '''
    fans = user.followers
    for fan_id, _ in fans.items():
        fan = UserInfo.objects.filter(id=int(fan_id)).first()
        if fan:
            message = Message(sender=user, receiver=fan, message=f"我发布了新的作品，快去 https://gifexplorer-frontend-nullptr.app.secoder.net/image/{gif_id} 看看吧~")
            message.save()

def generate_cache_body(body):
    '''
        Generate cache body
    '''
    width_param, height_param, duration_param = '0_0', '0_0', '0_0'
    for item in body["filter"]:
        if "range" in item and "width" in item["range"]:
            width_param = str(item["range"]["width"]["gte"]) + '_' + str(item["range"]["width"]["lte"])
        if "range" in item and "height" in item["range"]:
            height_param = str(item["range"]["height"]["gte"]) + '_' + str(item["range"]["height"]["lte"])
        if "range" in item and "duration" in item["range"]:
            duration_param = str(item["range"]["duration"]["gte"]) + '_' + str(item["range"]["duration"]["lte"])
    cache_body = body["type"] + '_' + body["target"] + '_' + body["keyword"] + '_' + body["category"] + '_' + width_param + '_' + height_param + '_' + duration_param + '_' + str(body["page"])
    return cache_body
