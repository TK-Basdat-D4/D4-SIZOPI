from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages

# In-memory storage for medical records
medical_records = [
    {
        'id': 1,
        'tanggal': '2025-04-01',
        'dokter': 'Drh. Andi',
        'status': 'Sehat',
        'diagnosa': 'Tidak ada keluhan',
        'pengobatan': 'Tidak diperlukan',
        'catatan_tindak_lanjut': 'Periksa rutin 3 bulan ke depan'
    },
    {
        'id': 2,
        'tanggal': '2025-03-25',
        'dokter': 'Drh. Budi',
        'status': 'Sakit',
        'diagnosa': 'Infeksi pencernaan',
        'pengobatan': 'Antibiotik dan diet lunak',
        'catatan_tindak_lanjut': 'Pantau selama 1 minggu'
    },
    {
        'id': 3,
        'tanggal': '2025-02-20',
        'dokter': 'Drh. Clara',
        'status': 'Sakit',
        'diagnosa': 'Luka gores di kaki kanan',
        'pengobatan': 'Pembersihan luka dan salep antiseptik',
        'catatan_tindak_lanjut': 'Lihat kembali dalam 5 hari'
    }
]  

# Helper functions remain the same
def check_doctor_access(request):
    """Check if user is a logged-in doctor"""
    # Get user from session
    if 'user' not in request.session:
        messages.error(request, 'Silahkan login terlebih dahulu!')
        return False
    
    current_user = request.session['user']
    if current_user.get('role') != 'dokter_hewan':
        messages.error(request, 'Anda tidak memiliki akses ke halaman ini!')
        return False
    return True

def check_keeper_access(request):
    """Check if user is a logged-in animal keeper"""
    # Get user from session
    if 'user' not in request.session:
        messages.error(request, 'Silahkan login terlebih dahulu!')
        return False
    
    current_user = request.session['user']
    if not (current_user.get('role') == 'staff' and current_user.get('peran') == 'penjaga_hewan'):
        messages.error(request, 'Anda tidak memiliki akses ke halaman ini!')
        return False
    return True

# Rekam Medis Hewan - for doctors only
def rekam_medis_list(request):
    if not check_doctor_access(request):
        return redirect('register_login:login')
    
    # Sort records by date in descending order
    sorted_list = sorted(medical_records, key=lambda x: x['tanggal'], reverse=True)
    context = {
        'rekam_medis_list': sorted_list
    }
    return render(request, 'hijau_kesehatan_satwa/rekam_medis_list.html', context)

def rekam_medis_form(request):
    if not check_doctor_access(request):
        return redirect('register_login:login')
    
    if request.method == 'POST':
        try:
            # Generate new ID
            if not medical_records:
                new_id = 1
            else:
                new_id = max(record['id'] for record in medical_records) + 1
            
            # Get the doctor name from the form
            # If it's empty (old form without hidden field), use the session data
            dokter = request.POST.get('dokter')
            if not dokter and 'user' in request.session:
                # Format with "dr." prefix
                dokter = f"dr. {request.session['user'].get('nama_lengkap', '')}"
            
            # Create new record
            new_record = {
                'id': new_id,
                'tanggal': request.POST.get('tanggal'),
                'dokter': dokter,
                'status': request.POST.get('status'),
                'diagnosa': request.POST.get('diagnosa'),
                'pengobatan': request.POST.get('pengobatan'),
                'catatan_tindak_lanjut': request.POST.get('catatan_tindak_lanjut', '')
            }
            
            medical_records.append(new_record)
            messages.success(request, 'Data rekam medis hewan berhasil disimpan!')
            return redirect('hijau_kesehatan_satwa:rekam_medis_list')
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
    
    return render(request, 'hijau_kesehatan_satwa/rekam_medis_form.html')

