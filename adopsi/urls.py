from django.urls import path
from . import views

app_name = 'adopsi'


urlpatterns = [
    # Kelola Pengunjung
    path('admin/daftar-pengunjung/', views.admin_daftar_pengunjung, name='admin_daftar_pengunjung'),
    path('admin/tambah-pengunjung/', views.admin_tambah_pengunjung, name='admin_tambah_pengunjung'),

    # Admin Program Adopsi
    path('', views.admin_program_adopsi, name='admin_program_adopsi'),
    path('hewan/<str:id_hewan>/', views.admin_detail_adopsi, name='admin_detail_adopsi'),
    path('hewan/<str:id_hewan>/pendataan/', views.admin_pendataan_adopter, name='admin_pendataan_adopter'),  
    path('hewan/<str:id_hewan>/daftar/', views.admin_form_adopsi, name='admin_form_adopsi'),
    path('hewan/<str:id_hewan>/hentikan/', views.hentikan_adopsi, name='hentikan_adopsi'),

    # Adopter Program
    path('program-adopter/', views.adopter_program_adopsi, name='adopter_program_adopsi'),
    path('adopter/<str:id_hewan>/', views.adopter_lihat_adopsi, name='adopter_lihat_adopsi'),
    path('adopter-lihat/<uuid:id_hewan>/', views.adopter_lihat_adopsi, name='adopter_lihat_adopsi'),
    path('pantau-kondisi/<str:id_hewan>/', views.adopter_pantau_kondisi, name='adopter_pantau_kondisi'),
    path('sertifikat-adopsi/<str:id_hewan>/', views.adopter_sertifikat, name='adopter_sertifikat'),
    path('perpanjang-adopsi/<str:id_hewan>/', views.adopter_perpanjang_adopsi, name='adopter_perpanjang_adopsi'),
    path('adopter/hentikan-adopsi/<uuid:id_hewan>/', views.hentikan_adopsi_adopter, name='hentikan_adopsi_adopter'),
    path('adopsi/adopter/hewan/<uuid:id_hewan>/', views.adopter_lihat_adopsi, name='adopter_lihat_adopsi'),

    # Admin Daftar Adopter
    path('adopter/', views.admin_list_adopter, name='admin_list_adopter'),
    path('adopter/<uuid:id_adopter>/hapus/', views.hapus_adopter, name='hapus_adopter'),
    path('adopter/<uuid:id_adopter>/riwayat/', views.admin_riwayat_adopsi, name='admin_riwayat_adopsi'),
    path('adopter/<uuid:id_adopter>/hapus/<uuid:id_hewan>/<str:tanggal_mulai>/', views.hapus_riwayat_adopsi, name='hapus_riwayat_adopsi'),
    
]
