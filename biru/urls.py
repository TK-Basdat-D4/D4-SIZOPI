from django.urls import path
from biru.views import *

app_name = 'biru'

urlpatterns = [
    path('atraksi/', list_atraksi, name='list_atraksi'),
    path('atraksi/tambah/', tambah_atraksi, name='tambah_atraksi'),
    path('atraksi/edit/<slug:slug_atraksi>/', edit_atraksi, name='edit_atraksi'),
    path('atraksi/delete/<slug:slug_atraksi>/', delete_atraksi, name='delete_atraksi'),

    path('wahana/', list_wahana, name='list_wahana'),
    path('wahana/tambah/', tambah_wahana, name='tambah_wahana'),
    path('wahana/edit/<slug:slug_wahana>/', edit_wahana, name='edit_wahana'),
    path('wahana/delete/<slug:slug_wahana>/', delete_wahana, name='delete_wahana'),

    path('reservasi/atraksi/', buat_reservasi_atraksi, name='buat_reservasi_atraksi'),
    path('reservasi/atraksi/<int:reservasi_id>/', detail_reservasi_atraksi, name='detail_reservasi_atraksi'),
    path('reservasi/atraksi/edit/<int:reservasi_id>/', edit_reservasi_atraksi, name='edit_reservasi_atraksi'),
    path('reservasi/atraksi/cancel/<int:reservasi_id>/', cancel_reservasi_atraksi, name='cancel_reservasi_atraksi'),
    path('reservasi/atraksi/list/', list_reservasi, name='list_reservasi'),
    path('reservasi/atraksi/delete/<int:reservasi_id>/', delete_reservasi_atraksi, name='delete_reservasi_atraksi'),
    path('reservasi/atraksi/edit/admin/<int:reservasi_id>/', edit_reservasi_atraksi_admin, name='edit_reservasi_atraksi_admin'),
]
