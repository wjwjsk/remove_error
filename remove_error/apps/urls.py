from django.urls import include, path
from . import views
from django.contrib.auth import views as auth_views

# from .views import find_account

urlpatterns = [
    path("items/<int:category_id>/", views.item_list_by_category, name="item_list_by_category"),
    path("search/", views.search, name="search"),
    path("detail/<int:item_id>/", views.detail, name="detail"),
    path("", views.main, name="main"),
    path("load-more-items", views.load_more_items, name="load_more_items"),
    # 로그인 관련 url
    path("login/", views.login, name="login"),
    path("login_form/", views.login_form, name="login_form"),
    path("signup/", views.signup, name="signup"),
    path("logout/", views.logout, name="logout"),
    # path('social/', include('social_django.urls', namespace='social')),
    path("day/", views.day_ranking, name="ranking"),
    path("week/", views.week_ranking, name="week"),
    path("month/", views.month_ranking, name="month"),
    # path("find_account/", find_account, name="find_account"),
    path("board/", views.board, name="board"),
]
