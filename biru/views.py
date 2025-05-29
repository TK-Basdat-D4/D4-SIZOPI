from django.http import HttpResponseNotFound
from django.shortcuts import render, redirect
from django.utils.text import slugify
from django.contrib import messages
from datetime import datetime
from utils.db_utils import get_db_connection

# Dummy Data
HEWAN = ['Anjing Laut', 'Gajah Sumatera', 'Burung Kakaktua', 'Lumba-lumba', 'Singa', 'Harimau', 'Beruang']
PELATIH = ['Andi', 'Siti', 'Budi', 'Rina', 'Danu', 'Tomi', 'Rini', 'Bobi']
STATUS = ['Terjadwal', 'Dibatalkan', 'Selesai']

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
    """Check if user is a logged-in admin"""
    if 'user' not in request.session:
        messages.error(request, 'Silahkan login terlebih dahulu!')
        return False

    current_user = request.session['user']
    if current_user.get('peran') != 'staff_administrasi':
        messages.error(request, 'Anda tidak memiliki akses ke halaman ini!')
        return False
    return True

def check_visitor_admin_access(request):
    """Check if user is a logged-in visitor or admin"""
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

    return render(request, 'list_atraksi.html', {'atraksi_list': get_list_atraksi()})

def tambah_atraksi(request):
    if not check_admin_access(request):
        return redirect('register_login:login')

    if request.method == 'POST':
        nama_atraksi = request.POST.get('nama_atraksi')
        lokasi = request.POST.get('lokasi')
        kapasitas = int(request.POST.get('kapasitas'))
        jadwal_str = request.POST.get('jadwal')
        jadwal = datetime.strptime(jadwal_str, "%Y-%m-%dT%H:%M")
        hewan_terlibat = request.POST.getlist('hewan_terlibat')
        pelatih_list = request.POST.getlist('pelatih')

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "INSERT INTO FASILITAS VALUES (%s, %s, %s)",
            (nama_atraksi, jadwal, kapasitas)
        )

        cursor.execute(
            "INSERT INTO ATRAKSI VALUES (%s, %s)",
            (nama_atraksi, lokasi)
        )

        for pelatih in pelatih_list:
            cursor.execute(
                "INSERT INTO JADWAL_PENUGASAN VALUES (%s, %s, %s)",
                (pelatih, datetime.now(), nama_atraksi)
            )

        for hewan in hewan_terlibat:
            cursor.execute(
                "INSERT INTO BERPARTISIPASI VALUES (%s, %s)",
                (nama_atraksi, hewan)
            )

        connection.commit()
        cursor.close()
        connection.close()

        return redirect('biru:list_atraksi')

    return render(request, 'tambah_atraksi.html', {'hewan': get_dict_hewan(), 'pelatih': get_dict_pelatih()})

def edit_atraksi(request, slug_atraksi):
    if not check_admin_access(request):
        return redirect('register_login:login')

    connection = get_db_connection()
    cursor = connection.cursor()
    nama_atraksi = slug_atraksi.replace('-',' ')

    cursor.execute("""
    SELECT
        a.nama_atraksi,
        a.lokasi,
        f.kapasitas_max,
        f.jadwal,
        STRING_AGG(DISTINCT h.nama || ' - ' || h.spesies, ', ') AS nama_hewan,
        STRING_AGG(DISTINCT p.nama_depan || ' ' || p.nama_belakang, ', ') AS petugas
    FROM ATRAKSI a
    JOIN FASILITAS f ON f.nama = a.nama_atraksi
    JOIN JADWAL_PENUGASAN jp ON jp.nama_atraksi = a.nama_atraksi
    JOIN PENGGUNA p ON p.username = jp.username_lh
    JOIN BERPARTISIPASI b ON b.nama_fasilitas = a.nama_atraksi
    JOIN HEWAN h ON h.id = b.id_hewan
    WHERE a.nama_atraksi ILIKE %s
    GROUP BY
        a.nama_atraksi,
        a.lokasi,
        f.kapasitas_max,
        f.jadwal
    """, (nama_atraksi,))

    result = cursor.fetchone()

    atraksi = {
        'nama_atraksi': result[0],
        'lokasi': result[1],
        'kapasitas': result[2],
        'jadwal': result[3],
        'hewan_terlibat': result[4].split(', '),
        'pelatih': result[5].split(', ')
    }

    if request.method == 'POST':
        kapasitas_baru = int(request.POST.get('kapasitas'))
        jadwal_str = request.POST.get('jadwal')
        jadwal_baru = datetime.strptime(jadwal_str, "%Y-%m-%dT%H:%M")

        cursor.execute("""
        UPDATE FASILITAS
        SET kapasitas_max = %s,
            jadwal = %s
        WHERE nama = %s
        """, (kapasitas_baru, jadwal_baru, result[0]))

        connection.commit()
        cursor.close()
        connection.close()
        return redirect('biru:list_atraksi')

    cursor.close()
    connection.close()

    return render(request, 'edit_atraksi.html', {
        'atraksi': atraksi,
        'hewan': get_dict_hewan(),
        'pelatih': get_dict_pelatih(),
    })

