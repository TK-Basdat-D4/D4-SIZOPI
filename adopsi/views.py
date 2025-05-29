from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.urls import reverse
from django.http import HttpResponseRedirect
from utils.db_utils import get_db_connection
from django.db import connection
from datetime import date, timedelta
from django.http import Http404
from django.utils.dateformat import DateFormat

def admin_daftar_pengunjung(request):
    connect = get_db_connection()
    cursor = connect.cursor()
    cursor.execute("SET search_path TO sizopi")

    # Ambil semua pengunjung
    cursor.execute("""
        SELECT pg.username, pg.nama_depan || ' ' || COALESCE(pg.nama_tengah || ' ', '') || pg.nama_belakang AS nama
        FROM PENGGUNA pg
        JOIN PENGUNJUNG pj ON pg.username = pj.username_p
    """)
    semua_pengunjung = cursor.fetchall()

    # Ambil semua adopter (dari INDIVIDU atau ORGANISASI)
    cursor.execute("""
        SELECT pg.username,
               COALESCE(i.nama, o.nama_organisaasi) AS nama_adopter,
               CASE 
                   WHEN i.id_adopter IS NOT NULL THEN 'Individu'
                   WHEN o.id_adopter IS NOT NULL THEN 'Organisasi'
               END AS tipe_adopter
        FROM PENGGUNA pg
        JOIN PENGUNJUNG pj ON pg.username = pj.username_p
        JOIN ADOPTER a ON pj.username_p = a.username_adopter
        LEFT JOIN INDIVIDU i ON a.id_adopter = i.id_adopter
        LEFT JOIN ORGANISASI o ON a.id_adopter = o.id_adopter
    """)
    hasil_adopter = cursor.fetchall()

    cursor.close()
    connect.close()

    # Olah hasil jadi list of dict
    adopter_usernames = set()
    pengunjung_adopter = []
    for row in hasil_adopter:
        pengunjung_adopter.append({
            'username': row[0],
            'nama_adopter': row[1],
            'tipe_adopter': row[2]
        })
        adopter_usernames.add(row[0])

    pengunjung_biasa = []
    for row in semua_pengunjung:
        if row[0] not in adopter_usernames:
            pengunjung_biasa.append({
                'username': row[0],
                'nama': row[1]
            })

    context = {
        'pengunjung_biasa': pengunjung_biasa,
        'pengunjung_adopter': pengunjung_adopter
    }

    return render(request, 'adopsi/admin_daftar_pengunjung.html', context)

