from django.urls import path
from django.contrib.auth.views import LogoutView

from . import views


app_name = 'accounts'
urlpatterns = [
    path('accounts/login/', views.Login.as_view(), name='login'),
    path('accounts/logout/', LogoutView.as_view(), name='logout'),
]
