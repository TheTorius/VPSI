"""
URL configuration for Projekt project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from rezervace import views

urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    
    # Přidání URL pro přihlášení a odhlášení
    #path('login/', auth_views.LoginView.as_view(template_name='rezervace/login.html'), name='login'),
    #path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home, name='home'), 
    path('register/', views.register, name='register'),
    path('index/', views.index, name='index'),
    path('', views.main, name='main'),
    path('hriste/', views.hriste, name='hriste'),
    path('rezervace/', views.rezervace, name='rezervace'),
    path('rezervace/zrusit/<int:rez_id>/', views.zrusit_rezervaci, name='zrusit_rezervaci'),
    path('rezervace/tisk/<int:rez_id>/', views.tisk_rezervace, name='tisk_rezervace'),
    path('zrusit-rezervaci-zapujcky/<int:rez_id>/', views.zrusit_rezervaci_zapujcky, name='zrusit_rezervaci_zapujcky'),
    path('tisk-rezervace-zapujcka/<int:rez_id>/', views.tisk_rezervace_zapujcka, name='tisk_rezervace_zapujcka'),
    path('cennik/', views.cennik, name='cennik'),
    path('nastaveni/', views.nastaveni, name='nastaveni'),
    path('signup/', views.signup_view, name='signup'),
    path('login/',views.login_view, name='login'),
    path("reserve/<int:court>/<str:hour>/", views.reserve_hour, name="reserve"),
    path("profile/",views.profile_view,name='profile')
]
