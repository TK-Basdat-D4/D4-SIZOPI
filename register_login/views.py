from django.shortcuts import render, redirect
from django.contrib import messages
from biru.views import RESERVASI
from utils.db_utils import get_db_connection
import random
import uuid

def home(request):
    """Home page that can be accessed by guests"""
    return render(request, "home.html")

def choose_role(request):
    """Page to choose registration role"""
    return render(request, "choose_role.html")

def register_pengunjung(request):
    """Registration form for Visitors - FIXED"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        email = request.POST.get('email')
        
        # Simple password validation
        if password != confirm_password:
            messages.error(request, 'Password dan Konfirmasi Password tidak cocok!')
            return render(request, 'register_pengunjung.html')
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Insert into pengguna table (trigger akan memeriksa duplikasi)
            cur.execute("""
                INSERT INTO sizopi.pengguna (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                username,
                email,
                password,
                request.POST.get('nama_depan'),
                request.POST.get('nama_tengah') or '',
                request.POST.get('nama_belakang'),
                request.POST.get('nomor_telepon')
            ))
            
            # Insert into pengunjung table
            cur.execute("""
                INSERT INTO sizopi.pengunjung (username_p, alamat, tgl_lahir)
                VALUES (%s, %s, %s)
            """, (
                username,
                request.POST.get('alamat_lengkap'),
                request.POST.get('tanggal_lahir')
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            
            messages.success(request, 'Pendaftaran berhasil! Silahkan login.')
            return redirect('register_login:login')
            
        except Exception as e:
            conn.rollback()
            # Bersihkan pesan error dari database
            error_msg = str(e)
            if 'Username "' in error_msg and '" sudah digunakan' in error_msg:
                # Ambil hanya bagian pesan yang penting
                error_msg = error_msg.split('CONTEXT:')[0].strip()
                if error_msg.startswith('ERROR:  '):
                    error_msg = error_msg[8:]
            messages.error(request, error_msg)
            
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
            return render(request, 'register_pengunjung.html')
    
    return render(request, 'register_pengunjung.html')

def register_dokter(request):
    """Registration form for Veterinarians - FIXED (removed duplicate)"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        email = request.POST.get('email')
        nomor_sertifikasi = request.POST.get('nomor_sertifikasi')
        
        # Simple password validation
        if password != confirm_password:
            messages.error(request, 'Password dan Konfirmasi Password tidak cocok!')
            return render(request, 'register_dokter.html')
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Check if username already exists
            cur.execute("SELECT username FROM sizopi.pengguna WHERE username = %s", (username,))
            if cur.fetchone():
                messages.error(request, 'Username sudah terdaftar!')
                cur.close()
                conn.close()
                return render(request, 'register_dokter.html')
            
            # Check if email already exists
            cur.execute("SELECT email FROM sizopi.pengguna WHERE email = %s", (email,))
            if cur.fetchone():
                messages.error(request, 'Email sudah terdaftar!')
                cur.close()
                conn.close()
                return render(request, 'register_dokter.html')
                
            # Check if nomor_sertifikasi already exists 
            cur.execute("SELECT no_str FROM sizopi.dokter_hewan WHERE no_str = %s", (nomor_sertifikasi,))
            if cur.fetchone():
                messages.error(request, 'Nomor Sertifikasi sudah terdaftar!')
                cur.close()
                conn.close()
                return render(request, 'register_dokter.html')
            
            # Insert into pengguna table
            cur.execute("""
                INSERT INTO sizopi.pengguna (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                username,
                email,
                password,
                request.POST.get('nama_depan'),
                request.POST.get('nama_tengah') or '',
                request.POST.get('nama_belakang'),
                request.POST.get('nomor_telepon')
            ))
            
            # Insert into dokter_hewan table
            cur.execute("""
                INSERT INTO sizopi.dokter_hewan (username_dh, no_str)
                VALUES (%s, %s)
            """, (
                username,
                nomor_sertifikasi
            ))
            
            # Handle specializations
            spesialisasi_list = []
            if request.POST.get('mamalia_besar'):
                spesialisasi_list.append('Mamalia Besar')
            if request.POST.get('reptil'):
                spesialisasi_list.append('Reptil')
            if request.POST.get('burung_eksotis'):
                spesialisasi_list.append('Burung Eksotis')
            if request.POST.get('primata'):
                spesialisasi_list.append('Primata')
            if request.POST.get('lainnya'):
                spesialisasi_list.append(f"Lainnya: {request.POST.get('lainnya_isian')}")
            
            # Insert specializations
            for spesialisasi in spesialisasi_list:
                try:
                    cur.execute("""
                        INSERT INTO sizopi.spesialisasi (username_sh, nama_spesialisasi)
                        VALUES (%s, %s)
                    """, (username, spesialisasi))
                except Exception as spec_e:
                    print(f"DEBUG: Error inserting specialization: {spec_e}")
                    pass
            
            conn.commit()
            cur.close()
            conn.close()
            
            messages.success(request, 'Pendaftaran berhasil! Silahkan login.')
            return redirect('register_login:login')
            
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
            return render(request, 'register_dokter.html')
    
    return render(request, 'register_dokter.html')

def register_staff(request):
    """Registration form for Staff - FIXED with UUID generation"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        email = request.POST.get('email')
        peran = request.POST.get('peran')
        
        # Simple password validation
        if password != confirm_password:
            messages.error(request, 'Password dan Konfirmasi Password tidak cocok!')
            return render(request, 'register_staff.html')
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Check if username already exists
            cur.execute("SELECT username FROM sizopi.pengguna WHERE username = %s", (username,))
            if cur.fetchone():
                messages.error(request, 'Username sudah terdaftar!')
                cur.close()
                conn.close()
                return render(request, 'register_staff.html')
            
            # Check if email already exists
            cur.execute("SELECT email FROM sizopi.pengguna WHERE email = %s", (email,))
            if cur.fetchone():
                messages.error(request, 'Email sudah terdaftar!')
                cur.close()
                conn.close()
                return render(request, 'register_staff.html')
            
            # Insert into pengguna table
            cur.execute("""
                INSERT INTO sizopi.pengguna (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                username,
                email,
                password,
                request.POST.get('nama_depan'),
                request.POST.get('nama_tengah') or '',
                request.POST.get('nama_belakang'),
                request.POST.get('nomor_telepon')
            ))
            
            # Generate UUID for staff ID (required by database schema)
            staff_id = str(uuid.uuid4())
            
            # Insert into appropriate staff table using correct column names
            if peran == 'penjaga_hewan':
                cur.execute("""
                    INSERT INTO sizopi.penjaga_hewan (username_jh, id_staf)
                    VALUES (%s, %s)
                """, (username, staff_id))
            elif peran == 'staff_administrasi':
                cur.execute("""
                    INSERT INTO sizopi.staf_admin (username_sa, id_staf)
                    VALUES (%s, %s)
                """, (username, staff_id))
            elif peran == 'pelatih_pertunjukan':
                cur.execute("""
                    INSERT INTO sizopi.pelatih_hewan (username_lh, id_staf)
                    VALUES (%s, %s)
                """, (username, staff_id))
            
            conn.commit()
            cur.close()
            conn.close()
            
            messages.success(request, 'Pendaftaran berhasil! Silahkan login.')
            return redirect('register_login:login')
            
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
            return render(request, 'register_staff.html')
    
    return render(request, 'register_staff.html')

