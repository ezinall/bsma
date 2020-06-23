from django.urls import path, include

from . import views


articles_patterns = ([
    path('add/', views.ArticleCreateView.as_view(), name='add'),
    path('list/', views.ArticleListView.as_view(), name='list'),
    path('<int:pk>/', views.ArticleDetailView.as_view(), name='detail'),
    path('delete/<int:pk>/', views.ArticleDeleteView.as_view(), name='delete'),
    path('next/', views.get_next, name='next'),
], 'articles')

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('articles/', include(articles_patterns)),
]
