from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.urls import reverse
from django.http import HttpResponseRedirect

DAFTAR_HEWAN = [
    {
        'id': '1505a456-8553-4847-9741-1950a043483b',
        'nama': 'Mochi',
        'spesies': 'Harimau Sumatra',
        'kondisi': 'Sehat',
        'foto': 'https://thaka.bing.com/th/id/OIP.zFfSIR-hFqqY84hA9vrCPQHaFj?rs=1&pid=ImgDetMain',
        'status_adopsi': 'Diadopsi',
        'habitat' : 'Hujan Tropis',
        'adopter': 'Budi Santoso',
        'tanggal_mulai': '2025-01-01',
        'tanggal_akhir': '2025-12-31',
        'nominal': '5000000',
        'status_pembayaran': 'tertunda',
    },
    {
        'id': '6c265ae8-b424-482e-8420-3b6b93470a0e',
        'nama': 'Simba',
        'spesies': 'Panda Amerika Selatan',
        'kondisi': 'Sehat',
        'foto': 'https://th.bing.com/th/id/R.d0d586fd70a04bbde58462061468f792?rik=v%2fES7so2k2%2b9gw&riu=http%3a%2f%2f2.bp.blogspot.com%2f-aHBXLcUidp0%2fVJpA6eCxphI%2fAAAAAAAAAtc%2fXWr7uA6X6q8%2fs1600%2fSweet-Panda-pandas-12538504-1600-1200.jpg&ehk=EnRvyhDOFQqeG8dEP2M%2bfG3k0py5uWJUDuyVIB73KjI%3d&risl=&pid=ImgRaw&r=0',
        'status_adopsi': 'Diadopsi',
        'habitat' : 'Hujan Rambu',  
        'adopter': 'Rio Ayu Lestari',
        'tanggal_mulai': '2024-03-05',
        'tanggal_akhir': '2024-07-05',
        'nominal': '750000',
        'status_pembayaran': 'Tertunda',
    },
    {
        'id': 'a4fef9d2-1e9f-4d68-bf8a-2b63d2f0da79',
        'nama': 'Luna',
        'spesies': 'Kucing Persia',
        'kondisi': 'Sehat',
        'foto': 'https://th.bing.com/th/id/OIP.Z7H7v0mawF5676CTPx7gpQHaEK?rs=1&pid=ImgDetMain',
        'status_adopsi': 'Tidak Diadopsi',
        'habitat' : 'Hujan Tropis',
        'adopter': '',
        'tanggal_mulai': '',
        'tanggal_akhir': '',
        'nominal': '',
        'status_pembayaran': '',
    },
    {
        'id': 'a9f7ed56-85ed-48f5-90c0-3bf0b8b11b2b',
        'nama': 'Rocky',
        'spesies': 'Anjing Bulldog',
        'kondisi': 'Sehat',
        'foto': 'https://th.bing.com/th/id/OIP.h3lzKhnxU6twe_POtVQMywHaGg?w=1000&h=879&rs=1&pid=ImgDetMain',
        'status_adopsi': 'Tidak Diadopsi',
        'adopter': '',
        'habitat' : 'Domestik',
        'tanggal_mulai': '',
        'tanggal_akhir': '',
        'nominal': '',
        'status_pembayaran': '',
    },
]

def admin_program_adopsi(request):
    context = {
        'daftar_hewan': DAFTAR_HEWAN
    }
    return render(request, 'adopsi/admin_program_adopsi.html', context)

def admin_detail_adopsi(request, id_hewan):
    hewan = next((h for h in DAFTAR_HEWAN if h['id'] == id_hewan), None)
    if not hewan:
        return render(request, '404.html')   
    context = {
        'hewan': hewan
    }
    return render(request, 'adopsi/admin_detail_adopsi.html', context)

# Data adopter yang sudah terverifikasi
DAFTAR_PENGUNJUNG_ADOPTER = [
    {'username': 'pengunjung123', 'tipe_adopter': 'Individu', 'nama_adopter': 'Budi Santoso', 'nik': '1234567890123456'},
    {'username': 'rio.lestari', 'tipe_adopter': 'Individu', 'nama_adopter': 'Rio Ayu Lestari', 'nik': '9876543210987654'},
    {'username': 'organisasi_xyz', 'tipe_adopter': 'Organisasi', 'nama_adopter': 'Yayasan XYZ', 'npp': 'YAY001234'}
]

