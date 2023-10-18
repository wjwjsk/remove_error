from django.db import models
from django.contrib.auth import get_user_model
from uuid import uuid4
import os
from phonenumber_field.modelfields import PhoneNumberField
from datetime import datetime


class Items(models.Model):
    item_name = models.CharField(max_length=200) # 커뮤 게시글 제목
    end_url = models.CharField(max_length=200) # 커뮤 게시글상 구매페이지 URL
    clr_update_time = models.DateTimeField(default=datetime.now, blank=True) # 마지막 크롤링로 내부 게시글 업데이트된 시간
    find_item_time = models.DateTimeField(default=datetime.now, blank=True) # 핫딜아이템 생성 시간(크롤링으로 신규 아이템등록된 시간)
    board_price = models.IntegerField() # 커뮤 게시글상 현재 가격
    board_desciption = models.TextField() # 커뮤 게시글상 설명(이미지 제외)
    board_url = models.CharField(max_length=200, default="") # 커뮤 게시글 URL
    first_price = models.IntegerField() # 커뮤에 올라온 처음 가격
    delivery_price = models.IntegerField(null=True) # 게시글 상 배송비(있을 경우에만)
    is_end_deal = models.BooleanField(default=False) # 게시글 삭제 여부 
    category = models.ForeignKey("Category", on_delete=models.CASCADE) 

    class Meta:
        db_table = "Items"


class Category(models.Model):
    name = models.CharField(max_length=30) # 가전, 음식, 상품권 등

    class Meta:
        db_table = "Category"
