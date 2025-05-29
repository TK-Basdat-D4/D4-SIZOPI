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

    path('reservasi/atraksi/<slug:slug_reservasi>/', buat_reservasi_atraksi, name='buat_reservasi_atraksi'),
    path('reservasi/wahana/<slug:slug_reservasi>/', buat_reservasi_wahana, name='buat_reservasi_wahana'),
    path('reservasi/detail/<slug:slug_reservasi>/', detail_reservasi, name='detail_reservasi'),
    path('reservasi/atraksi/edit/list/<slug:slug_reservasi>/', edit_reservasi_atraksi_list, name='edit_reservasi_atraksi_list'),
    path('reservasi/wahana/edit/list/<slug:slug_reservasi>/', edit_reservasi_wahana_list, name='edit_reservasi_wahana_list'),
    path('reservasi/cancel/<slug:slug_reservasi>/', cancel_reservasi_list, name='cancel_reservasi_list'),
    path('reservasi/cancel/detail/<slug:slug_reservasi>/', cancel_reservasi_detail, name='cancel_reservasi_detail'),
    path('reservasi/list/', list_reservasi, name='list_reservasi'),
    path('reservasi/list/data/', list_data_reservasi, name='list_data_reservasi'),
    path('reservasi/list/admin/', list_reservasi_admin, name='list_reservasi_admin'),
    path('reservasi/cancel/admin/<slug:slug_reservasi>/', cancel_reservasi_admin, name='cancel_reservasi_admin'),
    path('reservasi/atraksi/edit/admin/<slug:slug_reservasi>/', edit_reservasi_atraksi_admin, name='edit_reservasi_atraksi_admin'),
    path('reservasi/wahana/edit/admin/<slug:slug_reservasi>/', edit_reservasi_wahana_admin, name='edit_reservasi_wahana_admin'),
]
