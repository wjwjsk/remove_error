import json, re, os, time
from pathlib import Path
from django.shortcuts import render, get_object_or_404, redirect
from .models import Items, Category
from django.http import JsonResponse
from django.db.models import Q
from .crawl import (
    fm_crawling_function,
    pp_crawling_function,
    qz_crawling_function,
    al_crawling_function,
    ce_crawling_function,
    cl_crawling_function,
)
import openai
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage
from django.contrib import auth
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend



BASE_DIR = Path(__file__).resolve().parent.parent
with open("remove_error/config.json") as f:
    json_object = json.load(f)


#     # OpenAI API 키 설정


openai.api_key = json_object["OPENAI_API_KEY"]


#  1. 먹거리
# 2. SW/게임
# 3. PC제품
# 4. 가전제품
# 5. 생활용품
# 6. 의류
# 7. 세일정보
# 8. 화장품
# 9. 모바일/상품권
# 10. 패키지/이용권
# 11. 기타
# 12. 해외핫딜
def categorize_deals(category, item_name):
    if category in [
        "PC제품",
        "가전제품",
        "컴퓨터",
        "디지털",
        "PC/하드웨어",
        "노트북/모바일",
        "가전/TV",
        "전자제품",
        "PC관련",
        "가전",
    ]:
        return Category.objects.get(name="전자제품 및 가전제품")

    elif category in ["의류", "의류/잡화", "패션/의류", "의류잡화"]:
        return Category.objects.get(name="의류 및 패션")

    elif category in ["먹거리", "식품/건강", "생활/식품", "식품"]:
        return Category.objects.get(name="식품 및 식료품")

    elif category in ["생활용품", "가전/가구"]:
        return Category.objects.get(name="홈 및 가든")

    elif category in [
        "패키지/이용권",
        "상품권",
        "세일정보",
        "모바일/상품권",
        "상품권/쿠폰",
        "이벤트",
        "쿠폰",
    ]:
        return Category.objects.get(name="할인 및 상품권")

    elif category in ["화장품"]:
        return Category.objects.get(name="뷰티 및 화장품")

    elif category in ["SW/게임", "등산/캠핑", "게임/SW", "게임"]:
        return Category.objects.get(name="스포츠 및 액티비티")

    elif category in ["기타", "해외핫딜", "인터넷", "모바일"]:
        product_title = item_name

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": f"이 상품의 주요 카테고리는 무엇인가요? 전자제품 및 가전제품, 의류 및 패션 ,식품 및 식료품,홈 및 가든,할인 및 상품권,뷰티 및 화장품,스포츠 및 액티비티,기타 중 하나를 정확하고 최대한 짧게 카테고리 자체만 대답하세요. {product_title}은(는) ",
                },
            ],
        )

        category_ai = response["choices"][0]["message"]["content"].strip()
        print(f"{product_title} 기존 카테고리: {category} = > 예측 카테고리 :{category_ai}")
        # 사전에 정의된 카테고리 목록
        predefined_categories = [
            "전자제품 및 가전제품",
            "의류 및 패션",
            "식품 및 식료품",
            "홈 및 가든",
            "할인 및 상품권",
            "뷰티 및 화장품",
            "스포츠 및 액티비티",
        ]

        for cate in predefined_categories:
            if cate.strip() in category_ai.strip() or category_ai.strip() in cate.strip():
                print(f"{product_title} : 결과 기존 카테고리: {category} -> {cate}")
                return Category.objects.get(name=cate)

        # 미리 정의된 카테고리 목록 또는 category_ai에 없는 경우 "기타" 카테고리 반환
        return Category.objects.get(name="기타")

    return Category.objects.get(name="기타")


def test(request):
    items = Items.objects.all()

    categories = Category.objects.all()

    context = {
        "items": items,
        "categories": categories,
    }

    return render(request, "index.html", context)


