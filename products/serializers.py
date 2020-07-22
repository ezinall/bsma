from rest_framework import serializers

from .models import Article


class ArticleSerializer(serializers.ModelSerializer):
    serial = serializers.IntegerField(required=False, read_only=True)
    imei = serializers.CharField(required=False, read_only=True)
    mac = serializers.StringRelatedField(many=True, read_only=True, source='mac_set', required=False)
    success = serializers.NullBooleanField(required=False)

    class Meta:
        model = Article
        fields = ['product', 'barcode', 'serial', 'imei', 'mac', 'success']
