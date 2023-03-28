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
        self.user_id = []
        self.user_num = len(self.user_name_list)
        for i in range(self.user_num):
            user_name = self.user_name_list[i]
            password = self.user_password[i]
            user = UserInfo.objects.create(user_name=user_name, password=helpers.hash_password(password))
            user.full_clean()
            user.save()
            self.user_id.append(user.id)

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

    def user_register_with_wrong_response_method(self, user_name, password):
        '''
            Create a GET/user/register HttpRequest
        '''
        req = {
            "user_name": user_name,
            "password": password
        }
        return self.client.get('/user/register', data=req, content_type="application/json")

    def user_register_with_correct_response_method(self, user_name, password):
        '''
            Create a POST/user/register HttpRequest
        '''
        req = {
            "user_name": user_name,
            "password": password
        }
        return self.client.post('/user/register', data=req, content_type="application/json")



    def test_user_login(self):
        '''
            Test user login
        '''
        for i in range(self.user_num):
            user_name = self.user_name_list[i]
            password = self.user_password[i]

            res = self.user_login_with_correct_response_method(user_name=user_name, password=password)
            self.assertEqual(res.status_code, 200)

    def test_user_login_with_wrong_response_method(self):
        '''
            Test user login with wrong response method
        '''
        for i in range(self.user_num):
            user_name = self.user_name_list[i]
            password = self.user_password[i]
            res = self.user_login_with_wrong_response_method(user_name=user_name, password=password)
            self.assertEqual(res.status_code, 404)

    def test_user_login_with_wrong_type(self):
        '''
            Test user login with wrong data type
        '''
        res = self.user_login_with_correct_response_method(user_name="Cindy", password=1145141919810)
        self.assertEqual(res.status_code, 400)

        res = self.user_login_with_correct_response_method(user_name=1145141919810, password="password")
        self.assertEqual(res.status_code, 400)

    def test_user_login_with_wrong_password(self):
        '''
            Test user login with wrong password
        '''
        for i in range(self.user_num):
            user_name = self.user_name_list[i]

            res = self.user_login_with_correct_response_method(user_name=user_name, password="Wrong!")
            self.assertEqual(res.status_code, 400)

    def test_user_login_with_non_exist_user(self):
        '''
            Test user login when user does not exist
        '''
        res = self.user_login_with_correct_response_method(user_name="Wrong_name!", password="Wrong!")
        self.assertEqual(res.status_code, 400)

    def test_user_register(self):
        '''
            Test user register
        '''
        res = self.user_register_with_correct_response_method(user_name="Helen", password="Helen_123")
        self.assertEqual(res.status_code, 200)

    def test_user_register_name_conflict(self):
        '''
            Test user name conflict when registering
        '''
        res = self.user_register_with_correct_response_method(user_name="Alice", password="Alice_1234")
        self.assertEqual(res.status_code, 400)

    def test_register_with_wrong_response_method(self):
        '''
            Test user register with get method
        '''
        res = self.user_register_with_wrong_response_method(user_name="LiuTao", password="WrongMethod!")
        self.assertEqual(res.status_code, 404)

    def test_user_register_with_wrong_type(self):
        '''
            Test user register with wrong data type
        '''
        res = self.user_register_with_correct_response_method(user_name="Cindy", password=1145141919810)
        self.assertEqual(res.status_code, 400)

        res = self.user_register_with_correct_response_method(user_name=1145141919810, password="password")
        self.assertEqual(res.status_code, 400)