def delete_atraksi(request, slug_atraksi):
    if not check_admin_access(request):
        return redirect('register_login:login')

    connection = get_db_connection()
    cursor = connection.cursor()
    nama_atraksi = slug_atraksi.replace('-',' ')

    cursor.execute("""
    DELETE FROM FASILITAS
    WHERE nama ILIKE %s
    """, (nama_atraksi,))

    connection.commit()
    cursor.close()
    connection.close()

    return redirect('biru:list_atraksi')

def list_wahana(request):
    if not check_admin_access(request):
        return redirect('register_login:login')

    return render(request, 'list_wahana.html', {'wahana_list': get_list_wahana()})

def tambah_wahana(request):
    if not check_admin_access(request):
        return redirect('register_login:login')

    if request.method == 'POST':
        nama_wahana = request.POST.get('nama_wahana')
        kapasitas = int(request.POST.get('kapasitas'))
        jadwal_str = request.POST.get('jadwal')
        jadwal = datetime.strptime(jadwal_str, "%Y-%m-%dT%H:%M")
        peraturan_list = request.POST.getlist('peraturan')
        peraturan = ', '.join(peraturan_list)

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "INSERT INTO FASILITAS VALUES (%s, %s, %s)",
            (nama_wahana, jadwal, kapasitas)
        )

        cursor.execute(
            "INSERT INTO WAHANA VALUES (%s, %s)",
            (nama_wahana, peraturan)
        )

        connection.commit()
        cursor.close()
        connection.close()

        return redirect('biru:list_wahana')

    return render(request, 'tambah_wahana.html')

def edit_wahana(request, slug_wahana):
    if not check_admin_access(request):
        return redirect('register_login:login')

    connection = get_db_connection()
    cursor = connection.cursor()
    nama_wahana = slug_wahana.replace('-',' ')

    cursor.execute("""
    SELECT
        w.nama_wahana,
        f.kapasitas_max,
        f.jadwal,
        w.peraturan
    FROM WAHANA w
    JOIN FASILITAS f ON f.nama = w.nama_wahana
    WHERE w.nama_wahana ILIKE %s
    """, (nama_wahana,))

    result = cursor.fetchone()

    wahana = {
        'nama_wahana': result[0],
        'kapasitas': result[1],
        'jadwal': result[2],
        'peraturan': result[3]
    }

    if request.method == 'POST':
        kapasitas_baru = int(request.POST.get('kapasitas'))
        jadwal_str = request.POST.get('jadwal')
        jadwal_baru = datetime.strptime(jadwal_str, "%Y-%m-%dT%H:%M")

        cursor.execute("""
        UPDATE FASILITAS
        SET kapasitas_max = %s,
            jadwal = %s
        WHERE nama = %s
        """, (kapasitas_baru, jadwal_baru, result[0]))

        connection.commit()
        cursor.close()
        connection.close()
        return redirect('biru:list_wahana')

    cursor.close()
    connection.close()

    return render(request, 'edit_wahana.html', {
        'wahana': wahana,
    })

def delete_wahana(request, slug_wahana):
    if not check_admin_access(request):
        return redirect('register_login:login')

    connection = get_db_connection()
    cursor = connection.cursor()
    nama_wahana = slug_wahana.replace('-',' ')

    cursor.execute("""
    DELETE FROM FASILITAS
    WHERE nama ILIKE %s
    """, (nama_wahana,))

    connection.commit()
    cursor.close()
    connection.close()

    return redirect('biru:list_wahana')

