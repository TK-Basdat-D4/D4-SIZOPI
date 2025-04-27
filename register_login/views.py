# Create your views here.
from django.shortcuts import render, redirect
from django.contrib import messages

# Dummy users database (in-memory storage)
users = [
    # Pengunjung
    {
        'role': 'pengunjung',
        'username': 'pengunjung123',
        'password': 'Visit@123',
        'nama_depan': 'Budi',
        'nama_tengah': '',
        'nama_belakang': 'Santoso',
        'email': 'budi.santoso@email.com',
        'nomor_telepon': '081234567890',
        'alamat': 'Jl. Kebun Raya No. 10, Bandung',
        'tanggal_lahir': '1995-08-20'
    },
    # Dokter Hewan
    {
        'role': 'dokter_hewan',
        'username': 'drhewan456',
        'password': 'Vet!456',
        'nama_depan': 'Siti',
        'nama_tengah': 'Nur',
        'nama_belakang': 'Hidayah',
        'email': 'siti.hidayah@vetclinic.com',
        'nomor_telepon': '081298765432',
        'nomor_sertifikasi': 'VET-2024-001',
        'spesialisasi': ['Mamalia Besar']
    },
    # Staff Penjaga Hewan
    {
        'role': 'staff',
        'username': 'penjaga789',
        'password': 'ZooKeeper@789',
        'nama_depan': 'Andi',
        'nama_tengah': '',
        'nama_belakang': 'Wijaya',
        'email': 'andi.wijaya@zoo.com',
        'nomor_telepon': '082112223333',
        'peran': 'penjaga_hewan',
        'staff_id': 'PJH001'
    },
    # Staff Administrasi
    {
        'role': 'staff',
        'username': 'admin321',
        'password': 'Admin#321',
        'nama_depan': 'Lina',
        'nama_tengah': '',
        'nama_belakang': 'Pratiwi',
        'email': 'lina.pratiwi@zoo.com',
        'nomor_telepon': '085566778899',
        'peran': 'staff_administrasi',
        'staff_id': 'ADM001'
    },
    # Staff Pelatih Pertunjukan
    {
        'role': 'staff',
        'username': 'pelatih654',
        'password': 'Trainer!654',
        'nama_depan': 'Rizky',
        'nama_tengah': '',
        'nama_belakang': 'Saputra',
        'email': 'rizky.saputra@zoo.com',
        'nomor_telepon': '087712341234',
        'peran': 'pelatih_pertunjukan',
        'staff_id': 'PLP001'
    }
]

# Variable to store currently logged in user
current_user = {}

def home(request):
    """Home page that can be accessed by guests"""
    return render(request, "home.html", {"current_user": current_user})

def choose_role(request):
    """Page to choose registration role"""
    return render(request, "choose_role.html")

