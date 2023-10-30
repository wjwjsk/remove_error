from django.urls import include, path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("test/", views.test, name="test"),
    # path('item/<int:item_id>/', views.item_detail, name='item_detail'),
    path("items/<int:category_id>/", views.item_list_by_category, name="item_list_by_category"),
    path("delete_item/<int:item_id>/", views.delete_item, name="delete_item"),
    path("search/", views.search, name="search"),
    path("detail/<int:item_id>/", views.detail, name="detail"),
    path("crawl/", views.crawl_page, name="crawl_page"),
    path("", views.main, name="main"),
    path("load-more-items/", views.load_more_items, name="load_more_items"),
    
        # 로그인 관련 url
    path('login', views.login, name='login'),
    path('login_success/', views.login_success, name='login_success'),
    path('logout/', auth_views.LogoutView.as_view(next_page='main'), name='logout'),