def login(request):
    """Login with proper role detection - FIXED for JSON serialization and UUID handling"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Get user from database
            cur.execute("""
                SELECT username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon
                FROM sizopi.pengguna 
                WHERE username = %s AND password = %s
            """, (username, password))
            
            user_data = cur.fetchone()
            
            if user_data:
                # Create user dictionary
                user = {
                    'username': user_data[0],
                    'email': user_data[1],
                    'nama_depan': user_data[3],
                    'nama_tengah': user_data[4] or '',
                    'nama_belakang': user_data[5],
                    'nomor_telepon': user_data[6]
                }
                
                # Determine user role
                user_role_found = False
                
                # Check pengunjung
                try:
                    cur.execute("SELECT alamat, tgl_lahir FROM sizopi.pengunjung WHERE username_p = %s", (username,))
                    pengunjung_data = cur.fetchone()
                    if pengunjung_data:
                        user['role'] = 'pengunjung'
                        user['alamat'] = pengunjung_data[0]
                        # Convert date to string for JSON serialization
                        if pengunjung_data[1]:
                            user['tanggal_lahir'] = pengunjung_data[1].strftime('%Y-%m-%d')
                        else:
                            user['tanggal_lahir'] = None
                        user_role_found = True
                        print("DEBUG: User role: pengunjung")
                except Exception as e:
                    print(f"DEBUG: Error checking pengunjung: {e}")
                
                # Check dokter_hewan
                if not user_role_found:
                    try:
                        cur.execute("SELECT no_str FROM sizopi.dokter_hewan WHERE username_dh = %s", (username,))
                        dokter_data = cur.fetchone()
                        if dokter_data:
                            user['role'] = 'dokter_hewan'
                            user['nomor_sertifikasi'] = dokter_data[0]  # Map no_str to nomor_sertifikasi for consistency
                            
                            # Get specializations
                            try:
                                cur.execute("SELECT nama_spesialisasi FROM sizopi.spesialisasi WHERE username_sh = %s", (username,))
                                spesialisasi_data = cur.fetchall()
                                user['spesialisasi'] = [s[0] for s in spesialisasi_data] if spesialisasi_data else []
                            except Exception as spec_e:
                                print(f"DEBUG: Error getting specializations: {spec_e}")
                                user['spesialisasi'] = []
                            
                            user_role_found = True
                            print("DEBUG: User role: dokter_hewan")
                    except Exception as e:
                        print(f"DEBUG: Error checking dokter_hewan: {e}")
                
                # Check staff tables
                if not user_role_found:
                    try:
                        # Check penjaga_hewan
                        cur.execute("SELECT id_staf FROM sizopi.penjaga_hewan WHERE username_jh = %s", (username,))
                        penjaga_data = cur.fetchone()
                        if penjaga_data:
                            user['role'] = 'staff'
                            user['peran'] = 'penjaga_hewan'
                            # Convert UUID to string for JSON serialization
                            user['staff_id'] = str(penjaga_data[0])
                            user_role_found = True
                            print("DEBUG: User role: staff (penjaga_hewan)")
                    except Exception as e:
                        print(f"DEBUG: Error checking penjaga_hewan: {e}")
                
                if not user_role_found:
                    try:
                        # Check staf_admin
                        cur.execute("SELECT id_staf FROM sizopi.staf_admin WHERE username_sa = %s", (username,))
                        admin_data = cur.fetchone()
                        if admin_data:
                            user['role'] = 'staff'
                            user['peran'] = 'staff_administrasi'
                            # Convert UUID to string for JSON serialization
                            user['staff_id'] = str(admin_data[0])
                            user_role_found = True
                            print("DEBUG: User role: staff (staff_administrasi)")
                    except Exception as e:
                        print(f"DEBUG: Error checking staf_admin: {e}")
                
                if not user_role_found:
                    try:
                        # Check pelatih_hewan
                        cur.execute("SELECT id_staf FROM sizopi.pelatih_hewan WHERE username_lh = %s", (username,))
                        pelatih_data = cur.fetchone()
                        if pelatih_data:
                            user['role'] = 'staff'
                            user['peran'] = 'pelatih_pertunjukan'
                            # Convert UUID to string for JSON serialization
                            user['staff_id'] = str(pelatih_data[0])
                            user_role_found = True
                            print("DEBUG: User role: staff (pelatih_pertunjukan)")
                    except Exception as e:
                        print(f"DEBUG: Error checking pelatih_hewan: {e}")
                
                # If no specific role found, set as basic user
                if not user_role_found:
                    user['role'] = 'user'
                    print("DEBUG: User role: default user")
                
                cur.close()
                conn.close()
                
                # Save user to session
                request.session['user'] = user
                print(f"DEBUG: Final user data: {user}")
                messages.success(request, f"Selamat datang, {user['nama_depan']}!")
                return redirect('register_login:dashboard')
            else:
                messages.error(request, 'Username atau Password salah!')
                cur.close()
                conn.close()
                
        except Exception as e:
            print(f"DEBUG: Main exception occurred: {str(e)}")
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
    
    return render(request, 'login.html')

def logout(request):
    """Logout function"""
    if 'user' in request.session:
        del request.session['user']
    messages.success(request, 'Berhasil logout!')
    return redirect('register_login:login')

def profile(request):
    """Profile page based on user role"""
    if 'user' not in request.session:
        messages.error(request, 'Silahkan login terlebih dahulu!')
        return redirect('register_login:login')
    
    user = request.session['user']
    
    if user['role'] == 'pengunjung':
        return render(request, 'profile_pengunjung.html', {'user': user})
    elif user['role'] == 'dokter_hewan':
        return render(request, 'profile_dokter.html', {'user': user})
    else:  # staff
        return render(request, 'profile_staff.html', {'user': user})
    
def dashboard(request):
    """Dashboard page after login"""
    if 'user' not in request.session:
        messages.error(request, 'Silahkan login terlebih dahulu!')
        return redirect('register_login:login')

    user = request.session['user']

    reservasi_terjadwal = []
    if user['role'] == 'pengunjung':
        reservasi_terjadwal = [
            r for r in RESERVASI
            if r.get('username') == user['username'] and r.get('status') == 'Terjadwal'
        ]

    return render(request, 'dashboard.html', {
        'user': user,
        'reservasi_terjadwal': reservasi_terjadwal,
    })

def profile_settings(request):
    """Profile settings page"""
    if 'user' not in request.session:
        messages.error(request, 'Silahkan login terlebih dahulu!')
        return redirect('register_login:login')
    
    user = request.session['user']
    return render(request, 'profile_settings.html', {'user': user})

def update_profile(request):
    """Update user profile information - FIXED with correct column names and JSON serialization"""
    if 'user' not in request.session:
        messages.error(request, 'Silahkan login terlebih dahulu!')
        return redirect('register_login:login')
    
    if request.method == 'POST':
        current_user = request.session['user']
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Update pengguna table
            cur.execute("""
                UPDATE sizopi.pengguna 
                SET email = %s, nama_depan = %s, nama_tengah = %s, nama_belakang = %s, no_telepon = %s
                WHERE username = %s
            """, (
                request.POST.get('email'),
                request.POST.get('nama_depan'),
                request.POST.get('nama_tengah') or '',
                request.POST.get('nama_belakang'),
                request.POST.get('nomor_telepon'),
                current_user['username']
            ))
            
            # Update role-specific information
            if current_user['role'] == 'pengunjung':
                # Use correct column name tgl_lahir
                cur.execute("""
                    UPDATE sizopi.pengunjung 
                    SET alamat = %s, tgl_lahir = %s
                    WHERE username_p = %s
                """, (
                    request.POST.get('alamat'),
                    request.POST.get('tanggal_lahir'),
                    current_user['username']
                ))
            
            elif current_user['role'] == 'dokter_hewan':
                # Update specializations - use correct foreign key username_sh
                cur.execute("DELETE FROM sizopi.spesialisasi WHERE username_sh = %s", (current_user['username'],))
                
                spesialisasi_list = []
                if 'spesialisasi[]' in request.POST:
                    spesialisasi_list = request.POST.getlist('spesialisasi[]')
                
                if request.POST.get('spesialisasi_lainnya_cb'):
                    spesialisasi_list.append(f"Lainnya: {request.POST.get('spesialisasi_lainnya', '')}")
                
                for spesialisasi in spesialisasi_list:
                    cur.execute("""
                        INSERT INTO sizopi.spesialisasi (username_sh, nama_spesialisasi)
                        VALUES (%s, %s)
                    """, (current_user['username'], spesialisasi))
            
            conn.commit()
            
            # Update session data
            cur.execute("""
                SELECT username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon
                FROM sizopi.pengguna 
                WHERE username = %s
            """, (current_user['username'],))
            
            updated_user_data = cur.fetchone()
            if updated_user_data:
                current_user.update({
                    'email': updated_user_data[1],
                    'nama_depan': updated_user_data[3],
                    'nama_tengah': updated_user_data[4] or '',
                    'nama_belakang': updated_user_data[5],
                    'nomor_telepon': updated_user_data[6]
                })
                
                # Update role-specific data in session
                if current_user['role'] == 'pengunjung':
                    # Use correct column name tgl_lahir and convert to string
                    cur.execute("SELECT alamat, tgl_lahir FROM sizopi.pengunjung WHERE username_p = %s", (current_user['username'],))
                    pengunjung_data = cur.fetchone()
                    if pengunjung_data:
                        current_user['alamat'] = pengunjung_data[0]
                        # Convert date to string for JSON serialization
                        if pengunjung_data[1]:
                            current_user['tanggal_lahir'] = pengunjung_data[1].strftime('%Y-%m-%d')
                        else:
                            current_user['tanggal_lahir'] = None
                
                elif current_user['role'] == 'dokter_hewan':
                    # Use correct foreign key username_sh
                    cur.execute("SELECT nama_spesialisasi FROM sizopi.spesialisasi WHERE username_sh = %s", (current_user['username'],))
                    spesialisasi_data = cur.fetchall()
                    current_user['spesialisasi'] = [s[0] for s in spesialisasi_data] if spesialisasi_data else []
                
                request.session['user'] = current_user
            
            cur.close()
            conn.close()
            
            messages.success(request, 'Profil berhasil diperbarui!')
            return redirect('register_login:profile_settings')
            
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
    
    return redirect('register_login:profile_settings')

def change_password(request):
    """Simple password change"""
    if 'user' not in request.session:
        messages.error(request, 'Silahkan login terlebih dahulu!')
        return redirect('register_login:login')
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        current_user = request.session['user']
        
        # Simple password validation
        if new_password != confirm_password:
            messages.error(request, 'Password baru dan konfirmasi tidak cocok!')
            return render(request, 'change_password.html')
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Check current password
            cur.execute("SELECT password FROM sizopi.pengguna WHERE username = %s AND password = %s", 
                       (current_user['username'], current_password))
            
            if not cur.fetchone():
                messages.error(request, 'Password saat ini tidak benar!')
                cur.close()
                conn.close()
                return render(request, 'change_password.html')
            
            # Update password (plain text)
            cur.execute("""
                UPDATE sizopi.pengguna 
                SET password = %s 
                WHERE username = %s
            """, (new_password, current_user['username']))
            
            conn.commit()
            cur.close()
            conn.close()
            
            messages.success(request, 'Password berhasil diubah!')
            return redirect('register_login:dashboard')
            
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
    
    return render(request, 'change_password.html')