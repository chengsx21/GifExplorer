'''
    test.py in django frame work
'''
from django.test import TestCase
from main.models import UserInfo
from . import helpers

class ViewsTests(TestCase):
    '''
        Test functions in views.py
    '''
    def setUp(self):
        self.user_name_list = ["Alice", "Bob", "a刘华强"]
        self.user_password = ["Alice_123", "Bob_123", "Huaqiang_123"]
        self.user_salt = ["alicesalt", "bobsalt", "huaqiangsalt"]
        self.user_id = []
        self.user_num = len(self.user_name_list)
        for i in range(self.user_num):
            user_name = self.user_name_list[i]
            password = self.user_password[i]
            salt = self.user_salt[i]
            user = UserInfo.objects.create(user_name=user_name, password=helpers.hash_password(password), salt=salt)
            user.full_clean()
            user.save()
            self.user_id.append(user.id)

    def user_register_with_wrong_response_method(self, user_name, password, salt):
        '''
            Create a GET/user/register HttpRequest
        '''
        req = {
            "user_name": user_name,
            "password": password,
            "salt": salt
        }
        return self.client.get('/user/register', data=req, content_type="application/json")

    def user_register_with_correct_response_method(self, user_name, password, salt):
        '''
            Create a POST/user/register HttpRequest
        '''
        req = {
            "user_name": user_name,
            "password": password,
            "salt": salt
        }
        return self.client.post('/user/register', data=req, content_type="application/json")

    def user_salt_with_wrong_response_method(self, user_name):
        '''
            Create a GET/user/salt HttpRequest
        '''
        req = {
            "user_name": user_name
        }
        return self.client.get('/user/salt', data=req, content_type="application/json")

    def user_salt_with_correct_response_method(self, user_name):
        '''
            Create a POST/user/salt HttpRequest
        '''
        req = {
            "user_name": user_name,
            "id": 1
        }
        return self.client.post('/user/salt', data=req, content_type="application/json")

    def user_login_with_wrong_response_method(self, user_name, password):
        '''
            Create a GET/user/login HttpRequest
        '''
        req = {
            "user_name": user_name,
            "password": password
        }
        return self.client.get('/user/login', data=req, content_type="application/json")

    def user_login_with_correct_response_method(self, user_name, password):
        '''
            Create a POST/user/login HttpRequest
        '''
        req = {
            "user_name": user_name,
            "password": password
        }
        return self.client.post('/user/login', data=req, content_type="application/json")

    def user_modify_password_with_wrong_response_method(self, user_name, old_password, new_password, token):
        '''
            Create a GET/user/modifypassword HttpRequest
        '''
        req = {
            "user_name": user_name,
            "old_password": old_password,
            "new_password": new_password
        }
        return self.client.get('/user/modifypassword', data=req, content_type="application/json", HTTP_AUTHORIZATION=token)

    def user_modify_password_with_correct_response_method(self, user_name, old_password, new_password, token):
        '''
            Create a POST/user/modifypassword HttpRequest
        '''
        req = {
            "user_name": user_name,
            "old_password": old_password,
            "new_password": new_password
        }
        return self.client.post('/user/modifypassword', data=req, content_type="application/json", HTTP_AUTHORIZATION=token)

    def user_logout_with_wrong_response_method(self, token):
        '''
            Create a GET/user/logout HttpRequest
        '''
        return self.client.get('/user/logout', data={}, content_type="application/json", HTTP_AUTHORIZATION=token)

    def user_logout_with_correct_response_method(self, token):
        '''
            Create a POST/user/logout HttpRequest
        '''
        return self.client.post('/user/logout', data={}, content_type="application/json", HTTP_AUTHORIZATION=token)

    def user_checklogin_with_wrong_response_method(self, token):
        '''
            Create a GET/user/checklogin HttpRequest
        '''
        return self.client.get('/user/checklogin', data={}, content_type="application/json", HTTP_AUTHORIZATION=token)

    def user_checklogin_with_correct_response_method(self, token):
        '''
            Create a POST/user/checklogin HttpRequest
        '''
        return self.client.post('/user/checklogin', data={}, content_type="application/json", HTTP_AUTHORIZATION=token)

    def image_upload_with_wrong_response_method(self, image, token):
        '''
            Create a POST/image/upload HttpRequest
        request:
            {
                "title": "Wonderful Gif",
                "category": "animals"
                "tags": ["funny", "cat"]
            }
            Tip: The gif file is sent within the request!
        response:
            {
                "code": 0,
                "info": "SUCCESS",
                "data": {
                    "id": 1,
                    "width": 640,
                    "height": 480,
                    "duration": 5.2,
                    "uploader": 3, 
                    "pub_time": "2023-03-21T19:02:16.305Z",
                    }
            }
        '''
        req = {
            "title": "Wonderful Gif",
            "category": "animals",
            "tags": ["funny", "cat"]
        }
        return self.client.get('/image/upload', data=req, content_type="application/json", HTTP_AUTHORIZATION=token, HTTP_IMAGE=image)


    def test_user_login(self):
        '''
            Test user login
        '''
        for i in range(self.user_num):
            user_name = self.user_name_list[i]
            password = self.user_password[i]

            res = self.user_login_with_correct_response_method(user_name=user_name, password=password)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["code"], 0)

    def test_user_login_with_wrong_response_method(self):
        '''
            Test user login with wrong response method
        '''
        for i in range(self.user_num):
            user_name = self.user_name_list[i]
            password = self.user_password[i]
            res = self.user_login_with_wrong_response_method(user_name=user_name, password=password)
            self.assertEqual(res.status_code, 404)
            self.assertEqual(res.json()["code"], 1000)

    def test_user_login_with_wrong_type(self):
        '''
            Test user login with wrong data type
        '''
        res = self.user_login_with_correct_response_method(user_name="Cindy", password=1145141919810)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 3)

        res = self.user_login_with_correct_response_method(user_name=1145141919810, password="password")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 2)

    def test_user_login_with_wrong_password(self):
        '''
            Test user login with wrong password
        '''
        for i in range(self.user_num):
            user_name = self.user_name_list[i]

            res = self.user_login_with_correct_response_method(user_name=user_name, password="Wrong!")
            self.assertEqual(res.status_code, 400)
            self.assertEqual(res.json()["code"], 4)

    def test_user_login_with_non_exist_user(self):
        '''
            Test user login when user does not exist
        '''
        res = self.user_login_with_correct_response_method(user_name="Wrong_name!", password="Wrong!")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 4)

    def test_user_salt(self):
        '''
            Test user salt
        '''
        for i in range(self.user_num):
            user_name = self.user_name_list[i]

            res = self.user_salt_with_correct_response_method(user_name=user_name)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["code"], 0)

    def test_user_salt_with_wrong_response_method(self):
        '''
            Test user salt with wrong response method
        '''
        for i in range(self.user_num):
            user_name = self.user_name_list[i]

            res = self.user_salt_with_wrong_response_method(user_name=user_name)
            self.assertEqual(res.status_code, 404)
            self.assertEqual(res.json()["code"], 1000)

    def test_user_salt_with_non_exist_user(self):
        '''
            Test user salt when user does not exist
        '''
        res = self.user_salt_with_correct_response_method(user_name="Wrong_name!")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 4)

    def test_user_register(self):
        '''
            Test user register
        '''
        res = self.user_register_with_correct_response_method(user_name="Helen", password="Helen_123", salt="es123")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)

    def test_user_register_name_conflict(self):
        '''
            Test user name conflict when registering
        '''
        res = self.user_register_with_correct_response_method(user_name="Alice", password="Alice_1234", salt="es123")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 1)

    def test_register_with_wrong_response_method(self):
        '''
            Test user register with get method
        '''
        res = self.user_register_with_wrong_response_method(user_name="LiuTao", password="WrongMethod!", salt="es123")
        self.assertEqual(res.status_code, 404)

    def test_user_register_with_wrong_type(self):
        '''
            Test user register with wrong data type
        '''
        res = self.user_register_with_correct_response_method(user_name="Cindy", password=1145141919810, salt="es123")
        self.assertEqual(res.status_code, 400)

        res = self.user_register_with_correct_response_method(user_name=1145141919810, password="password", salt="es123")
        self.assertEqual(res.status_code, 400)

    def test_user_modify_password(self):
        '''
            Test user modify password
        '''
        for i in range(self.user_num):
            user_name = self.user_name_list[i]
            old_password = self.user_password[i]
            new_password = "New_" + self.user_password[i]

            token = helpers.create_token(user_name=user_name, user_id=i)
            helpers.add_token_to_white_list(token)
            self.assertEqual(helpers.is_token_valid(token), True)

            res = self.user_modify_password_with_correct_response_method(user_name=user_name, old_password=old_password, new_password=new_password, token=token)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["code"], 0)

            res = self.user_modify_password_with_correct_response_method(user_name=user_name, old_password=new_password, new_password=old_password, token=token)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["code"], 0)

    def test_user_modify_password_with_wrong_response_method(self):
        '''
            Test user modify password with wrong response method
        '''
        for i in range(self.user_num):
            user_name = self.user_name_list[i]
            old_password = self.user_password[i]
            new_password = "New!" + self.user_password[i]

            token = helpers.create_token(user_name=user_name, user_id=i)
            helpers.add_token_to_white_list(token)
            res = self.user_modify_password_with_wrong_response_method(user_name=user_name, old_password=old_password, new_password=new_password, token=token)
            self.assertEqual(res.status_code, 404)
            self.assertEqual(res.json()["code"], 1000)

    def test_user_modify_password_with_wrong_token(self):
        '''
            Test user modify password with wrong token
        '''
        for i in range(self.user_num):
            user_name = self.user_name_list[i]
            old_password = self.user_password[i]
            new_password = "New!" + self.user_password[i]

            token = helpers.create_token(user_name=self.user_name_list[i - 1], user_id=i)
            helpers.add_token_to_white_list(token)
            res = self.user_modify_password_with_correct_response_method(user_name=user_name, old_password=old_password, new_password=new_password, token=token)
            self.assertEqual(res.status_code, 401)
            self.assertEqual(res.json()["code"], 1001)

    def test_user_modify_password_with_user_not_exist(self):
        '''
            Test user modify password when user not exist
        '''
        for i in range(self.user_num):
            user_name = "New!" + self.user_name_list[i]
            old_password = self.user_password[i]
            new_password = "New!" + self.user_password[i]

            token = helpers.create_token(user_name=user_name, user_id=i)
            helpers.add_token_to_white_list(token)
            res = self.user_modify_password_with_correct_response_method(user_name=user_name, old_password=old_password, new_password=new_password, token=token)
            self.assertEqual(res.status_code, 400)
            self.assertEqual(res.json()["code"], 4)

    def test_user_modify_password_with_wrong_password(self):
        '''
            Test user modify password with wrong old password
        '''
        for i in range(self.user_num):
            user_name = self.user_name_list[i]
            old_password = self.user_password[i - 1]
            new_password = self.user_password[i] + "new"

            token = helpers.create_token(user_name=user_name, user_id=i)
            helpers.add_token_to_white_list(token)
            res = self.user_modify_password_with_correct_response_method(user_name=user_name, old_password=old_password, new_password=new_password, token=token)
            self.assertEqual(res.status_code, 400)
            self.assertEqual(res.json()["code"], 4)

    def test_user_logout(self):
        '''
            Test user logout function
        '''
        for i in range(self.user_num):
            user_name = self.user_name_list[i]
            res = self.user_logout_with_correct_response_method(helpers.create_token(user_name="", user_id=""))
            self.assertEqual(res.status_code, 401)
            self.assertEqual(res.json()["code"], 1001)

            token = helpers.create_token(user_name=user_name, user_id=i)
            res = self.user_logout_with_correct_response_method(token)
            self.assertEqual(res.status_code, 401)
            self.assertEqual(res.json()["code"], 1001)

            helpers.add_token_to_white_list(token)
            res = self.user_logout_with_correct_response_method(token)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["code"], 0)

            res = self.user_logout_with_correct_response_method(token)
            self.assertEqual(res.status_code, 401)
            self.assertEqual(res.json()["code"], 1001)

    def test_user_logout_with_wrong_response_method(self):
        '''
            Test user logout with wrong response method
        '''
        for i in range(self.user_num):
            user_name = self.user_name_list[i]
            token = helpers.create_token(user_name=user_name, user_id=i)
            res = self.user_logout_with_wrong_response_method(token)
            self.assertEqual(res.status_code, 404)
            self.assertEqual(res.json()["code"], 1000)

    def test_user_checklogin(self):
        '''
            Test user check login function
        '''
        for i in range(self.user_num):
            user_name = self.user_name_list[i]
            token = helpers.create_token(user_name=user_name, user_id=i)
            res = self.user_checklogin_with_correct_response_method(token)
            self.assertEqual(res.status_code, 401)
            self.assertEqual(res.json()["code"], 1001)

            helpers.add_token_to_white_list(token)
            res = self.user_checklogin_with_correct_response_method(token)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["code"], 0)

            helpers.delete_token_from_white_list(token)
            res = self.user_checklogin_with_correct_response_method(token)
            self.assertEqual(res.status_code, 401)
            self.assertEqual(res.json()["code"], 1001)

    def test_user_checklogin_with_wrong_response_method(self):
        '''
            Test user check login with wrong response method
        '''
        for i in range(self.user_num):
            user_name = self.user_name_list[i]
            token = helpers.create_token(user_name=user_name, user_id=i)
            res = self.user_checklogin_with_wrong_response_method(token)
            self.assertEqual(res.status_code, 404)
            self.assertEqual(res.json()["code"], 1000)
            