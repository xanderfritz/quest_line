from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from . import views
from . import api_views

urlpatterns = [
    # public
    path('', views.home, name='home'),
    path('article/<int:pk>/', views.article_detail, name='article_detail'),
    path('newsletters/', views.newsletter_list, name='newsletter_list'),
    path('newsletters/<int:pk>/', views.newsletter_detail, name='newsletter_detail'),

    # auth
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # journalist
    path('articles/new/', views.article_create, name='article_create'),
    path('articles/mine/', views.my_articles, name='my_articles'),
    path('newsletters/new/', views.newsletter_create, name='newsletter_create'),

    # editor
    path('editor/queue/', views.editor_queue, name='editor_queue'),
    path('editor/approve/<int:pk>/', views.article_approve, name='article_approve'),
    path('editor/delete/<int:pk>/', views.article_delete, name='article_delete'),

    # reader
    path('subscriptions/', views.subscriptions, name='subscriptions'),

    # rest api
    path('api/token/', obtain_auth_token, name='api_token'),
    path('api/articles/', api_views.api_article_list, name='api_article_list'),
    path('api/articles/subscribed/', api_views.api_articles_subscribed, name='api_articles_subscribed'),
    path('api/articles/<int:pk>/', api_views.api_article_detail, name='api_article_detail'),
    path('api/approved/', api_views.api_approved_log, name='api_approved_log'),
]
