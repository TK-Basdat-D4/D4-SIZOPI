from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Hewan(models.Model):
    nama = models.CharField(max_length=100)
    jenis = models.CharField(max_length=100)
    usia = models.IntegerField()
    deskripsi = models.TextField()
    gambar = models.ImageField(upload_to='hewan_images/', null=True, blank=True)
    
    def __str__(self):
        return self.nama
    
    def status_adopsi(self):
        try:
            adopsi = self.adopsi_set.filter(status_pembayaran='lunas', tanggal_akhir__gte=timezone.now()).latest('tanggal_mulai')
            return "Diadopsi"
        except Adopsi.DoesNotExist:
            return "Tidak Diadopsi"
    
    def get_active_adoption(self):
        try:
            return self.adopsi_set.filter(status_pembayaran='lunas', tanggal_akhir__gte=timezone.now()).latest('tanggal_mulai')
        except Adopsi.DoesNotExist:
            return None

class Adopter(models.Model):
    TIPE_CHOICES = (
        ('individu', 'Individu'),
        ('organisasi', 'Organisasi'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tipe = models.CharField(max_length=10, choices=TIPE_CHOICES)
    nama_lengkap = models.CharField(max_length=200)
    email = models.EmailField()
    no_telepon = models.CharField(max_length=15)
    alamat = models.TextField()
    nama_organisasi = models.CharField(max_length=200, null=True, blank=True)
    
    def __str__(self):
        if self.tipe == 'organisasi':
            return f"{self.nama_organisasi} ({self.user.username})"
        return f"{self.nama_lengkap} ({self.user.username})"

class Adopsi(models.Model):
    STATUS_PEMBAYARAN_CHOICES = (
        ('tertunda', 'Tertunda'),
        ('lunas', 'Lunas'),
        ('dibatalkan', 'Dibatalkan'),
    )
    
    adopter = models.ForeignKey(Adopter, on_delete=models.CASCADE)
    hewan = models.ForeignKey(Hewan, on_delete=models.CASCADE)
    tanggal_mulai = models.DateField()
    tanggal_akhir = models.DateField()
    kontribusi_finansial = models.DecimalField(max_digits=10, decimal_places=2)
    status_pembayaran = models.CharField(max_length=10, choices=STATUS_PEMBAYARAN_CHOICES, default='tertunda')
    alasan_adopsi = models.TextField()
    dibuat_pada = models.DateTimeField(auto_now_add=True)
    diupdate_pada = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.adopter} - {self.hewan} ({self.tanggal_mulai} - {self.tanggal_akhir})"
    
    def is_active(self):
        return self.status_pembayaran == 'lunas' and self.tanggal_akhir >= timezone.now().date()