# 크롤링 페이지
def crawl_page(request):
    # 크롤링 수행 및 추가된 레코드 수 카운트
    current_time = timezone.now()
    # fm_crawling_function
    start_time = time.time()  # 작업 시작 시간 기록

    result = fm_crawling_function()
    transposed_result = list(zip(*result))
    fm_count = 0
    for column in transposed_result:
        for data in column:
            board_url = data.get("board_url", "")
            end_url = data.get("end_url", "")

            # 추가된 부분: 길이 검사
            if len(board_url) > 500 or len(end_url) > 500:
                continue  # 500자가 넘으면 저장하지 않음

            if not Items.objects.filter(
                Q(item_name=data["item_name"]) | Q(end_url=data["end_url"])
            ).exists():
                if data["is_end_deal"] == False:
                    # 첫 번째 단어 추출
                    first_word = data["item_name"].split()[0]

                    # 링크에서 "//"와 "/" 사이 부분 추출
                    link_part = re.search(r"\/\/(.*?)\/", data["end_url"])
                    if link_part:
                        extracted_url = link_part.group(1)
                    else:
                        extracted_url = data["end_url"]

                    if not Items.objects.filter(
                        Q(item_name__icontains=first_word)
                        & Q(end_url__icontains=extracted_url)
                        & Q(board_price=data["board_price"])
                    ).exists():
                        result_model = Items(
                            item_name=data["item_name"],
                            end_url=data["end_url"],
                            board_url=data["board_url"],
                            clr_update_time=current_time,
                            board_price=data["board_price"][:30],
                            board_description=data["board_description"],
                            delivery_price=data["delivery_price"][:30],
                            is_end_deal=data["is_end_deal"],
                            category=categorize_deals(data["category"], data["item_name"]),
                            find_item_time=current_time,
                        )
                        result_model.save()
                        fm_count += 1

            else:
                result_model = Items.objects.filter(
                    Q(item_name=data["item_name"]) | Q(end_url=data["end_url"])
                ).first()
                if data["board_url"] == result_model.board_url:
                    result_model.board_url = data["board_url"]
                    result_model.clr_update_time = current_time
                    result_model.board_price = data["board_price"][:30]
                    result_model.board_description = data["board_description"]
                    result_model.delivery_price = data["delivery_price"][:30]
                    result_model.is_end_deal = data["is_end_deal"]
                    result_model.save()
    end_time = time.time()  # 작업 종료 시간 기록
    elapsed_time = end_time - start_time  # 작업 소요 시간 계산

    print(f"에펨코리아 작업 완료. 소요 시간: {elapsed_time:.2f} 초")

    start_time = time.time()
    # qz_crawling_function
    result = qz_crawling_function()
    transposed_result = list(zip(*result))
    qz_count = 0
    for column in transposed_result:
        for data in column:
            board_url = data.get("board_url", "")
            end_url = data.get("end_url", "")

            # 추가된 부분: 길이 검사
            if len(board_url) > 500 or len(end_url) > 500:
                continue  # 500자가 넘으면 저장하지 않음

            if not Items.objects.filter(
                Q(item_name=data["item_name"]) | Q(end_url=data["end_url"])
            ).exists():
                if data["is_end_deal"] == False:
                    # 첫 번째 단어 추출
                    first_word = data["item_name"].split()[0]

                    # 링크에서 "//"와 "/" 사이 부분 추출
                    link_part = re.search(r"\/\/(.*?)\/", data["end_url"])
                    if link_part:
                        extracted_url = link_part.group(1)
                    else:
                        extracted_url = data["end_url"]

                    if not Items.objects.filter(
                        Q(item_name__icontains=first_word)
                        & Q(end_url__icontains=extracted_url)
                        & Q(board_price=data["board_price"])
                    ).exists():
                        result_model = Items(
                            item_name=data["item_name"],
                            end_url=data["end_url"],
                            board_url=data["board_url"],
                            clr_update_time=current_time,
                            board_price=data["board_price"][:30],
                            board_description=data["board_description"],
                            delivery_price=data["delivery_price"][:30],
                            is_end_deal=data["is_end_deal"],
                            category=categorize_deals(data["category"], data["item_name"]),
                            find_item_time=current_time,
                        )
                        result_model.save()
                        qz_count += 1
            else:
                result_model = Items.objects.filter(
                    Q(item_name=data["item_name"]) | Q(end_url=data["end_url"])
                ).first()
                if data["board_url"] == result_model.board_url:
                    result_model.board_url = data["board_url"]
                    result_model.clr_update_time = current_time
                    result_model.board_price = data["board_price"][:30]
                    result_model.board_description = data["board_description"]
                    result_model.delivery_price = data["delivery_price"][:30]
                    result_model.is_end_deal = data["is_end_deal"]
                    result_model.save()
    end_time = time.time()  # 작업 종료 시간 기록
    elapsed_time = end_time - start_time  # 작업 소요 시간 계산

    print(f"퀘이사존 작업 완료. 소요 시간: {elapsed_time:.2f} 초")

    start_time = time.time()

    # al_crawling_function
    result = al_crawling_function()
    transposed_result = list(zip(*result))
    al_count = 0
    for column in transposed_result:
        for data in column:
            board_url = data.get("board_url", "")
            end_url = data.get("end_url", "")

            # 추가된 부분: 길이 검사
            if len(board_url) > 500 or len(end_url) > 500:
                continue  # 500자가 넘으면 저장하지 않음

            if not Items.objects.filter(
                Q(item_name=data["item_name"]) | Q(end_url=data["end_url"])
            ).exists():
                if data["is_end_deal"] == False:
                    # 첫 번째 단어 추출
                    first_word = data["item_name"].split()[0]

                    # 링크에서 "//"와 "/" 사이 부분 추출
                    link_part = re.search(r"\/\/(.*?)\/", data["end_url"])
                    if link_part:
                        extracted_url = link_part.group(1)
                    else:
                        extracted_url = data["end_url"]

                    if not Items.objects.filter(
                        Q(item_name__icontains=first_word)
                        & Q(end_url__icontains=extracted_url)
                        & Q(board_price=data["board_price"])
                    ).exists():
                        result_model = Items(
                            item_name=data["item_name"],
                            end_url=data["end_url"],
                            board_url=data["board_url"],
                            clr_update_time=current_time,
                            board_price=data["board_price"][:30],
                            board_description=data["board_description"],
                            delivery_price=data["delivery_price"][:30],
                            is_end_deal=data["is_end_deal"],
                            category=categorize_deals(data["category"], data["item_name"]),
                            find_item_time=current_time,
                        )
                        result_model.save()
                        al_count += 1
            else:
                result_model = Items.objects.filter(
                    Q(item_name=data["item_name"]) | Q(end_url=data["end_url"])
                ).first()
                if data["board_url"] == result_model.board_url:
                    result_model.board_url = data["board_url"]
                    result_model.clr_update_time = current_time
                    result_model.board_price = data["board_price"][:30]
                    result_model.board_description = data["board_description"]
                    result_model.delivery_price = data["delivery_price"][:30]
                    result_model.is_end_deal = data["is_end_deal"]
                    result_model.save()

    end_time = time.time()  # 작업 종료 시간 기록
    elapsed_time = end_time - start_time  # 작업 소요 시간 계산

    print(f"아카라이브 작업 완료. 소요 시간: {elapsed_time:.2f} 초")

    start_time = time.time()
    # # ce_crawling_function
    result = ce_crawling_function()
    transposed_result = list(zip(*result))
    ce_count = 0
    for column in transposed_result:
        for data in column:
            board_url = data.get("board_url", "")
            end_url = data.get("end_url", "")

            # 추가된 부분: 길이 검사
            if len(board_url) > 500 or len(end_url) > 500:
                continue  # 500자가 넘으면 저장하지 않음

            if not Items.objects.filter(
                Q(item_name=data["item_name"]) | Q(end_url=data["end_url"])
            ).exists():
                if data["is_end_deal"] == False:
                    # 첫 번째 단어 추출
                    first_word = data["item_name"].split()[0]

                    # 링크에서 "//"와 "/" 사이 부분 추출
                    link_part = re.search(r"\/\/(.*?)\/", data["end_url"])
                    if link_part:
                        extracted_url = link_part.group(1)
                    else:
                        extracted_url = data["end_url"]

                    if not Items.objects.filter(
                        Q(item_name__icontains=first_word)
                        & Q(end_url__icontains=extracted_url)
                        & Q(board_price=data["board_price"])
                    ).exists():
                        result_model = Items(
                            item_name=data["item_name"],
                            end_url=data["end_url"],
                            board_url=data["board_url"],
                            clr_update_time=current_time,
                            board_price=data["board_price"][:30],
                            board_description=data["board_description"],
                            delivery_price=data["delivery_price"][:30],
                            is_end_deal=data["is_end_deal"],
                            category=categorize_deals(data["category"], data["item_name"]),
                            find_item_time=current_time,
                        )
                        result_model.save()
                        ce_count += 1
            else:
                result_model = Items.objects.filter(
                    Q(item_name=data["item_name"]) | Q(end_url=data["end_url"])
                ).first()
                if data["board_url"] == result_model.board_url:
                    result_model.board_url = data["board_url"]
                    result_model.clr_update_time = current_time
                    result_model.board_price = data["board_price"][:30]
                    result_model.board_description = data["board_description"]
                    result_model.delivery_price = data["delivery_price"][:30]
                    result_model.is_end_deal = data["is_end_deal"]
                    result_model.save()
    end_time = time.time()  # 작업 종료 시간 기록
    elapsed_time = end_time - start_time  # 작업 소요 시간 계산

    print(f"쿨엔조이 작업 완료. 소요 시간: {elapsed_time:.2f} 초")

    start_time = time.time()
    # cl_crawling_function
    result = cl_crawling_function()
    transposed_result = list(zip(*result))
    cl_count = 0
    for column in transposed_result:
        for data in column:
            board_url = data.get("board_url", "")
            end_url = data.get("end_url", "")

            # 추가된 부분: 길이 검사
            if len(board_url) > 500 or len(end_url) > 500:
                continue  # 500자가 넘으면 저장하지 않음

            if not Items.objects.filter(
                Q(item_name=data["item_name"]) | Q(end_url=data["end_url"])
            ).exists():
                if data["is_end_deal"] == False:
                    # 첫 번째 단어 추출
                    first_word = data["item_name"].split()[0]

                    # 링크에서 "//"와 "/" 사이 부분 추출
                    link_part = re.search(r"\/\/(.*?)\/", data["end_url"])
                    if link_part:
                        extracted_url = link_part.group(1)
                    else:
                        extracted_url = data["end_url"]

                    if not Items.objects.filter(
                        Q(item_name__icontains=first_word)
                        & Q(end_url__icontains=extracted_url)
                        & Q(board_price=data["board_price"])
                    ).exists():
                        result_model = Items(
                            item_name=data["item_name"],
                            end_url=data["end_url"],
                            board_url=data["board_url"],
                            clr_update_time=current_time,
                            board_price=data["board_price"][:30],
                            board_description=data["board_description"],
                            delivery_price=data["delivery_price"][:30],
                            is_end_deal=data["is_end_deal"],
                            category=categorize_deals(data["category"], data["item_name"]),
                            find_item_time=current_time,
                        )
                        result_model.save()
                        cl_count += 1
            else:
                result_model = Items.objects.filter(
                    Q(item_name=data["item_name"]) | Q(end_url=data["end_url"])
                ).first()
                if data["board_url"] == result_model.board_url:
                    result_model.board_url = data["board_url"]
                    result_model.clr_update_time = current_time
                    result_model.board_price = data["board_price"][:30]
                    result_model.board_description = data["board_description"]
                    result_model.delivery_price = data["delivery_price"][:30]
                    result_model.is_end_deal = data["is_end_deal"]
                    result_model.save()
    end_time = time.time()  # 작업 종료 시간 기록
    elapsed_time = end_time - start_time  # 작업 소요 시간 계산

    print(f"클리앙 작업 완료. 소요 시간: {elapsed_time:.2f} 초")
    # pp_crawling_function
    pp_count = 0
    # result = pp_crawling_function()
    # transposed_result = list(zip(*result))

    # for column in transposed_result:
    #     for data in column:

    #         board_url = data.get("board_url", "")
    #         end_url = data.get("end_url", "")

    #         # 추가된 부분: 길이 검사
    #         if len(board_url) > 500 or len(end_url) > 500:
    #             continue  # 500자가 넘으면 저장하지 않음

    #         if not Items.objects.filter(
    #             Q(item_name=data["item_name"]) | Q(end_url=data["end_url"])
    #         ).exists():
    #             if data["is_end_deal"] == False:
    #                 # 첫 번째 단어 추출
    #                 first_word = data["item_name"].split()[0]

    #                 # 링크에서 "//"와 "/" 사이 부분 추출
    #                 link_part = re.search(r"\/\/(.*?)\/", data["end_url"])
    #                 if link_part:
    #                     extracted_url = link_part.group(1)
    #                 else:
    #                     extracted_url = data["end_url"]

    #                 if not Items.objects.filter(
    #                     Q(item_name__icontains=first_word)
    #                     & Q(end_url__icontains=extracted_url)
    #                     & Q(board_price=data["board_price"])
    #                 ).exists():
    #                     result_model = Items(
    #                         item_name=data["item_name"],
    #                         end_url=data["end_url"],
    #                         board_url=data["board_url"],
    #                         clr_update_time=current_time,
    #                         board_price="제목 참조",
    #                         board_description=data["board_description"],
    #                         delivery_price="제목 참조",
    #                         is_end_deal=data["is_end_deal"],
    #                         category=categorize_deals(data["category"],data["item_name"]),
    #                         find_item_time=current_time,
    #                     )
    #                     result_model.save()
    #                     pp_count += 1
    #         else:
    #             result_model = Items.objects.filter(
    #                 Q(item_name=data["item_name"]) | Q(end_url=data["end_url"])
    #             ).first()
    #             if data["board_url"] == result_model.board_url:
    #                 result_model.board_url = data["board_url"]
    #                 result_model.clr_update_time = current_time
    #                 result_model.board_description = data["board_description"]
    #                 result_model.is_end_deal = data["is_end_deal"]
    #                 result_model.save()

    # is_end_deal이 True인 항목 삭제
    deleted_items = Items.objects.filter(is_end_deal=True)
    deleted_count = deleted_items.count()
    deleted_items.delete()

    context = {
        "fm_count": fm_count,
        "pp_count": pp_count,
        "qz_count": qz_count,
        "al_count": al_count,
        "ce_count": ce_count,
        "cl_count": cl_count,
        "deleted_count": deleted_count,
    }

    # crawl_page.html 템플릿 렌더링
    return render(request, "crawl_page.html", context)


