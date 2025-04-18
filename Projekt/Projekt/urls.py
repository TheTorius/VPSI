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
    path('', views.index, name='index'),
    path('hriste/', views.hriste, name='hriste'),
    path('reserve_multiple/', views.reserve_multiple, name='reserve_multiple'),
    path('rezervace/', views.rezervace, name='rezervace'),
    path('rezervace/<int:rez_id>/zapujcky/', views.zapujcky_k_rezervaci, name='zapujcky_k_rezervaci'),
    path('rezervace/zrusit/<int:rez_id>/', views.zrusit_rezervaci, name='zrusit_rezervaci'),
    path('rezervace/tisk/<int:rez_id>/', views.tisk_rezervace, name='tisk_rezervace'),
    path('zrusit-rezervaci-zapujcky/<int:rez_id>/', views.zrusit_rezervaci_zapujcky, name='zrusit_rezervaci_zapujcky'),
    path('tisk-rezervace-zapujcka/<int:rez_id>/', views.tisk_rezervace_zapujcka, name='tisk_rezervace_zapujcka'),
    path('cennik/', views.cennik, name='cennik'),
    path('nastaveni/', views.nastaveni, name='nastaveni'),
    path('signup/', views.signup_view, name='signup'),
    path('login/',views.login_view, name='login'),
    path("reserve/<int:court>/<str:hour>/", views.reserve_hour, name="reserve"),
    path("profile/",views.profile_view,name='profile'),
    path('novinky/', views.novinky, name='novinky'),
    
    # Správa sportovišť (pouze pro administrátory)
    path('hriste-management/', views.hriste_management, name='hriste_management'),
    path('hriste-management/vytvorit/', views.hriste_create, name='hriste_create'),
    path('hriste-management/<int:pk>/', views.hriste_detail, name='hriste_detail'),
    path('hriste-management/<int:pk>/upravit/', views.hriste_update, name='hriste_update'),
    path('hriste-management/<int:pk>/smazat/', views.hriste_delete, name='hriste_delete'),
    
    # Veřejný přehled sportovišť (pro všechny uživatele)
    path('sportoviste/', views.hriste_public_list, name='hriste_public_list'),
    path('rezervace/<int:rez_id>/', views.rezervace_detail, name='rezervace_detail'),
    path('rezervace/upravit/<int:rez_id>/', views.rezervace_update, name='rezervace_update'),
    path('admin_reservations/', views.admin_reservations, name='admin_reservations'),
]
