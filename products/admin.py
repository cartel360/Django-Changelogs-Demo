from django.contrib import admin
from .models import Product, ChangeLog

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'quantity', 'updated_by']
    readonly_fields = ['created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ChangeLog)
class ChangeLogAdmin(admin.ModelAdmin):
    list_display = ['model_name', 'object_id', 'action', 'user', 'timestamp']
    list_filter = ['action', 'model_name']
    search_fields = ['object_id', 'changes']
    readonly_fields = ['model_name', 'object_id', 'action', 'changes', 'user', 'timestamp']