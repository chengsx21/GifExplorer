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
    favorites = models.JSONField(null=True, blank=True, default=dict)
    read_history = models.JSONField(null=True, blank=True, default=dict)
    search_history = models.JSONField(null=True, blank=True, default=dict)
    objects = models.Manager()

    def __str__(self) -> str:
        return str(self.user_name)

    class Meta:
        '''
            set table name in db
        '''
        db_table = "user_info"

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
