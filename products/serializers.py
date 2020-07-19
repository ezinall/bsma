from rest_framework import serializers

from .models import Article


class ArticleSerializer(serializers.ModelSerializer):
    serial = serializers.IntegerField(required=False, read_only=True)
    imei = serializers.CharField(required=False, read_only=True)
    mac = serializers.StringRelatedField(many=True, read_only=True, source='mac_set', required=False)
    success = serializers.NullBooleanField(required=False)

    class Meta:
        model = Article
        fields = ['id', 'product', 'barcode1', 'barcode2', 'serial', 'imei', 'mac', 'success']

    def update(self, instance, validated_data):
        instance.success = validated_data.get('success', instance.success)
        instance.save()
        return instance
