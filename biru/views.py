from django.shortcuts import render, redirect
from django.utils.text import slugify
from django.contrib import messages
from datetime import datetime

# Dummy Data
HEWAN = ['Anjing Laut', 'Gajah Sumatera', 'Burung Kakaktua', 'Lumba-lumba', 'Singa', 'Harimau', 'Beruang']
PELATIH = ['Andi', 'Siti', 'Budi', 'Rina', 'Danu', 'Tomi', 'Rini', 'Bobi']

ATRAKSI = [
    {
        'nama_atraksi': 'Pertunjukan Anjing Laut',
        'lokasi': 'Zona Akuatik',
        'kapasitas': 150,
        'jadwal': datetime(2025, 4, 29, 14, 30, 0),
        'hewan_terlibat': ['Anjing Laut'],
        'pelatih': ['Andi'],
    },
    {
        'nama_atraksi': 'Tari Burung Kakaktua',
        'lokasi': 'Zona Burung Tropis',
        'kapasitas': 100,
        'jadwal': datetime(2025, 4, 29, 10, 0, 0),
        'hewan_terlibat': ['Burung Kakaktua'],
        'pelatih': ['Siti'],
    },
    {
        'nama_atraksi': 'Atraksi Gajah ',
        'lokasi': 'Zona Mamalia Besar',
        'kapasitas': 200,
        'jadwal': datetime(2025, 4, 29, 11, 30, 0),
        'hewan_terlibat': ['Gajah Sumatera'],
        'pelatih': ['Budi'],
    },
    {
        'nama_atraksi': 'Pertunjukan Lumba-lumba',
        'lokasi': 'Zona Akuatik',
        'kapasitas': 180,
        'jadwal': datetime(2025, 4, 29, 13, 0, 0),
        'hewan_terlibat': ['Lumba-lumba'],
        'pelatih': ['Rina'],
    },
    {
        'nama_atraksi': 'Pertunjukan Singa dan Harimau',
        'lokasi': 'Zona Predator',
        'kapasitas': 120,
        'jadwal': datetime(2025, 4, 29, 16, 0, 0),
        'hewan_terlibat': ['Singa','Harimau'],
        'pelatih': ['Danu', 'Tomi'],
    },
]

WAHANA = [
    {
        'nama_wahana': 'Komidi Putar',
        'kapasitas': 20,
        'jadwal': datetime(2025, 4, 29, 14, 0, 0),
        'peraturan': [
            'Ikuti instruksi petugas',
            'Dilarang membawa makanan',
            'Usia minimum 12 tahun'
        ]
    },
    {
        'nama_wahana': 'Roller Coaster Safari',
        'kapasitas': 30,
        'jadwal': datetime(2025, 4, 29, 16, 0, 0),
        'peraturan': [
            'Ikuti instruksi petugas',
            'Hanya untuk pengunjung dengan tinggi badan minimal 150 cm'
        ]
    },
    {
        'nama_wahana': 'Ferris Wheel',
        'kapasitas': 50,
        'jadwal': datetime(2025, 4, 29, 18, 0, 0),
        'peraturan': [
            'Ikuti instruksi petugas',
            'Usia dibawah 6 tahun wajib didampingi'
        ]
    },
]

RESERVASI = [
    {
        'id': 1,
        'atraksi': ATRAKSI[1]['nama_atraksi'],
        'lokasi': ATRAKSI[1]['lokasi'],
        'jam': ATRAKSI[1]['jadwal'].strftime('%H:%M'),
        'tanggal': '2025-04-30',
        'username': 'pengunjung123',
        'jumlah_tiket': 3,
        'waktu_reservasi': datetime.now().strftime('%Y-%m-%d'),
        'status': 'Terjadwal'
    },
]

RESERVASI_ID = 2

# Helper function untuk autentikasi pengguna
def check_admin_access(request):
    """Check if user is a logged-in doctor"""
    if 'user' not in request.session:
        messages.error(request, 'Silahkan login terlebih dahulu!')
        return False

    current_user = request.session['user']
    if current_user.get('peran') != 'staff_administrasi':
        messages.error(request, 'Anda tidak memiliki akses ke halaman ini!')
        return False
    return True

