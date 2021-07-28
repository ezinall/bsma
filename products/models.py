from functools import reduce

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MaxValueValidator, RegexValidator, ValidationError
from django.dispatch import receiver
import netaddr

# Create your models here.


MAC_REGEX = r'^(?:[A-Fa-f0-9]{2}([-:]))(?:[A-Fa-f0-9]{2}\1){4}[A-Fa-f0-9]{2}$'

# Предварительно рассчитанные результаты умножения на 2 с вычетом 9 для больших цифр
# Номер индекса равен числу, над которым проводится операция
LOOKUP = (0, 2, 4, 6, 8, 1, 3, 5, 7, 9)


def luhn(code):
    code = reduce(str.__add__, filter(str.isdigit, code))
    evens = sum(int(i) for i in code[0::2])
    odds = sum(LOOKUP[int(i)] for i in code[1::2])
    return 10 - (evens + odds) % 10 if (evens + odds) % 10 else (evens + odds) % 10


class Product(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name=_('name'))
    serial_mask = models.CharField(max_length=255, blank=True, null=True,
                                   validators=[RegexValidator(r'{serial(:\d+)?}')], verbose_name=_('serial mask'),
                                   help_text='serial number format, {serial[:0-9]} key must be present')

    # IMEI property
    body_identifier = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('body identifier'),
                                       validators=[RegexValidator(r'[0-9]{2}')])
    mark = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('model number'),
                            validators=[RegexValidator(r'[0-9]{4}')])
    fac = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('FAC'),
                           validators=[RegexValidator(r'[0-9]{2}')])

    # MAC property
    mac_quantity = models.PositiveSmallIntegerField(default=0, verbose_name=_('MAC quantity'))
    oui = models.CharField(blank=True, null=True, max_length=3 * 8, validators=[RegexValidator(r'[0-9a-fA-F]{6}')],
                           verbose_name=_('organizationally unique identifier'))
    mac_start = models.CharField(blank=True, null=True, max_length=3 * 8,
                                 validators=[RegexValidator(r'[0-9a-fA-F]{6}')], verbose_name=_('MAC address start'))
    mac_end = models.CharField(blank=True, null=True, max_length=3 * 8, validators=[RegexValidator(r'[0-9a-fA-F]{6}')],
                               verbose_name=_('MAC address end'))

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
    mac = models.IntegerField(verbose_name=_('MAC address'))
    article = models.ForeignKey('Article', on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name=_('article'))

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['product', 'mac'], name='unique_product_mac_%(class)s'),
        ]
        verbose_name = _('MAC address')
        verbose_name_plural = _('MAC addresses')

    def __str__(self):
        return str(netaddr.EUI(f'{self.product.oui}{int(self.product.mac_start, 16) + self.mac:0>6x}'))


class Article(models.Model):
    product = models.ForeignKey('Product', on_delete=models.PROTECT, verbose_name=_('product'))
    serial = models.PositiveIntegerField(validators=[MaxValueValidator(999999)], verbose_name=_('serial number'))
    barcode = models.CharField(max_length=255, unique=True, verbose_name=_('barcode'))
    # imei = models.CharField(null=True, blank=True, max_length=255, unique=True, verbose_name=_('IMEI'))

    success = models.BooleanField(null=True, verbose_name=_('success'))

    created_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT, verbose_name=_('created by'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))

    extra = models.JSONField(blank=True, default=dict, verbose_name=_('extra'))

    @property
    def imei(self):
        if self.product.body_identifier is None:
            return
        tac = '{}-{}{}'.format(self.product.body_identifier, self.product.mark, self.product.fac)
        identity = '{}-{:0>6}'.format(tac, self.serial)
        return f'{identity}-{luhn(identity)}'

    @property
    def serial_number(self):
        if self.product.serial_mask:
            return self.product.serial_mask.format(serial=self.serial)
        return self.serial

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['product', 'serial'], name='unique_product_ser_%(class)s'),
        ]
        verbose_name = _('article')
        verbose_name_plural = _('articles')

    def clean(self):
        super(Article, self).clean()

        # Validation MAC
        if self.pk is None:
            mac = Mac.objects.filter(product=self.product).order_by('-mac').first()
            if mac:
                last_mac = netaddr.EUI(f'{self.product.oui}{int(self.product.mac_start, 16) + mac.mac:0>6x}')
                if int(last_mac.ei.replace('-', ''), 16) >= int(self.product.mac_end, 16):
                    params = {'product': self.product}
                    raise ValidationError(_('Out of mac addresses for %(product)s'), code='max_value', params=params)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.pk is None and self.serial is None:
            last_serial = Article.objects.all().aggregate(
                serial__max=models.Max('serial', filter=models.Q(product=self.product)))
            self.serial = (last_serial.get('serial__max', 0) or 0) + 1

        super(Article, self).save(force_insert, force_update, using, update_fields)

    # def get_absolute_url(self):
    #     return reverse('articles:detail', kwargs={'pk': self.pk})

    def __str__(self):
        return str(self.serial)


@receiver(models.signals.post_save, sender=Article)
def add_mac(sender, instance, created, **kwargs):
    if created:
        quantity = instance.product.mac_quantity
        if quantity == 0:
            return

        if Mac.objects.filter(product=instance.product, article__isnull=True).count() >= quantity:
            for mac in Mac.objects.filter(product=instance.product, article__isnull=True)[:quantity]:
                mac.article = instance
                mac.save()

        else:
            last_mac_object = Mac.objects.filter(product=instance.product).order_by('-mac').first()
            last_mac = last_mac_object.mac if last_mac_object else 0

            for i in range(1, quantity + 1):
                new_mac = Mac(product=instance.product, mac=last_mac + i, article=instance)
                new_mac.save()


class Operation(models.Model):
    article = models.ForeignKey('Article', on_delete=models.CASCADE, verbose_name=_('article'))
    type = models.PositiveSmallIntegerField(verbose_name=_('type'))
    responsible = models.CharField(max_length=255, verbose_name=_('responsible'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))

    class Meta:
        verbose_name = _('operation')
        verbose_name_plural = _('operations')

    def __str__(self):
        return str(self.type)