# 상세 페이지
# def item_detail(request, item_id):
#     item = get_object_or_404(Items, pk=item_id)
#     context = {
#         'item': item,
#     }

#     return render(request, 'item.html', context)


def item_list_by_category(request, category_id):
    # 선택한 카테고리에 해당하는 아이템들을 필터링합니다.
    items = Items.objects.filter(category=category_id).order_by("-id")
    items_per_page = 8  # 페이지당 아이템 수
    max_pages = (items.count() + items_per_page - 1) // items_per_page

    results = items[:items_per_page]
    categories_in_results = Category.objects.all().order_by("id")

    for item in results:
        board_description = item.board_description
        image_urls = board_description.split("<br>")
        item.image_url = image_urls[0] if image_urls else ""  # 첫 번째 이미지 URL을 사용

    context = {
        "items": results,
        "categories": categories_in_results,
        "max_pages": max_pages,  # max_pages를 context에 추가
        "category_id": category_id,
    }
    return render(request, "main.html", context)


def delete_item(request, item_id):
    try:
        item = Items.objects.get(id=item_id)
        item.delete()
        return redirect("main")
    except Items.DoesNotExist:
        return JsonResponse({"message": "아이템이 존재하지 않습니다."}, status=404)


def search(request):
    query = request.GET.get("search")
    categories = Category.objects.all().order_by("id")
    if query:
        results = Items.objects.filter(
            Q(item_name__icontains=query) | Q(category__name__icontains=query)
        ).order_by("-id")

        items_per_page = 8  # 페이지당 아이템 수
        max_pages = (results.count() + items_per_page - 1) // items_per_page

        results = results[:items_per_page]

        for item in results:
            board_description = item.board_description
            image_urls = board_description.split("<br>")
            item.image_url = image_urls[0] if image_urls else ""  # 첫 번째 이미지 URL을 사용

        context = {
            "items": results,
            "categories": categories,
            "max_pages": max_pages,  # max_pages를 context에 추가
            "query": query,
        }
    else:
        all_items = Items.objects.all().order_by("-id")
        items_per_page = 8  # 페이지당 아이템 수
        max_pages = (all_items.count() + items_per_page - 1) // items_per_page

        results = all_items[:items_per_page]
        context = {
            "items": results,
            "categories": categories,
            "max_pages": max_pages,  # max_pages를 context에 추가
        }
    return render(request, "main.html", context)