def check_visitor_admin_access(request):
    """Check if user is a logged-in animal keeper"""
    if 'user' not in request.session:
        messages.error(request, 'Silahkan login terlebih dahulu!')
        return False

    current_user = request.session['user']
    if current_user.get('role') == 'pengunjung' or current_user.get('peran') == 'staff_administrasi':
        return True
    messages.error(request, 'Anda tidak memiliki akses ke halaman ini!')
    return False

def list_atraksi(request):
    if not check_admin_access(request):
        return redirect('register_login:login')

    for a in ATRAKSI:
        a['slug'] = slugify(a['nama_atraksi'])
    return render(request, 'list_atraksi.html', {'atraksi_list': ATRAKSI})

def tambah_atraksi(request):
    if not check_admin_access(request):
        return redirect('register_login:login')

    if request.method == 'POST':
        nama_atraksi = request.POST.get('nama_atraksi')
        lokasi = request.POST.get('lokasi')
        kapasitas = int(request.POST.get('kapasitas'))
        jadwal_str = request.POST.get('jadwal')
        jadwal = datetime(2025, 4, 29, int(jadwal_str[:2]), int(jadwal_str[3:]))  # fix date, dynamic time
        hewan_terlibat = request.POST.getlist('hewan_terlibat')
        pelatih = request.POST.getlist('pelatih')

        atraksi_baru = {
            'nama_atraksi': nama_atraksi,
            'lokasi': lokasi,
            'kapasitas': kapasitas,
            'jadwal': jadwal,
            'hewan_terlibat': hewan_terlibat,
            'pelatih': pelatih,
        }

        ATRAKSI.append(atraksi_baru)
        return redirect('biru:list_atraksi')

    return render(request, 'tambah_atraksi.html', {'hewan': HEWAN, 'pelatih': PELATIH})

def edit_atraksi(request, slug_atraksi):
    if not check_admin_access(request):
        return redirect('register_login:login')

    atraksi = next((a for a in ATRAKSI if slugify(a['nama_atraksi']) == slug_atraksi), None)
    if not atraksi:
        return HttpResponseNotFound("Atraksi tidak ditemukan.")

    if request.method == 'POST':
        atraksi['nama_atraksi'] = request.POST.get('nama_atraksi')
        atraksi['lokasi'] = request.POST.get('lokasi')
        atraksi['kapasitas'] = int(request.POST.get('kapasitas'))
        atraksi['jadwal'] = datetime.strptime(request.POST.get('jadwal'), "%H:%M")
        atraksi['hewan_terlibat'] = request.POST.getlist('hewan_terlibat')
        atraksi['pelatih'] = request.POST.getlist('pelatih')
        return redirect('biru:list_atraksi')

    return render(request, 'edit_atraksi.html', {
        'atraksi': atraksi,
        'hewan': HEWAN,
        'pelatih': PELATIH,
    })

def delete_atraksi(request, slug_atraksi):
    if not check_admin_access(request):
        return redirect('register_login:login')

    atraksi = next((a for a in ATRAKSI if slugify(a['nama_atraksi']) == slug_atraksi), None)
    if not atraksi:
        return HttpResponseNotFound("Atraksi tidak ditemukan.")
    ATRAKSI.remove(atraksi)
    return redirect('biru:list_atraksi')

def list_wahana(request):
    if not check_admin_access(request):
        return redirect('register_login:login')

    for a in WAHANA:
        a['slug'] = slugify(a['nama_wahana'])
    return render(request, 'list_wahana.html', {'wahana_list': WAHANA})

def tambah_wahana(request):
    if not check_admin_access(request):
        return redirect('register_login:login')

    if request.method == 'POST':
        nama_wahana = request.POST.get('nama_wahana')
        kapasitas = int(request.POST.get('kapasitas'))
        jadwal_str = request.POST.get('jadwal')
        jadwal = datetime(2025, 4, 29, int(jadwal_str[:2]), int(jadwal_str[3:]))
        peraturan = request.POST.getlist('peraturan')

        wahana_baru = {
            'nama_wahana': nama_wahana,
            'kapasitas': kapasitas,
            'jadwal': jadwal,
            'peraturan': peraturan,
        }

        WAHANA.append(wahana_baru)
        return redirect('biru:list_wahana')

    return render(request, 'tambah_wahana.html')

