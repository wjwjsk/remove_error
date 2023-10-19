from django.shortcuts import render, get_object_or_404, redirect
from .models import Items, Category
from django.http import JsonResponse
from django.db.models import Q
from .crawl import fm_crawling_function


# 메인 페이지
def main(request):
    items = Items.objects.all()
    categories = Category.objects.all()

    context = {
        "items": items,
        "categories": categories,
    }

    # 해당 내용 주석 해제 후 새로고침시 db에 크롤링 데이터 추가됩니다(같은내용도 추가되므로 추후 수정필요)
    #     result = fm_crawling_function()
    # # 전치 수행
    #     transposed_result = list(zip(*result))

    #     for column in transposed_result:
    #         for data in column:
    #             # 전달받은 데이터를 ResultModel에 매핑하여 저장합니다.
    #             result_model = Items(
    #                 board_url=data['board_url'],
    #                 item_name=data['item_name'],
    #                 end_url=data['end_url'],
    #                 clr_update_time=data['clr_update_time'],
    #                 board_price=data['board_price'],
    #                 board_description=data['board_description'],
    #                 delivery_price=data['delivery_price'],
    #                 is_end_deal=data['is_end_deal'],
    #             )
    #             result_model.save()
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
    items = Items.objects.filter(category=category_id)
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
        )
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
