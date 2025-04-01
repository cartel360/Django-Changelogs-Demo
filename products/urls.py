from django.urls import path
from .views import (
    ProductListView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
)

urlpatterns = [
    path('', ProductListView.as_view(), name='product-list'),
    path('new/', ProductCreateView.as_view(), name='product-create'),
    path('<int:pk>/edit/', ProductUpdateView.as_view(), name='product-update'),
    path('<int:pk>/delete/', ProductDeleteView.as_view(), name='product-delete'),
]