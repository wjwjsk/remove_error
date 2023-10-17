from django.db import models
from django.contrib.auth import get_user_model
from uuid import uuid4
import os
from phonenumber_field.modelfields import PhoneNumberField
from datetime import datetime


def rename_imagefile_to_uuid(instance, filename):
    upload_to = f""
    ext = filename.split(".")[-1]
    uuid = uuid4().hex
    filename = "{}.{}".format(uuid, ext)

    return os.path.join(upload_to, filename)


# Create your models here.
class Base_profile(models.Model):
    username = models.OneToOneField(get_user_model(), primary_key=True, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=20, default="")
    introduction = models.CharField(max_length=300, default="")
    is_company = models.BooleanField(default=False)
    company_name = models.CharField(max_length=50, null=True)
    selfi_url = models.FileField(upload_to=rename_imagefile_to_uuid, default="")
    gender = models.CharField(max_length=1, default="")
    is_findjob = models.BooleanField(default=False)


class Advanced_profile(models.Model):
    phone_number = PhoneNumberField(blank=True, null=True)
    education = models.CharField(max_length=100, default="")
    career = models.CharField(max_length=100, default="")
    is_experienced = models.BooleanField(default=False)
    amount_month_career = models.IntegerField()
    birth = models.DateField()
    last_words = models.CharField(max_length=50, default="")


class Portfolio(models.Model):
    name = models.ForeignKey(Base_profile, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    tag = models.CharField(max_length=50, default="")
    read_count = models.IntegerField()
    thumb_count = models.IntegerField()
    # 파일부분은 추후 수정 필요
    file_url = models.FileField(upload_to=None)
    image_url = models.FileField(upload_to=None)
    is_use = models.BooleanField()


class Message(models.Model):
    sender = models.CharField(max_length=50, default="")
    receiver = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING)
    content = models.TextField(max_length=3000)
    date = models.DateTimeField(auto_now_add=True)


class Alert(models.Model):
    username = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    content = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