def buat_reservasi_atraksi(request, slug_reservasi):
    if not check_visitor_admin_access(request):
        return redirect('register_login:login')

    connection = get_db_connection()
    cursor = connection.cursor()
    nama_atraksi = slug_reservasi.replace('-',' ')
    current_user = request.session['user']
    current_username = current_user.get('username')

    cursor.execute("""
    SELECT *
    FROM FASILITAS f
    JOIN ATRAKSI a ON a.nama_atraksi = f.nama
    WHERE f.nama ILIKE %s
    """, (nama_atraksi,))

    result = cursor.fetchone()

    atraksi = {
        'nama_atraksi': result[0],
        'lokasi': result[4],
        'jadwal': result[1]
    }

    if request.method == 'POST':
        jumlah_tiket = int(request.POST.get('jumlah_tiket'))

        try:
            cursor.execute(
                "INSERT INTO RESERVASI VALUES (%s, %s, CURRENT_DATE, %s, %s)",
                (current_username, result[0], jumlah_tiket, 'Terjadwal')
            )
            connection.commit()
            cursor.close()
            connection.close()
            return redirect('biru:list_reservasi')

        except Exception as e:
            msg_clean = str(e).split("CONTEXT:")[0].strip()
            messages.error(request, msg_clean)

    cursor.close()
    connection.close()

    return render(request, 'buat_reservasi_atraksi.html', {
        'atraksi': atraksi,
    })

def buat_reservasi_wahana(request, slug_reservasi):
    if not check_visitor_admin_access(request):
        return redirect('register_login:login')

    connection = get_db_connection()
    cursor = connection.cursor()
    nama_wahana = slug_reservasi.replace('-',' ')
    current_user = request.session['user']
    current_username = current_user.get('username')

    cursor.execute("""
    SELECT *
    FROM FASILITAS f
    JOIN WAHANA w ON w.nama_wahana = f.nama
    WHERE f.nama ILIKE %s
    """, (nama_wahana,))

    result = cursor.fetchone()

    wahana = {
        'nama_wahana': result[0],
        'jadwal': result[1],
        'peraturan': result[4].split(", ")
    }

    if request.method == 'POST':
        jumlah_tiket = int(request.POST.get('jumlah_tiket'))

        try:
            cursor.execute(
                "INSERT INTO RESERVASI VALUES (%s, %s, CURRENT_DATE, %s, %s)",
                (current_username, result[0], jumlah_tiket, 'Terjadwal')
            )
            connection.commit()
            cursor.close()
            connection.close()
            return redirect('biru:list_reservasi')

        except Exception as e:
            msg_clean = str(e).split("CONTEXT:")[0].strip()
            messages.error(request, msg_clean)

    cursor.close()
    connection.close()

    return render(request, 'buat_reservasi_wahana.html', {
        'wahana': wahana,
    })

def list_reservasi(request):
    if not check_visitor_admin_access(request):
        return redirect('register_login:login')

    connection = get_db_connection()
    cursor = connection.cursor()
    current_user = request.session['user']
    current_username = current_user.get('username')

    cursor.execute("""
    SELECT *
    FROM RESERVASI r
    JOIN FASILITAS f ON f.nama = r.nama_fasilitas
    WHERE r.username_p = %s
    ORDER BY tanggal_kunjungan;
    """, (current_username,))

    result = cursor.fetchall()

    cursor.close()
    connection.close()

    reservasi_list = []
    for row in result:
        reservasi = {
            'jenis_reservasi': get_jenis_reservasi(row[1]),
            'nama_fasilitas': row[1],
            'tanggal_reservasi': row[6],
            'jumlah_tiket': row[3],
            'status': row[4],
            'slug': create_reservasi_slug(row[0], row[1], row[2])
        }
        reservasi_list.append(reservasi)

    return render(request, 'list_reservasi.html', {'reservasi_list': reservasi_list})

