from django.urls import path, include

from . import views


articles_patterns = ([
    path('add/', views.ArticleCreateView.as_view(), name='add'),
    path('<int:pk>/', views.ArticleCreateView.as_view(), name='detail'),
    path('next/', views.get_next, name='next'),
], 'articles')

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('articles/', include(articles_patterns)),
]
