from django.db import models
from django.contrib.auth import get_user_model
from uuid import uuid4
import os
from phonenumber_field.modelfields import PhoneNumberField
from datetime import datetime


class Items(models.Model):
    item_name = models.CharField(max_length=200)
    end_url = models.CharField(max_length=200)
    clr_update_time = models.DateTimeField(default=datetime.now, blank=True)
    find_item_time = models.DateTimeField(default=datetime.now, blank=True)
    board_price = models.IntegerField()
    board_desciption = models.TextField()
    first_price = models.IntegerField()
    delivery_price = models.IntegerField()
    is_end_deal = models.BooleanField(default=False)
    category = models.ForeignKey("Category", on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'Items'

class Category(models.Model):
    name = models.CharField(max_length=30)

    class Meta:
        db_table = 'Category'