def list_data_reservasi(request):
    if not check_visitor_admin_access(request):
        return redirect('register_login:login')

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
    SELECT f.nama, f.jadwal, f.kapasitas_max, COALESCE(SUM(r.jumlah_tiket), 0) AS jumlah_reservasi
    FROM FASILITAS f
    LEFT JOIN RESERVASI r ON r.nama_fasilitas = f.nama
    WHERE f.jadwal > '2025-05-11 09:00:00'
    GROUP BY f.nama, f.jadwal, f.kapasitas_max
    ORDER BY f.jadwal;
    """)
    # JANGAN LUPA GANTI JADWAL JADI CURRENT_TIME SETELAH KELAR BENERIN DB

    result = cursor.fetchall()

    cursor.close()
    connection.close()

    fasilitas_list = []
    for row in result:
        kapasitas_tersisa = row[2] - row[3]
        fasilitas = {
            'jenis_reservasi': get_jenis_reservasi(row[0]),
            'nama_fasilitas': row[0],
            'tanggal_reservasi': row[1],
            'kapasitas_total': row[2],
            'kapasitas_tersisa': kapasitas_tersisa,
            'slug': slugify(row[0])
        }
        fasilitas_list.append(fasilitas)

    return render(request, 'list_data_reservasi.html', {'fasilitas_list': fasilitas_list})

def detail_reservasi(request, slug_reservasi):
    if not check_visitor_admin_access(request):
        return redirect('register_login:login')

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
    SELECT r.nama_fasilitas, f.jadwal, r.jumlah_tiket, a.lokasi, w.peraturan
    FROM RESERVASI r
    JOIN FASILITAS f ON f.nama = r.nama_fasilitas
    LEFT JOIN ATRAKSI a ON a.nama_atraksi = f.nama
    LEFT JOIN WAHANA w ON w.nama_wahana = w.nama_wahana
    WHERE username_p ILIKE %s
    AND nama_fasilitas ILIKE %s
    AND tanggal_kunjungan = %s;
    """, (parse_reservasi_slug(slug_reservasi)))

    result = cursor.fetchone()

    if get_jenis_reservasi(result[0]) == "atraksi":
        reservasi = {
            'jenis_reservasi': 'atraksi',
            'nama_atraksi': result[0],
            'lokasi': result[3],
            'tanggal_reservasi': result[1],
            'jumlah_tiket': result[2],
            'slug': slug_reservasi,
        }
    else:
        reservasi = {
            'jenis_reservasi': 'wahana',
            'nama_atraksi': result[0],
            'peraturan': result[4].split(", "),
            'tanggal_reservasi': result[1],
            'jumlah_tiket': result[2],
            'slug': slug_reservasi,
        }

    cursor.close()
    connection.close()

    return render(request, 'detail_reservasi.html', {'reservasi': reservasi})

def edit_reservasi_atraksi_list(request, slug_reservasi):
    if not check_visitor_admin_access(request):
        return redirect('register_login:login')

    connection = get_db_connection()
    cursor = connection.cursor()
    parse_reservasi = parse_reservasi_slug(slug_reservasi)

    cursor.execute("""
    SELECT r.nama_fasilitas, a.lokasi, f.jadwal, r.jumlah_tiket
    FROM RESERVASI r
    JOIN FASILITAS f ON f.nama = r.nama_fasilitas
    JOIN ATRAKSI a ON a.nama_atraksi = r.nama_fasilitas
    WHERE r.username_p ILIKE %s
    AND r.nama_fasilitas ILIKE %s
    AND r.tanggal_kunjungan = %s
    """, parse_reservasi)

    result = cursor.fetchone()

    atraksi = {
        'nama_atraksi': result[0],
        'lokasi': result[1],
        'jadwal': result[2],
        'jumlah_tiket': result[3]
    }

    if request.method == 'POST':
        jumlah_tiket = int(request.POST.get('jumlah_tiket'))

        cursor.execute("""
        UPDATE RESERVASI
        SET jumlah_tiket = %s
        WHERE username_p ILIKE %s
        AND nama_fasilitas ILIKE %s
        AND tanggal_kunjungan = %s;
        """, (jumlah_tiket, parse_reservasi[0], parse_reservasi[1], parse_reservasi[2]))

        connection.commit()
        cursor.close()
        connection.close()
        return redirect('biru:list_reservasi')

    cursor.close()
    connection.close()

    return render(request, 'edit_reservasi_atraksi_list.html', {
        'atraksi': atraksi,
    })

