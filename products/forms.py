from django import forms

from .models import Product


class MediaForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.all(), label='product')
    serial = forms.IntegerField(label='serial', max_value=999999)
    files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
