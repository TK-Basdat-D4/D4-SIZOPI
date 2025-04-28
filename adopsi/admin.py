from django.contrib import admin
from .models import Hewan, Adopter, Adopsi

@admin.register(Hewan)
class HewanAdmin(admin.ModelAdmin):
    list_display = ('nama', 'jenis', 'usia', 'status_adopsi')
    search_fields = ('nama', 'jenis')
    list_filter = ('jenis',)

@admin.register(Adopter)
class AdopterAdmin(admin.ModelAdmin):
    list_display = ('nama_lengkap', 'nama_organisasi', 'tipe', 'email', 'no_telepon')
    search_fields = ('nama_lengkap', 'nama_organisasi', 'email')
    list_filter = ('tipe',)

@admin.register(Adopsi)
class AdopsiAdmin(admin.ModelAdmin):
    list_display = ('hewan', 'adopter', 'tanggal_mulai', 'tanggal_akhir', 'kontribusi_finansial', 'status_pembayaran')
    search_fields = ('hewan__nama', 'adopter__nama_lengkap', 'adopter__nama_organisasi')
    list_filter = ('status_pembayaran', 'tanggal_mulai', 'tanggal_akhir')
    date_hierarchy = 'tanggal_mulai'