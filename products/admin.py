from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Product, Mac, Article, Operation

# Register your models here.


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'mark']


@admin.register(Mac)
class MacAdmin(admin.ModelAdmin):
    list_display = ['product', '__str__', 'article']


class OperationsInline(admin.TabularInline):
    model = Operation
    readonly_fields = ['created_at']


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    fieldsets = (
        (None, {
            'fields': (
                ('product', 'serial'), 'barcode', 'imei', 'mac_set', 'success',
                ('created_by', 'created_at')),
        }),
    )
    list_display = ('product', 'barcode', 'serial', 'imei', 'mac_set', 'success', 'created_at')
    list_filter = ('success', )
    search_fields = ('barcode',)
    readonly_fields = ('imei', 'created_at', 'mac_set')
    inlines = [
        OperationsInline,
    ]

    def imei(self, obj):
        return obj.imei
    imei.short_description = 'IMEI'

    def mac_set(self, obj):
        return list(obj.mac_set.all())
    mac_set.short_description = _('MAC address')