def admin_tambah_pengunjung(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        nama_depan = request.POST.get('nama_depan')
        nama_tengah = request.POST.get('nama_tengah') or None
        nama_belakang = request.POST.get('nama_belakang')
        no_telepon = request.POST.get('no_telepon')
        alamat = request.POST.get('alamat')
        tgl_lahir = request.POST.get('tgl_lahir')

        connect = get_db_connection()
        cursor = connect.cursor()

        cursor.execute("SET search_path TO sizopi")

        # Cek apakah username sudah ada
        cursor.execute("SELECT 1 FROM PENGGUNA WHERE username = %s", [username])
        if cursor.fetchone():
            messages.error(request, 'Username sudah digunakan.')
            cursor.close()
            connect.close()
            return render(request, 'adopsi/admin_tambah_pengunjung.html')

        # Insert ke PENGGUNA
        cursor.execute("""
            INSERT INTO PENGGUNA (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, [username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon])

        # Insert ke PENGUNJUNG
        cursor.execute("""
            INSERT INTO PENGUNJUNG (username_p, alamat, tgl_lahir)
            VALUES (%s, %s, %s)
        """, [username, alamat, tgl_lahir])

        connect.commit()
        cursor.close()
        connect.close()

        messages.success(request, 'Pengunjung berhasil ditambahkan.')
        return redirect(reverse('adopsi:admin_daftar_pengunjung'))

    return render(request, 'adopsi/admin_tambah_pengunjung.html')

def admin_program_adopsi(request):
    connect = get_db_connection()
    cursor = connect.cursor()

    cursor.execute("SET search_path TO sizopi")

    cursor.execute("""
        SELECT
            H.id,
            H.nama,
            H.spesies,
            H.status_kesehatan,
            H.url_foto,
            EXISTS (
                SELECT 1
                FROM SIZOPI.ADOPSI AD2
                WHERE AD2.id_hewan = H.id
                AND CURRENT_DATE >= AD2.tgl_mulai_adopsi
                AND CURRENT_DATE < AD2.tgl_berhenti_adopsi
            ) AS is_diadopsi
        FROM SIZOPI.HEWAN H
    """)

    raw_hewan_list = cursor.fetchall()
    columns = [col[0] for col in cursor.description]

    cursor.close()
    connect.close()

    hewan_list = []
    for row in raw_hewan_list:
        row_dict = dict(zip(columns, row))
        hewan_list.append({
            'id': row_dict['id'],
            'nama': row_dict['nama'],
            'spesies': row_dict['spesies'],
            'kondisi': row_dict['status_kesehatan'],
            'foto': row_dict['url_foto'],
            'status_adopsi': 'Diadopsi' if row_dict['is_diadopsi'] else 'Tidak Diadopsi'
        })

    context = {
        'daftar_hewan': hewan_list
    }
    return render(request, 'adopsi/admin_program_adopsi.html', context)

def admin_detail_adopsi(request, id_hewan):
    connect = get_db_connection()
    cursor = connect.cursor()
    cursor.execute("SET search_path TO sizopi")

    # Ambil ID adopter berdasarkan hewan & adopsi aktif
    cursor.execute("""
        SELECT AD.id_adopter
        FROM ADOPSI AD
        WHERE AD.id_hewan = %s
        AND CURRENT_DATE BETWEEN AD.tgl_mulai_adopsi AND AD.tgl_berhenti_adopsi
    """, [str(id_hewan)])
    result = cursor.fetchone()
    if not result:
        cursor.close()
        connect.close()
        return render(request, '404.html')

    id_adopter = result[0]

    # Handle POST (update status pembayaran)
    if request.method == 'POST':
        new_status = request.POST.get('status_pembayaran')
        cursor.execute("""
            UPDATE ADOPSI
            SET status_pembayaran = %s
            WHERE id_hewan = %s
            AND CURRENT_DATE BETWEEN tgl_mulai_adopsi AND tgl_berhenti_adopsi
        """, [new_status, str(id_hewan)])
        connect.commit()
        
        cursor.execute("""
            SELECT COALESCE(i.nama, o.nama_organisaasi)
            FROM ADOPTER a
            LEFT JOIN INDIVIDU i ON a.id_adopter = i.id_adopter
            LEFT JOIN ORGANISASI o ON a.id_adopter = o.id_adopter
            WHERE a.id_adopter = %s
        """, [id_adopter])
        nama_adopter = cursor.fetchone()[0]

        messages.success(request, f'SUKSES: Total kontribusi adopter "{nama_adopter}" telah diperbarui.')

    # Ambil data detail adopsi
    cursor.execute("""
        SELECT
            H.id,
            H.nama,
            H.spesies,
            COALESCE(I.nama, O.nama_organisaasi) AS adopter,
            AD.tgl_mulai_adopsi AS tanggal_mulai,
            AD.tgl_berhenti_adopsi AS tanggal_akhir,
            AD.kontribusi_finansial AS nominal,
            AD.status_pembayaran
        FROM HEWAN H
        JOIN ADOPSI AD ON H.id = AD.id_hewan
        JOIN ADOPTER A ON AD.id_adopter = A.id_adopter
        LEFT JOIN INDIVIDU I ON A.id_adopter = I.id_adopter
        LEFT JOIN ORGANISASI O ON A.id_adopter = O.id_adopter
        WHERE H.id = %s
        AND CURRENT_DATE BETWEEN AD.tgl_mulai_adopsi AND AD.tgl_berhenti_adopsi
    """, [str(id_hewan)])
    row = cursor.fetchone()

    if not row:
        cursor.close()
        connect.close()
        return render(request, '404.html')

    columns = [col[0] for col in cursor.description]
    hewan = dict(zip(columns, row))

    # Hitung total kontribusi LUNAS untuk adopter ini
    # cursor.execute("""
    #     SELECT SUM(kontribusi_finansial)
    #     FROM ADOPSI
    #     WHERE id_adopter = %s AND status_pembayaran = 'lunas'
    # """, [id_adopter])
    # total_kontribusi = cursor.fetchone()[0] or 0
    # ini udah ada di trigger, tapi aku ttep adain

    # Ambil nilai total kontribusi yang sudah diupdate lewat trigger
    cursor.execute("SELECT total_kontribusi FROM ADOPTER WHERE id_adopter = %s", [id_adopter])
    total_kontribusi = cursor.fetchone()[0]

    cursor.close()
    connect.close()

    context = {
        'hewan': hewan,
        'total_kontribusi_adopter': total_kontribusi
    }
    return render(request, 'adopsi/admin_detail_adopsi.html', context)

def admin_form_adopsi(request, id_hewan):
    from django.db import DatabaseError
    username = request.session.get('username_adopter')
    tipe = request.session.get('tipe_adopter')

    if not username or not tipe:
        messages.error(request, 'Session adopter tidak ditemukan.')
        return redirect('adopsi:admin_program_adopsi')

    connect = get_db_connection()
    cursor = connect.cursor()
    cursor.execute("SET search_path TO sizopi")

    # Ambil info hewan
    cursor.execute("""
        SELECT nama, spesies 
        FROM HEWAN 
        WHERE id = %s
    """, [str(id_hewan)])
    row = cursor.fetchone()

    if not row:
        cursor.close()
        connect.close()
        return render(request, '404.html')

    nama_hewan, jenis_hewan = row

    # Ambil info user
    cursor.execute("""
        SELECT pg.nama_depan, pj.alamat, pg.no_telepon, pg.email
        FROM PENGGUNA pg
        JOIN PENGUNJUNG pj ON pg.username = pj.username_p
        WHERE pj.username_p = %s
    """, [username])
    user_data = cursor.fetchone()

    if not user_data:
        cursor.close()
        connect.close()
        messages.error(request, 'Data pengguna tidak ditemukan.')
        return redirect('adopsi:admin_program_adopsi')

    nama_depan, alamat, no_telepon, email = user_data

    if request.method == 'POST':
        nik_or_npp = request.POST.get('nik') or request.POST.get('npp')
        periode = request.POST.get('periode')
        nama_organisasi = request.POST.get('nama_organisasi')
        nominal = int(request.POST.get("nominal", 0))
        if nominal < 1000:
            messages.error(request, "Kontribusi minimal adalah Rp 1000.")
            return redirect('adopsi:admin_form_adopsi') 
        
        if not all([nik_or_npp, nominal, periode]):
            messages.error(request, 'Semua field wajib diisi.')
            return redirect(reverse('adopsi:admin_form_adopsi', args=[id_hewan]))

        try:
            cursor.execute("""
                SELECT id_adopter FROM ADOPTER WHERE username_adopter = %s
            """, [username])
            existing = cursor.fetchone()

            if existing:
                id_adopter = existing[0]
            else:
                # Kalau belum ada, baru insert
                cursor.execute("""
                    INSERT INTO ADOPTER (id_adopter, username_adopter, total_kontribusi)
                    VALUES (gen_random_uuid(), %s, 0)
                    RETURNING id_adopter
                """, [username])
                id_adopter = cursor.fetchone()[0]

                # Insert ke INDIVIDU / ORGANISASI
                if tipe == 'Individu':
                    cursor.execute("""
                        INSERT INTO INDIVIDU (id_adopter, nama, nik)
                        VALUES (%s, %s, %s)
                    """, [id_adopter, nama_depan, nik_or_npp])
                else:
                    cursor.execute("""
                        INSERT INTO ORGANISASI (id_adopter, nama_organisaasi, npp)
                        VALUES (%s, %s, %s)
                    """, [id_adopter, nama_organisasi, nik_or_npp])

            # Insert ke ADOPSI
            cursor.execute("""
                INSERT INTO ADOPSI (
                    id_adopter, id_hewan, tgl_mulai_adopsi,
                    tgl_berhenti_adopsi, kontribusi_finansial, status_pembayaran
                ) VALUES (
                    %s, %s, NOW(),
                    NOW() + (%s || ' months')::interval,
                    %s, 'tertunda'
                )
            """, [id_adopter, str(id_hewan), int(periode), int(nominal)])

            connect.commit() 
            messages.success(request, 'Adopsi berhasil didaftarkan.')

            return redirect('adopsi:admin_program_adopsi')

        except DatabaseError as e:
            connect.rollback()
            messages.error(request, f'Gagal mendaftarkan adopsi: {e}')

        finally:
            cursor.close()
            connect.close()

    # Kirim data ke template
    context = {
        'hewan': {
            'nama': nama_hewan,
            'spesies': jenis_hewan
        },
        'tipe_adopter': tipe,
        'username_adopter': username,
        'alamat': alamat,
        'telepon': no_telepon,
        'nama': nama_depan,
        'email': email,
    }

    cursor.close()
    connect.close()

    return render(request, 'adopsi/admin_form_adopsi.html', context)

def admin_pendataan_adopter(request, id_hewan):
    if request.method == 'POST':
        username = request.POST.get('username')
        tipe_adopter = request.POST.get('tipe_adopter')

        connect = get_db_connection()
        cursor = connect.cursor()

        cursor.execute("""
            SELECT 1 FROM sizopi.PENGGUNA pg
            JOIN sizopi.PENGUNJUNG pj ON pg.username = pj.username_p
            WHERE pj.username_p = %s
        """, [username])
        pengunjung_ada = cursor.fetchone()

        cursor.close()
        connect.close()

        if pengunjung_ada:
            request.session['username_adopter'] = username
            request.session['tipe_adopter'] = tipe_adopter
            return redirect(reverse('adopsi:admin_form_adopsi', args=[id_hewan]))
        else:
            messages.error(request, 'Username tidak ditemukan atau belum menjadi pengunjung.')

    return render(request, 'adopsi/admin_pendataan_adopter.html', {'id_hewan': id_hewan})

def hentikan_adopsi(request, id_hewan):
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO sizopi")

        # Ambil adopsi aktif (hari ini masih dalam masa adopsi)
        cursor.execute("""
            SELECT id_adopter, tgl_mulai_adopsi
            FROM ADOPSI
            WHERE id_hewan = %s
              AND CURRENT_DATE BETWEEN tgl_mulai_adopsi AND tgl_berhenti_adopsi
            ORDER BY tgl_mulai_adopsi DESC
            LIMIT 1
        """, [str(id_hewan)])
        result = cursor.fetchone()

        if not result:
            messages.error(request, 'Tidak ditemukan adopsi aktif untuk hewan ini.')
            return redirect('adopsi:admin_program_adopsi')

        id_adopter, tgl_mulai = result

        # Hentikan adopsi dengan update tgl_berhenti_adopsi
        cursor.execute("""
            UPDATE ADOPSI
            SET tgl_berhenti_adopsi = CURRENT_DATE
            WHERE id_adopter = %s
              AND id_hewan = %s
              AND tgl_mulai_adopsi = %s
        """, [id_adopter, str(id_hewan), tgl_mulai])

        messages.success(request, 'Adopsi berhasil dihentikan.')

    return redirect('adopsi:admin_program_adopsi')

def adopter_lihat_adopsi(request, id_hewan):
    username_adopter = request.session.get('user', {}).get('username')

    if not username_adopter:
        messages.error(request, "Anda harus login untuk melihat informasi adopsi.")
        return redirect('register_login:login')  

    connect = get_db_connection()
    cursor = connect.cursor()
    cursor.execute("SET search_path TO sizopi")

    cursor.execute("""
        SELECT 
            h.id,
            h.nama,
            h.spesies,
            h.status_kesehatan,
            h.url_foto,
            ad.tgl_mulai_adopsi,
            ad.tgl_berhenti_adopsi,
            ad.kontribusi_finansial,
            hab.nama AS habitat,
            ad.status_pembayaran
        FROM HEWAN h
        JOIN ADOPSI ad ON h.id = ad.id_hewan
        JOIN ADOPTER a ON ad.id_adopter = a.id_adopter
        LEFT JOIN HABITAT hab ON h.nama_habitat = hab.nama
        WHERE h.id = %s
        AND a.username_adopter = %s
        ORDER BY ad.tgl_mulai_adopsi DESC
        LIMIT 1
    """, [str(id_hewan), username_adopter])

    row = cursor.fetchone()
    cursor.close()

    if not row:
        return render(request, '404.html')

    hewan = {
        'id': row[0],
        'nama': row[1],
        'spesies': row[2],
        'kondisi': row[3],
        'foto': row[4],
        'tanggal_mulai': row[5],
        'tanggal_akhir': row[6],
        'nominal': row[7],
        'habitat': row[8],
        'status_pembayaran': row[9]
    }

    context = {
        'hewan': hewan
    }
    return render(request, 'adopsi/adopter_lihat_adopsi.html', context)

def adopter_program_adopsi(request):
    username = request.session.get('user', {}).get('username')
    if not username:
        return redirect('register_login:login')

    connect = get_db_connection()
    cursor = connect.cursor()
    cursor.execute("SET search_path TO sizopi")

    cursor.execute("""
        SELECT 
            h.id,
            h.nama,
            h.spesies,
            h.status_kesehatan,
            h.url_foto,
            a.id_adopter,
            COALESCE(i.nama, o.nama_organisaasi) AS nama_adopter,
            ad.tgl_mulai_adopsi,
            ad.tgl_berhenti_adopsi,
            ad.kontribusi_finansial,
            ad.status_pembayaran
        FROM ADOPTER a
        JOIN ADOPSI ad ON a.id_adopter = ad.id_adopter
        JOIN HEWAN h ON ad.id_hewan = h.id
        LEFT JOIN INDIVIDU i ON i.id_adopter = a.id_adopter
        LEFT JOIN ORGANISASI o ON o.id_adopter = a.id_adopter
        WHERE a.username_adopter = %s
            AND CURRENT_DATE BETWEEN ad.tgl_mulai_adopsi AND ad.tgl_berhenti_adopsi
        ORDER BY h.id, ad.tgl_mulai_adopsi DESC

    """, [username])
    
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    cursor.close()
    connect.close()

    hewan_diadopsi = [dict(zip(columns, row)) for row in rows]

    context = {
        'hewan_diadopsi': hewan_diadopsi,
        'username': username
    }
    return render(request, 'adopsi/adopter_program_adopsi.html', context)

def adopter_pantau_kondisi(request, id_hewan):
    connect = get_db_connection()
    cursor = connect.cursor()
    cursor.execute("SET search_path TO sizopi")

    # Cek apakah hewan valid
    cursor.execute("""
        SELECT id, nama, spesies, status_kesehatan, url_foto, nama_habitat
        FROM HEWAN
        WHERE id = %s
    """, [str(id_hewan)])
    row = cursor.fetchone()

    if not row:
        cursor.close()
        connect.close()
        return render(request, '404.html')

    hewan = {
        'id': row[0],
        'nama': row[1],
        'spesies': row[2],
        'status_kesehatan': row[3],
        'foto': row[4],
        'habitat': row[5], 
    }

    # Ambil tanggal mulai adopsi aktif saat ini
    cursor.execute("""
        SELECT tgl_mulai_adopsi
        FROM ADOPSI
        WHERE id_hewan = %s
          AND CURRENT_DATE >= tgl_mulai_adopsi
          AND CURRENT_DATE < tgl_berhenti_adopsi
        ORDER BY tgl_mulai_adopsi DESC
        LIMIT 1
    """, [str(id_hewan)])
    result = cursor.fetchone()

    tanggal_mulai = result[0] if result else None

    # Ambil rekam medis setelah tanggal mulai (jika ada)
    if tanggal_mulai:
        cursor.execute("""
            SELECT cm.tanggal_pemeriksaan, pg.nama_depan || ' ' || pg.nama_belakang AS nama_dokter,
                   cm.diagnosis, cm.pengobatan, cm.status_kesehatan, cm.catatan_tindak_lanjut
            FROM CATATAN_MEDIS cm
            JOIN DOKTER_HEWAN dh ON cm.username_dh = dh.username_dh
            JOIN PENGGUNA pg ON dh.username_dh = pg.username
            WHERE cm.id_hewan = %s
              AND cm.tanggal_pemeriksaan > %s
            ORDER BY cm.tanggal_pemeriksaan DESC
        """, [str(id_hewan), tanggal_mulai])
    else:
        cursor.execute("""
            SELECT cm.tanggal_pemeriksaan, pg.nama_depan || ' ' || pg.nama_belakang AS nama_dokter,
                   cm.diagnosis, cm.pengobatan, cm.status_kesehatan, cm.catatan_tindak_lanjut
            FROM CATATAN_MEDIS cm
            JOIN DOKTER_HEWAN dh ON cm.username_dh = dh.username_dh
            JOIN PENGGUNA pg ON dh.username_dh = pg.username
            WHERE cm.id_hewan = %s
            ORDER BY cm.tanggal_pemeriksaan DESC
        """, [str(id_hewan)])

    rekam_medis_raw = cursor.fetchall()
    rekam_medis = [
        {
            'tanggal': str(r[0]),
            'nama_dokter': r[1],
            'diagnosis': r[2],
            'pengobatan': r[3],
            'status': r[4],
            'catatan': r[5],
        }
        for r in rekam_medis_raw
    ]

    cursor.close()
    connect.close()

    context = {
        'hewan': hewan,
        'rekam_medis': rekam_medis,
    }
    return render(request, 'adopsi/adopter_pantau_kondisi.html', context)

def adopter_sertifikat(request, id_hewan):
    connect = get_db_connection()
    cursor = connect.cursor()
    cursor.execute("SET search_path TO sizopi")

    # Ambil info hewan
    cursor.execute("""
        SELECT nama, spesies, status_kesehatan, url_foto
        FROM HEWAN
        WHERE id = %s
    """, [str(id_hewan)])
    row = cursor.fetchone()

    if not row:
        cursor.close()
        connect.close()
        return render(request, '404.html')

    nama_hewan, spesies, status_kesehatan, url_foto = row

    # Ambil info adopsi aktif
    cursor.execute("""
        SELECT A.tgl_mulai_adopsi, A.tgl_berhenti_adopsi, A.id_adopter, P.nama_depan
        FROM ADOPSI A
        JOIN ADOPTER AD ON A.id_adopter = AD.id_adopter
        JOIN PENGGUNA P ON AD.username_adopter = P.username
        WHERE A.id_hewan = %s
          AND CURRENT_DATE >= A.tgl_mulai_adopsi
          AND CURRENT_DATE < A.tgl_berhenti_adopsi
        ORDER BY A.tgl_mulai_adopsi DESC
        LIMIT 1
    """, [str(id_hewan)])

    adopsi = cursor.fetchone()
    if not adopsi:
        cursor.close()
        connect.close()
        return render(request, '404.html')

    tanggal_mulai, tanggal_berhenti, id_adopter, nama_adopter = adopsi

    # Format sertifikat
    nomor_sertifikat = f"ADP-{str(id_hewan)[:4].upper()}-{nama_adopter[:3].upper()}-2025"

    # Gabung semua data ke dalam dict hewan agar mudah dipanggil di template
    hewan = {
        'id': id_hewan,
        'nama': nama_hewan,
        'spesies': spesies,
        'kondisi': status_kesehatan,
        'foto': url_foto,
        'adopter': nama_adopter,
        'tanggal_mulai': DateFormat(tanggal_mulai).format("Y-m-d"),
        'tanggal_akhir': DateFormat(tanggal_berhenti).format("Y-m-d"),
    }

    context = {
        'hewan': hewan,
        'nomor_sertifikat': nomor_sertifikat,
    }

    cursor.close()
    connect.close()

    return render(request, 'adopsi/adopter_sertifikat.html', context)

def adopter_perpanjang_adopsi(request, id_hewan):
    connect = get_db_connection()
    cursor = connect.cursor()
    cursor.execute("SET search_path TO sizopi")

    username_adopter = request.session.get('username_adopter')
    tipe_adopter = request.session.get('tipe_adopter')

    # Ambil data hewan dan adopsi aktif yang sedang berlangsung & sudah lunas
    cursor.execute("""
        SELECT 
            h.nama, h.spesies, h.url_foto,
            ad.tgl_berhenti_adopsi, ad.kontribusi_finansial,
            COALESCE(i.nama, o.nama_organisaasi) AS nama_adopter,
            i.nik, o.npp,
            pj.alamat, pg.no_telepon
        FROM HEWAN h
        JOIN ADOPSI ad ON h.id = ad.id_hewan
        JOIN ADOPTER a ON ad.id_adopter = a.id_adopter
        JOIN PENGUNJUNG pj ON a.username_adopter = pj.username_p
        JOIN PENGGUNA pg ON pj.username_p = pg.username
        LEFT JOIN INDIVIDU i ON a.id_adopter = i.id_adopter
        LEFT JOIN ORGANISASI o ON a.id_adopter = o.id_adopter
        WHERE h.id = %s
          AND a.username_adopter = %s
          AND ad.status_pembayaran = 'lunas'
          AND CURRENT_DATE BETWEEN ad.tgl_mulai_adopsi AND ad.tgl_berhenti_adopsi
    """, [str(id_hewan), username_adopter])
    
    row = cursor.fetchone()
    if not row:
        cursor.close()
        connect.close()
        messages.error(request, 'Data adopsi tidak valid atau belum lunas.')
        return redirect('adopsi:adopter_program_adopsi')

    nama_hewan, spesies, foto, tgl_akhir_lama, kontribusi_lama, nama_adopter, nik, npp, alamat, no_telepon = row

    if request.method == 'POST':
        periode = request.POST.get('periode')
        nominal = int(request.POST.get("nominal", 0))
        if nominal < 1000:
            messages.error(request, "Kontribusi minimal adalah Rp 1")
            return redirect(reverse('adopsi:adopter_perpanjang_adopsi', args=[id_hewan]))  

        if not all([nominal, periode]):
            messages.error(request, 'Semua field wajib diisi!')
            return redirect(reverse('adopsi:adopter_perpanjang_adopsi', args=[id_hewan]))

        tambahan_bulan = int(periode)
        tgl_mulai_baru = date.today()
        tgl_akhir_baru = tgl_akhir_lama + relativedelta(months=tambahan_bulan)

        # Ambil ID adopter
        cursor.execute("SELECT id_adopter FROM ADOPTER WHERE username_adopter = %s", [username_adopter])
        id_adopter = cursor.fetchone()[0]

        # Tambah periode dan kontribusi ke adopsi aktif
        cursor.execute("""
            UPDATE ADOPSI
            SET 
                tgl_berhenti_adopsi = tgl_berhenti_adopsi + INTERVAL '%s month',
                kontribusi_finansial = kontribusi_finansial + %s
            WHERE id_adopter = %s AND id_hewan = %s
            AND CURRENT_DATE BETWEEN tgl_mulai_adopsi AND tgl_berhenti_adopsi
        """, [
            tambahan_bulan,
            nominal,
            id_adopter,
            str(id_hewan)
        ])

        # Update juga total kontribusi di tabel ADOPTER
        cursor.execute("""
            UPDATE ADOPTER
            SET total_kontribusi = (
                SELECT COALESCE(SUM(kontribusi_finansial), 0)
                FROM ADOPSI
                WHERE id_adopter = %s AND status_pembayaran = 'lunas'
            )
            WHERE id_adopter = %s
        """, [id_adopter, id_adopter])

        connect.commit()
        cursor.close()
        connect.close()
        messages.success(request, 'Perpanjangan adopsi berhasil dilakukan!')
        return redirect(reverse('adopsi:adopter_lihat_adopsi', args=[id_hewan]))

    context = {
        'hewan': {
            'id': id_hewan,
            'nama': nama_hewan,
            'spesies': spesies,
            'adopter': nama_adopter
        },
        'adopter': {
            'nik': nik,
            'npp': npp,
            'alamat': alamat,
            'kontak': no_telepon
        },
        'tipe_adopter': tipe_adopter,
        'username_adopter': username_adopter
    }

    cursor.close()
    connect.close()
    return render(request, 'adopsi/adopter_perpanjang_adopsi.html', context)

def hentikan_adopsi_adopter(request, id_hewan):
    username_adopter = request.session.get('username_adopter')

    if request.method == 'POST':
        connect = get_db_connection()
        cursor = connect.cursor()
        cursor.execute("SET search_path TO sizopi")

        # Cari adopsi aktif milik adopter ini untuk hewan ini
        cursor.execute("""
            SELECT ad.id_adopter, ad.tgl_mulai_adopsi
            FROM ADOPSI ad
            JOIN ADOPTER a ON ad.id_adopter = a.id_adopter
            WHERE a.username_adopter = %s
            AND ad.id_hewan = %s
            AND ad.tgl_berhenti_adopsi >= CURRENT_DATE
            ORDER BY ad.tgl_mulai_adopsi DESC
            LIMIT 1
        """, [username_adopter, str(id_hewan)])
        result = cursor.fetchone()

        if not result:
            messages.error(request, "Tidak ditemukan adopsi aktif yang bisa dihentikan.")
            return redirect('adopsi:adopter_program_adopsi')

        id_adopter, tgl_mulai = result

        # Potong masa adopsi ke hari kemarin supaya langsung tidak aktif
        cursor.execute("""
            UPDATE ADOPSI
            SET tgl_berhenti_adopsi = CURRENT_DATE - INTERVAL '1 day'
            WHERE id_hewan = %s
            AND CURRENT_DATE BETWEEN tgl_mulai_adopsi AND tgl_berhenti_adopsi
            AND id_adopter = (
                SELECT id_adopter FROM ADOPTER WHERE username_adopter = %s
            )
        """, [str(id_hewan), username_adopter])

        connect.commit()
        cursor.close()
        connect.close()

        messages.success(request, "Adopsi berhasil dihentikan.")
        return redirect('adopsi:adopter_program_adopsi')

    return redirect('adopsi:adopter_program_adopsi')

def admin_list_adopter(request):
    connect = get_db_connection()
    cursor = connect.cursor()
    cursor.execute("SET search_path TO sizopi")

    one_year_ago = date.today() - timedelta(days=365)

    cursor.execute("""
        SELECT 
            a.id_adopter,
            COALESCE(i.nama, o.nama_organisaasi) AS nama_adopter,
            pg.no_telepon,
            pj.alamat,
            COALESCE(SUM(CASE WHEN ad.status_pembayaran = 'lunas' THEN ad.kontribusi_finansial ELSE 0 END), 0) AS total_kontribusi,
            COUNT(*) FILTER (
                WHERE CURRENT_DATE >= ad.tgl_mulai_adopsi AND CURRENT_DATE < ad.tgl_berhenti_adopsi
            ) > 0 AS sedang_berlangsung,
            CASE
                WHEN i.id_adopter IS NOT NULL THEN 'Individu'
                ELSE 'Organisasi'
            END AS tipe_adopter
        FROM ADOPTER a
        JOIN PENGUNJUNG pj ON a.username_adopter = pj.username_p
        JOIN PENGGUNA pg ON pj.username_p = pg.username
        LEFT JOIN INDIVIDU i ON a.id_adopter = i.id_adopter
        LEFT JOIN ORGANISASI o ON a.id_adopter = o.id_adopter
        LEFT JOIN ADOPSI ad ON a.id_adopter = ad.id_adopter
        GROUP BY a.id_adopter, nama_adopter, pg.no_telepon, pj.alamat, i.id_adopter
    """)
    rows = cursor.fetchall()

    # Pemeringkatan
    # cursor.execute("""
    #     SELECT 
    #         COALESCE(i.nama, o.nama_organisaasi) AS nama_adopter,
    #         SUM(ad.kontribusi_finansial) AS total_lunas_1thn
    #     FROM ADOPTER a
    #     LEFT JOIN INDIVIDU i ON a.id_adopter = i.id_adopter
    #     LEFT JOIN ORGANISASI o ON a.id_adopter = o.id_adopter
    #     JOIN ADOPSI ad ON a.id_adopter = ad.id_adopter
    #     WHERE ad.status_pembayaran = 'lunas' AND ad.tgl_mulai_adopsi >= %s
    #     GROUP BY nama_adopter
    #     ORDER BY total_lunas_1thn DESC
    #     LIMIT 5
    # """, [one_year_ago])
    # top_5 = cursor.fetchall() 
    # udah ada di procedured tapi tetep aku taro aja

    cursor.execute("SELECT * FROM get_top5_adopter()")
    top_5 = cursor.fetchall()

    cursor.close()
    connect.close()

    # Pisahkan berdasarkan tipe
    individu = []
    organisasi = []

    for row in rows:
        data = {
            'id': row[0],
            'nama': row[1],
            'kontak': row[2],
            'alamat': row[3],
            'total_kontribusi': row[4],
            'sedang_berlangsung': row[5],
        }
        if row[6] == 'Individu':
            individu.append(data)
        else:
            organisasi.append(data)
    
    individu.sort(key=lambda x: x['total_kontribusi'], reverse=True)
    organisasi.sort(key=lambda x: x['total_kontribusi'], reverse=True)

    # top_contributors = [{
    #     'rank': i+1,
    #     'nama': r[0],
    #     'kontribusi': r[1]
    # } for i, r in enumerate(top_5)]
    # udah ada di procedured tapi tetep aku taro aja

    top_contributors = [{
        'rank': r[0],
        'nama': r[1],
        'kontribusi': r[2]
    } for r in top_5]

    if top_5:
        messages.success(
            request,
            f'SUKSES: Daftar Top 5 Adopter satu tahun terakhir berhasil diperbarui, '
            f'dengan peringkat pertama dengan nama adopter "{top_5[0][1]}" berkontribusi sebesar "Rp{top_5[0][2]:,}".'
        )

    context = {
        'pengunjung_individu': individu,
        'pengunjung_organisasi': organisasi,
        'top_contributors': top_contributors
    }

    return render(request, 'adopsi/admin_list_adopter.html', context)

def admin_riwayat_adopsi(request, id_adopter):
    connect = get_db_connection()
    cursor = connect.cursor()
    cursor.execute("SET search_path TO sizopi")

    # Ambil data profil adopter
    cursor.execute("""
        SELECT 
            COALESCE(i.nama, o.nama_organisaasi),
            pg.no_telepon,
            pj.alamat
        FROM ADOPTER a
        JOIN PENGUNJUNG pj ON a.username_adopter = pj.username_p
        JOIN PENGGUNA pg ON pj.username_p = pg.username
        LEFT JOIN INDIVIDU i ON a.id_adopter = i.id_adopter
        LEFT JOIN ORGANISASI o ON a.id_adopter = o.id_adopter
        WHERE a.id_adopter = %s
    """, [id_adopter])
    row = cursor.fetchone()
    if not row:
        return render(request, '404.html')

    # Ambil semua adopsi lunas
    cursor.execute("""
        SELECT 
            h.id,
            h.nama,
            h.spesies,
            ad.tgl_mulai_adopsi,
            ad.tgl_berhenti_adopsi,
            ad.kontribusi_finansial,
            CASE 
                WHEN CURRENT_DATE >= ad.tgl_mulai_adopsi AND CURRENT_DATE < ad.tgl_berhenti_adopsi THEN 'Sedang Berlangsung'
                ELSE 'Selesai'
            END AS status_adopsi
        FROM ADOPSI ad
        JOIN HEWAN h ON ad.id_hewan = h.id
        WHERE ad.id_adopter = %s AND ad.status_pembayaran = 'lunas'
        ORDER BY ad.tgl_mulai_adopsi DESC
    """, [id_adopter])

    riwayat = cursor.fetchall()
    cursor.close()
    connect.close()

    context = {
        'adopter': {
            'id': id_adopter,
            'nama': row[0],
            'kontak': row[1],
            'alamat': row[2],
            'riwayat_adopsi': [{
                'id_hewan': r[0],
                'nama_hewan': r[1],
                'jenis_hewan': r[2],
                'tanggal_mulai': r[3],
                'tanggal_akhir': r[4],
                'nominal': r[5],
                'status': r[6]
            } for r in riwayat]
        }
    }
    return render(request, 'adopsi/admin_riwayat_adopsi.html', context)

def hapus_riwayat_adopsi(request, id_adopter, id_hewan, tanggal_mulai):
    connect = get_db_connection()
    cursor = connect.cursor()
    cursor.execute("SET search_path TO sizopi")

    if request.method == 'POST':
        cursor.execute("""
            DELETE FROM ADOPSI 
            WHERE id_adopter = %s 
            AND id_hewan = %s 
            AND tgl_mulai_adopsi = %s
        """, [id_adopter, id_hewan, tanggal_mulai])
        connect.commit()
        messages.success(request, 'Riwayat adopsi berhasil dihapus.')

    cursor.close()
    connect.close()
    return redirect('adopsi:admin_riwayat_adopsi', id_adopter=id_adopter)

def hapus_adopter(request, id_adopter):
    if request.method == 'POST':
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO sizopi")

            # Cek apakah masih ada adopsi aktif
            cursor.execute("""
                SELECT COUNT(*) 
                FROM ADOPSI 
                WHERE id_adopter = %s
                  AND status_pembayaran = 'lunas'
                  AND CURRENT_DATE >= tgl_mulai_adopsi
                  AND CURRENT_DATE < tgl_berhenti_adopsi
            """, [id_adopter])

            count = cursor.fetchone()[0]

            if count > 0:
                messages.warning(request, "Adopter masih aktif mengadopsi satwa dan tidak dapat dihapus.")
                return redirect('adopsi:admin_list_adopter')

            # Hapus riwayat adopsi adopter
            cursor.execute("DELETE FROM ADOPSI WHERE id_adopter = %s", [id_adopter])

            # Hapus data adopter
            cursor.execute("DELETE FROM ADOPTER WHERE id_adopter = %s", [id_adopter])

            messages.success(request, "Data adopter dan riwayat adopsinya berhasil dihapus.")
        return redirect('adopsi:admin_list_adopter')

    # GET method fallback
    return redirect('adopsi:admin_list_adopter')