def admin_form_adopsi(request, id_hewan):
    hewan = next((h for h in DAFTAR_HEWAN if h['id'] == id_hewan), None)
    if not hewan:
        return render(request, '404.html')
        
    username_adopter = request.session.get('username_adopter')

    adopter = next((a for a in DAFTAR_PENGUNJUNG_ADOPTER if a['username'] == username_adopter), None)
    
    if not adopter:
        messages.error(request, 'Username adopter tidak terdaftar!')
        return HttpResponseRedirect(reverse('adopsi:admin_form_adopsi', args=[id_hewan]))

    tipe_adopter = adopter['tipe_adopter']

    if request.method == 'POST':
        if tipe_adopter == 'Individu':
            nama = request.POST.get('nama_adopter')
            nik = request.POST.get('nik')
        else:
            nama = request.POST.get('nama_organisasi')
            nik = request.POST.get('npp')
        
        alamat = request.POST.get('alamat')
        email = request.POST.get('email')
        telepon = request.POST.get('telepon')
        nominal = request.POST.get('nominal')
        periode = request.POST.get('periode')
        
        if not all([nama, nik, alamat, email, telepon, nominal, periode]):
            messages.error(request, 'Semua field wajib diisi!')
            return HttpResponseRedirect(reverse('adopsi:admin_form_adopsi', args=[id_hewan]))

        hewan['adopter'] = nama
        hewan['tanggal_mulai'] = '2025-04-28'  
        hewan['tanggal_akhir'] = '2026-04-28'  
        hewan['nominal'] = nominal
        hewan['status_pembayaran'] = 'tertunda'
        hewan['status_adopsi'] = 'Diadopsi'

        messages.success(request, 'Adopsi berhasil didaftarkan!')
        return HttpResponseRedirect(reverse('adopsi:admin_program_adopsi'))
    context = {
        'hewan': hewan,
        'tipe_adopter': tipe_adopter,
        'username_adopter': username_adopter,
        'adopter': adopter  
    }
    return render(request, 'adopsi/admin_form_adopsi.html', context)

# Dummy daftar username yang sudah jadi 'pengunjung'
DAFTAR_PENGUNJUNG = [
    {'username': 'pengunjung123', 'nama': 'Budi Santoso'},
    {'username': 'rio.lestari', 'nama': 'Rio Ayu Lestari'},
    {'username': 'dewi.nugroho', 'nama': 'Dewi Nugroho'},
    {'username': 'mira.handayani', 'nama': 'Mira Handayani'},
    {'username': 'organisasi_xyz', 'nama': 'Yayasan XYZ'}
]

def admin_pendataan_adopter(request, id_hewan):
    hewan = next((h for h in DAFTAR_HEWAN if h['id'] == id_hewan), None)
    if not hewan:
        return render(request, '404.html')

    if request.method == 'POST':
        username = request.POST.get('username')
        tipe_adopter = request.POST.get('tipe_adopter')
        pengunjung = next((p for p in DAFTAR_PENGUNJUNG if p['username'] == username), None)
        
        if pengunjung:
            request.session['tipe_adopter'] = tipe_adopter
            request.session['username_adopter'] = username
            adopter = next((a for a in DAFTAR_PENGUNJUNG_ADOPTER if a['username'] == username), None)
            
            if not adopter:
                new_adopter = {
                    'username': username,
                    'tipe_adopter': tipe_adopter,
                    'nama_adopter': pengunjung['nama'],
                    'nik': '1234567890123456' if tipe_adopter == 'Individu' else None,
                    'npp': 'NPP12345' if tipe_adopter == 'Organisasi' else None
                }
                DAFTAR_PENGUNJUNG_ADOPTER.append(new_adopter)
            
            return HttpResponseRedirect(reverse('adopsi:admin_form_adopsi', args=[id_hewan]))
        else:
            messages.error(request, 'Username tidak ditemukan atau bukan pengunjung!')

    context = {
        'hewan': hewan,
        'daftar_pengunjung': DAFTAR_PENGUNJUNG  
    }
    return render(request, 'adopsi/admin_pendataan_adopter.html', context)


def hentikan_adopsi(request, id_hewan):
    hewan = next((h for h in DAFTAR_HEWAN if h['id'] == id_hewan), None)
    if not hewan:
        return render(request, '404.html')

    if request.method == 'POST':
        hewan['status_adopsi'] = 'Tidak Diadopsi'
        hewan['adopter'] = ''
        hewan['tanggal_mulai'] = ''
        hewan['tanggal_akhir'] = ''
        hewan['nominal'] = ''
        hewan['status_pembayaran'] = ''
        messages.success(request, 'Adopsi berhasil dihentikan.')
        return HttpResponseRedirect(reverse('adopsi:admin_program_adopsi', args=[id_hewan]))

    return HttpResponseRedirect(reverse('adopsi:admin_detail_adopsi', args=[id_hewan]))

def adopter_lihat_adopsi(request, id_hewan):
    hewan = next((h for h in DAFTAR_HEWAN if h['id'] == id_hewan), None)
    if not hewan:
        return render(request, '404.html')

    username_adopter = "Budi Santoso"

    # if hewan['adopter'] != username_adopter:
    #     messages.error(request, "Anda tidak memiliki akses ke hewan ini.")
    #     return HttpResponseRedirect(reverse('adopsi:adopter_program_adopsi', args=[id_hewan]))
    context = {
        'hewan': hewan
    }
    return render(request, 'adopsi/adopter_lihat_adopsi.html', context)

