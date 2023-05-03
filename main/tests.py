'''
    test.py in django frame work
'''
import time
import uuid
import datetime
from PIL import Image
from django.core.files.base import ContentFile
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from main.models import UserInfo, GifMetadata, GifFile, UserVerification
from . import helpers

class ViewsTests(TestCase):
    '''
        Test functions in views.py
    '''
    def setUp(self):
        self.user_name_list = ["Alice", "Bob", "a刘华强"]
        self.user_password = ["Alice_123", "Bob_123", "Huaqiang_123"]
        self.user_salt = ["alicesalt", "bobsalt", "huaqiangsalt"]
        self.user_mail = ["Alice@163.com", "Bob@126.com", "huaqiang@126.com"]
        self.user_verified_token = ["309bb939-145a-4793-91f6-d868bef1db3e",
                           "309bb939-145a-4793-91f6-d868bef1db3f",
                           "309bb939-145a-4793-91f6-d868bef1db3g"]
        self.user_id = []
        self.user_token = []
        self.user_num = len(self.user_name_list)
        for i in range(self.user_num):
            user_name = self.user_name_list[i]
            password = self.user_password[i]
            salt = self.user_salt[i]
            mail = self.user_mail[i]
            verified_token = self.user_verified_token[i]
            user = UserInfo.objects.create(user_name=user_name, password=helpers.hash_password(password), salt=salt, mail=mail)
            user.full_clean()
            user.save()
            vertificates_user = UserVerification.objects.create(user_name=user_name, token=verified_token, password=helpers.hash_password(password), salt=salt, mail=mail, is_verified=True)
            vertificates_user.full_clean()
            vertificates_user.save()
            self.user_id.append(user.id)
            token = helpers.create_token(user_name=user.user_name, user_id=user.id)
            self.user_token.append(token)

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

    def user_register_with_wrong_response_method(self, user_name, password, salt, mail):
        '''
            Create a GET/user/register HttpRequest
        '''
        req = {
            "user_name": user_name,
            "password": password,
            "salt": salt,
            "mail": mail
        }
        return self.client.get('/user/register', data=req, content_type="application/json")

    def user_register_with_correct_response_method(self, user_name, password, salt, mail):
        '''
            Create a POST/user/register HttpRequest
        '''
        req = {
            "user_name": user_name,
            "password": password,
            "salt": salt,
            "mail": mail
        }
        return self.client.post('/user/register', data=req, content_type="application/json")

    def user_mail_verify_with_wrong_response_method(self, token):
        '''
            Create a POST/user/verify HttpRequest
        '''
        return self.client.post('/user/verify/'+token)

    def user_mail_verify_with_correct_response_method(self, token):
        '''
            Create a GET/user/verify HttpRequest
        '''
        return self.client.get('/user/verify/'+token)

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

    def user_avatar_with_wrong_response_method(self, url, token):
        '''
            Create a PUT/user/avatar HttpRequest
        '''
        with open(url, 'rb') as reader:
            file_data = reader.read()
        uploaded_file = SimpleUploadedFile(url, file_data)

        req = {
            'file': uploaded_file,
        }
        return self.client.put('/user/avatar', data=req, format='multipart', HTTP_AUTHORIZATION=token)

    def user_avatar_with_file_not_exist(self, url, token):
        '''
            Create a POST/user/avatar HttpRequest
        '''
        with open(url, 'rb') as reader:
            file_data = reader.read()
        uploaded_file = SimpleUploadedFile(url, file_data)

        req = {
            'files': uploaded_file,
        }
        return self.client.post('/user/avatar', data=req, format='multipart', HTTP_AUTHORIZATION=token)

    def user_avatar_with_correct_response_method(self, url, token):
        '''
            Create a POST/user/avatar HttpRequest
        '''
        with open(url, 'rb') as reader:
            file_data = reader.read()
        uploaded_file = SimpleUploadedFile(url, file_data)

        req = {
            'file': uploaded_file,
        }
        return self.client.post('/user/avatar', data=req, format='multipart', HTTP_AUTHORIZATION=token)

    def user_avatar_get_with_correct_response_method(self, token):
        '''
            Create a GET/user/avatar HttpRequest
        '''
        return self.client.get('/user/avatar', HTTP_AUTHORIZATION=token)

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

    def user_profile_with_wrong_response_method(self, user_id):
        '''
            Create a POST/user/profile HttpRequest
        '''
        return self.client.post('/user/profile/'+user_id)

    def user_profile_with_correct_response_method(self, user_id):
        '''
            Create a GET/user/profile HttpRequest
        '''
        return self.client.get('/user/profile/'+user_id)

    def user_follow_with_wrong_response_method(self, user_id, token):
        '''
            Create a GET/user/follow HttpRequest
        '''
        return self.client.get('/user/follow/'+str(user_id), HTTP_AUTHORIZATION=token)

    def user_follow_with_correct_response_method(self, user_id, token):
        '''
            Create a POST/user/follow HttpRequest
        '''
        return self.client.post('/user/follow/'+str(user_id), HTTP_AUTHORIZATION=token)

    def user_unfollow_with_wrong_response_method(self, user_id, token):
        '''
            Create a GET/user/unfollow HttpRequest
        '''
        return self.client.get('/user/unfollow/'+str(user_id), HTTP_AUTHORIZATION=token)

    def user_unfollow_with_correct_response_method(self, user_id, token):
        '''
            Create a POST/user/unfollow HttpRequest
        '''
        return self.client.post('/user/unfollow/'+str(user_id), HTTP_AUTHORIZATION=token)

    def user_add_history_with_wrong_response_method(self, gif_id, token):
        '''
            Create a DELETE/user/history HttpRequest
        '''
        url = f'/user/readhistory?id={gif_id}'
        return self.client.delete(url, HTTP_AUTHORIZATION=token)

    def user_add_history_with_correct_response_method(self, gif_id, token):
        '''
            Create a POST/user/history HttpRequest
        '''
        url = f'/user/readhistory?id={gif_id}'
        return self.client.post(url, HTTP_AUTHORIZATION=token)

    def user_history_with_wrong_response_method(self, page, token):
        '''
            Create a DELETE/user/history HttpRequest
        '''
        url = f'/user/readhistory?page={page}'
        return self.client.delete(url, HTTP_AUTHORIZATION=token)

    def user_history_with_correct_response_method(self, page, token):
        '''
            Create a GET/user/history HttpRequest
        '''
        url = f'/user/readhistory?page={page}'
        return self.client.get(url, HTTP_AUTHORIZATION=token)

    def image_upload_with_correct_response_method(self, url, title, category, tags, token):
        '''
            Create a POST/image/upload HttpRequest
        '''
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
            'categori': category,
            'tags': tags
        }
        return self.client.post('/image/upload', data=req, format='multipart', HTTP_AUTHORIZATION=token)

    def image_update_with_correct_response_method(self, gif_id, category, tags, token):
        '''
            Create a POST/image/update HttpRequest
        '''
        req = {
            'category': category,
            'tags': tags
        }
        return self.client.post('/image/update/' + gif_id, data=req, content_type="application/json", HTTP_AUTHORIZATION=token)

    def image_update_with_wrong_response_method(self, gif_id, category, tags, token):
        '''
            Create a GET/image/update HttpRequest
        '''
        req = {
            'category': category,
            'tags': tags
        }
        return self.client.get('/image/update/' + gif_id, data=req, content_type="application/json", HTTP_AUTHORIZATION=token)

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

    def image_downloadzip_with_wrong_response_method(self, image_ids):
        '''
            Create a GET/image/downloadzip HttpRequest
        '''
        req = {
            "gif_ids": image_ids
        }
        return self.client.get('/image/downloadzip', data=req, content_type="application/json")

    def image_downloadzip_with_correct_response_method(self, image_ids):
        '''
            Create a POST/image/downloadzip HttpRequest
        '''
        req = {
            "gif_ids": image_ids
        }
        return self.client.post('/image/downloadzip', data=req, content_type="application/json")

    def image_like_with_wrong_response_method(self, image_id, token):
        '''
            Create a GET/image/like HttpRequest
        '''
        return self.client.get('/image/like/'+str(image_id), HTTP_AUTHORIZATION=token)

    def image_like_with_correct_response_method(self, image_id, token):
        '''
            Create a POST/image/like HttpRequest
        '''
        return self.client.post('/image/like/'+str(image_id), HTTP_AUTHORIZATION=token)

    def image_cancel_like_with_wrong_response_method(self, image_id, token):
        '''
            Create a GET/image/cancellike HttpRequest
        '''
        return self.client.get('/image/cancellike/'+str(image_id), HTTP_AUTHORIZATION=token)

    def image_cancel_like_with_correct_response_method(self, image_id, token):
        '''
            Create a POST/image/cancellike HttpRequest
        '''
        return self.client.post('/image/cancellike/'+str(image_id), HTTP_AUTHORIZATION=token)

    def image_comment_with_wrong_response_method(self, gif_id, token):
        '''
            Create a PUT/image/comment HttpRequest
        '''
        req = {
            "content": "这是一条测试评论"
        }
        return self.client.put('/image/comment/'+str(gif_id), data=req, content_type="application/json", HTTP_AUTHORIZATION=token)

    def image_comment_with_wrong_token(self, gif_id, token):
        '''
            Create a POST/image/comment HttpRequest
        '''
        req = {
            "content": "这是一条测试评论"
        }
        return self.client.post('/image/comment/'+str(gif_id), data=req, content_type="application/json", HTTP_AUTHORIZATION=token)

    def image_comment_with_gif_not_exists(self, gif_id, token):
        '''
            Create a POST/image/comment HttpRequest
        '''
        req = {
            "content": "这是一条测试评论"
        }
        return self.client.post('/image/comment/'+str(gif_id), data=req, content_type="application/json", HTTP_AUTHORIZATION=token)

    def image_comment_with_comment_not_exists(self, gif_id, parent_id, token):
        '''
            Create a POST/image/comment HttpRequest
        '''
        req = {
            "content": "这是一条测试评论",
            "parent_id": parent_id
        }
        return self.client.post('/image/comment/'+str(gif_id), data=req, content_type="application/json", HTTP_AUTHORIZATION=token)

    def image_comment_parent_with_correct_response_method(self, gif_id, token):
        '''
            Create a POST/image/comment HttpRequest
        '''
        req = {
            "content": "这是一条测试评论"
        }
        return self.client.post('/image/comment/'+str(gif_id), data=req, content_type="application/json", HTTP_AUTHORIZATION=token)

    def image_comment_son_with_correct_response_method(self, gif_id, parent_id, token):
        '''
            Create a POST/image/comment HttpRequest
        '''
        req = {
            "content": "这是一条测试评论",
            "parent_id": parent_id
        }
        return self.client.post('/image/comment/'+str(gif_id), data=req, content_type="application/json", HTTP_AUTHORIZATION=token)

    def image_comment_get_with_wrong_response_method(self, gif_id, token):
        '''
            Create a PUT/image/comment HttpRequest
        '''
        return self.client.put('/image/comment/'+str(gif_id), HTTP_AUTHORIZATION=token)

    def image_comment_get_with_gif_not_found(self, gif_id, token):
        '''
            Create a GET/image/comment HttpRequest
        '''
        return self.client.get('/image/comment/'+str(gif_id), HTTP_AUTHORIZATION=token)

    def image_comment_get_with_wrong_token(self, gif_id, token):
        '''
            Create a GET/image/comment HttpRequest
        '''
        return self.client.get('/image/comment/'+str(gif_id), HTTP_AUTHORIZATION=token)

    def image_comment_get_with_correct_response_method(self, gif_id, token):
        '''
            Create a GET/image/comment HttpRequest
        '''
        return self.client.get('/image/comment/'+str(gif_id), HTTP_AUTHORIZATION=token)

    def image_comment_delete_with_wrong_response_method(self, comment_id, token):
        '''
            Create a PUT/image/comment/delete HttpRequest
        '''
        return self.client.put('/image/comment/delete/'+str(comment_id), HTTP_AUTHORIZATION=token)

    def image_comment_delete_with_comment_not_found(self, comment_id, token):
        '''
            Create a DELETE/image/comment/delete HttpRequest
        '''
        return self.client.delete('/image/comment/delete/'+str(comment_id), HTTP_AUTHORIZATION=token)

    def image_comment_delete_with_wrong_token(self, comment_id, token):
        '''
            Create a DELETE/image/comment/delete HttpRequest
        '''
        return self.client.delete('/image/comment/delete/'+str(comment_id), HTTP_AUTHORIZATION=token)

    def image_comment_delete_with_correct_response_method(self, comment_id, token):
        '''
            Create a DELETE/image/comment/delete HttpRequest
        '''
        return self.client.delete('/image/comment/delete/'+str(comment_id), HTTP_AUTHORIZATION=token)

    def image_comment_like_with_wrong_response_method(self, comment_id, token):
        '''
            Create a GET/image/comment/like HttpRequest
        '''
        return self.client.get('/image/comment/like/'+str(comment_id), HTTP_AUTHORIZATION=token)

    def image_comment_like_with_correct_response_method(self, comment_id, token):
        '''
            Create a POST/image/comment/like HttpRequest
        '''
        return self.client.post('/image/comment/like/'+str(comment_id), HTTP_AUTHORIZATION=token)

    def image_comment_cancel_like_with_wrong_response_method(self, comment_id, token):
        '''
            Create a GET/image/comment/cancellike HttpRequest
        '''
        return self.client.get('/image/comment/cancellike/'+str(comment_id), HTTP_AUTHORIZATION=token)

    def image_comment_cancel_like_with_correct_response_method(self, comment_id, token):
        '''
            Create a POST/image/comment/cancellike HttpRequest
        '''
        return self.client.post('/image/comment/cancellike/'+str(comment_id), HTTP_AUTHORIZATION=token)

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

    def test_user_mail_verify(self):
        '''
            Test user mail verify
        '''
        verification_token = str(uuid.uuid4())
        vertificated_user = UserVerification.objects.create(user_name="Helen6",
                                                            token=verification_token,
                                                            mail="Helen@163.com",
                                                            password=helpers.hash_password("Helen123"),
                                                            salt="6ev3hi91",
                                                            created_at=datetime.datetime.now())
        vertificated_user.save()

        res = self.user_mail_verify_with_correct_response_method(token=verification_token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)

    def test_user_mail_verify_with_wrong_response_method(self):
        '''
            Test user mail verify with wrong response method
        '''
        verification_token = str(uuid.uuid4())
        res = self.user_mail_verify_with_wrong_response_method(token=verification_token)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)

    def test_user_mail_verify_with_wrong_token(self):
        '''
            Test user mail verify with wrong token
        '''
        verification_token = str(uuid.uuid4())
        res = self.user_mail_verify_with_correct_response_method(token=verification_token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 15)

    def test_user_mail_verify_with_verified_user(self):
        '''
            Test user mail verify with verified user
        '''
        verification_token = self.user_verified_token[0]
        res = self.user_mail_verify_with_correct_response_method(token=verification_token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 16)

    def test_user_mail_verify_with_too_long_time(self):
        '''
            Test user mail verify with too long time
        '''
        verification_token = str(uuid.uuid4())
        vertificated_user = UserVerification.objects.create(user_name="Helen123",
                                                            token=verification_token,
                                                            mail="Helen@qq.com",
                                                            password=helpers.hash_password("Helen1314"),
                                                            salt="vcs7d206",
                                                            created_at=datetime.datetime.now())
        vertificated_user.save()
        time.sleep(6)

        res = self.user_mail_verify_with_correct_response_method(token=verification_token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 17)

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
        res = self.user_register_with_correct_response_method(user_name="Helen", password="Helen_123", salt="es123", mail="Helen@163.com")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)

    def test_user_register_name_conflict(self):
        '''
            Test user name conflict when registering
        '''
        res = self.user_register_with_correct_response_method(user_name="Alice", password="Alice_1234", salt="es123", mail="AliceBeauty@126.com")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 1)

        verification_token = str(uuid.uuid4())
        vertificated_user = UserVerification.objects.create(user_name="Helen181",
                                                            token=verification_token,
                                                            mail="Helen@126.com",
                                                            password="Helen5672",
                                                            salt="7ca6dqe3",
                                                            created_at=datetime.datetime.now())
        vertificated_user.save()

        res = self.user_register_with_correct_response_method(user_name="Helen181", password="Alice_1234", salt="es123", mail="AliceBeauty@126.com")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 1)

    def test_register_with_wrong_response_method(self):
        '''
            Test user register with get method
        '''
        res = self.user_register_with_wrong_response_method(user_name="LiuTao", password="WrongMethod!", salt="es123", mail="AliceBeauty@126.com")
        self.assertEqual(res.status_code, 404)

    def test_user_register_with_wrong_type(self):
        '''
            Test user register with wrong data type
        '''
        res = self.user_register_with_correct_response_method(user_name="Cindy", password=1145141919810, salt="es123", mail="Cindy@126.com")
        self.assertEqual(res.status_code, 400)

        res = self.user_register_with_correct_response_method(user_name=1145141919810, password="password", salt="es123", mail="Tensorflow@126.com")
        self.assertEqual(res.status_code, 400)

    def test_user_modify_password(self):
        '''
            Test user modify password
        '''
        for i in range(self.user_num):
            user_name = self.user_name_list[i]
            old_password = self.user_password[i]
            new_password = "New_" + self.user_password[i]

            token = self.user_token[i]
            helpers.add_token_to_white_list(token)
            self.assertEqual(helpers.is_token_valid(token), True)

            res = self.user_modify_password_with_correct_response_method(user_name=user_name, old_password=old_password, new_password=new_password, token=token)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["code"], 0)

            res = self.user_modify_password_with_correct_response_method(user_name=user_name, old_password=new_password, new_password=old_password, token=token)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["code"], 0)
            helpers.delete_token_from_white_list(token)

    def test_user_modify_password_with_wrong_response_method(self):
        '''
            Test user modify password with wrong response method
        '''
        for i in range(self.user_num):
            user_name = self.user_name_list[i]
            old_password = self.user_password[i]
            new_password = "New!" + self.user_password[i]

            token = self.user_token[i]
            helpers.add_token_to_white_list(token)
            res = self.user_modify_password_with_wrong_response_method(user_name=user_name, old_password=old_password, new_password=new_password, token=token)
            self.assertEqual(res.status_code, 404)
            self.assertEqual(res.json()["code"], 1000)
            helpers.delete_token_from_white_list(token)

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
            helpers.delete_token_from_white_list(token)

    def test_user_modify_password_with_user_not_exist(self):
        '''
            Test user modify password when user not exist
        '''
        for i in range(self.user_num):
            user_name = "New!" + self.user_name_list[i]
            old_password = self.user_password[i]
            new_password = "New!" + self.user_password[i]

            token = helpers.create_token(user_name=user_name, user_id=i+1)
            helpers.add_token_to_white_list(token)
            res = self.user_modify_password_with_correct_response_method(user_name=user_name, old_password=old_password, new_password=new_password, token=token)
            self.assertEqual(res.status_code, 400)
            self.assertEqual(res.json()["code"], 4)
            helpers.delete_token_from_white_list(token)

    def test_user_modify_password_with_wrong_password(self):
        '''
            Test user modify password with wrong old password
        '''
        for i in range(self.user_num):
            user_name = self.user_name_list[i]
            old_password = self.user_password[i - 1]
            new_password = self.user_password[i] + "new"

            token = self.user_token[i]
            helpers.add_token_to_white_list(token)
            res = self.user_modify_password_with_correct_response_method(user_name=user_name, old_password=old_password, new_password=new_password, token=token)
            self.assertEqual(res.status_code, 400)
            self.assertEqual(res.json()["code"], 4)
            helpers.delete_token_from_white_list(token)

    def test_user_avatar(self):
        '''
            Test user avatar function
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.user_avatar_with_correct_response_method(url="files/tests/avatar.jpeg", token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        self.assertEqual(res.json()["data"]["id"], 1)
        helpers.delete_token_from_white_list(token)

    def test_user_avatar_with_wrong_response_method(self):
        '''
            Test user avatar with wrong response method
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.user_avatar_with_wrong_response_method(url="files/tests/avatar.jpeg", token=token)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)
        helpers.delete_token_from_white_list(token)

    def test_user_avatar_with_wrong_token(self):
        '''
            Test user avatar with wrong token
        '''
        token = helpers.create_token(user_name="Not exist", user_id=100)
        helpers.add_token_to_white_list(token)

        res = self.user_avatar_with_wrong_response_method(url="files/tests/avatar.jpeg", token=token)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], 1001)
        helpers.delete_token_from_white_list(token)

        token = helpers.create_token(user_name="Not exist", user_id=1)
        helpers.add_token_to_white_list(token)

        res = self.user_avatar_with_wrong_response_method(url="files/tests/avatar.jpeg", token=token)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], 1001)
        helpers.delete_token_from_white_list(token)

    def test_user_avatar_with_invalid_file_format(self):
        '''
            Test user avatar with wrong token
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.user_avatar_with_file_not_exist(url="files/tests/avatar.jpeg", token=token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 18)
        res = self.user_avatar_with_file_not_exist(url="files/tests/Milk.gif", token=token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 18)
        helpers.delete_token_from_white_list(token)

    def test_user_avatar_get(self):
        '''
            Test user avatar function
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.user_avatar_with_correct_response_method(url="files/tests/avatar.jpeg", token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        self.assertEqual(res.json()["data"]["id"], 1)
        res = self.user_avatar_get_with_correct_response_method(token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        self.assertEqual(res.json()["data"]["id"], 1)
        helpers.delete_token_from_white_list(token)

    def test_user_logout(self):
        '''
            Test user logout function
        '''
        for i in range(self.user_num):
            user_name = self.user_name_list[i]
            res = self.user_logout_with_correct_response_method(helpers.create_token(user_name="", user_id="100"))
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
            helpers.delete_token_from_white_list(token)

    def test_user_logout_with_wrong_response_method(self):
        '''
            Test user logout with wrong response method
        '''
        for i in range(self.user_num):
            token = self.user_token[i]
            res = self.user_logout_with_wrong_response_method(token)
            self.assertEqual(res.status_code, 404)
            self.assertEqual(res.json()["code"], 1000)
            helpers.delete_token_from_white_list(token)

    def test_user_checklogin(self):
        '''
            Test user check login function
        '''
        for i in range(self.user_num):
            token = self.user_token[i]
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
            token = self.user_token[i]
            res = self.user_checklogin_with_wrong_response_method(token)
            self.assertEqual(res.status_code, 404)
            self.assertEqual(res.json()["code"], 1000)
            helpers.delete_token_from_white_list(token)

    def test_user_profile(self):
        '''
            Test user profile function
        '''
        for i in range(self.user_num):
            res = self.user_profile_with_correct_response_method(str(self.user_id[i]))
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["code"], 0)

    def test_user_profile_with_wrong_response_method(self):
        '''
            Test user profile with wrong response method
        '''
        for i in range(self.user_num):
            res = self.user_profile_with_wrong_response_method(str(self.user_id[i]))
            self.assertEqual(res.status_code, 404)
            self.assertEqual(res.json()["code"], 1000)

    def test_user_profile_with_user_not_exists(self):
        '''
            Test user profile with user not exists
        '''
        res = self.user_profile_with_correct_response_method(str(114514))
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 12)

    def test_user_profile_with_invalid_user_id(self):
        '''
            Test user profile with user not exists
        '''
        res = self.user_profile_with_correct_response_method("A string!")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 1005)

    def test_user_follow(self):
        '''
            Test user follow function
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.user_follow_with_correct_response_method(user_id=2, token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        res = self.user_follow_with_correct_response_method(user_id=2, token=token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 14)
        res = self.user_unfollow_with_correct_response_method(user_id=2, token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        res = self.user_unfollow_with_correct_response_method(user_id=2, token=token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 14)
        helpers.delete_token_from_white_list(token)

    def test_user_follow_with_wrong_response_method(self):
        '''
            Test user follow with wrong response method
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.user_follow_with_wrong_response_method(user_id=2, token=token)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)
        res = self.user_unfollow_with_wrong_response_method(user_id=2, token=token)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)
        helpers.delete_token_from_white_list(token)

    def test_user_follow_with_invalid_token(self):
        '''
            Test user follow with invalid token
        '''
        token = helpers.create_token(user_name="NotExist!", user_id=114514)
        helpers.add_token_to_white_list(token)

        res = self.user_follow_with_correct_response_method(user_id=self.user_id[0], token=token)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], 1001)
        helpers.delete_token_from_white_list(token)

    def test_user_follow_with_wrong_type(self):
        '''
            Test user follow with wrong type
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.user_follow_with_correct_response_method(user_id="string", token=token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 1005)
        res = self.user_unfollow_with_correct_response_method(user_id="string", token=token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 1005)
        helpers.delete_token_from_white_list(token)

    def test_user_follow_with_user_conflicts(self):
        '''
            Test user follow with user conflicts
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.user_follow_with_correct_response_method(user_id=321, token=token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 12)
        res = self.user_follow_with_correct_response_method(user_id=1, token=token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 13)
        res = self.user_unfollow_with_correct_response_method(user_id=321, token=token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 12)
        res = self.user_unfollow_with_correct_response_method(user_id=1, token=token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 13)
        helpers.delete_token_from_white_list(token)

    def test_user_history(self):
        '''
            Test user history function
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.user_history_with_correct_response_method(1, token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        self.assertEqual(res.json()["data"]["page_count"], 0)

        self.user_add_history_with_correct_response_method(1, token)
        res = self.user_history_with_correct_response_method(1, token)
        self.assertEqual(res.json()["data"]["page_count"], 1)
        self.assertEqual(len(res.json()["data"]["page_data"]), 1)

        self.user_add_history_with_correct_response_method(2, token)
        res = self.user_history_with_correct_response_method(1, token)
        self.assertEqual(res.json()["data"]["page_count"], 1)
        self.assertEqual(len(res.json()["data"]["page_data"]), 2)
        helpers.delete_token_from_white_list(token)

    def test_user_history_with_wrong_response_method(self):
        '''
            Test user history with wrong response method
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.user_add_history_with_wrong_response_method(1, token)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)

        res = self.user_history_with_wrong_response_method(1, token)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)
        helpers.delete_token_from_white_list(token)

    def test_image_upload(self):
        '''
            Test image upload function
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_upload_with_correct_response_method(url="files/tests/Strawberry.gif", title="Strawberry", category="food", tags=["food", "strawberry"], token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        self.assertEqual(res.json()["data"]["uploader"], 1)
        helpers.delete_token_from_white_list(token)

    def test_image_upload_with_user_not_exist(self):
        '''
            Test image upload when user not exist
        '''
        token = helpers.create_token(user_name="not_exist", user_id=100)
        helpers.add_token_to_white_list(token)
        res = self.image_upload_with_correct_response_method(url="files/tests/Strawberry.gif", title="Strawberry", category="food", tags=["food", "strawberry"], token=token)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], 1001)
        helpers.delete_token_from_white_list(token)

    def test_image_upload_with_wrong_response_method(self):
        '''
            Test image upload with wrong response method
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_upload_with_wrong_response_method(url="files/tests/Strawberry.gif", title="Strawberry", category="food", tags=["food", "strawberry"], token=token)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)
        helpers.delete_token_from_white_list(token)

    def test_image_upload_with_wrong_type(self):
        '''
            Test image upload with wrong type
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_upload_with_wrong_type(url="files/tests/Strawberry.gif", title="Strawberry", category="food", tags=["food", "yummy"], token=token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 1005)
        helpers.delete_token_from_white_list(token)

    def test_image_upload_with_invalid_token(self):
        '''
            Test image upload function
        '''
        token = helpers.create_token(user_name="NotExist!", user_id=114514)
        helpers.add_token_to_white_list(token)

        res = self.image_upload_with_correct_response_method(url="files/tests/Strawberry.gif", title="Strawberry", category="food", tags=["food", "strawberry"], token=token)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], 1001)
        helpers.delete_token_from_white_list(token)

    def test_image_update(self):
        '''
            Test image update function
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_update_with_correct_response_method(gif_id="1", category="food", tags=["food", "strawberry"], token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        self.assertEqual(res.json()["data"]["id"], 1)
        helpers.delete_token_from_white_list(token)

    def test_image_update_with_user_not_exist(self):
        '''
            Test image update when user not exist
        '''
        token = helpers.create_token(user_name="not_exist", user_id=100)
        helpers.add_token_to_white_list(token)
        res = self.image_update_with_correct_response_method(gif_id="1", category="food", tags=["food", "strawberry"], token=token)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], 1001)
        helpers.delete_token_from_white_list(token)

    def test_image_update_with_wrong_response_method(self):
        '''
            Test image update with wrong response method
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_update_with_wrong_response_method(gif_id="1", category="food", tags=["food", "strawberry"], token=token)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)
        helpers.delete_token_from_white_list(token)

    def test_image_update_with_wrong_type(self):
        '''
            Test image update with wrong type
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_update_with_correct_response_method(gif_id="1", category="food", tags="food", token=token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 1005)
        helpers.delete_token_from_white_list(token)

    def test_image_update_with_invalid_token(self):
        '''
            Test image update with invalid token
        '''
        token = helpers.create_token(user_name="NotExist!", user_id=114514)

        res = self.image_update_with_correct_response_method(gif_id="1", category="food", tags=["food", "strawberry"], token=token)
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
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_upload_with_correct_response_method(url="files/tests/Noodles.gif", title="Noodles", category="food", tags=["food", "noodles"], token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        image_id = str(res.json()["data"]["id"])

        res = self.image_delete_with_correct_response_method(image_id=image_id, token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)

        res = self.image_delete_with_correct_response_method(image_id=image_id, token=token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 9)
        helpers.delete_token_from_white_list(token)

    def test_image_delete_with_user_not_eixst(self):
        '''
            Test image delete with user not eixst
        '''
        token = self.user_token[0]
        wrong_token = helpers.create_token(user_name="NotThis", user_id=321)
        helpers.add_token_to_white_list(token)
        helpers.add_token_to_white_list(wrong_token)

        res = self.image_upload_with_correct_response_method(url="files/tests/Noodles.gif", title="Noodles", category="food", tags=["food", "noodles"], token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        image_id = str(res.json()["data"]["id"])

        res = self.image_delete_with_correct_response_method(image_id=image_id, token=wrong_token)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], 1001)

        res = self.image_delete_with_correct_response_method(image_id=image_id, token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        helpers.delete_token_from_white_list(token)
        helpers.delete_token_from_white_list(wrong_token)

    def test_image_delete_with_wrong_method(self):
        '''
            Test image delete with wrong method
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_upload_with_correct_response_method(url="files/tests/Noodles.gif", title="Noodles", category="food", tags=["food", "noodles"], token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        image_id = str(res.json()["data"]["id"])

        res = self.image_delete_with_wrong_response_method(image_id=image_id, token=token)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)

        res = self.image_delete_with_correct_response_method(image_id=image_id, token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        helpers.delete_token_from_white_list(token)

    def test_image_upload_uniqueness(self):
        '''
            Test image upload uniqueness
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_upload_with_correct_response_method(url="files/tests/Noodles.gif", title="Noodles", category="food", tags=["food", "noodles"], token=token)
        image_id = str(res.json()["data"]["id"])
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        self.assertEqual(res.json()["data"]["uploader"], 1)

        res = self.image_upload_with_correct_response_method(url="files/tests/Noodles.gif", title="Noodles", category="food", tags=["food", "noodles"], token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        self.assertEqual(res.json()["data"], {'id': 4})

        res = self.image_delete_with_correct_response_method(image_id=image_id, token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        helpers.delete_token_from_white_list(token)

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
            self.assertEqual(res['Content-Disposition'], f'attachment; filename="{gif.name}"')
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

    def test_image_downloadzip(self):
        '''
            Test image downloadzip
        '''
        image_ids = []
        for i in self.image_id:
            image_ids.append(i)
        res = self.image_downloadzip_with_correct_response_method(image_ids=image_ids)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'application/zip')

    def test_image_downloadzip_with_image_not_eixst(self):
        '''
            Test image downloadzip with image not eixst
        '''
        image_ids = []
        for i in self.image_id:
            image_ids.append(i)
        image_ids.append(114514)
        res = self.image_downloadzip_with_correct_response_method(image_ids=image_ids)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 9)
        image_ids.remove(114514)

    def test_image_downloadzip_with_wrong_method(self):
        '''
            Test image downloadzip with wrong method
        '''
        image_ids = []
        for i in self.image_id:
            image_ids.append(i)
        res = self.image_downloadzip_with_wrong_response_method(image_ids=image_ids)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)

    def test_image_like(self):
        '''
            Test image like
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        for i in self.image_id:
            res = self.image_like_with_correct_response_method(image_id=i, token=token)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["code"], 0)
            res = self.image_detail_with_correct_response_method(image_id=str(i))
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["code"], 0)
            self.assertEqual(res.json()["data"]["gif_data"]["like"], 1)
            res = self.image_cancel_like_with_correct_response_method(image_id=i, token=token)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["code"], 0)
            res = self.image_detail_with_correct_response_method(image_id=str(i))
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["code"], 0)
            self.assertEqual(res.json()["data"]["gif_data"]["like"], 0)
        helpers.delete_token_from_white_list(token)

    def test_image_like_with_wrong_response_method(self):
        '''
            Test image like with wrong response method
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_like_with_wrong_response_method(image_id=self.image_id[0], token=token)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)
        res = self.image_cancel_like_with_wrong_response_method(image_id=self.image_id[0], token=token)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)
        helpers.delete_token_from_white_list(token)

    def test_image_like_with_invalid_token(self):
        '''
            Test image like with invalid token
        '''
        token = helpers.create_token(user_name="NotExist!", user_id=114514)

        res = self.image_like_with_correct_response_method(image_id=self.image_id[0], token=token)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], 1001)
        res = self.image_like_with_correct_response_method(image_id=self.image_id[0], token=token)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], 1001)
        helpers.delete_token_from_white_list(token)

    def test_image_like_with_wrong_type(self):
        '''
            Test image like with wrong type
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_like_with_correct_response_method(image_id="string", token=token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 1005)
        res = self.image_cancel_like_with_correct_response_method(image_id="string", token=token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 1005)
        helpers.delete_token_from_white_list(token)

    def test_image_comment(self):
        '''
            Test image comment
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_comment_parent_with_correct_response_method(gif_id=1, token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        res = self.image_comment_son_with_correct_response_method(gif_id=1, parent_id=1, token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        helpers.delete_token_from_white_list(token)

    def test_image_comment_with_wrong_response_method(self):
        '''
            Test image comment with wrong response method
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_comment_with_wrong_response_method(gif_id=1, token=token)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)
        helpers.delete_token_from_white_list(token)

    def test_image_comment_with_wrong_token(self):
        '''
            Test image comment with wrong token
        '''
        token = helpers.create_token(user_name="NotExist!", user_id=114514)
        helpers.add_token_to_white_list(token)

        res = self.image_comment_with_wrong_token(gif_id=1, token=token)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], 1001)
        helpers.delete_token_from_white_list(token)

    def test_image_comment_with_gif_not_exists(self):
        '''
            Test image comment with gif not exists
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_comment_with_gif_not_exists(gif_id=100, token=token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 9)
        helpers.delete_token_from_white_list(token)

    def test_image_comment_with_comment_not_exists(self):
        '''
            Test image comment with comment not exists
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_comment_with_comment_not_exists(gif_id=1, parent_id=100, token=token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 11)
        helpers.delete_token_from_white_list(token)

    def test_image_comment_get(self):
        '''
            Test image comment get
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_comment_parent_with_correct_response_method(gif_id=2, token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        res = self.image_comment_parent_with_correct_response_method(gif_id=2, token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        res = self.image_comment_son_with_correct_response_method(gif_id=2, parent_id=1, token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        res = self.image_comment_get_with_correct_response_method(gif_id=2, token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        self.assertEqual(len(res.json()["data"]), 2)
        helpers.delete_token_from_white_list(token)

    def test_image_comment_get_with_wrong_token(self):
        '''
            Test image comment get with wrong token
        '''
        token = helpers.create_token(user_name="NotExist!", user_id=114)
        helpers.add_token_to_white_list(token)

        res = self.image_comment_get_with_wrong_token(gif_id=1, token=token)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], 1001)
        helpers.delete_token_from_white_list(token)

    def test_image_comment_get_with_wrong_response_method(self):
        '''
            Test image comment get with wrong response method
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_comment_get_with_wrong_response_method(gif_id=1, token=token)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)
        helpers.delete_token_from_white_list(token)

    def test_image_comment_get_with_gif_not_found(self):
        '''
            Test image comment get with gif not found
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_comment_get_with_gif_not_found(gif_id=100, token=token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 9)
        helpers.delete_token_from_white_list(token)

    def test_image_comment_delete(self):
        '''
            Test image comment delete
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_comment_parent_with_correct_response_method(gif_id=3, token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        res = self.image_comment_parent_with_correct_response_method(gif_id=3, token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        res = self.image_comment_get_with_correct_response_method(gif_id=3, token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        self.assertEqual(len(res.json()["data"]), 2)
        comment_id = res.json()["data"][0]["id"]
        res = self.image_comment_delete_with_correct_response_method(comment_id=comment_id, token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        res = self.image_comment_get_with_correct_response_method(gif_id=3, token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        self.assertEqual(len(res.json()["data"]), 1)
        helpers.delete_token_from_white_list(token)

    def test_image_comment_delete_with_wrong_token(self):
        '''
            Test image comment delete with wrong token
        '''
        token = self.user_token[0]
        wrong_token = helpers.create_token(user_name="NotExist!", user_id=114514)
        helpers.add_token_to_white_list(token)

        res = self.image_comment_parent_with_correct_response_method(gif_id=3, token=token)
        res = self.image_comment_get_with_correct_response_method(gif_id=3, token=token)
        comment_id = res.json()["data"][0]["id"]
        res = self.image_comment_delete_with_wrong_token(comment_id=comment_id, token=wrong_token)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], 1001)
        res = self.image_comment_delete_with_correct_response_method(comment_id=comment_id, token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        helpers.delete_token_from_white_list(token)

    def test_image_comment_delete_with_wrong_response_method(self):
        '''
            Test image comment delete with wrong response method
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_comment_delete_with_wrong_response_method(comment_id=1, token=token)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)
        helpers.delete_token_from_white_list(token)

    def test_image_comment_delete_with_comment_not_found(self):
        '''
            Test image comment delete with comment not found
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_comment_delete_with_comment_not_found(comment_id=100, token=token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 11)
        helpers.delete_token_from_white_list(token)

    def test_image_comment_like(self):
        '''
            Test image comment like
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_comment_parent_with_correct_response_method(gif_id=1, token=token)
        comment_id = res.json()["data"]["id"]
        res = self.image_comment_like_with_correct_response_method(comment_id=comment_id, token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        res = self.image_comment_get_with_correct_response_method(gif_id=1, token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        self.assertEqual(res.json()["data"][0]["like"], 1)
        res = self.image_comment_cancel_like_with_correct_response_method(comment_id=comment_id, token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        res = self.image_comment_get_with_correct_response_method(gif_id=1, token=token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["code"], 0)
        self.assertEqual(res.json()["data"][0]["like"], 0)
        helpers.delete_token_from_white_list(token)

    def test_image_comment_like_with_wrong_response_method(self):
        '''
            Test image comment like with wrong response method
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_comment_like_with_wrong_response_method(comment_id=1, token=token)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)
        res = self.image_comment_cancel_like_with_wrong_response_method(comment_id=1, token=token)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 1000)
        helpers.delete_token_from_white_list(token)

    def test_image_comment_like_with_invalid_token(self):
        '''
            Test image comment like with invalid token
        '''
        token = helpers.create_token(user_name="NotExist!", user_id=114514)

        res = self.image_comment_like_with_correct_response_method(comment_id=1, token=token)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], 1001)
        res = self.image_comment_like_with_correct_response_method(comment_id=1, token=token)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["code"], 1001)
        helpers.delete_token_from_white_list(token)

    def test_image_comment_like_with_wrong_type(self):
        '''
            Test image comment like with wrong type
        '''
        token = self.user_token[0]
        helpers.add_token_to_white_list(token)

        res = self.image_comment_like_with_correct_response_method(comment_id="string", token=token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 1005)
        res = self.image_comment_cancel_like_with_correct_response_method(comment_id="string", token=token)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 1005)
        helpers.delete_token_from_white_list(token)

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
