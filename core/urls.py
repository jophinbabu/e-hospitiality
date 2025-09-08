from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    # Homepage - shows landing page with registration info
    path('', views.home, name='home'),
    
    # Registration
    path('register/', views.register, name='register'),
    
    # Dashboard redirect (after login)
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    
    # Authentication
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html'
    ), name='login'),
    
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
