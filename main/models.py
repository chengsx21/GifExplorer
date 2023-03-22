from django.db import models
from django.db.models import AutoField, CharField, URLField, DateTimeField
from django.db.models import TextField, ForeignKey, IntegerField, JSONField
from django.db.models import BooleanField
from utils import utils_time
from utils.utils_request import return_field
from utils.utils_require import MAX_CHAR_LENGTH

# Create your models here.
class User(models.Model):
    """
        model for user
    """
    id = models.BigAutoField(primary_key=True)
    tags = models.JSONField(null=True, blank=True, default=dict)
    user_name = models.CharField(max_length=12, unique=True)
    password = models.CharField(max_length=40)
    signature = models.CharField(max_length=200, blank=True)
    mail = models.CharField(max_length=100, blank=True)
    register_time = DateTimeField(auto_now_add=True)
    # avatar = TextField(blank=True)
    # favorites = JSONField(null=True, blank=True, default=dict)
    # read_history = JSONField(null=True, blank=True, default=dict)
    # search_history = JSONField(null=True, blank=True, default=dict)

    def __str__(self) -> str:
        return str(self.user_name)

    class Meta:
        indexes = [models.Index(fields=["user_name"])]