def adopter_program_adopsi(request):
    username = "Budi Santoso"
    hewan_diadopsi = [
        hewan for hewan in DAFTAR_HEWAN 
        if hewan['adopter'] == username and hewan['status_adopsi'] == 'Diadopsi'
    ]
   
    rocky = next((h for h in DAFTAR_HEWAN if h['nama'] == 'Rocky'), None)
    if rocky and rocky not in hewan_diadopsi:
        rocky_copy = rocky.copy()
        rocky_copy['adopter'] = username
        rocky_copy['status_adopsi'] = 'Diadopsi'
        rocky_copy['tanggal_mulai'] = '2025-03-15'
        rocky_copy['tanggal_akhir'] = '2025-09-15'
        rocky_copy['nominal'] = '3500000'
        rocky_copy['status_pembayaran'] = 'lunas'
        hewan_diadopsi.append(rocky_copy)
    
    context = {
        'hewan_diadopsi': hewan_diadopsi,
        'username': username
    }
    return render(request, 'adopsi/adopter_program_adopsi.html', context)

def adopter_pantau_kondisi(request, id_hewan):
    hewan = next((h for h in DAFTAR_HEWAN if h['id'] == id_hewan), None)
    if not hewan:
        return render(request, '404.html')

    DUMMY_REKAM_MEDIS = [
        {'tanggal': '2025-05-05', 'diagnosis': 'Infeksi', 'pengobatan': 'Obat B', 'status': 'Sakit Ringan', 'catatan': 'Observasi rutin'},
        {'tanggal': '2025-06-01', 'diagnosis': 'Cedera', 'pengobatan': 'Obat A', 'status': 'Sehat', 'catatan': 'Kontrol 1 minggu'},
        {'tanggal': '2025-03-20', 'diagnosis': 'Malnutrisi', 'pengobatan': 'Perawatan Khusus', 'status': 'Sehat', 'catatan': 'Kontrol rutin'},
    ]

    tanggal_mulai_str = hewan.get('tanggal_mulai', '')
    rekam_medis = []

    if tanggal_mulai_str:  
        try:
            tanggal_mulai = datetime.strptime(tanggal_mulai_str, '%Y-%m-%d')
            rekam_medis = [r for r in DUMMY_REKAM_MEDIS if datetime.strptime(r['tanggal'], '%Y-%m-%d') > tanggal_mulai]
        except ValueError:
            rekam_medis = []  
    else:
        rekam_medis = DUMMY_REKAM_MEDIS 
    context = {
        'hewan': hewan,
        'rekam_medis': rekam_medis,
    }
    return render(request, 'adopsi/adopter_pantau_kondisi.html', context)

def adopter_sertifikat(request, id_hewan):
    hewan = next((h for h in DAFTAR_HEWAN if h['id'] == id_hewan), None)
    if not hewan:
        return render(request, '404.html')

    context = {
        'hewan': hewan,
        'nomor_sertifikat': f"ADP-{hewan['id'][:4].upper()}-{hewan['adopter'][:3].upper()}-2025",  
        'tanggal_sertifikat': hewan['tanggal_mulai'],  
    }
    return render(request, 'adopsi/adopter_sertifikat.html', context)

def adopter_perpanjang_adopsi(request, id_hewan):
    hewan = next((h for h in DAFTAR_HEWAN if h['id'] == id_hewan), None)
    if not hewan:
        return render(request, '404.html')

    if hewan['status_adopsi'] != 'Diadopsi':
        messages.error(request, 'Hewan ini belum diadopsi, tidak bisa perpanjang adopsi!')
        return HttpResponseRedirect(reverse('adopsi:adopter_lihat_adopsi', args=[id_hewan]))

    tipe_adopter = request.session.get('tipe_adopter')
    username_adopter = request.session.get('username_adopter')

    if request.method == 'POST':
        nominal = request.POST.get('nominal')
        periode = request.POST.get('periode')

        if not all([nominal, periode]):
            messages.error(request, 'Semua field wajib diisi!')
            return HttpResponseRedirect(reverse('adopsi:adopter_perpanjang_adopsi', args=[id_hewan]))

        from datetime import datetime
        from dateutil.relativedelta import relativedelta

        today = datetime.today()
        if hewan['tanggal_akhir']:
            tanggal_akhir_lama = datetime.strptime(hewan['tanggal_akhir'], '%Y-%m-%d')
        else:
            tanggal_akhir_lama = today

        tambahan_bulan = int(periode)
        tanggal_akhir_baru = tanggal_akhir_lama + relativedelta(months=tambahan_bulan)

        hewan['tanggal_akhir'] = tanggal_akhir_baru.strftime('%Y-%m-%d')
        hewan['nominal'] = str(int(hewan.get('nominal', 0)) + int(nominal))
        hewan['status_pembayaran'] = 'tertunda'

        messages.success(request, 'Perpanjangan adopsi berhasil dilakukan!')
        return HttpResponseRedirect(reverse('adopsi:adopter_lihat_adopsi', args=[id_hewan]))

    context = {
        'hewan': hewan,
        'tipe_adopter': tipe_adopter,
        'username_adopter': username_adopter,
    }
    return render(request, 'adopsi/adopter_perpanjang_adopsi.html', context)

