from django.urls import path
from . import views

app_name = 'hijau_kesehatan_satwa'

urlpatterns = [
    # Rekam Medis Hewan (Dokter Hewan only)
    path('rekam-medis/', views.rekam_medis_list, name='rekam_medis_list'),
    path('rekam-medis/form/', views.rekam_medis_form, name='rekam_medis_form'),
    path('rekam-medis/edit/<int:id>/', views.rekam_medis_edit, name='rekam_medis_edit'),
    path('rekam-medis/delete/<int:id>/', views.rekam_medis_delete, name='rekam_medis_delete'),

    # Jadwal Pemeriksaan Kesehatan (Dokter Hewan only)
    path('jadwal-pemeriksaan/', views.jadwal_pemeriksaan_list, name='jadwal_pemeriksaan_list'),
    path('jadwal-pemeriksaan/form/', views.jadwal_pemeriksaan_form, name='jadwal_pemeriksaan_form'),
    path('jadwal-pemeriksaan/delete/<int:id>/', views.jadwal_pemeriksaan_delete, name='jadwal_pemeriksaan_delete'),
    path('jadwal-pemeriksaan/update-frequency/', views.update_frequency, name='update_frequency'),

    # Pemberian Pakan (Penjaga Hewan only)
    path('pemberian-pakan/', views.pemberian_pakan_list, name='pemberian_pakan_list'),
    path('pemberian-pakan/form/', views.pemberian_pakan_form, name='pemberian_pakan_form'),
    path('pemberian-pakan/edit/<int:id>/', views.pemberian_pakan_edit, name='pemberian_pakan_edit'),
    path('pemberian-pakan/delete/<int:id>/', views.pemberian_pakan_delete, name='pemberian_pakan_delete'),
    path('pemberian-pakan/beri-pakan/<int:id>/', views.beri_pakan, name='beri_pakan'),
    path('riwayat-pemberian-pakan/', views.riwayat_pemberian_pakan, name='riwayat_pemberian_pakan'),
]