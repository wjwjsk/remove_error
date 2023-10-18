from django.urls import include, path
from . import views

urlpatterns = [
    path("", views.main, name="main"),
    # path('item/<int:item_id>/', views.item_detail, name='item_detail'),
]