def edit_wahana(request, slug_wahana):
    if not check_admin_access(request):
        return redirect('register_login:login')

    wahana = next((a for a in WAHANA if slugify(a['nama_wahana']) == slug_wahana), None)
    if not wahana:
        return HttpResponseNotFound("Wahana tidak ditemukan.")

    if request.method == 'POST':
        wahana['nama_wahana'] = request.POST.get('nama_wahana')
        wahana['kapasitas'] = int(request.POST.get('kapasitas'))
        wahana['jadwal'] = datetime.strptime(request.POST.get('jadwal'), "%H:%M")
        wahana['peraturan'] = request.POST.getlist('peraturan')
        return redirect('biru:list_wahana')

    return render(request, 'edit_wahana.html', {
        'wahana': wahana,
    })

def delete_wahana(request, slug_wahana):
    if not check_admin_access(request):
        return redirect('register_login:login')

    wahana = next((a for a in WAHANA if slugify(a['nama_wahana']) == slug_wahana), None)
    if not wahana:
        return HttpResponseNotFound("Wahana tidak ditemukan.")
    WAHANA.remove(wahana)
    return redirect('biru:list_wahana')

def buat_reservasi_atraksi(request):
    global RESERVASI_ID
    if not check_visitor_admin_access(request):
        return redirect('register_login:login')

    if request.method == 'POST':
        # Process form submission
        atraksi_idx = int(request.POST.get('atraksi'))
        username = request.session.get('user', {}).get('username')
        tanggal = request.POST.get('tanggal')
        jumlah_tiket = int(request.POST.get('jumlah_tiket'))

        selected_atraksi = ATRAKSI[atraksi_idx]

        # Create reservation
        reservasi = {
            'id': RESERVASI_ID,
            'atraksi': selected_atraksi['nama_atraksi'],
            'lokasi': selected_atraksi['lokasi'],
            'jam': selected_atraksi['jadwal'].strftime('%H:%M'),
            'tanggal': tanggal,
            'username': username,
            'jumlah_tiket': jumlah_tiket,
            'waktu_reservasi': datetime.now().strftime('%Y-%m-%d'),
            'status': 'Terjadwal'
        }

        RESERVASI.append(reservasi)
        RESERVASI_ID += 1
        return redirect('biru:detail_reservasi_atraksi', reservasi_id=reservasi['id'])

    # GET request - show form
    atraksi_options = []
    for idx, atraksi in enumerate(ATRAKSI):
        atraksi_options.append({
            'id': idx,
            'nama': atraksi['nama_atraksi'],
            'lokasi': atraksi['lokasi'],
            'jam': atraksi['jadwal'].strftime('%H:%M'),
            'kapasitas': atraksi['kapasitas']
        })

    context = {
        'atraksi_options': atraksi_options,
        'min_date': datetime.now().strftime('%Y-%m-%d')  # Today's date
    }
    return render(request, 'buat_reservasi_atraksi.html', context)

def detail_reservasi_atraksi(request, reservasi_id):
    if not check_visitor_admin_access(request):
        return redirect('register_login:login')

    reservasi = next((r for r in RESERVASI if r['id'] == reservasi_id), None)
    if not reservasi:
        return redirect('biru:buat_reservasi_atraksi')

    return render(request, 'detail_reservasi_atraksi.html', {'reservasi': reservasi})