def rekam_medis_edit(request, id):
    if not check_doctor_access(request):
        return redirect('register_login:login')
    
    # Find the record to edit
    record_to_edit = None
    for record in medical_records:
        if record['id'] == int(id):
            record_to_edit = record
            break
    
    if not record_to_edit:
        messages.error(request, 'Data tidak ditemukan!')
        return redirect('hijau_kesehatan_satwa:rekam_medis_list')
    
    if request.method == 'POST':
        try:
            # Get the doctor name from the form
            dokter = request.POST.get('dokter', record_to_edit['dokter'])
            
            # Update the record
            record_to_edit.update({
                'tanggal': request.POST.get('tanggal'),
                'dokter': dokter,
                'status': request.POST.get('status'),
                'diagnosa': request.POST.get('diagnosa'),
                'pengobatan': request.POST.get('pengobatan'),
                'catatan_tindak_lanjut': request.POST.get('catatan_tindak_lanjut', '')
            })
            
            messages.success(request, 'Data rekam medis hewan berhasil diperbarui!')
            return redirect('hijau_kesehatan_satwa:rekam_medis_list')
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
    
    context = {'rekam_medis': record_to_edit}
    return render(request, 'hijau_kesehatan_satwa/rekam_medis_form.html', context)

def rekam_medis_delete(request, id):
    if not check_doctor_access(request):
        return redirect('register_login:login')
    
    try:
        # Find and remove the record
        for i, record in enumerate(medical_records):
            if record['id'] == int(id):
                medical_records.pop(i)
                messages.success(request, 'Data rekam medis hewan berhasil dihapus!')
                break
    except Exception as e:
        messages.error(request, f'Terjadi kesalahan: {str(e)}')
    
    return redirect('hijau_kesehatan_satwa:rekam_medis_list')

# Jadwal Pemeriksaan Kesehatan - for doctors only
examination_schedules = [
    {'id': 1, 'tanggal': '2025-05-01'},
    {'id': 2, 'tanggal': '2025-08-01'},
    {'id': 3, 'tanggal': '2025-11-01'}
]  # In-memory storage for examination schedules

# Store frequency setting in memory
examination_frequency = 3  # Default frequency (3 months)

# Update the jadwal_pemeriksaan_list function
def jadwal_pemeriksaan_list(request):
    if not check_doctor_access(request):
        return redirect('register_login:login')
    
    # Sort schedules by date in ascending order (closest date first)
    sorted_schedules = sorted(examination_schedules, key=lambda x: x['tanggal'])
    
    context = {
        'jadwal_list': sorted_schedules,
        'frequency': examination_frequency  # Use the variable instead of hardcoded value
    }
    
    return render(request, 'hijau_kesehatan_satwa/jadwal_pemeriksaan_list.html', context)

def update_frequency(request):
    if not check_doctor_access(request):
        return redirect('register_login:login')
    
    if request.method == 'POST':
        try:
            global examination_frequency
            new_frequency = int(request.POST.get('frequency', 3))
            
            # Validate frequency (optional: you can add more validation)
            if new_frequency < 1:
                messages.error(request, 'Frekuensi harus lebih dari atau sama dengan 1 bulan!')
            else:
                examination_frequency = new_frequency
                messages.success(request, f'Frekuensi pemeriksaan berhasil diubah menjadi {examination_frequency} bulan!')
        except ValueError:
            messages.error(request, 'Frekuensi harus berupa angka!')
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
    
    return redirect('hijau_kesehatan_satwa:jadwal_pemeriksaan_list')

def jadwal_pemeriksaan_form(request):
    if not check_doctor_access(request):
        return redirect('register_login:login')
    
    if request.method == 'POST':
        try:
            # Generate new ID
            if not examination_schedules:
                new_id = 1
            else:
                new_id = max(schedule['id'] for schedule in examination_schedules) + 1
            
            # Create new schedule
            new_schedule = {
                'id': new_id,
                'tanggal': request.POST.get('tanggal'),
            }
            
            examination_schedules.append(new_schedule)
            messages.success(request, 'Jadwal pemeriksaan berhasil disimpan!')
            return redirect('hijau_kesehatan_satwa:jadwal_pemeriksaan_list')
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
    
    return render(request, 'hijau_kesehatan_satwa/jadwal_pemeriksaan_form.html')

