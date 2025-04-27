from django.urls import path
from . import views

app_name = 'register_login'

urlpatterns = [
    path('', views.home, name='home'),
    path('choose-role/', views.choose_role, name='choose_role'),
    path('register-pengunjung/', views.register_pengunjung, name='register_pengunjung'),
    path('register-dokter/', views.register_dokter, name='register_dokter'),
    path('register-staff/', views.register_staff, name='register_staff'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('profile/', views.profile, name='profile'),
]