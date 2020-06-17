from django.contrib import admin

from .models import Product, Article

# Register your models here.


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    fieldsets = (
        (None, {
            'fields': (('product', 'serial'), 'imei', 'mac', 'created_at'),
        }),
    )
    list_display = ['product', 'serial', 'imei', 'mac']
    readonly_fields = ('created_at',)

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False