def edit_reservasi_atraksi(request, reservasi_id):
    if not check_visitor_admin_access(request):
        return redirect('register_login:login')

    reservasi = next((r for r in RESERVASI if r['id'] == reservasi_id), None)
    if not reservasi:
        return redirect('biru:buat_reservasi_atraksi')

    if request.method == 'POST':
        atraksi_idx = int(request.POST.get('atraksi'))
        tanggal = request.POST.get('tanggal')
        jumlah_tiket = int(request.POST.get('jumlah_tiket'))

        selected_atraksi = ATRAKSI[atraksi_idx]

        # Update reservasi
        reservasi.update({
            'atraksi': selected_atraksi['nama_atraksi'],
            'lokasi': selected_atraksi['lokasi'],
            'jam': selected_atraksi['jadwal'].strftime('%H:%M'),
            'tanggal': tanggal,
            'jumlah_tiket': jumlah_tiket,
        })

        return redirect('biru:detail_reservasi_atraksi', reservasi_id=reservasi['id'])

    # GET request - pre-fill form
    atraksi_options = []
    selected_idx = 0
    for idx, atraksi in enumerate(ATRAKSI):
        atraksi_options.append({
            'id': idx,
            'nama': atraksi['nama_atraksi'],
            'lokasi': atraksi['lokasi'],
            'jam': atraksi['jadwal'].strftime('%H:%M'),
            'kapasitas': atraksi['kapasitas']
        })
        if atraksi['nama_atraksi'] == reservasi['atraksi']:
            selected_idx = idx

    context = {
        'atraksi_options': atraksi_options,
        'min_date': datetime.now().strftime('%Y-%m-%d'),
        'edit': True,
        'reservasi': reservasi,
        'selected_idx': selected_idx
    }
    return render(request, 'edit_reservasi_atraksi.html', context)

def cancel_reservasi_atraksi(request, reservasi_id):
    if not check_visitor_admin_access(request):
        return redirect('register_login:login')

    reservasi = next((r for r in RESERVASI if r['id'] == reservasi_id), None)
    if not reservasi:
        return HttpResponseNotFound("Reservasi tidak ditemukan.")
    reservasi['status'] = 'Dibatalkan'
    return redirect('register_login:dashboard')

def list_reservasi(request):
    if not check_admin_access(request):
        return redirect('register_login:login')

    return render(request, 'list_reservasi.html', {'reservasi_list': RESERVASI})

def delete_reservasi_atraksi(request, reservasi_id):
    if not check_admin_access(request):
        return redirect('register_login:login')

    reservasi = next((r for r in RESERVASI if r['id'] == reservasi_id), None)
    if not reservasi:
        return HttpResponseNotFound("Reservasi tidak ditemukan.")
    RESERVASI.remove(reservasi)
    return redirect('biru:list_reservasi')

def edit_reservasi_atraksi_admin(request, reservasi_id):
    if not check_admin_access(request):
        return redirect('register_login:login')

    reservasi = next((r for r in RESERVASI if r['id'] == reservasi_id), None)
    if not reservasi:
        return redirect('biru:list_reservasi')

    if request.method == 'POST':
        atraksi_idx = int(request.POST.get('atraksi'))
        tanggal = request.POST.get('tanggal')
        jumlah_tiket = int(request.POST.get('jumlah_tiket'))

        selected_atraksi = ATRAKSI[atraksi_idx]

        # Update reservasi
        reservasi.update({
            'atraksi': selected_atraksi['nama_atraksi'],
            'lokasi': selected_atraksi['lokasi'],
            'jam': selected_atraksi['jadwal'].strftime('%H:%M'),
            'tanggal': tanggal,
            'jumlah_tiket': jumlah_tiket,
        })

        return redirect('biru:list_reservasi')

    # GET request - pre-fill form
    atraksi_options = []
    selected_idx = 0
    for idx, atraksi in enumerate(ATRAKSI):
        atraksi_options.append({
            'id': idx,
            'nama': atraksi['nama_atraksi'],
            'lokasi': atraksi['lokasi'],
            'jam': atraksi['jadwal'].strftime('%H:%M'),
            'kapasitas': atraksi['kapasitas']
        })
        if atraksi['nama_atraksi'] == reservasi['atraksi']:
            selected_idx = idx

    context = {
        'atraksi_options': atraksi_options,
        'min_date': datetime.now().strftime('%Y-%m-%d'),
        'edit': True,
        'reservasi': reservasi,
        'selected_idx': selected_idx
    }
    return render(request, 'edit_reservasi_atraksi_admin.html', context)