def jadwal_pemeriksaan_delete(request, id):
    if not check_doctor_access(request):
        return redirect('register_login:login')
    
    try:
        # Find and remove the schedule
        for i, schedule in enumerate(examination_schedules):
            if schedule['id'] == int(id):
                examination_schedules.pop(i)
                messages.success(request, 'Jadwal pemeriksaan berhasil dihapus!')
                break
    except Exception as e:
        messages.error(request, f'Terjadi kesalahan: {str(e)}')
    
    return redirect('hijau_kesehatan_satwa:jadwal_pemeriksaan_list')

# Tambahkan fungsi jadwal_pemeriksaan_edit di bagian jadwal pemeriksaan
def jadwal_pemeriksaan_edit(request, id):
    if not check_doctor_access(request):
        return redirect('register_login:login')
    
    # Find the schedule to edit
    schedule_to_edit = None
    for schedule in examination_schedules:
        if schedule['id'] == int(id):
            schedule_to_edit = schedule
            break
    
    if not schedule_to_edit:
        messages.error(request, 'Jadwal tidak ditemukan!')
        return redirect('hijau_kesehatan_satwa:jadwal_pemeriksaan_list')
    
    if request.method == 'POST':
        try:
            # Update the schedule
            schedule_to_edit.update({
                'tanggal': request.POST.get('tanggal')
            })
            
            messages.success(request, 'Jadwal pemeriksaan berhasil diperbarui!')
            return redirect('hijau_kesehatan_satwa:jadwal_pemeriksaan_list')
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
    
    context = {'schedule': schedule_to_edit}
    return render(request, 'hijau_kesehatan_satwa/jadwal_pemeriksaan_form.html', context)

# Dictionary of available animals (for demonstration)
# In a real application, this would be fetched from the database
animals = {
    1: {
        'nama_individu': 'Harimau Sumatera',
        'spesies': 'Panthera tigris sumatrae',
        'asal_hewan': 'Sumatera',
        'tanggal_lahir': '2018-05-15',
        'habitat': 'Kandang Harimau Besar',
        'status_kesehatan': 'Sehat',
    },
    2: {
        'nama_individu': 'Gajah Sumatera',
        'spesies': 'Elephas maximus sumatranus',
        'asal_hewan': 'Lampung',
        'tanggal_lahir': '2015-09-12',
        'habitat': 'Kandang Besar Tengah',
        'status_kesehatan': 'Sehat',
    },
    3: {
        'nama_individu': 'Komodo',
        'spesies': 'Varanus komodoensis',
        'asal_hewan': 'Nusa Tenggara Timur',
        'tanggal_lahir': '2017-03-21',
        'habitat': 'Zona Reptil',
        'status_kesehatan': 'Sehat',
    },
    4: {
        'nama_individu': 'Orangutan Kalimantan',
        'spesies': 'Pongo pygmaeus',
        'asal_hewan': 'Kalimantan Tengah',
        'tanggal_lahir': '2012-06-01',
        'habitat': 'Kubah Primata',
        'status_kesehatan': 'Dalam Perawatan',
    }
}

# In-memory storage for feeding schedules
feeding_schedules = [
    {
        'id': 1,
        'animal_id': 1,  # Harimau Sumatera
        'jenis_pakan': 'Daging Sapi',
        'jumlah': '4 kg',
        'jadwal': '2025-04-29 07:00',
        'status': 'Menunggu Pemberian'
    },
    {
        'id': 2,
        'animal_id': 4,  # Orangutan Kalimantan
        'jenis_pakan': 'Buah Campur',
        'jumlah': '3 kg',
        'jadwal': '2025-04-29 12:00',
        'status': 'Menunggu Pemberian'
    },
    {
        'id': 3,
        'animal_id': 3,  # Komodo
        'jenis_pakan': 'Pelet Ikan',
        'jumlah': '5 kg',
        'jadwal': '2025-04-29 17:00',
        'status': 'Menunggu Pemberian'
    }
]

