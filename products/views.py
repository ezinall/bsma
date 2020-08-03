from http import HTTPStatus
from functools import reduce

from django.shortcuts import render, HttpResponseRedirect, HttpResponse, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import CreateView, DeleteView
from rest_framework import viewsets, mixins, permissions
import netaddr

from .models import Article, Operation
from .serializers import ArticleSerializer, OperationSerializer


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
    fields = ['product', 'serial']

    def form_valid(self, form):
        """If the form is valid, save the associated model and redirect to the supplied URL."""
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class ArticleListView(LoginRequiredMixin, ListView):
    model = Article
    ordering = '-pk'


class ArticleDetailView(LoginRequiredMixin, DetailView):
    model = Article


class ArticleDeleteView(LoginRequiredMixin, DeleteView):
    model = Article
    success_url = reverse_lazy('articles:list')


def get_next(request):
    if request.method != 'GET':
        return HttpResponse(status=HTTPStatus.METHOD_NOT_ALLOWED)

    if 'product' not in request.GET:
        return HttpResponse(status=HTTPStatus.NOT_FOUND)

    # product = get_object_or_404(Product, pk=request.GET.get('product'))
    article = Article.objects.create(product_id=request.GET.get('product'), created_by=request.user)

    # identity = '{}-{:0>4}00-{:0>6}'.format(35, article.product.mark, article.serial)
    # article.imei = f'{identity}-{luhn(identity)}'
    #
    # mac_count = Article.objects.filter(product=product, mac__isnull=False).count()
    # if mac_count:
    #     mac = netaddr.EUI(f'{product.oui}{int(product.mac_start, 16) + mac_count:0>6x}')
    # else:
    #     mac = netaddr.EUI(f'{product.oui}{product.mac_start}')
    # article.mac = str(mac)

    article.save()

    return redirect('articles:detail', pk=article.pk)


# API ViewSets
class ArticleViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    queryset = Article.objects.all().order_by('-id')
    serializer_class = ArticleSerializer
    permission_classes = (permissions.IsAdminUser,)
    lookup_field = 'barcode'

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class OperationViewSet(mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.ListModelMixin,
                       viewsets.GenericViewSet):
    queryset = Operation.objects.all().order_by('-id')
    serializer_class = OperationSerializer
    permission_classes = (permissions.IsAdminUser,)
