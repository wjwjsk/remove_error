import json
import os
from django.shortcuts import render, get_object_or_404, redirect
from .models import Items, Category
from django.http import JsonResponse
from django.db.models import Q
from .crawl import fm_crawling_function
import openai
from django.core.exceptions import ImproperlyConfigured


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# secrets.json 파일의 경로를 계산합니다.
secret_file = os.path.join(BASE_DIR, "..", "config.json")

with open(secret_file) as f:
    secrets = json.loads(f.read())


def get_secret(setting, secrets=secrets):
    try:
        return secrets[setting]
    except KeyError:
        error_msg = "Set the {} environment variable".format(setting)
        raise ImproperlyConfigured(error_msg)

    # OpenAI API 키 설정


openai.api_key = get_secret("openai_api_key")
# for i in range(3):
#     product_title = items[i].item_name

#     response = openai.ChatCompletion.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {"role": "system", "content": "You are a helpful assistant."},
#             {
#                 "role": "user",
#                 "content": f"이 상품의 주요 카테고리는 무엇인가요? 최대한 짧게 카테고리만 대답하세요. {product_title}은(는) ",
#             },
#         ],
#     )

#     category = response["choices"][0]["message"]["content"].strip()
#     print(f"{product_title} 카테고리: {category}")


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
def categorize_deals(category):
    if category == "PC제품" or category == "가전제품":
        return Category.objects.get(name="전자제품 및 가전제품")

    elif category == "의류":
        return Category.objects.get(name="의류 및 패션")

    elif category == "먹거리":
        return Category.objects.get(name="식품 및 식료품")

    elif category == "생활용품":
        return Category.objects.get(name="홈 및 가든")

    elif category == "패키지/이용권":
        return Category.objects.get(name="여행 및 숙박")

    elif category == "화장품":
        return Category.objects.get(name="뷰티 및 화장품")

    elif category == "SW/게임":
        return Category.objects.get(name="스포츠 및 액티비티")

    elif category == "세일정보" or category == "모바일/상품권" or category == "기타" or category == "해외핫딜":
        return Category.objects.get(name="기타")

    return Category.objects.get(name="기타")


def main(request):
    items = Items.objects.all()[:10]
    # 너무 많아서 우선 10개만
    categories = Category.objects.all()

    context = {
        "items": items,
        "categories": categories,
    }

    # 해당 내용 주석 해제 후 새로고침시 db에 크롤링 데이터 추가됩니다(같은내용도 추가되므로 추후 수정필요)
    result = fm_crawling_function()
    # 전치 수행
    transposed_result = list(zip(*result))
    count = 0

    for column in transposed_result:
        for data in column:
            # item_name 또는 end_url 중 하나라도 같은 레코드가 있는지 확인
            if not Items.objects.filter(
                Q(item_name=data["item_name"]) | Q(end_url=data["end_url"])
            ).exists():
                # 중복된 레코드가 없을 때만 저장
                result_model = Items(
                    item_name=data["item_name"],
                    end_url=data["end_url"],
                    board_url=data["board_url"],
                    clr_update_time=data["clr_update_time"],
                    board_price=data["board_price"],
                    board_description=data["board_description"],
                    delivery_price=data["delivery_price"],
                    is_end_deal=data["is_end_deal"],
                    category=categorize_deals(data["category"]),
                )
                result_model.save()
                count += 1

    print(f"{count} 레코드 추가")
    return render(request, "index.html", context)


# 상세 페이지
# def item_detail(request, item_id):
#     item = get_object_or_404(Items, pk=item_id)
#     context = {
#         'item': item,
#     }

#     return render(request, 'item.html', context)


def item_list_by_category(request, category_id):
    # 선택한 카테고리에 해당하는 아이템들을 필터링합니다.
    items = Items.objects.filter(category=category_id)[:10]
    categories = Category.objects.all()

    context = {
        "items": items,
        "categories": categories,
    }
    return render(request, "index.html", context)


def delete_item(request, item_id):
    try:
        item = Items.objects.get(id=item_id)
        item.delete()
        return redirect("main")
    except Items.DoesNotExist:
        return JsonResponse({"message": "아이템이 존재하지 않습니다."}, status=404)


def search(request):
    query = request.GET.get("search")
    if query:
        results = Items.objects.filter(
            Q(item_name__icontains=query)
            | Q(board_desciption__icontains=query)
            | Q(category__name__icontains=query)
        )[:10]
        categories_in_results = Category.objects.filter(items__in=results).distinct()

        context = {
            "items": results,
            "categories": categories_in_results,
        }
    else:
        context = {
            "items": Items.objects.all(),
            "categories": Category.objects.all(),
        }
    return render(request, "index.html", context)

def detail(request):
    return render(request, "detail.html", )
