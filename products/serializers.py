from rest_framework import serializers
from django.shortcuts import get_object_or_404

from .models import Article, Operation


class WriteOnceMixin:
    """Adds support for write once fields to serializers.

    To use it, specify a list of fields as `write_once_fields` on the
    serializer's Meta:
    ```
    class Meta:
        model = SomeModel
        fields = '__all__'
        write_once_fields = ('collection', )
    ```

    Now the fields in `write_once_fields` can be set during POST (create),
    but cannot be changed afterwards via PUT or PATCH (update).
    """

    def get_extra_kwargs(self):
        extra_kwargs = super().get_extra_kwargs()

        # We're only interested in PATCH/PUT.
        if 'update' in getattr(self.context.get('view'), 'action', ''):
            return self._set_write_once_fields(extra_kwargs)

        return extra_kwargs

    def _set_write_once_fields(self, extra_kwargs):
        """Set all fields in `Meta.write_once_fields` to read_only."""
        write_once_fields = getattr(self.Meta, 'write_once_fields', None)
        if not write_once_fields:
            return extra_kwargs

        if not isinstance(write_once_fields, (list, tuple)):
            raise TypeError(
                'The `write_once_fields` option must be a list or tuple. '
                'Got {}.'.format(type(write_once_fields).__name__)
            )

        for field_name in write_once_fields:
            kwargs = extra_kwargs.get(field_name, {})
            kwargs['read_only'] = True
            extra_kwargs[field_name] = kwargs

        return extra_kwargs


class ArticleBarcodeField(serializers.RelatedField):
    def to_representation(self, value):
        return value.barcode

    def to_internal_value(self, data):
        article = get_object_or_404(Article, barcode=data)
        return article


class OperationSerializer(serializers.ModelSerializer):
    article = ArticleBarcodeField(queryset=Article.objects.all())

    class Meta:
        model = Operation
        fields = ['article',  'type', 'responsible', 'created_at']


class ArticleSerializer(WriteOnceMixin, serializers.ModelSerializer):
    serial = serializers.IntegerField(required=False, read_only=True)
    imei = serializers.CharField(required=False, read_only=True)
    mac = serializers.StringRelatedField(many=True, read_only=True, source='mac_set', required=False)
    success = serializers.NullBooleanField(required=False)
    operations = OperationSerializer(source='operation_set', many=True, read_only=True)

    class Meta:
        model = Article
        fields = ['product', 'barcode', 'serial', 'imei', 'mac', 'success', 'operations']
        write_once_fields = ('barcode',)