def hentikan_adopsi_adopter(request, id_hewan):
    hewan = next((h for h in DAFTAR_HEWAN if h['id'] == id_hewan), None)
    if not hewan:
        return render(request, '404.html')

    if request.method == 'POST':
        hewan['status_adopsi'] = 'Tidak Diadopsi'
        hewan['adopter'] = ''
        hewan['tanggal_mulai'] = ''
        hewan['tanggal_akhir'] = ''
        hewan['nominal'] = ''
        hewan['status_pembayaran'] = ''
        messages.success(request, f'Adopsi {hewan["nama"]} berhasil dihentikan.')
        return HttpResponseRedirect(reverse('adopsi:admin_program_adopsi', args=[id_hewan]))

    return HttpResponseRedirect(reverse('adopsi:admin_', args=[id_hewan]))

# Tambahan dummy data adopter
DAFTAR_ADOPTER = [
    {'id': 1, 'nama': 'Bambang', 'total_kontribusi': 5000000, 'alamat': 'Jl. Mawar No. 1', 'kontak': '081234567890', 'riwayat_adopsi': [{'id': 'h1', 'nama_hewan': 'Melly', 'jenis_hewan': 'Gajah', 'tanggal_mulai': '2025-02-26', 'tanggal_akhir': '2025-08-26', 'nominal': 850000, 'status': 'Sedang Berlangsung'}, {'id': 'h2', 'nama_hewan': 'Simba', 'jenis_hewan': 'Singa', 'tanggal_mulai': '2024-07-10', 'tanggal_akhir': '2024-10-10', 'nominal': 1500000, 'status': 'Berakhir'}]},
    {'id': 2, 'nama': 'Cindy', 'total_kontribusi': 3500000, 'alamat': 'Jl. Melati No. 2', 'kontak': '082345678901', 'riwayat_adopsi': [{'id': 'h3', 'nama_hewan': 'Nala', 'jenis_hewan': 'Zebra', 'tanggal_mulai': '2023-12-12', 'tanggal_akhir': '2024-12-12', 'nominal': 1200000, 'status': 'Berakhir'}, {'id': 'h4', 'nama_hewan': 'Rio', 'jenis_hewan': 'Harimau', 'tanggal_mulai': '2023-01-01', 'tanggal_akhir': '2023-07-01', 'nominal': 800000, 'status': 'Berakhir'}]}
]

def admin_list_adopter(request):
    context = {
        'admin_list_adopter': DAFTAR_ADOPTER
    }
    return render(request, 'adopsi/admin_list_adopter.html', context)

def admin_riwayat_adopsi(request, id_adopter):
    adopter = next((a for a in DAFTAR_ADOPTER if a['id'] == id_adopter), None)
    if not adopter:
        return render(request, '404.html')
    context = {
        'adopter': adopter
    }
    return render(request, 'adopsi/admin_riwayat_adopsi.html', context)

def hapus_adopter(request, id_adopter):
    global DAFTAR_ADOPTER
    adopter = next((a for a in DAFTAR_ADOPTER if a['id'] == id_adopter), None)
    if not adopter:
        return render(request, '404.html')
    
    if request.method == 'POST':
        DAFTAR_ADOPTER = [a for a in DAFTAR_ADOPTER if a['id'] != id_adopter]
        messages.success(request, f'Adopter {adopter["nama"]} berhasil dihapus.')
        return redirect('adopsi:admin_list_adopter')
    
    return redirect('adopsi:admin_list_adopter')

def hapus_riwayat_adopsi(request, id_adopter, id_adopsi):
    adopter = next((a for a in DAFTAR_ADOPTER if a['id'] == id_adopter), None)
    if not adopter:
        return render(request, '404.html')

    if request.method == 'POST':
        adopter['riwayat_adopsi'] = [adopsi for adopsi in adopter['riwayat_adopsi'] if adopsi['id'] != id_adopsi]
        messages.success(request, 'Riwayat adopsi berhasil dihapus.')
        return redirect('adopsi:admin_riwayat_adopsi', id_adopter=id_adopter)

    return redirect('adopsi:admin_riwayat_adopsi', id_adopter=id_adopter)