def edit_reservasi_wahana_list(request, slug_reservasi):
    if not check_visitor_admin_access(request):
        return redirect('register_login:login')

    connection = get_db_connection()
    cursor = connection.cursor()
    parse_reservasi = parse_reservasi_slug(slug_reservasi)

    cursor.execute("""
    SELECT r.nama_fasilitas, w.peraturan, f.jadwal, r.jumlah_tiket
    FROM RESERVASI r
    JOIN FASILITAS f ON f.nama = r.nama_fasilitas
    JOIN WAHANA w ON w.nama_wahana = r.nama_fasilitas
    WHERE r.username_p ILIKE %s
    AND r.nama_fasilitas ILIKE %s
    AND r.tanggal_kunjungan = %s
    """, parse_reservasi)

    result = cursor.fetchone()

    wahana = {
        'nama_wahana': result[0],
        'peraturan': result[1].split(", "),
        'jadwal': result[2],
        'jumlah_tiket': result[3]
    }

    if request.method == 'POST':
        jumlah_tiket = int(request.POST.get('jumlah_tiket'))

        cursor.execute("""
        UPDATE RESERVASI
        SET jumlah_tiket = %s
        WHERE username_p ILIKE %s
        AND nama_fasilitas ILIKE %s
        AND tanggal_kunjungan = %s;
        """, (jumlah_tiket, parse_reservasi[0], parse_reservasi[1], parse_reservasi[2]))

        connection.commit()
        cursor.close()
        connection.close()
        return redirect('biru:list_reservasi')

    cursor.close()
    connection.close()

    return render(request, 'edit_reservasi_wahana_list.html', {
        'wahana': wahana,
    })

def cancel_reservasi_detail(request, slug_reservasi):
    if not check_visitor_admin_access(request):
        return redirect('register_login:login')

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
    UPDATE RESERVASI
    SET status = 'Dibatalkan', jumlah_tiket = '0'
    WHERE username_p ILIKE %s
    AND nama_fasilitas ILIKE %s
    AND tanggal_kunjungan = %s;
    """, (parse_reservasi_slug(slug_reservasi)))

    connection.commit()
    cursor.close()
    connection.close()

    return redirect('register_login:dashboard')

def cancel_reservasi_list(request, slug_reservasi):
    if not check_visitor_admin_access(request):
        return redirect('register_login:login')

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
    UPDATE RESERVASI
    SET status = 'Dibatalkan', jumlah_tiket = '0'
    WHERE username_p ILIKE %s
    AND nama_fasilitas ILIKE %s
    AND tanggal_kunjungan = %s;
    """, (parse_reservasi_slug(slug_reservasi)))

    connection.commit()
    cursor.close()
    connection.close()

    return redirect('biru:list_reservasi')

def list_reservasi_admin(request):
    if not check_admin_access(request):
        return redirect('register_login:login')

    reservasi_list = get_list_reservasi()
    return render(request, 'list_reservasi_admin.html', {'reservasi_list': reservasi_list})

