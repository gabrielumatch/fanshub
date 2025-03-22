from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('become-creator/', views.become_creator, name='become_creator'),
    path('creator/dashboard/', views.creator_dashboard, name='creator_dashboard'),
    path('creator/<str:username>/', views.creator_profile, name='creator_profile'),
] 