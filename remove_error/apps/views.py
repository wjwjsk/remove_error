from django.utils import timezone
from datetime import datetime, timedelta
import json, re, os, time
from pathlib import Path
from django.shortcuts import render, get_object_or_404, redirect
from .models import Items, Category, Comment
from django.http import JsonResponse
from django.db.models import Q, F

import openai
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage
from django.contrib import auth
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend

# from django.contrib.auth.tokens import default_token_generator
# from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
# from django.template.loader import render_to_string
# from django.utils.encoding import force_bytes
# from django.core.mail import EmailMessage


from django.contrib.auth.decorators import login_required


def item_list_by_category(request, category_id):
    # 선택한 카테고리에 해당하는 아이템들을 필터링합니다.
    items = Items.objects.filter(category=category_id, is_end_deal=False).order_by(
        "-find_item_time"
    )
    items_per_page = 8  # 페이지당 아이템 수
    max_pages = (items.count() + items_per_page - 1) // items_per_page

    results = items[:items_per_page]
    categories_in_results = Category.objects.all().order_by("id")

    for item in results:
        board_description = item.board_description
        image_urls = board_description.split("<br>")
        item.elapsed_time = calculate_time_difference(item.find_item_time)
        item.image_url = image_urls[0] if image_urls else ""  # 첫 번째 이미지 URL을 사용

    context = {
        "items": results,
        "categories": categories_in_results,
        "max_pages": max_pages,  # max_pages를 context에 추가
        "category_id": category_id,
    }
    return render(request, "main.html", context)


def search(request):
    query = request.GET.get("search")
    categories = Category.objects.all().order_by("id")
    if query:
        results = Items.objects.filter(
            (Q(item_name__icontains=query) | Q(category__name__icontains=query))
            & Q(is_end_deal=False)
        ).order_by("-find_item_time")

        items_per_page = 8  # 페이지당 아이템 수
        max_pages = (results.count() + items_per_page - 1) // items_per_page

        results = results[:items_per_page]

        for item in results:
            board_description = item.board_description
            image_urls = board_description.split("<br>")
            item.elapsed_time = calculate_time_difference(item.find_item_time)
            item.image_url = image_urls[0] if image_urls else ""  # 첫 번째 이미지 URL을 사용

        context = {
            "items": results,
            "categories": categories,
            "max_pages": max_pages,  # max_pages를 context에 추가
            "query": query,
        }
    else:
        all_items = Items.objects.filter(is_end_deal=False).order_by("-find_item_time")
        items_per_page = 8  # 페이지당 아이템 수
        max_pages = (all_items.count() + items_per_page - 1) // items_per_page

        results = all_items[:items_per_page]
        for item in results:
            board_description = item.board_description
            image_urls = board_description.split("<br>")
            item.elapsed_time = calculate_time_difference(item.find_item_time)
            item.image_url = image_urls[0] if image_urls else ""  # 첫 번째 이미지 URL을 사용

        context = {
            "items": results,
            "categories": categories,
            "max_pages": max_pages,  # max_pages를 context에 추가
        }
    return render(request, "main.html", context)


def calculate_time_difference(find_item_time):
    try:
        current_time = datetime.now()
        find_item_time = datetime.strptime(find_item_time, "%Y-%m-%d %H:%M")
        time_difference = current_time - find_item_time

        if time_difference < timedelta(minutes=1):
            return "방금 전"
        elif time_difference < timedelta(hours=1):
            return f"{int(time_difference.seconds / 60)}분 전"
        elif time_difference < timedelta(days=1):
            return f"{int(time_difference.seconds / 3600)}시간 전"
        else:
            days = time_difference.days
            return f"{days}일 전"

    except ValueError:
        return "유효하지 않은 형식입니다."


def detail(request, item_id):
    item = Items.objects.get(id=item_id)
    # 조회수 1 증가
    Items.objects.filter(id=item_id).update(hits=F("hits") + 1)

    board_description = item.board_description
    image_urls = board_description.split("<br>")
    item.image_urls = image_urls
    item.elapsed_time = calculate_time_difference(item.find_item_time)
    return render(request, "detail_ex1.html", {"item": item})


def main(request):
    all_items = Items.objects.filter(is_end_deal=False).order_by("-find_item_time")
    items_per_page = 8  # 페이지당 아이템 수
    max_pages = (all_items.count() + items_per_page - 1) // items_per_page

    results = all_items[:items_per_page]
    categories_in_results = Category.objects.all().order_by("id")

    for item in results:
        board_description = item.board_description
        image_urls = board_description.split("<br>")
        item.image_url = image_urls[0] if image_urls else ""  # 첫 번째 이미지 URL을 사용
        item.elapsed_time = calculate_time_difference(item.find_item_time)

    context = {
        "items": results,
        "categories": categories_in_results,
        "max_pages": max_pages,  # max_pages를 context에 추가
    }
    
    # 데이터베이스에서 현재 데이터의 수를 가져옵니다.
    current_count = Items.objects.count()

    # 데이터의 수가 2000개를 초과하는지 확인합니다.
    if current_count > 2000:
        # 오래된 데이터의 ID 값을 가져옵니다.
        old_item_ids = Items.objects.order_by("clr_update_time")[:current_count - 2000].values_list("id", flat=True)

        # 해당 ID 값을 가진 레코드를 삭제합니다.
        Items.objects.filter(id__in=old_item_ids).delete()

    return render(request, "main.html", context)


