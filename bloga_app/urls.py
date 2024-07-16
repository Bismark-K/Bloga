from django.urls import path 
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('create-blog', views.blog_creation, name='create-blog'),
]