from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

# Create your models here.


class Product(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name=_('name'))
    mark = models.PositiveIntegerField(verbose_name=_('model number'))

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'mark'], name='unique_%(class)s'),
        ]
        verbose_name = _('product')
        verbose_name_plural = _('products')

    def __str__(self):
        return self.name


class Article(models.Model):
    product = models.ForeignKey('Product', on_delete=models.PROTECT, verbose_name=_('product'))
    serial = models.BigIntegerField(validators=[MinValueValidator(0)], verbose_name=_('serial number'))
    imei = models.CharField(blank=True, max_length=255, unique=True, verbose_name=_('IMEI'))
    mac = models.CharField(blank=True, max_length=255, unique=True, verbose_name=_('MAC-address'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))
    # created_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT, verbose_name=_('created by'))

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['product', 'serial'], name='unique_%(class)s'),
        ]
        verbose_name = _('article')
        verbose_name_plural = _('article')

    def __str__(self):
        return str(self.serial)
