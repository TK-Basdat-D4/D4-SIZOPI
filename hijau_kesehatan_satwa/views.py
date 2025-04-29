from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages

# Rename the list to avoid conflict with the function
medical_records = []  # In-memory storage for medical records

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
            
            # Create new record
            new_record = {
                'id': new_id,
                'tanggal': request.POST.get('tanggal'),
                'dokter': request.POST.get('dokter'),
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
            # Update the record
            record_to_edit.update({
                'tanggal': request.POST.get('tanggal'),
                'dokter': request.POST.get('dokter'),
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
# Add this at the top of your views.py file, after the medical_records list
examination_schedules = []  # In-memory storage for examination schedules

# Update the jadwal_pemeriksaan_list function
def jadwal_pemeriksaan_list(request):
    if not check_doctor_access(request):
        return redirect('register_login:login')
    
    # Sort schedules by date in ascending order (closest date first)
    sorted_schedules = sorted(examination_schedules, key=lambda x: x['tanggal'])
    
    context = {
        'jadwal_list': sorted_schedules,
        # Add a default frequency - in a real app, this would come from settings or animal's data
        'frequency': 3  
    }
    
    return render(request, 'hijau_kesehatan_satwa/jadwal_pemeriksaan_list.html', context)

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
                # You could add more fields here if needed, 
                # like 'notes' or 'reason' for the examination
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

# Add this at the top of your views.py file, after the examination_schedules list
feeding_schedules = []  # In-memory storage for feeding schedules
feeding_history = []  # In-memory storage for feeding history

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
    current_user = getattr(request, 'current_user', {})
    
    # Filter history for the current keeper
    user_history = [
        record for record in feeding_history 
        if record.get('penjaga_id') == current_user.get('id')
    ]
    
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
            
            # Create new feeding schedule
            new_schedule = {
                'id': new_id,
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
    
    return render(request, 'hijau_kesehatan_satwa/pemberian_pakan_form.html')

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
            # Update the schedule
            schedule_to_edit.update({
                'jenis_pakan': request.POST.get('jenis'),
                'jumlah': request.POST.get('jumlah'),
                'jadwal': request.POST.get('jadwal')
            })
            
            messages.success(request, 'Data pemberian pakan berhasil diperbarui!')
            return redirect('hijau_kesehatan_satwa:pemberian_pakan_list')
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
    
    context = {'feeding': schedule_to_edit}
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
        current_user = getattr(request, 'current_user', {})
        
        # Add to feeding history
        # In a real app, you would include more animal details
        feeding_history.append({
            'id': len(feeding_history) + 1,
            'penjaga_id': current_user.get('id'),
            'penjaga_nama': current_user.get('nama', 'Unknown'),
            'nama_individu': 'Sample Animal',  # This would come from a real database
            'spesies': 'Sample Species',       # This would come from a real database
            'asal_hewan': 'Sample Origin',     # This would come from a real database
            'tanggal_lahir': '2020-01-01',     # This would come from a real database
            'habitat': 'Sample Habitat',       # This would come from a real database
            'status_kesehatan': 'Sehat',       # This would come from a real database
            'jenis_pakan': schedule['jenis_pakan'],
            'jumlah': schedule['jumlah'],
            'jadwal': schedule['jadwal']
        })
        
        messages.success(request, 'Pemberian pakan berhasil dicatat!')
    except Exception as e:
        messages.error(request, f'Terjadi kesalahan: {str(e)}')
    
    return redirect('hijau_kesehatan_satwa:pemberian_pakan_list')