def load_more_items(request):
    category_id = request.GET.get("category_id")
    page = int(request.GET.get("page", 1))  # 페이지 번호를 가져옵니다
    query = request.GET.get("query")

    items_per_page = 8  # 페이지당 아이템 수
    start = (page - 1) * items_per_page
    end = start + items_per_page

    if category_id:
        items = Items.objects.filter(category=category_id, is_end_deal=False).order_by(
            "-find_item_time"
        )
    elif query:
        items = Items.objects.filter(
            (Q(item_name__icontains=query) | Q(category__name__icontains=query))
            & Q(is_end_deal=False)
        ).order_by("-find_item_time")
    else:
        items = Items.objects.filter(is_end_deal=False).order_by("-find_item_time")

    results = items[start:end]

    item_data = []

    for item in results:
        board_description = item.board_description
        image_urls = board_description.split("<br>")
        item.elapsed_time = calculate_time_difference(item.find_item_time)
        item.image_url = image_urls[0] if image_urls else ""  # 첫 번째 이미지 URL을 사용

        item_data.append(
            {
                "item_name": item.item_name,
                "image_url": item.image_url,
                "board_price": item.board_price,
                "id": item.id,
                "elapsed_time": item.elapsed_time,
                # 필요한 다른 필드를 여기에 추가하세요.
            }
        )
    return JsonResponse({"items": item_data})


# 로그인 관련
def signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        email = request.POST.get("email")

        if not (username and password1 and password2):  # and email):#
            return render(request, "signup.html", {"error": "모든 값을 입력해야 합니다."})

        username_regex = re.compile("^[a-zA-Z0-9]+$")
        if not username_regex.match(username):
            return render(request, "signup.html", {"error": "아이디는 영문자와 숫자만 가능합니다."})

        if User.objects.filter(username=username).exists():
            return render(request, "signup.html", {"error": "이미 존재하는 아이디입니다."})

        if User.objects.filter(email=email).exists():
            return render(request, "signup.html", {"error": "이미 사용중인 이메일입니다."})

        password_regex = re.compile("^(?=.*[!@#$%^&*()_+=-])(?=.*[a-zA-Z0-9]).{8,}$")

        if not password_regex.match(password1):
            return render(request, "signup.html", {"error": "비밀번호는 8자 이상이며, 특수문자를 포함해야 합니다."})

        if password1 == password2:
            user = User.objects.create_user(username=username)  # email=email)
            user.set_password(password1)
            user.save()
            user.backend = "django.contrib.auth.backends.ModelBackend"

            auth.login(request, user)
            return redirect("/")
        else:
            return render(request, "signup.html", {"error": "비밀번호가 일치하지 않습니다."})

    return render(request, "signup.html")


def login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect("main")
        else:
            return render(request, "login.html", {"error": "아이디 또는 비밀번호가 일치하지 않습니다. 다시 확인해 주세요."})
    else:
        return render(request, "login.html")


def logout(request):
    auth.logout(request)
    return redirect("main")


def home(request):
    return render(request, "home.html")


def login_form(request):
    return render(request, "login_form.html")


# def find_account(request):
#     if request.method == "POST":
#         email = request.POST["email"]
#         if User.objects.filter(email=email).exists():
#             user = User.objects.get(email=email)
#             token = default_token_generator.make_token(user)
#             uid = urlsafe_base64_encode(force_bytes(user.pk))
#             mail_subject = "Reset your password"
#             message = render_to_string(
#                 "find_account_email.html",
#                 {
#                     "user": user,
#                     "domain": request.META["HTTP_HOST"],
#                     "uid": uid,
#                     "token": token,
#                 },
#             )
#             to_email = email
#             email = EmailMessage(mail_subject, message, to=[to_email])
#             email.send()
#             return render(request, "find_account_done.html")
#         else:
#             return render(request, "find_account.html", {"error": "해당 이메일이 존재하지 않습니다."})
#     else:
#         return render(request, "find_account.html")


def get_ranking(request, delta_days):
    # 현재 시간을 얻고 delta_days 이전의 날짜를 계산합니다.
    today = datetime.now()

    start_date = today - timedelta(days=delta_days)

    # delta_days 이전부터 오늘까지의 데이터를 필터링합니다.
    results = Items.objects.filter(
        is_end_deal=False, find_item_time__gte=start_date, find_item_time__lte=today
    ).order_by("-hits", "-find_item_time")[:20]

    # 순위 부여
    rank = 1
    for item in results:
        item.rank = rank
        rank += 1
        board_description = item.board_description
        image_urls = board_description.split("<br>")
        item.elapsed_time = calculate_time_difference(item.find_item_time)
        item.image_url = image_urls[0] if image_urls else ""

    context = {
        "items": results,
        "ranking_day": delta_days,
    }

    return render(request, "ranking.html", context)


def day_ranking(request):
    return get_ranking(request, 1)


def week_ranking(request):
    return get_ranking(request, 7)


def month_ranking(request):
    return get_ranking(request, 30)


@login_required
def board(request):
    comment = Comment.objects.all().order_by("created_at")
    if request.method == "POST":
        content = request.POST.get("content")

        if not content:
            return render(request, "board.html", {"error": "댓글을 입력해주세요."})
        if len(content) > 300:
            return render(request, "board.html", {"error": "댓글은 300자까지만 입력 가능합니다."})

        comment = Comment.objects.create(
            content=content, author=request.user, created_at=timezone.now()
        )
        comment.save()
        return redirect("board")

    return render(request, "board.html", {"comment": comment})
