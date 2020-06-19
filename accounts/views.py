from django.shortcuts import render
from django.contrib.auth.views import LoginView
# from ratelimit.decorators import ratelimit

from BSMA.admin import CustomAuthenticationForm

# Create your views here.


class Login(LoginView):
    authentication_form = CustomAuthenticationForm

    # @ratelimit(group='login', key='ip', rate='5/m', method='POST', block=True)
    def post(self, request, *args, **kwargs):
        return super(Login, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        if not form.cleaned_data['remember_me']:
            self.request.session.set_expiry(0)
        return super(Login, self).form_valid(form)
