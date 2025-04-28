from django import forms
from django.contrib.auth.models import User
from .models import Adopter, Adopsi
from django.utils import timezone

class VerifikasiAkunForm(forms.Form):
    username = forms.CharField(label="Username", max_length=100)

class AdopsiForm(forms.ModelForm):
    class Meta:
        model = Adopsi
        fields = ['tanggal_mulai', 'tanggal_akhir', 'kontribusi_finansial', 'alasan_adopsi']
        widgets = {
            'tanggal_mulai': forms.DateInput(attrs={'type': 'date', 'min': timezone.now().date().isoformat()}),
            'tanggal_akhir': forms.DateInput(attrs={'type': 'date', 'min': timezone.now().date().isoformat()}),
        }

    def clean(self):
        cleaned_data = super().clean()
        tanggal_mulai = cleaned_data.get('tanggal_mulai')
        tanggal_akhir = cleaned_data.get('tanggal_akhir')
        
        if tanggal_mulai and tanggal_akhir:
            if tanggal_mulai > tanggal_akhir:
                raise forms.ValidationError("Tanggal akhir harus setelah tanggal mulai")
        
        return cleaned_data

class AdopterForm(forms.ModelForm):
    class Meta:
        model = Adopter
        fields = ['tipe', 'nama_lengkap', 'email', 'no_telepon', 'alamat', 'nama_organisasi']
        widgets = {
            'tipe': forms.RadioSelect(choices=Adopter.TIPE_CHOICES),
            'nama_organisasi': forms.TextInput(attrs={'required': False}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        tipe = cleaned_data.get('tipe')
        nama_organisasi = cleaned_data.get('nama_organisasi')
        
        if tipe == 'organisasi' and not nama_organisasi:
            raise forms.ValidationError("Nama organisasi harus diisi untuk tipe adopter organisasi")
        
        return cleaned_data

class UpdateStatusPembayaranForm(forms.ModelForm):
    class Meta:
        model = Adopsi
        fields = ['status_pembayaran']
        widgets = {
            'status_pembayaran': forms.Select(choices=Adopsi.STATUS_PEMBAYARAN_CHOICES),
        }