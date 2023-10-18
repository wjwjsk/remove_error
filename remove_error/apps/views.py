from django.shortcuts import render, get_object_or_404
from .models import Items, Category


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
