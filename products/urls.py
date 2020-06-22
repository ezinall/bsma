from django.urls import path, include

from . import views


articles_patterns = ([
    path('add/', views.ArticleCreateView.as_view(), name='add'),
    path('detail/<int:pk>/', views.ArticleUpdateView.as_view(), name='detail'),
    path('update/<int:pk>/', views.ArticleUpdateView.as_view(), name='update'),
    path('next/', views.get_next, name='next'),
], 'articles')

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('articles/', include(articles_patterns)),
]
