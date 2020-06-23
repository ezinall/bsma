from functools import reduce

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.urls import reverse
import netaddr

# Create your models here.


MAC_REGEX = r'^(?:[A-Fa-f0-9]{2}([-:]))(?:[A-Fa-f0-9]{2}\1){4}[A-Fa-f0-9]{2}$'


def luhn(code):
    # Предварительно рассчитанные результаты умножения на 2 с вычетом 9 для больших цифр
    # Номер индекса равен числу, над которым проводится операция
    LOOKUP = (0, 2, 4, 6, 8, 1, 3, 5, 7, 9)
    code = reduce(str.__add__, filter(str.isdigit, code))
    evens = sum(int(i) for i in code[0::2])
    odds = sum(LOOKUP[int(i)] for i in code[1::2])
    return 10 - (evens + odds) % 10 if (evens + odds) % 10 else (evens + odds) % 10


class Product(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name=_('name'))
    mark = models.PositiveIntegerField(verbose_name=_('model number'), validators=[MaxValueValidator(9999)])
    oui = models.CharField(max_length=3 * 8, validators=[RegexValidator(r'[0-9a-fA-F]{6}')],
                           verbose_name=_('organizationally unique identifier'))
    mac_start = models.CharField(max_length=3 * 8, validators=[RegexValidator(r'[0-9a-fA-F]{6}')],
                                 verbose_name=_('MAC address start'))
    mac_end = models.CharField(max_length=3 * 8, validators=[RegexValidator(r'[0-9a-fA-F]{6}')],
                               verbose_name=_('MAC address end'))

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
    # imei = models.CharField(null=True, blank=True, max_length=255, unique=True, verbose_name=_('IMEI'))
    # mac = models.CharField(null=True, blank=True, max_length=255, unique=True, verbose_name=_('MAC address'),
    #                        validators=[RegexValidator(MAC_REGEX)])

    created_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT, verbose_name=_('created by'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))

    @property
    def imei(self):
        identity = '{}-{:0>4}00-{:0>6}'.format(35, self.product.mark, self.serial)
        return f'{identity}-{luhn(identity)}'

    @property
    def mac(self):
        return netaddr.EUI(f'{self.product.oui}{int(self.product.mac_start, 16) + self.serial-1:0>6x}')

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.pk is None and self.serial is None:
            last_serial = Article.objects.all().aggregate(
                serial__max=models.Max('serial', filter=models.Q(product=self.product)))
            self.serial = (last_serial.get('serial__max', 0) or 0) + 1

        super(Article, self).save(force_insert, force_update, using, update_fields)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['product', 'serial'], name='unique_%(class)s'),
        ]
        verbose_name = _('article')
        verbose_name_plural = _('articles')

    def get_absolute_url(self):
        return reverse('articles:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return str(self.serial)
