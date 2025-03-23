from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('discover/', views.discover, name='discover'),
    path('post/create/', views.create_post, name='create_post'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('api/posts/<int:post_id>/like/', views.like_post, name='like_post'),
    
    # Chat URLs
    path('chats/', views.chat_list, name='chat_list'),
    path('chats/<str:chat_id>/', views.chat_detail, name='chat_detail'),
    path('chats/start/<str:username>/', views.start_chat, name='start_chat'),
] 