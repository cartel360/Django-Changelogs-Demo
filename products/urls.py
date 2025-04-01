from django.urls import path
from .views import (
    ProductChangeLogView,
    ProductListView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
    revert_product,
)

urlpatterns = [
    path('', ProductListView.as_view(), name='product-list'),
    path('new/', ProductCreateView.as_view(), name='product-create'),
    path('<int:pk>/edit/', ProductUpdateView.as_view(), name='product-update'),
    path('<int:pk>/delete/', ProductDeleteView.as_view(), name='product-delete'),
    path('<int:pk>/changelog/', ProductChangeLogView.as_view(), name='product-changelog'),
    path('<int:pk>/revert/<uuid:history_id>/', revert_product, name='product-revert'),
]