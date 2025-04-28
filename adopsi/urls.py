from django.urls import path
from . import views

urlpatterns = [
    path('', views.daftar_hewan, name='daftar_hewan'),
    path('hewan/<str:id_hewan>/', views.detail_adopsi, name='detail_adopsi'),
    path('hewan/<str:id_hewan>/pendataan/', views.pendataan_adopter, name='pendataan_adopter'),  
    path('hewan/<str:id_hewan>/daftar/', views.daftarkan_adopter, name='daftarkan_adopter'),
    path('hewan/<str:id_hewan>/hentikan/', views.hentikan_adopsi, name='hentikan_adopsi'),
    path('adopter/<str:id_hewan>/', views.adopter_lihat_detail, name='adopter_lihat_detail'),
]
