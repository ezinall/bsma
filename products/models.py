from functools import reduce

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.urls import reverse
from django.dispatch import receiver
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
    code_babt = models.CharField(max_length=255, verbose_name=_('code BABT'), validators=[RegexValidator(r'[0-9]{2}')])
    mark = models.CharField(max_length=255, verbose_name=_('model number'), validators=[RegexValidator(r'[0-9]{4}')])
    fac = models.CharField(max_length=255, verbose_name=_('FAC'), validators=[RegexValidator(r'[0-9]{2}')])
    oui = models.CharField(max_length=3 * 8, validators=[RegexValidator(r'[0-9a-fA-F]{6}')],
                           verbose_name=_('organizationally unique identifier'))
    mac_start = models.CharField(max_length=3 * 8, validators=[RegexValidator(r'[0-9a-fA-F]{6}')],
                                 verbose_name=_('MAC address start'))
    mac_end = models.CharField(max_length=3 * 8, validators=[RegexValidator(r'[0-9a-fA-F]{6}')],
                               verbose_name=_('MAC address end'))

    @property
    def tac(self):
        return '{}-{}{}'.format(self.code_babt, self.mark, self.fac)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'mark'], name='unique_%(class)s'),
        ]
        verbose_name = _('product')
        verbose_name_plural = _('products')

    def __str__(self):
        return self.name


class Mac(models.Model):
    product = models.ForeignKey('Product', on_delete=models.PROTECT, verbose_name=_('product'))
    mac = models.IntegerField(unique=True, verbose_name=_('MAC address'))
    article = models.ForeignKey('Article', on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name=_('article'))

    class Meta:
        verbose_name = _('MAC address')
        verbose_name_plural = _('MAC addresses')

    def __str__(self):
        return str(netaddr.EUI(f'{self.product.oui}{int(self.product.mac_start, 16) + self.mac:0>6x}'))


class Article(models.Model):
    product = models.ForeignKey('Product', on_delete=models.PROTECT, verbose_name=_('product'))
    serial = models.PositiveIntegerField(validators=[MaxValueValidator(999999)], verbose_name=_('serial number'))
    barcode = models.CharField(max_length=255, unique=True, verbose_name=_('barcode'))
    # imei = models.CharField(null=True, blank=True, max_length=255, unique=True, verbose_name=_('IMEI'))

    success = models.NullBooleanField(verbose_name=_('success'))

    created_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT, verbose_name=_('created by'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))

    @property
    def imei(self):
        identity = '{}-{:0>6}'.format(self.product.tac, self.serial)
        return f'{identity}-{luhn(identity)}'

    # @property
    # def mac(self):
    #     return netaddr.EUI(f'{self.product.oui}{int(self.product.mac_start, 16) + self.serial-1:0>6x}')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['product', 'serial'], name='unique_product_ser_%(class)s'),
        ]
        verbose_name = _('article')
        verbose_name_plural = _('articles')

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.pk is None and self.serial is None:
            last_serial = Article.objects.all().aggregate(
                serial__max=models.Max('serial', filter=models.Q(product=self.product)))
            self.serial = (last_serial.get('serial__max', 0) or 0) + 1

        super(Article, self).save(force_insert, force_update, using, update_fields)

    def get_absolute_url(self):
        return reverse('articles:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return str(self.serial)


class Operation(models.Model):
    TYPE = [
        (0, '0'),
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
    ]
    article = models.ForeignKey('Article', on_delete=models.CASCADE, verbose_name=_('article'))
    type = models.PositiveSmallIntegerField(choices=TYPE, verbose_name=_('type'))
    responsible = models.CharField(max_length=255, verbose_name=_('responsible'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))

    class Meta:
        verbose_name = _('operation')
        verbose_name_plural = _('operations')

    def __str__(self):
        return self.get_type_display()


@receiver(models.signals.post_save, sender=Article)
def add_mac(sender, instance, created, **kwargs):
    if created:
        if Mac.objects.filter(product=instance.product, article__isnull=True).count() >= 2:
            for mac in Mac.objects.filter(product=instance.product, article__isnull=True)[:2]:
                mac.article = instance
                mac.save()

        else:
            last_mac_object = Mac.objects.order_by('-mac').first()
            if last_mac_object:
                last_mac = last_mac_object.mac + 1
            else:
                last_mac = 1

            new_mac = Mac(product=instance.product, mac=last_mac, article=instance)
            new_mac.save()

            new_mac = Mac(product=instance.product, mac=last_mac + 1, article=instance)
            new_mac.save()
