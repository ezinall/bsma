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


class ActivationStatusListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('activation status')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'activation_status'

    def lookups(self, request, model_admin):
        return (
            ('1', _('Yes')),
            ('0', _('No')),
            ('2', _('Unknown'))
        )

    def queryset(self, request, queryset):
        if self.value() == '0':
            return queryset.filter(extra__devices__0__activation_status=False)
        if self.value() == '1':
            return queryset.filter(extra__devices__0__activation_status=True)
        if self.value() == '2':
            return queryset.filter(extra__devices__isnull=True)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    fieldsets = (
        (None, {
            'fields': (
                ('product', 'serial'), 'barcode', 'imei', 'mac_set', 'success',
                ('created_by', 'created_at'),
                'extra',
            ),
        }),
    )
    list_display = ('product', 'barcode', 'serial', 'imei', 'mac_set', 'success', 'activation_status', 'created_at')
    list_filter = ('success', ActivationStatusListFilter)
    search_fields = ('barcode', 'serial')
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

    def activation_status(self, obj):
        if obj.extra is None:
            return

        devices = obj.extra.get('devices')
        if devices:
            return devices[0].get('activation_status')

    activation_status.short_description = _('activation status')
    activation_status.boolean = True
