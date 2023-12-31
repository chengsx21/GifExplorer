'''
    models.py in django frame work
'''

from django.db import models
from django.db.models import DateTimeField

class UserInfo(models.Model):
    '''
        model for user
    '''
    id = models.BigAutoField(primary_key=True)
    tags = models.JSONField(null=True, blank=True, default=dict)
    user_name = models.CharField(max_length=12, unique=True)
    password = models.CharField(max_length=80)
    salt = models.CharField(max_length=40)
    signature = models.CharField(max_length=200, blank=True)
    mail = models.CharField(max_length=100, blank=True)
    register_time = DateTimeField(auto_now_add=True)
    avatar = models.TextField(blank=True)
    followings = models.JSONField(null=True, blank=True, default=dict)
    followers = models.JSONField(null=True, blank=True, default=dict)
    favorites = models.JSONField(null=True, blank=True, default=dict)
    comment_favorites = models.JSONField(null=True, blank=True, default=list)
    read_history = models.JSONField(null=True, blank=True, default=dict)
    search_history = models.JSONField(null=True, blank=True, default=dict)
    task_history = models.JSONField(null=True, blank=True, default=dict)
    objects = models.Manager()

    def __str__(self) -> str:
        return str(self.user_name)

    class Meta:
        '''
            set table name in db
        '''
        db_table = "user_info"

class UserVerification(models.Model):
    '''
        model for user verification
    '''
    user_name = models.CharField(max_length=12, unique=True)
    token = models.CharField(null=True, blank=True, max_length=60)
    mail = models.CharField(null=True, blank=True, max_length=100)
    is_verified = models.BooleanField(default=False)
    password = models.CharField(null=True, blank=True, max_length=80)
    salt = models.CharField(null=True, blank=True, max_length=40)
    created_at = models.DateTimeField(default=None, null=True, blank=True)
    objects = models.Manager()

    class Meta:
        '''
            set table name in db
        '''
        db_table = "user_verification"

class UserToken(models.Model):
    '''
        model for user token
    '''
    user_id = models.PositiveIntegerField(default=0)
    token = models.CharField(max_length=200)
    objects = models.Manager()

    class Meta:
        '''
            set table name in db
        '''
        db_table = "usertoken"

class GifMetadata(models.Model):
    '''
        model for gif metadata
    '''
    id = models.AutoField(primary_key=True)
    # gif_file = models.ImageField(upload_to='gifs/')
    name = models.CharField(null=True, blank=True, max_length=200)
    title = models.CharField(max_length=200)
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    duration = models.FloatField(default=0.0)
    uploader = models.PositiveIntegerField(default=1)
    category = models.CharField(null=True, blank=True, max_length=20)
    tags = models.JSONField(null=True, blank=True, default=list)
    likes = models.PositiveIntegerField(default=0)
    pub_time = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

    class Meta:
        '''
            set table name in db
        '''
        db_table = "gifmetadata"

class GifFile(models.Model):
    '''
        model for gif file
    '''
    file = models.ImageField(upload_to='gifs/')
    metadata = models.OneToOneField(GifMetadata, on_delete=models.CASCADE)
    objects = models.Manager()

    class Meta:
        '''
            set table name in db
        '''
        db_table = "giffile"

class GifComment(models.Model):
    '''
        model for gif comment
    '''
    id = models.AutoField(primary_key=True)
    metadata = models.ForeignKey(GifMetadata, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    content = models.TextField(max_length=200)
    likes = models.PositiveIntegerField(default=0)
    pub_time = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

class GifFingerprint(models.Model):
    '''
        model for gif fingerprint
    '''
    gif_id = models.PositiveIntegerField(default=0)
    fingerprint = models.CharField(max_length=64, unique=True)
    objects = models.Manager()

    class Meta:
        '''
            set table name in db
        '''
        db_table = "giffingerprint"

class Message(models.Model):
    '''
        model for message
    '''
    sender = models.ForeignKey(UserInfo, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(UserInfo, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField(max_length=200)
    is_read = models.BooleanField(default=False)
    pub_time = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

    class Meta:
        '''
            set table name in db
        '''
        db_table = "message"

class GifShare(models.Model):
    '''
        model for message
    '''
    token = models.TextField(max_length=200)
    gif_ids = models.JSONField(default=list)
    pub_time = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

    class Meta:
        '''
            set table name in db
        '''
        db_table = "gifshare"

class TaskInfo(models.Model):
    '''
        model for task
    '''
    id = models.BigAutoField(primary_key=True)
    task_id = models.CharField(null=True, blank=True, max_length=200)
    task_type = models.CharField(max_length=200)
    task_status = models.CharField(max_length=200)
    task_time = models.DateTimeField(auto_now_add=True)
    task_result = models.JSONField(null=True, blank=True, default=dict)
    objects = models.Manager()

    class Meta:
        '''
            set table name in db
        '''
        db_table = "taskinfo"
