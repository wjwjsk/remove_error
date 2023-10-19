from django.shortcuts import render, get_object_or_404, redirect
from .models import Items, Category
from django.http import JsonResponse
from django.db.models import Q


# 메인 페이지
def main(request):
    items = Items.objects.all()
    categories = Category.objects.all()

    context = {
        "items": items,
        "categories": categories,
    }
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
