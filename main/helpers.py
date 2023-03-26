'''
    This helpers.py file contains tools used in views.py - Created by csx
'''
import hashlib
import re
import jwt

SECRET_KEY = "Welcome to the god damned SE world!"

def is_english(char: str):
    """
        Test if char is english
    """
    if re.search('[a-z]', char) or re.search('[A-Z]', char):
        return True
    return False

def is_chinese(char: str):
    """
        Test if char is chinese
    """
    return re.match(".*[\u3400-\u4DB5\u4E00-\u9FCB\uF900-\uFA6A].*", char)

def user_username_checker(user_name: str):
    """
        Check user's username
    """
    if not isinstance(user_name, str):
        return False
    if len(user_name) > 14:
        return False
    if not (is_english(user_name[0]) or is_chinese(user_name[0])):
        return False
    return True

# def user_password_checker(password: str):
#     """
#         Check user's password
#     """
#     if not isinstance(password, str):
#         return False
#     if not 8 <= len(password) <= 14:
#         return False
#     if not re.search(r"\d", password):
#         return False
#     if not re.search(r"[a-z]", password):
#         return False
#     if not re.search(r"[A-Z]", password):
#         return False
#     if not re.search(r"[#_!-]", password):
#         return False
#     common_password = ["12345678", "password"]
#     if password in common_password:
#         return False
#     if len(re.findall('[A-Za-z0-9#_!-]', password)) < len(password):
#         return False
#     return True

# def md5(password):
#     """
#         Input: str
#         Output: md5(str)
#     """
#     password_md5 = hashlib.md5()
#     password_md5.update(password.encode(encoding='UTF-8'))
#     encrypted_password = password_md5.hexdigest()
#     return str(encrypted_password)

def hash_password(password):
    """
        Encrypts password using MD5 hash function
    """
    # perform 1000 iterations of MD5 hash function on the password
    password = password.encode('utf-8')
    for _ in range(1000):
        password = hashlib.md5(password).hexdigest().encode('utf-8')
    return password.decode('utf-8')

def check_password(password, password_hashed):
    """
        Checks whether a password matches its hashed representation
    """
    password = hash_password(password)
    return password == password_hashed

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
    """
        Decode a jwt token for user
    """
    encoded_token = token.replace("Bearer ", "")
    return jwt.decode(encoded_token, SECRET_KEY, algorithms=["HS256"])