# In-memory storage for feeding history
feeding_history = [
    {
        'id': 1,
        'penjaga_id': 101,
        'penjaga_nama': 'Siti',
        'nama_individu': 'Gajah Sumatera',
        'spesies': 'Elephas maximus sumatranus',
        'asal_hewan': 'Lampung',
        'tanggal_lahir': '2015-09-12',
        'habitat': 'Kandang Besar Tengah',
        'status_kesehatan': 'Sehat',
        'jenis_pakan': 'Rumput dan buah',
        'jumlah': '15 kg',
        'jadwal': '2025-04-28 09:00'
    },
    {
        'id': 2,
        'penjaga_id': 102,
        'penjaga_nama': 'Joko',
        'nama_individu': 'Komodo',
        'spesies': 'Varanus komodoensis',
        'asal_hewan': 'Nusa Tenggara Timur',
        'tanggal_lahir': '2017-03-21',
        'habitat': 'Zona Reptil',
        'status_kesehatan': 'Sehat',
        'jenis_pakan': 'Daging Ayam',
        'jumlah': '2 kg',
        'jadwal': '2025-04-28 15:00'
    },
    {
        'id': 3,
        'penjaga_id': 101,
        'penjaga_nama': 'Siti',
        'nama_individu': 'Orangutan Kalimantan',
        'spesies': 'Pongo pygmaeus',
        'asal_hewan': 'Kalimantan Tengah',
        'tanggal_lahir': '2012-06-01',
        'habitat': 'Kubah Primata',
        'status_kesehatan': 'Dalam Perawatan',
        'jenis_pakan': 'Buah dan Sayur',
        'jumlah': '6 kg',
        'jadwal': '2025-04-27 08:30'
    }
]


def pemberian_pakan_list(request):
    if not check_keeper_access(request):
        return redirect('register_login:login')
    
    # Sort feeding schedules by date
    sorted_schedules = sorted(feeding_schedules, key=lambda x: x['jadwal'])
    
    context = {
        'feeding_schedules': sorted_schedules
    }
    return render(request, 'hijau_kesehatan_satwa/pemberian_pakan_list.html', context)

def riwayat_pemberian_pakan(request):
    if not check_keeper_access(request):
        return redirect('register_login:login')
    
    # Get current user
    current_user = request.session.get('user', {})
    
    # Filter history for the current keeper if user ID exists
    if 'id' in current_user:
        user_history = [
            record for record in feeding_history 
            if record.get('penjaga_id') == current_user.get('id')
        ]
    else:
        # If no user ID, show all records (for demonstration)
        user_history = feeding_history
    
    # Sort by date in descending order
    sorted_history = sorted(user_history, key=lambda x: x['jadwal'], reverse=True)
    
    context = {
        'feeding_history': sorted_history
    }
    return render(request, 'hijau_kesehatan_satwa/riwayat_pemberian_pakan.html', context)

def pemberian_pakan_form(request):
    if not check_keeper_access(request):
        return redirect('register_login:login')
    
    if request.method == 'POST':
        try:
            # Generate new ID
            if not feeding_schedules:
                new_id = 1
            else:
                new_id = max(schedule['id'] for schedule in feeding_schedules) + 1
            
            # Get animal ID from form
            animal_id = int(request.POST.get('animal_id', 1))
            
            # Create new feeding schedule
            new_schedule = {
                'id': new_id,
                'animal_id': animal_id,
                'jenis_pakan': request.POST.get('jenis'),
                'jumlah': request.POST.get('jumlah'),
                'jadwal': request.POST.get('jadwal'),
                'status': 'Menunggu Pemberian'  # Default status
            }
            
            feeding_schedules.append(new_schedule)
            messages.success(request, 'Data pemberian pakan berhasil disimpan!')
            return redirect('hijau_kesehatan_satwa:pemberian_pakan_list')
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
    
    # Pass the animals dictionary to the template
    context = {'animals': animals}
    return render(request, 'hijau_kesehatan_satwa/pemberian_pakan_form.html', context)

