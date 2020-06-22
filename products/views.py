from http import HTTPStatus
from functools import reduce
import django.forms

from django.shortcuts import render, HttpResponseRedirect, HttpResponse, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.http import JsonResponse
from django.forms.models import model_to_dict
import netaddr

from .models import Article


# Create your views here.


def luhn(code):
    # Предварительно рассчитанные результаты умножения на 2 с вычетом 9 для больших цифр
    # Номер индекса равен числу, над которым проводится операция
    LOOKUP = (0, 2, 4, 6, 8, 1, 3, 5, 7, 9)
    code = reduce(str.__add__, filter(str.isdigit, code))
    evens = sum(int(i) for i in code[0::2])
    odds = sum(LOOKUP[int(i)] for i in code[1::2])
    return 10 - (evens + odds) % 10 if (evens + odds) % 10 else (evens + odds) % 10


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'products/index.html'


class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    fields = ['product', 'serial', 'imei', 'mac']

    def form_valid(self, form):
        """If the form is valid, save the associated model and redirect to the supplied URL."""
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    model = Article
    fields = ['mac']
    template_name_suffix = '_update_form'


def get_next(request):
    if request.method != 'GET':
        return HttpResponse(status=HTTPStatus.METHOD_NOT_ALLOWED)

    if 'product' not in request.GET:
        return HttpResponse(status=HTTPStatus.NOT_FOUND)

    product_id = request.GET.get('product')
    article = Article.objects.create(product_id=product_id, created_by=request.user)

    identity = '{}-{:0>4}00-{:0>6}'.format(35, article.product.mark, article.serial)
    article.imei = f'{identity}-{luhn(identity)}'

    mac_last = Article.objects.latest('mac').mac
    if mac_last:
        mac = netaddr.EUI(mac_last)
        mac = netaddr.EUI(format(int(mac) + 1, '0>12x'))
    else:
        mac = netaddr.EUI('CC-C2-61-90-00-00')
    article.mac = str(mac)

    article.save()

    # return JsonResponse(model_to_dict(article))
    return redirect('articles:update', pk=article.pk)
