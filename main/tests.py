'''
    test.py in django frame work
'''
from PIL import Image
from django.core.files.base import ContentFile
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from main.models import UserInfo, GifMetadata, GifFile
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

        self.image_title_list = ["Cake", "Milk", "Muffin"]
        self.image_category = ["food", "food", "food"]
        self.image_tags = [["food", "cake"], ["food", "milk"], ["food", "muffin"]]
        self.image_id = []
        self.image_num = len(self.image_title_list)
        for i in range(self.image_num):
            image_title = self.image_title_list[i]
            category = self.image_category[i]
            tags = self.image_tags[i]
            image_url = 'files/tests/'+image_title+'.gif'

            gif = GifMetadata.objects.create(title=image_title, uploader=user.id, category=category, tags=tags)
            gif.full_clean()
            gif.save()
            gif_file = GifFile.objects.create(metadata=gif, file=image_url)

            with open(image_url, 'rb') as temp_gif:
                gif_file.file.save(image_title+'.gif', ContentFile(temp_gif.read()))
            gif_file.save()

            with Image.open(gif_file.file) as image:
                duration = image.info['duration'] * image.n_frames
            gif.duration = duration / 1000.0
            gif.width = gif_file.file.width
            gif.height = gif_file.file.height
            gif.name = gif_file.file.name
            gif.save()
            self.image_id.append(gif.id)

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

    def user_add_history_with_wrong_response_method(self, gif_id, token):
        '''
            Create a DELETE/user/history HttpRequest
        '''
        url = f'/user/read_history?id={gif_id}'
        return self.client.delete(url, HTTP_AUTHORIZATION=token)

    def user_add_history_with_correct_response_method(self, gif_id, token):
        '''
            Create a POST/user/history HttpRequest
        '''
        url = f'/user/read_history?id={gif_id}'
        return self.client.post(url, HTTP_AUTHORIZATION=token)

    def user_history_with_wrong_response_method(self, page, token):
        '''
            Create a DELETE/user/history HttpRequest
        '''
        url = f'/user/read_history?page={page}'
        return self.client.delete(url, HTTP_AUTHORIZATION=token)

    def user_history_with_correct_response_method(self, page, token):
        '''
            Create a GET/user/history HttpRequest
        '''
        url = f'/user/read_history?page={page}'
        return self.client.get(url, HTTP_AUTHORIZATION=token)

    def image_upload_with_correct_response_method(self, url, title, category, tags, token):
        '''
            Create a POST/image/upload HttpRequest
        '''
        # with open('/files/tests/Cake.jpg', 'rb') as f:
        #     file_data = f.read()
        # uploaded_file = SimpleUploadedFile('Strawberry.jpg', file_data)

        with open(url, 'rb') as reader:
            file_data = reader.read()
        uploaded_file = SimpleUploadedFile(url, file_data)

        req = {
            'file': uploaded_file,
            'title': title,
            'category': category,
            'tags': tags
        }
        return self.client.post('/image/upload', data=req, format='multipart', HTTP_AUTHORIZATION=token)

    def image_upload_with_wrong_response_method(self, url, title, category, tags, token):
        '''
            Create a GET/image/upload HttpRequest
        '''
        # with open('/files/tests/Cake.jpg', 'rb') as f:
        #     file_data = f.read()
        # uploaded_file = SimpleUploadedFile('Strawberry.jpg', file_data)

        with open(url, 'rb') as reader:
            file_data = reader.read()
        uploaded_file = SimpleUploadedFile(url, file_data)

        req = {
            'file': uploaded_file,
            'title': title,
            'category': category,
            'tags': tags
        }
        return self.client.get('/image/upload', data=req, format='multipart', HTTP_AUTHORIZATION=token)

    def image_upload_with_wrong_type(self, url, title, category, tags, token):
        '''
            Create a GET/image/upload HttpRequest
        '''
        with open(url, 'rb') as reader:
            file_data = reader.read()
        uploaded_file = SimpleUploadedFile(url, file_data)

        req = {
            'file': uploaded_file,
            'title': title,
            'category': category,
            'tag': tags
        }
        return self.client.post('/image/upload', data=req, format='multipart', HTTP_AUTHORIZATION=token)

    def image_detail_with_wrong_response_method(self, image_id):
        '''
            Create a POST/image/detail HttpRequest
        '''
        return self.client.post('/image/detail/'+image_id)

    def image_detail_with_correct_response_method(self, image_id):
        '''
            Create a GET/image/detail HttpRequest
        '''
        return self.client.get('/image/detail/'+image_id)

    def image_delete_with_wrong_response_method(self, image_id, token):
        '''
            Create a POST/image/detail HttpRequest
        '''
        return self.client.post('/image/detail/'+image_id, HTTP_AUTHORIZATION=token)

    def image_delete_with_correct_response_method(self, image_id, token):
        '''
            Create a DELETE/image/detail HttpRequest
        '''
        return self.client.delete('/image/detail/'+image_id, HTTP_AUTHORIZATION=token)

    def image_preview_with_wrong_response_method(self, image_id):
        '''
            Create a POST/image/preview HttpRequest
        '''
        return self.client.post('/image/preview/'+image_id)

    def image_preview_with_correct_response_method(self, image_id):
        '''
            Create a GET/image/preview HttpRequest
        '''
        return self.client.get('/image/preview/'+image_id)

    def image_download_with_wrong_response_method(self, image_id):
        '''
            Create a POST/image/download HttpRequest
        '''
        return self.client.post('/image/download/'+image_id)

    def image_download_with_correct_response_method(self, image_id):
        '''
            Create a GET/image/download HttpRequest
        '''
        return self.client.get('/image/download/'+image_id)

    def image_download_zip_with_wrong_response_method(self, image_ids):
        '''
            Create a GET/image/download_zip HttpRequest
        '''
        req = {
            "gif_ids": image_ids
        }
        return self.client.get('/image/download_zip', data=req, content_type="application/json")

    def image_download_zip_with_correct_response_method(self, image_ids):
        '''
            Create a POST/image/download_zip HttpRequest
        '''
        req = {
            "gif_ids": image_ids
        }
        return self.client.post('/image/download_zip', data=req, content_type="application/json")

    def image_like_with_wrong_response_method(self, image_id, token):
        '''
            Create a GET/image/like HttpRequest
        '''
        req = {
            "gif_id": image_id
        }
        return self.client.get('/image/like', data=req, content_type="application/json", HTTP_AUTHORIZATION=token)

    def image_like_with_correct_response_method(self, image_id, token):
        '''
            Create a POST/image/like HttpRequest
        '''
        req = {
            "gif_id": image_id
        }
        return self.client.post('/image/like', data=req, content_type="application/json", HTTP_AUTHORIZATION=token)

    def image_cancel_like_with_wrong_response_method(self, image_id, token):
        '''
            Create a GET/image/cancel-like HttpRequest
        '''
        req = {
            "gif_id": image_id
        }
        return self.client.get('/image/cancel-like', data=req, content_type="application/json", HTTP_AUTHORIZATION=token)

    def image_cancel_like_with_correct_response_method(self, image_id, token):
        '''
            Create a POST/image/cancel-like HttpRequest
        '''
        req = {
            "gif_id": image_id
        }
        return self.client.post('/image/cancel-like', data=req, content_type="application/json", HTTP_AUTHORIZATION=token)

    def image_allgifs_with_wrong_response_method(self, category):
        '''
            Create a GET/image/allgifs HttpRequest
        '''
        req = {
            "category": category
        }
        return self.client.get('/image/allgifs', data=req, content_type="application/json")

    def image_allgifs_with_correct_response_method(self, category):
        '''
            Create a POST/image/allgifs HttpRequest
        '''
        req = {
            "category": category
        }
        return self.client.post('/image/allgifs', data=req, content_type="application/json")


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

    def test_user_history(self):
        '''
            Test user history function
        '''
        user = UserInfo.objects.filter(user_name=self.user_name_list[0]).first()
        user_token = helpers.create_token(user_name=user.user_name, user_id=user.id)
        helpers.add_token_to_white_list(user_token)

        res = self.user_history_with_correct_response_method(1, user_token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        self.assertEqual(res.json()["data"]["page_count"], 0)

        self.user_add_history_with_correct_response_method(1, user_token)
        res = self.user_history_with_correct_response_method(1, user_token)
        self.assertEqual(res.json()["data"]["page_count"], 1)
        self.assertEqual(len(res.json()["data"]["page_data"]), 1)

        self.user_add_history_with_correct_response_method(2, user_token)
        res = self.user_history_with_correct_response_method(1, user_token)
        self.assertEqual(res.json()["data"]["page_count"], 1)
        self.assertEqual(len(res.json()["data"]["page_data"]), 2)

    def test_user_history_with_wrong_response_method(self):
        '''
            Test user history with wrong response method
        '''
        user = UserInfo.objects.filter(user_name=self.user_name_list[0]).first()
        user_token = helpers.create_token(user_name=user.user_name, user_id=user.id)
        helpers.add_token_to_white_list(user_token)

        res = self.user_add_history_with_wrong_response_method(1, user_token)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)

        res = self.user_history_with_wrong_response_method(1, user_token)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)

    def test_image_upload(self):
        '''
            Test image upload function
        '''
        user = UserInfo.objects.filter(user_name=self.user_name_list[0]).first()
        user_token = helpers.create_token(user_name=user.user_name, user_id=user.id)
        helpers.add_token_to_white_list(user_token)

        res = self.image_upload_with_correct_response_method(url="files/tests/Strawberry.gif", title="Strawberry", category="food", tags=["food", "strawberry"], token=user_token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        self.assertEqual(res.json()["data"]["uploader"], 1)

    def test_image_upload_with_user_not_exist(self):
        '''
            Test image upload when user not exist
        '''
        token = helpers.create_token(user_name="not_exist", user_id=100)
        res = self.image_upload_with_correct_response_method(url="files/tests/Strawberry.gif", title="Strawberry", category="food", tags=["food", "strawberry"], token=token)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], 1001)

    def test_image_upload_with_wrong_response_method(self):
        '''
            Test image upload with wrong response method
        '''
        user = UserInfo.objects.filter(user_name=self.user_name_list[0]).first()
        user_token = helpers.create_token(user_name=user.user_name, user_id=user.id)
        helpers.add_token_to_white_list(user_token)

        res = self.image_upload_with_wrong_response_method(url="files/tests/Strawberry.gif", title="Strawberry", category="food", tags=["food", "strawberry"], token=user_token)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)

    def test_image_upload_with_wrong_type(self):
        '''
            Test image upload with wrong type
        '''
        user = UserInfo.objects.filter(user_name=self.user_name_list[0]).first()
        user_token = helpers.create_token(user_name=user.user_name, user_id=user.id)
        helpers.add_token_to_white_list(user_token)

        res = self.image_upload_with_wrong_type(url="files/tests/Strawberry.gif", title="Strawberry", category="food", tags=["food"], token=user_token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 1005)

    def test_image_upload_with_invalid_token(self):
        '''
            Test image upload function
        '''
        user_token = helpers.create_token(user_name="NotExist!", user_id=114514)

        res = self.image_upload_with_correct_response_method(url="files/tests/Strawberry.gif", title="Strawberry", category="food", tags=["food", "strawberry"], token=user_token)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], 1001)

    def test_image_detail(self):
        '''
            Test image detail function
        '''
        for i in range(self.image_num):
            image_index = str(self.image_id[i])

            res = self.image_detail_with_correct_response_method(image_id=image_index)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["code"], 0)

    def test_image_detail_with_image_not_eixst(self):
        '''
            Test image detail when image not exist
        '''
        res = self.image_detail_with_correct_response_method(image_id="not_a_number")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 9)

        res = self.image_detail_with_correct_response_method(image_id="114514")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 9)

    def test_image_detail_with_wrong_response_method(self):
        '''
            Test image detail with wrong response method
        '''
        for i in range(self.image_num):
            image_index = str(self.image_id[i])

            res = self.image_detail_with_wrong_response_method(image_id=image_index)
            self.assertEqual(res.status_code, 404)
            self.assertEqual(res.json()["code"], 1000)

    def test_image_delete(self):
        '''
            Test image delete function
        '''
        user = UserInfo.objects.filter(user_name=self.user_name_list[0]).first()
        user_token = helpers.create_token(user_name=user.user_name, user_id=user.id)
        helpers.add_token_to_white_list(user_token)

        res = self.image_upload_with_correct_response_method(url="files/tests/Noodles.gif", title="Noodles", category="food", tags=["food", "noodles"], token=user_token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        image_id = str(res.json()["data"]["id"])

        res = self.image_delete_with_correct_response_method(image_id=image_id, token=user_token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)

        res = self.image_delete_with_correct_response_method(image_id=image_id, token=user_token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 9)

    def test_image_delete_with_user_not_eixst(self):
        '''
            Test image delete with user not eixst
        '''
        user = UserInfo.objects.filter(user_name=self.user_name_list[0]).first()
        user_token = helpers.create_token(user_name=user.user_name, user_id=user.id)
        wrong_token = helpers.create_token(user_name="NotThis", user_id=321)
        helpers.add_token_to_white_list(user_token)

        res = self.image_upload_with_correct_response_method(url="files/tests/Noodles.gif", title="Noodles", category="food", tags=["food", "noodles"], token=user_token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        image_id = str(res.json()["data"]["id"])

        res = self.image_delete_with_correct_response_method(image_id=image_id, token=wrong_token)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], 1001)

        res = self.image_delete_with_correct_response_method(image_id=image_id, token=user_token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)

    def test_image_delete_with_wrong_method(self):
        '''
            Test image delete with wrong method
        '''
        user = UserInfo.objects.filter(user_name=self.user_name_list[0]).first()
        user_token = helpers.create_token(user_name=user.user_name, user_id=user.id)
        helpers.add_token_to_white_list(user_token)

        res = self.image_upload_with_correct_response_method(url="files/tests/Noodles.gif", title="Noodles", category="food", tags=["food", "noodles"], token=user_token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        image_id = str(res.json()["data"]["id"])

        res = self.image_delete_with_wrong_response_method(image_id=image_id, token=user_token)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)

        res = self.image_delete_with_correct_response_method(image_id=image_id, token=user_token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)

    def test_image_upload_uniqueness(self):
        '''
            Test image upload uniqueness
        '''
        user = UserInfo.objects.filter(user_name=self.user_name_list[0]).first()
        user_token = helpers.create_token(user_name=user.user_name, user_id=user.id)
        helpers.add_token_to_white_list(user_token)

        res = self.image_upload_with_correct_response_method(url="files/tests/Noodles.gif", title="Noodles", category="food", tags=["food", "noodles"], token=user_token)
        image_id = str(res.json()["data"]["id"])
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        self.assertEqual(res.json()["data"]["uploader"], user.id)

        res = self.image_upload_with_correct_response_method(url="files/tests/Noodles.gif", title="Noodles", category="food", tags=["food", "noodles"], token=user_token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        self.assertEqual(res.json()["data"], {'id': 1})

        res = self.image_delete_with_correct_response_method(image_id=image_id, token=user_token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)

    def test_image_preview(self):
        '''
            Test image preview
        '''
        for i in self.image_id:
            res = self.image_preview_with_correct_response_method(image_id=str(i))
            gif = GifMetadata.objects.all().filter(id=i).first()
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res['Content-Disposition'], f'inline; filename="{gif.name}"')
            self.assertEqual(res['Content-Type'], 'image/gif')

    def test_image_preview_with_image_not_eixst(self):
        '''
            Test image preview with user not eixst
        '''
        res = self.image_preview_with_correct_response_method(image_id=str(114514))
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 9)

    def test_image_preview_with_wrong_method(self):
        '''
            Test image preview with wrong method
        '''
        for i in self.image_id:
            res = self.image_preview_with_wrong_response_method(image_id=str(i))
            self.assertEqual(res.status_code, 404)
            self.assertEqual(res.json()["code"], 1000)

    def test_image_download(self):
        '''
            Test image download
        '''
        for i in self.image_id:
            res = self.image_download_with_correct_response_method(image_id=str(i))
            gif = GifMetadata.objects.all().filter(id=i).first()
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res['Content-Disposition'], f'attachment; filename="{gif.title}.gif"')
            self.assertEqual(res['Content-Type'], 'application/octet-stream')

    def test_image_download_with_image_not_eixst(self):
        '''
            Test image download with image not eixst
        '''
        res = self.image_download_with_correct_response_method(image_id=str(114514))
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 9)

    def test_image_download_with_wrong_method(self):
        '''
            Test image download with wrong method
        '''
        for i in self.image_id:
            res = self.image_download_with_wrong_response_method(image_id=str(i))
            self.assertEqual(res.status_code, 404)
            self.assertEqual(res.json()["code"], 1000)

    def test_image_download_zip(self):
        '''
            Test image download_zip
        '''
        image_ids = []
        for i in self.image_id:
            image_ids.append(i)
        res = self.image_download_zip_with_correct_response_method(image_ids=image_ids)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'application/zip')

    def test_image_download_zip_with_image_not_eixst(self):
        '''
            Test image download_zip with image not eixst
        '''
        image_ids = []
        for i in self.image_id:
            image_ids.append(i)
        image_ids.append(114514)
        res = self.image_download_zip_with_correct_response_method(image_ids=image_ids)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 9)

    def test_image_download_zip_with_wrong_method(self):
        '''
            Test image download_zip with wrong method
        '''
        image_ids = []
        for i in self.image_id:
            image_ids.append(i)
        res = self.image_download_zip_with_wrong_response_method(image_ids=image_ids)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)

    def test_image_like(self):
        '''
            Test image like
        '''
        user = UserInfo.objects.filter(user_name=self.user_name_list[0]).first()
        user_token = helpers.create_token(user_name=user.user_name, user_id=user.id)
        helpers.add_token_to_white_list(user_token)

        for i in self.image_id:
            res = self.image_like_with_correct_response_method(image_id=i, token=user_token)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["code"], 0)
            res = self.image_detail_with_correct_response_method(image_id=str(i))
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["code"], 0)
            self.assertEqual(res.json()["data"]["like"], 1)
            res = self.image_cancel_like_with_correct_response_method(image_id=i, token=user_token)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["code"], 0)
            res = self.image_detail_with_correct_response_method(image_id=str(i))
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["code"], 0)
            self.assertEqual(res.json()["data"]["like"], 0)

    def test_image_like_with_wrong_response_method(self):
        '''
            Test image like with wrong response method
        '''
        user = UserInfo.objects.filter(user_name=self.user_name_list[0]).first()
        user_token = helpers.create_token(user_name=user.user_name, user_id=user.id)
        helpers.add_token_to_white_list(user_token)

        res = self.image_like_with_wrong_response_method(image_id=self.image_id[0], token=user_token)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)
        res = self.image_cancel_like_with_wrong_response_method(image_id=self.image_id[0], token=user_token)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)

    def test_image_like_with_invalid_token(self):
        '''
            Test image like with invalid token
        '''
        user_token = helpers.create_token(user_name="NotExist!", user_id=114514)

        res = self.image_like_with_correct_response_method(image_id=self.image_id[0], token=user_token)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], 1001)
        res = self.image_like_with_correct_response_method(image_id=self.image_id[0], token=user_token)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], 1001)

    def test_image_like_with_wrong_type(self):
        '''
            Test image like with wrong type
        '''
        user = UserInfo.objects.filter(user_name=self.user_name_list[0]).first()
        user_token = helpers.create_token(user_name=user.user_name, user_id=user.id)
        helpers.add_token_to_white_list(user_token)

        res = self.image_like_with_correct_response_method(image_id="string", token=user_token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 1005)
        res = self.image_cancel_like_with_correct_response_method(image_id="string", token=user_token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 1005)

    def test_image_allgifs(self):
        '''
            Test image allgifs
        '''
        res = self.image_allgifs_with_correct_response_method("food")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        self.assertEqual(len(res.json()["data"]), 3)

    def test_image_allgifs_with_category_not_eixst(self):
        '''
            Test image allgifs with category not eixst
        '''
        res = self.image_allgifs_with_correct_response_method("joyful")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)

    def test_image_allgifs_with_wrong_method(self):
        '''
            Test image allgifs with wrong method
        '''
        res = self.image_allgifs_with_wrong_response_method("food")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)
