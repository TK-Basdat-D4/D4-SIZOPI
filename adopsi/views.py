from django.shortcuts import render, redirect
from django.contrib import messages


DAFTAR_HEWAN = [
    {
        'id': '1505a456',
        'nama': 'Mochi',
        'spesies': 'Harimau Sumatra',
        'kondisi': 'Sehat',
        'foto': 'https://example.com/gamblang.jpg',
        'status_adopsi': 'Diadopsi',
        'adopter': 'Dewi Nugroho',
        'tanggal_mulai': '2025-01-01',
        'tanggal_akhir': '2025-12-31',
        'nominal': '5000000',
        'status_pembayaran': 'tertunda',
    },
    {
        'id': '6b8e76a5',
        'nama': 'Nala',
        'spesies': 'Domba Sumatra',
        'kondisi': 'Dalam Perawatan',
        'foto': 'https://example.com/halima.jpg',
        'status_adopsi': 'Tidak Diadopsi',  # <=== ini diganti Tidak Diadopsi
        'adopter': '',
        'tanggal_mulai': '',
        'tanggal_akhir': '',
        'nominal': '',
        'status_pembayaran': '',
    },
]

def daftar_hewan(request):
    context = {
        'daftar_hewan': DAFTAR_HEWAN
    }
    return render(request, 'adopsi/daftar_hewan.html', context)

def detail_adopsi(request, id_hewan):
    # Cari hewan berdasarkan id
    hewan = next((h for h in DAFTAR_HEWAN if h['id'] == id_hewan), None)
    if not hewan:
        return render(request, '404.html')  # Atau redirect ke halaman error
    context = {
        'hewan': hewan
    }
    return render(request, 'adopsi/detail_adopsi.html', context)

# def daftarkan_adopter(request, id_hewan):
#     hewan = next((h for h in DAFTAR_HEWAN if h['id'] == id_hewan), None)
#     if not hewan:
#         return render(request, '404.html')
#     context = {
#         'hewan': hewan
#     }
#     return render(request, 'adopsi/daftarkan_adopter.html', context)

# def daftarkan_adopter(request, id_hewan):
#     hewan = next((h for h in DAFTAR_HEWAN if h['id'] == id_hewan), None)
#     if not hewan:
#         return render(request, '404.html')

#     tipe_adopter = request.session.get('tipe_adopter')
#     username_adopter = request.session.get('username_adopter')

#     context = {
#         'hewan': hewan,
#         'tipe_adopter': tipe_adopter,
#         'username_adopter': username_adopter,
#     }
#     return render(request, 'adopsi/daftarkan_adopter.html', context)

def daftarkan_adopter(request, id_hewan):
    hewan = next((h for h in DAFTAR_HEWAN if h['id'] == id_hewan), None)
    if not hewan:
        return render(request, '404.html')

    tipe_adopter = request.session.get('tipe_adopter')
    username_adopter = request.session.get('username_adopter')

    if request.method == 'POST':
        # Ambil data dari form
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

        # Validasi sederhana
        if not all([nama, nik, alamat, email, telepon, nominal, periode]):
            messages.error(request, 'Semua field wajib diisi!')
            return redirect('daftarkan_adopter', id_hewan=id_hewan)

        # Update data hewan
        hewan['adopter'] = nama
        hewan['tanggal_mulai'] = '2025-04-28'  # contoh tanggal hari ini
        hewan['tanggal_akhir'] = '2026-04-28'  # kamu bisa hitung dari periode
        hewan['nominal'] = nominal
        hewan['status_pembayaran'] = 'tertunda'
        hewan['status_adopsi'] = 'Diadopsi'

        messages.success(request, 'Adopsi berhasil didaftarkan!')
        return redirect('daftar_hewan')

    context = {
        'hewan': hewan,
        'tipe_adopter': tipe_adopter,
        'username_adopter': username_adopter,
    }
    return render(request, 'adopsi/daftarkan_adopter.html', context)


# Dummy daftar username yang sudah jadi 'pengunjung'
DAFTAR_PENGUNJUNG = ['dewi.nugroho', 'mira.handayani', 'rio.lestari']

# def pendataan_adopter(request, id_hewan):
#     hewan = next((h for h in DAFTAR_HEWAN if h['id'] == id_hewan), None)
#     if not hewan:
#         return render(request, '404.html')

#     if request.method == 'POST':
#         username = request.POST.get('username')
#         tipe_adopter = request.POST.get('tipe_adopter')
#         if username in DAFTAR_PENGUNJUNG:
#             # Kalau username ditemukan, redirect ke form daftarkan adopter
#             return redirect('daftarkan_adopter', id_hewan=id_hewan)
#         else:
#             messages.error(request, 'Username tidak ditemukan atau bukan pengunjung!')

#     context = {
#         'hewan': hewan
#     }
#     return render(request, 'adopsi/pendataan_adopter.html', context)

def pendataan_adopter(request, id_hewan):
    hewan = next((h for h in DAFTAR_HEWAN if h['id'] == id_hewan), None)
    if not hewan:
        return render(request, '404.html')

    if request.method == 'POST':
        username = request.POST.get('username')
        tipe_adopter = request.POST.get('tipe_adopter')
        if username in DAFTAR_PENGUNJUNG:
            # Simpan tipe adopter di session
            request.session['tipe_adopter'] = tipe_adopter
            request.session['username_adopter'] = username
            return redirect('daftarkan_adopter', id_hewan=id_hewan)
        else:
            messages.error(request, 'Username tidak ditemukan atau bukan pengunjung!')

    context = {
        'hewan': hewan
    }
    return render(request, 'adopsi/pendataan_adopter.html', context)

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
        return redirect('daftar_hewan')

    return redirect('detail_adopsi', id_hewan=id_hewan)

def adopter_lihat_detail(request, id_hewan):
    hewan = next((h for h in DAFTAR_HEWAN if h['id'] == id_hewan), None)
    if not hewan:
        return render(request, '404.html')

    username_adopter = request.user.username

    if hewan['adopter'] != username_adopter:
        messages.error(request, "Anda tidak memiliki akses ke hewan ini.")
        return redirect('daftar_hewan')

    context = {
        'hewan': hewan
    }
    return render(request, 'adopsi/adopter_lihat_detail.html', context)