def detail(request, item_id):
    item = Items.objects.get(id=item_id)
    board_description = item.board_description
    image_urls = board_description.split("<br>")
    item.image_url = image_urls[0] if image_urls else ""  # 첫 번째 이미지 URL을 사용
    return render(request, "detail_ex1.html", {"item": item})


def main(request):
    all_items = Items.objects.all().order_by("-id")
    items_per_page = 8  # 페이지당 아이템 수
    max_pages = (all_items.count() + items_per_page - 1) // items_per_page

    results = all_items[:items_per_page]
    categories_in_results = Category.objects.all().order_by("id")

    for item in results:
        board_description = item.board_description
        image_urls = board_description.split("<br>")
        item.image_url = image_urls[0] if image_urls else ""  # 첫 번째 이미지 URL을 사용

    context = {
        "items": results,
        "categories": categories_in_results,
        "max_pages": max_pages,  # max_pages를 context에 추가
    }

    return render(request, "main.html", context)


def load_more_items(request):
    category_id = request.GET.get("category_id")
    page = int(request.GET.get("page", 1))  # 페이지 번호를 가져옵니다
    query = request.GET.get("query")

    items_per_page = 8  # 페이지당 아이템 수
    start = (page - 1) * items_per_page
    end = start + items_per_page

    if category_id:
        items = Items.objects.filter(category=category_id).order_by("-id")
    elif query:
        items = results = Items.objects.filter(
            Q(item_name__icontains=query) | Q(category__name__icontains=query)
        ).order_by("-id")
    else:
        items = Items.objects.all().order_by("-id")

    results = items[start:end]

    item_data = []
    for item in results:
        board_description = item.board_description
        image_urls = board_description.split("<br>")
        item.image_url = image_urls[0] if image_urls else ""  # 첫 번째 이미지 URL을 사용

        item_data.append(
            {
                "item_name": item.item_name,
                "image_url": item.image_url,
                "board_price": item.board_price,
                "id": item.id,
                # 필요한 다른 필드를 여기에 추가하세요.
            }
        )
    return JsonResponse({"items": item_data})      


# 로그인 관련
from django.shortcuts import render


def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if not (username and password1 and password2):
           return render(request, 'signup.html', {'error': '모든 값을 입력해야 합니다.'})

        if password1 == password2:
            user = User.objects.create_user(
                username=username,
                password=password1,)
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            auth.login(request, user)
            return redirect('/')
        else:
            return render(request, 'signup.html', {'error': '비밀번호가 일치하지 않습니다.'})
    
    return render(request, 'signup.html')


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('main')
        else:
            return render(request, 'login.html', {'error': 'username or password is incorrect.'})
    else:
        return render(request, 'login.html')


def logout(request):
    auth.logout(request)
    return redirect('main')

def home(request):
    return render(request, 'home.html')

def login_form(request):
    return render(request, 'login_form.html')
