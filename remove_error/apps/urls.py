from django.urls import include, path
from . import views
from django.contrib.auth import views as auth_views
from .views import find_account

urlpatterns = [
    path("test/", views.test, name="test"),
    # path('item/<int:item_id>/', views.item_detail, name='item_detail'),
    path("items/<int:category_id>/", views.item_list_by_category, name="item_list_by_category"),
    path("delete_item/<int:item_id>/", views.delete_item, name="delete_item"),
    path("search/", views.search, name="search"),
    path("detail/<int:item_id>/", views.detail, name="detail"),
    # path("crawl/", views.crawl_page, name="crawl_page"),
    path("", views.main, name="main"),
    path("load-more-items", views.load_more_items, name="load_more_items"),
    # 로그인 관련 url
    path("login/", views.login, name="login"),
    path("login_form/", views.login_form, name="login_form"),
    path("signup/", views.signup, name="signup"),
    path("logout/", views.logout, name="logout"),
    # path('social/', include('social_django.urls', namespace='social')),
    path("ranking/", views.ranking, name="ranking"),
    path("rank-load-more-items", views.rank_load_more_items, name="rank_load_more_items"),
    path('find_account/', find_account, name='find_account'),
]
