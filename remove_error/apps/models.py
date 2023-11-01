from django.db import models
from django.contrib.auth import get_user_model
from uuid import uuid4
import os
from phonenumber_field.modelfields import PhoneNumberField
from datetime import datetime
from django.contrib.auth.models import User


class Items(models.Model):
    item_name = models.CharField(max_length=500) # 커뮤 게시글 제목
    end_url = models.CharField(max_length=500) # 커뮤 게시글상 구매페이지 URL
    clr_update_time = models.DateTimeField(default=datetime.now, blank=True) # 마지막 크롤링로 내부 게시글 업데이트된 시간 
    find_item_time = models.CharField(max_length=50) # 핫딜아이템 생성 시간(크롤링으로 신규 아이템등록된 시간)
    board_price = models.CharField(max_length=30) # 커뮤 게시글상 현재 가격
    board_description = models.TextField() # 커뮤 게시글상 설명(이미지 제외)
    board_url = models.CharField(max_length=500, default="") # 커뮤 게시글 URL
    first_price = models.CharField(max_length=30) # 커뮤에 올라온 처음 가격
    delivery_price = models.CharField(max_length=30,null=True) # 게시글 상 배송비(있을 경우에만)
    is_end_deal = models.BooleanField(default=False) # 게시글 삭제 여부 
    category = models.ForeignKey("Category", on_delete=models.CASCADE, null=True, blank=True) 
    hits = models.IntegerField(default=0,null=True)
    content = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = "Items"


class Category(models.Model):
    name = models.CharField(max_length=30) # 가전, 음식, 상품권 등

    class Meta:
        db_table = "Category"

class Comment(models.Model):
    content = models.CharField(max_length=200)
    created_at = models.DateTimeField(default=datetime.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)


    class Meta:
        db_table = "Comment"

