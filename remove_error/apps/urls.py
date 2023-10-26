from django.urls import include, path
from . import views

urlpatterns = [
    path("test/", views.test, name="test"),
    # path('item/<int:item_id>/', views.item_detail, name='item_detail'),
    path("items/<int:category_id>/", views.item_list_by_category, name="item_list_by_category"),
    path("delete_item/<int:item_id>/", views.delete_item, name="delete_item"),
    path("search/", views.search, name="search"),
    path("detail/<int:item_id>/", views.detail, name="detail"),
    path("crawl/", views.crawl_page, name="crawl_page"),
    path("main_ex1/", views.main_ex1, name="main_ex1"),
    path("main_ex2/", views.main_ex2, name="main_ex2"),
    path("load-more-items/", views.load_more_items, name="load_more_items"),
    path('accounts/', include('accounts.urls')),
]