def pemberian_pakan_edit(request, id):
    if not check_keeper_access(request):
        return redirect('register_login:login')
    
    # Find the schedule to edit
    schedule_to_edit = None
    for schedule in feeding_schedules:
        if schedule['id'] == int(id):
            schedule_to_edit = schedule
            break
    
    if not schedule_to_edit:
        messages.error(request, 'Data tidak ditemukan!')
        return redirect('hijau_kesehatan_satwa:pemberian_pakan_list')
    
    if request.method == 'POST':
        try:
            # Get animal ID from form
            animal_id = int(request.POST.get('animal_id', schedule_to_edit.get('animal_id', 1)))
            
            # Update the schedule
            schedule_to_edit.update({
                'animal_id': animal_id,
                'jenis_pakan': request.POST.get('jenis'),
                'jumlah': request.POST.get('jumlah'),
                'jadwal': request.POST.get('jadwal')
            })
            
            messages.success(request, 'Data pemberian pakan berhasil diperbarui!')
            return redirect('hijau_kesehatan_satwa:pemberian_pakan_list')
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
    
    # Pass the animals dictionary and the schedule to the template
    context = {
        'feeding': schedule_to_edit,
        'animals': animals
    }
    return render(request, 'hijau_kesehatan_satwa/pemberian_pakan_form.html', context)

def pemberian_pakan_delete(request, id):
    if not check_keeper_access(request):
        return redirect('register_login:login')
    
    try:
        # Find and remove the schedule
        for i, schedule in enumerate(feeding_schedules):
            if schedule['id'] == int(id):
                feeding_schedules.pop(i)
                messages.success(request, 'Data pemberian pakan berhasil dihapus!')
                break
    except Exception as e:
        messages.error(request, f'Terjadi kesalahan: {str(e)}')
    
    return redirect('hijau_kesehatan_satwa:pemberian_pakan_list')

def beri_pakan(request, id):
    if not check_keeper_access(request):
        return redirect('register_login:login')
    
    try:
        # Find the feeding schedule
        schedule = None
        for s in feeding_schedules:
            if s['id'] == int(id):
                schedule = s
                break
        
        if not schedule:
            messages.error(request, 'Data tidak ditemukan!')
            return redirect('hijau_kesehatan_satwa:pemberian_pakan_list')
        
        # Update the status
        schedule['status'] = 'Selesai Diberikan'
        
        # Get current user
        current_user = request.session.get('user', {})
        
        # Get animal data
        animal_id = schedule.get('animal_id', 1)
        animal_data = animals.get(animal_id, {})
        
        # Add to feeding history with proper animal details
        feeding_history.append({
            'id': len(feeding_history) + 1,
            'penjaga_id': current_user.get('id', 0),
            'penjaga_nama': current_user.get('nama_lengkap', 'Tidak Diketahui'),
            'nama_individu': animal_data.get('nama_individu', 'Tidak Diketahui'),
            'spesies': animal_data.get('spesies', 'Tidak Diketahui'),
            'asal_hewan': animal_data.get('asal_hewan', 'Tidak Diketahui'),
            'tanggal_lahir': animal_data.get('tanggal_lahir', ''),
            'habitat': animal_data.get('habitat', 'Tidak Diketahui'),
            'status_kesehatan': animal_data.get('status_kesehatan', 'Tidak Diketahui'),
            'jenis_pakan': schedule['jenis_pakan'],
            'jumlah': schedule['jumlah'],
            'jadwal': schedule['jadwal']
        })
        
        messages.success(request, 'Pemberian pakan berhasil dicatat!')
    except Exception as e:
        messages.error(request, f'Terjadi kesalahan: {str(e)}')
    
    return redirect('hijau_kesehatan_satwa:pemberian_pakan_list')