from django.contrib import admin
from django.contrib.auth.models import Group as BaseGroup
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin, UserAdmin
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import User, Group


# Register your models here.


admin.site.unregister(BaseGroup)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin):
    pass


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        label=_("Email address"), required=True, widget=forms.EmailInput(attrs={'size': '35'}))

    def clean_email(self):
        return self.cleaned_data['email'].lower()

    class Meta:
        model = User
        fields = ('email',)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    add_form = CustomUserCreationForm
