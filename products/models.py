from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.urls import reverse

# Create your models here.


MAC_REGEX = r'^(?:[A-Fa-f0-9]{2}([-:]))(?:[A-Fa-f0-9]{2}\1){4}[A-Fa-f0-9]{2}$'


class Product(models.Model):
    PROP = [
        ('mac', 'MAC addres'),
        ('imei', 'IMEI')
    ]
    name = models.CharField(max_length=255, unique=True, verbose_name=_('name'))
    mark = models.PositiveIntegerField(verbose_name=_('model number'), validators=[MaxValueValidator(9999)])

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
    imei = models.CharField(null=True, blank=True, max_length=255, unique=True, verbose_name=_('IMEI'))
    mac = models.CharField(null=True, blank=True, max_length=255, unique=True, verbose_name=_('MAC address'),
                           validators=[RegexValidator(MAC_REGEX)])

    created_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT, verbose_name=_('created by'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['product', 'serial'], name='unique_%(class)s'),
        ]
        verbose_name = _('article')
        verbose_name_plural = _('article')

    def get_absolute_url(self):
        return reverse('articles:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return str(self.serial)