def cancel_reservasi_admin(request, slug_reservasi):
    if not check_admin_access(request):
        return redirect('register_login:login')

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
    UPDATE RESERVASI
    SET status = 'Dibatalkan'
    WHERE username_p ILIKE %s
    AND nama_fasilitas ILIKE %s
    AND tanggal_kunjungan = %s;
    """, (parse_reservasi_slug(slug_reservasi)))

    connection.commit()
    cursor.close()
    connection.close()

    return redirect('biru:list_reservasi_admin')

def edit_reservasi_atraksi_admin(request, slug_reservasi):
    if not check_admin_access(request):
        return redirect('register_login:login')

    connection = get_db_connection()
    cursor = connection.cursor()
    parse_reservasi = parse_reservasi_slug(slug_reservasi)
    username = parse_reservasi[0]
    nama_atraksi = parse_reservasi[1]
    tanggal_kunjungan = parse_reservasi[2]

    cursor.execute("""
    SELECT *
    FROM RESERVASI r
    JOIN FASILITAS f ON f.nama = r.nama_fasilitas
    WHERE r.username_p ILIKE %s
    AND r.nama_fasilitas ILIKE %s
    AND r.tanggal_kunjungan = %s
    ORDER BY tanggal_kunjungan;
    """, parse_reservasi)

    result = cursor.fetchone()
    reservasi = {
        'username': result[0],
        'jenis_reservasi': get_jenis_reservasi(result[1]),
        'nama_fasilitas': result[1],
        'tanggal_reservasi': result[6],
        'jumlah_tiket': result[3],
        'status': result[4],
        'slug': create_reservasi_slug(result[0], result[1], result[2])
    }

    if request.method == 'POST':
        nama_atraksi_baru = request.POST.get('atraksi')
        jumlah_tiket = int(request.POST.get('jumlah_tiket'))

        # UPDATE database
        cursor.execute("""
        UPDATE RESERVASI
        SET nama_fasilitas = %s, jumlah_tiket = %s
        WHERE username_p ILIKE %s
        AND nama_fasilitas ILIKE %s
        AND tanggal_kunjungan = %s;
        """, (nama_atraksi_baru, jumlah_tiket, username, nama_atraksi, tanggal_kunjungan))

        connection.commit()
        cursor.close()
        connection.close()
        return redirect('biru:list_reservasi_admin')

    cursor.close()
    connection.close()

    return render(request, 'edit_reservasi_atraksi_admin.html', {
        'atraksi_list': get_list_atraksi(),
        'reservasi': reservasi,
        'selected_atraksi': reservasi['nama_fasilitas']
    })

def edit_reservasi_wahana_admin(request, slug_reservasi):
    if not check_admin_access(request):
        return redirect('register_login:login')

    connection = get_db_connection()
    cursor = connection.cursor()
    parse_reservasi = parse_reservasi_slug(slug_reservasi)
    username = parse_reservasi[0]
    nama_wahana = parse_reservasi[1]
    tanggal_kunjungan = parse_reservasi[2]

    cursor.execute("""
    SELECT *
    FROM RESERVASI r
    JOIN WAHANA w ON w.nama_wahana = r.nama_fasilitas
    WHERE r.username_p ILIKE %s
    AND r.nama_fasilitas ILIKE %s
    AND r.tanggal_kunjungan = %s
    ORDER BY tanggal_kunjungan;
    """, parse_reservasi)

    result = cursor.fetchone()
    reservasi = {
        'username': result[0],
        'jenis_reservasi': get_jenis_reservasi(result[1]),
        'nama_wahana': result[1],
        'tanggal_reservasi': result[6],
        'jumlah_tiket': result[3],
        'status': result[4],
        'slug': create_reservasi_slug(result[0], result[1], result[2])
    }

    if request.method == 'POST':
        nama_wahana_baru = request.POST.get('wahana')
        jumlah_tiket = int(request.POST.get('jumlah_tiket'))

        # UPDATE database
        cursor.execute("""
            UPDATE RESERVASI
            SET nama_fasilitas = %s, jumlah_tiket = %s
            WHERE username_p ILIKE %s
            AND nama_fasilitas ILIKE %s
            AND tanggal_kunjungan = %s;
        """, (nama_wahana_baru, jumlah_tiket, username, nama_wahana, tanggal_kunjungan))

        connection.commit()
        cursor.close()
        connection.close()

        return redirect('biru:list_reservasi_admin')

    cursor.close()
    connection.close()

    return render(request, 'edit_reservasi_wahana_admin.html', {
        'wahana_list': get_list_wahana(),
        'reservasi': reservasi,
        'selected_wahana': reservasi['nama_wahana']
    })

def get_dict_hewan():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
    SELECT
        id, nama, spesies
    FROM HEWAN
    ORDER BY spesies, nama;
    """)
    result = cursor.fetchall()

    hewan_dict = {}
    for row in result:
        nama_spesies = f'{row[1]} - {row[2]}'
        hewan_dict[row[0]] = nama_spesies

    cursor.close()
    connection.close()

    return hewan_dict