def register_pengunjung(request):
    """Registration form for Visitors"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        email = request.POST.get('email')
        
        # Validate form data
        if password != confirm_password:
            messages.error(request, 'Password dan Konfirmasi Password tidak cocok!')
            return render(request, 'register_pengunjung.html')
        
        # Check if username already exists
        for user in users:
            if user.get('username') == username:
                messages.error(request, 'Username sudah terdaftar!')
                return render(request, 'register_pengunjung.html')
            
            if user.get('email') == email:
                messages.error(request, 'Email sudah terdaftar!')
                return render(request, 'register_pengunjung.html')
        
        # Create new user
        new_user = {
            'role': 'pengunjung',
            'username': username,
            'password': password,
            'nama_depan': request.POST.get('nama_depan'),
            'nama_tengah': request.POST.get('nama_tengah', ''),
            'nama_belakang': request.POST.get('nama_belakang'),
            'email': email,
            'nomor_telepon': request.POST.get('nomor_telepon'),
            'alamat': request.POST.get('alamat_lengkap'),
            'tanggal_lahir': request.POST.get('tanggal_lahir')
        }
        
        users.append(new_user)
        messages.success(request, 'Pendaftaran berhasil! Silahkan login.')
        return redirect('register_login:login')
    
    return render(request, 'register_pengunjung.html')

def register_dokter(request):
    """Registration form for Veterinarians"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        email = request.POST.get('email')
        nomor_sertifikasi = request.POST.get('nomor_sertifikasi')
        
        # Validate form data
        if password != confirm_password:
            messages.error(request, 'Password dan Konfirmasi Password tidak cocok!')
            return render(request, 'register_dokter.html')
        
        # Check if username already exists
        for user in users:
            if user.get('username') == username:
                messages.error(request, 'Username sudah terdaftar!')
                return render(request, 'register_dokter.html')
            
            if user.get('email') == email:
                messages.error(request, 'Email sudah terdaftar!')
                return render(request, 'register_dokter.html')
                
            if user.get('nomor_sertifikasi') == nomor_sertifikasi:
                messages.error(request, 'Nomor Sertifikasi sudah terdaftar!')
                return render(request, 'register_dokter.html')
        
        # Get specializations
        spesialisasi = []
        if request.POST.get('mamalia_besar'):
            spesialisasi.append('Mamalia Besar')
        if request.POST.get('reptil'):
            spesialisasi.append('Reptil')
        if request.POST.get('burung_eksotis'):
            spesialisasi.append('Burung Eksotis')
        if request.POST.get('primata'):
            spesialisasi.append('Primata')
        if request.POST.get('lainnya'):
            spesialisasi.append(f"Lainnya: {request.POST.get('lainnya_isian')}")
        
        # Create new user
        new_user = {
            'role': 'dokter_hewan',
            'username': username,
            'password': password,
            'nama_depan': request.POST.get('nama_depan'),
            'nama_tengah': request.POST.get('nama_tengah', ''),
            'nama_belakang': request.POST.get('nama_belakang'),
            'email': email,
            'nomor_telepon': request.POST.get('nomor_telepon'),
            'nomor_sertifikasi': nomor_sertifikasi,
            'spesialisasi': spesialisasi
        }
        
        users.append(new_user)
        messages.success(request, 'Pendaftaran berhasil! Silahkan login.')
        return redirect('register_login:login')
    
    return render(request, 'register_dokter.html')

def register_staff(request):
    """Registration form for Staff"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        email = request.POST.get('email')
        peran = request.POST.get('peran')
        
        # Validate form data
        if password != confirm_password:
            messages.error(request, 'Password dan Konfirmasi Password tidak cocok!')
            return render(request, 'register_staff.html')
        
        # Check if username already exists
        for user in users:
            if user.get('username') == username:
                messages.error(request, 'Username sudah terdaftar!')
                return render(request, 'register_staff.html')
            
            if user.get('email') == email:
                messages.error(request, 'Email sudah terdaftar!')
                return render(request, 'register_staff.html')
        
        # Generate ID based on role
        import random
        id_prefix = ''
        if peran == 'penjaga_hewan':
            id_prefix = 'PJH'
        elif peran == 'staff_administrasi':
            id_prefix = 'ADM'
        elif peran == 'pelatih_pertunjukan':
            id_prefix = 'PLP'
            
        staff_id = f"{id_prefix}{random.randint(100, 999)}"
        
        # Create new user
        new_user = {
            'role': 'staff',
            'username': username,
            'password': password,
            'nama_depan': request.POST.get('nama_depan'),
            'nama_tengah': request.POST.get('nama_tengah', ''),
            'nama_belakang': request.POST.get('nama_belakang'),
            'email': email,
            'nomor_telepon': request.POST.get('nomor_telepon'),
            'peran': peran,
            'staff_id': staff_id
        }
        
        users.append(new_user)
        messages.success(request, 'Pendaftaran berhasil! Silahkan login.')
        return redirect('register_login:login')
    
    return render(request, 'register_staff.html')

def login(request):
    """Login page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        global current_user
        
        # Check credentials
        for user in users:
            if user['username'] == username and user['password'] == password:
                current_user = user
                messages.success(request, f"Selamat datang, {user['nama_depan']}!")
                return redirect('register_login:profile')
        
        # If credentials don't match
        messages.error(request, 'Username atau Password salah!')
    
    return render(request, 'login.html')

def logout(request):
    """Logout function"""
    global current_user
    current_user = {}
    messages.success(request, 'Berhasil logout!')
    return redirect('register_login:login')

def profile(request):
    """Profile page based on user role"""
    global current_user
    
    if not current_user:
        messages.error(request, 'Silahkan login terlebih dahulu!')
        return redirect('register_login:login')
    
    if current_user['role'] == 'pengunjung':
        return render(request, 'profile_pengunjung.html', {'user': current_user})
    elif current_user['role'] == 'dokter_hewan':
        return render(request, 'profile_dokter.html', {'user': current_user})
    else:  # staff
        return render(request, 'profile_staff.html', {'user': current_user})