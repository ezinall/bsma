import base64
import os
from functools import wraps

from django.shortcuts import render, HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import CreateView, DeleteView
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django import forms
from rest_framework import viewsets, mixins, permissions
from django_filters.rest_framework import DjangoFilterBackend

from .models import Article, Operation
from .serializers import ArticleSerializer, OperationSerializer
from .forms import MediaForm


# Create your views here.


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


def http_basic_auth(func):
    @wraps(func)
    def _decorator(request, *args, **kwargs):
        if 'HTTP_AUTHORIZATION' in request.META:
            auth_method, auth = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
            if auth_method.lower() == 'basic':
                auth = base64.b64decode(auth.strip()).decode()
                username, password = auth.split(':', 1)
                user = authenticate(request, username=username, password=password)
                if user:
                    login(request, user)
        return func(request, *args, **kwargs)

    return _decorator


@csrf_exempt
@http_basic_auth
@login_required
def upload_media(request):
    if request.method == 'POST':
        form = MediaForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('files')
            path = os.path.join(settings.MEDIA_ROOT, request.POST["product"], request.POST["serial"])
            if not os.path.exists(path):
                os.makedirs(path)
            for f in files:
                with open(os.path.join(path, f.name), 'wb+') as destination:
                    for chunk in f.chunks():
                        destination.write(chunk)
            return HttpResponse(status=200)
        else:
            raise forms.ValidationError(f'{form}')


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
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'serial']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class OperationViewSet(mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.ListModelMixin,
                       viewsets.GenericViewSet):
    queryset = Operation.objects.all().order_by('-id')
    serializer_class = OperationSerializer
    permission_classes = (permissions.IsAdminUser,)