def get_dict_pelatih():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
    SELECT
        lh.username_lh AS username,
        p.nama_depan || ' ' || p.nama_belakang AS petugas
    FROM pelatih_hewan lh
    JOIN pengguna p ON p.username = lh.username_lh
    ORDER BY lh.username_lh;
    """)
    result = cursor.fetchall()

    pelatih_dict = {}
    for row in result:
        pelatih_dict[row[0]] = row[1]

    cursor.close()
    connection.close()

    return pelatih_dict

def get_list_atraksi():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
    SELECT
        a.nama_atraksi,
        a.lokasi,
        f.kapasitas_max,
        f.jadwal,
        STRING_AGG(DISTINCT h.nama || ' - ' || h.spesies, ', ') AS nama_hewan,
        STRING_AGG(DISTINCT p.nama_depan || ' ' || p.nama_belakang, ', ') AS petugas
    FROM ATRAKSI a
    JOIN FASILITAS f ON f.nama = a.nama_atraksi
    JOIN JADWAL_PENUGASAN jp ON jp.nama_atraksi = a.nama_atraksi
    JOIN PENGGUNA p ON p.username = jp.username_lh
    JOIN BERPARTISIPASI b ON b.nama_fasilitas = a.nama_atraksi
    JOIN HEWAN h ON h.id = b.id_hewan
    GROUP BY
        a.nama_atraksi,
        a.lokasi,
        f.kapasitas_max,
        f.jadwal
    ORDER BY
        f.jadwal;
    """)

    result = cursor.fetchall()

    cursor.close()
    connection.close()

    atraksi_list = []
    for row in result:
        atraksi = {
            'nama_atraksi': row[0],
            'lokasi': row[1],
            'kapasitas': row[2],
            'jadwal': row[3],
            'hewan_terlibat': row[4].split(', '),
            'pelatih': row[5].split(', '),
            'slug': slugify(row[0])
        }
        atraksi_list.append(atraksi)

    return atraksi_list

def get_list_wahana():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
    SELECT
        w.nama_wahana,
        f.kapasitas_max,
        f.jadwal,
        w.peraturan
    FROM WAHANA w
    JOIN FASILITAS f ON f.nama = w.nama_wahana
    ORDER BY
        f.jadwal;
    """)

    result = cursor.fetchall()

    cursor.close()
    connection.close()

    wahana_list = []
    for row in result:
        wahana = {
            'nama_wahana': row[0],
            'kapasitas': row[1],
            'jadwal': row[2],
            'peraturan': row[3].split(', '),
            'slug': slugify(row[0])
        }
        wahana_list.append(wahana)

    return wahana_list

def get_list_reservasi():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
    SELECT *
    FROM RESERVASI r
    JOIN FASILITAS f ON f.nama = r.nama_fasilitas
    ORDER BY tanggal_kunjungan;
    """)

    result = cursor.fetchall()

    cursor.close()
    connection.close()

    reservasi_list = []
    for row in result:
        reservasi = {
            'username': row[0],
            'jenis_reservasi': get_jenis_reservasi(row[1]),
            'nama_fasilitas': row[1],
            'tanggal_reservasi': row[6],
            'jumlah_tiket': row[3],
            'status': row[4],
            'slug': create_reservasi_slug(row[0], row[1], row[2])
        }
        reservasi_list.append(reservasi)

    return reservasi_list

def get_jenis_reservasi(nama_fasilitas):
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
        SELECT *
        FROM ATRAKSI
        WHERE nama_atraksi = %s
        """, (nama_fasilitas,))

        if cursor.fetchone():
            cursor.close()
            connection.close()
            return "atraksi"

        cursor.close()
        connection.close()
        return "wahana"

def create_reservasi_slug(username, nama_fasilitas, tanggal_kunjungan):
    username_slug = username.replace(".", "-")
    nama_fasilitas_slug = slugify(nama_fasilitas)
    tanggal_kunjungan_slug = tanggal_kunjungan.strftime('%Y-%m-%d')
    return slugify(f"{username_slug} -oxo- {nama_fasilitas_slug} -oxo- {tanggal_kunjungan_slug}")

def parse_reservasi_slug(reservasi_slug):
    reservasi_content = reservasi_slug.split("-oxo-")
    parse_username = reservasi_content[0].replace("-", ".")
    parse_nama_fasilitas = reservasi_content[1].replace("-", " ")
    parse_tanggal_kunjungan = datetime.strptime(reservasi_content[2], '%Y-%m-%d').date()
    return [parse_username, parse_nama_fasilitas, parse_tanggal_kunjungan]

def get_jumlah_penjualan():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
    SELECT COALESCE(SUM(jumlah_tiket), 0) AS total_tiket
    FROM RESERVASI
    WHERE tanggal_kunjungan = CURRENT_DATE;
    """)

    jumlah_penjualan = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return jumlah_penjualan

def get_jumlah_pengunjung():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
    SELECT COUNT(*) AS jumlah_pengunjung
    FROM RESERVASI
    WHERE tanggal_kunjungan = CURRENT_DATE;
    """)

    jumlah_pengunjung = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return jumlah_pengunjung