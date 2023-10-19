from django.shortcuts import render
from .crawl import fm_crawling_function
from .models import Items, Category
# Create your views here.
def index(request):

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
    
    return render(request, 'index.html')
