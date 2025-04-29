from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
import copy

# Dummy Data
SATWA = [
    {
        'id': 1,
        'nama': 'Simba',
        'spesies': 'Singa',
        'asal': 'Afrika',
        'tanggal_lahir': '2018-05-12',
        'status_kesehatan': 'Sehat',
        'habitat': 'Savana',
        'foto': 'https://surya24.com/assets/berita/original/79029453639-penampakan-raja-_hutan.jpg',
    },
    {
        'id': 2,
        'nama': 'Melly',
        'spesies': 'Gajah',
        'asal': 'Sumatra',
        'tanggal_lahir': '2015-09-22',
        'status_kesehatan': 'Dalam Pemantauan',
        'habitat': 'Hutan Tropis',
        'foto': 'https://cdn.rri.co.id/berita/Takengon/o/1731248243686-images/pjl1zf2bir98gvi.jpeg',
    },
    {
        'id': 3,
        'nama': 'Rio',
        'spesies': 'Harimau',
        'asal': 'Kalimantan',
        'tanggal_lahir': '2015-09-22',
        'status_kesehatan': 'Sakit',
        'habitat': 'Hutan Tropis',
        'foto': 'https://encrypted-tbn1.gstatic.com/images?q=tbn:ANd9GcSRqlFDv0i1EfNdgx1rPszk5CbLOh0KnsOBBE3_k4WfIck_WQuXlQTCHpTJMJNv2PrvGD8zNLprf6_W3AKmWDVR7A',
    },
    {
        'id': 4,
        'nama': 'Nala',
        'spesies': 'Zebra',
        'asal': 'Afrika',
        'tanggal_lahir': '2020-03-01',
        'status_kesehatan': 'Sehat',
        'habitat': 'Savana',
        'foto': 'https://www.treehugger.com/thmb/mIDnBoZOKmqQ74EHwi-QDbQBeRM=/750x0/filters:no_upscale():max_bytes(150000):strip_icc():format(webp)/GettyImages-1043597638-49acd69677d7442588c1d8930d298a59.jpg',
    },
    {
        'id': 5,
        'nama': 'Bimo',
        'spesies': 'Orangutan',
        'asal': 'Kalimantan',
        'tanggal_lahir': '2016-07-19',
        'status_kesehatan': 'Sehat',
        'habitat': 'Hutan Tropis',
        'foto': 'https://cdn.betahita.id/5/8/9/7/5897.jpeg',
    }
]

HABITAT = [
    {
        'id': 1,
        'nama': 'Savana',
        'luas_area': '5000',
        'kapasitas_maksimal': '25',
        'status_lingkungan': 'Suhu: 30°C, Kelembapan: 40%, Vegetasi: Rumput luas'
    },
    {
        'id': 2,
        'nama': 'Hutan Tropis',
        'luas_area': '8200',
        'kapasitas_maksimal': '40',
        'status_lingkungan': 'Suhu: 28°C, Kelembapan: 85%, Pepohonan lebat'
    },
    {
        'id': 3,
        'nama': 'Padang Rumput',
        'luas_area': '3000',
        'kapasitas_maksimal': '15',
        'status_lingkungan': 'Suhu: 32°C, Kelembapan: 50%, Terbuka tanpa kanopi'
    }
]

# Helper function to get next available ID
def get_next_satwa_id():
    return max(satwa['id'] for satwa in SATWA) + 1 if SATWA else 1

def get_next_habitat_id():
    return max(habitat['id'] for habitat in HABITAT) + 1 if HABITAT else 1

# SATWA CRUD Operations
def list_satwa(request):
    # Make a copy of the data to avoid modifying the original
    satwa_display = copy.deepcopy(SATWA)
    return render(request, 'list_satwa.html', {'satwa': satwa_display})

def tambah_satwa(request):
    if request.method == 'POST':
        # Get form data
        nama = request.POST.get('nama', '')
        spesies = request.POST.get('spesies')
        asal = request.POST.get('asal')
        tanggal_lahir = request.POST.get('tanggal_lahir', '')
        status_kesehatan = request.POST.get('status_kesehatan')
        # Get only the habitat name, not the full object
        habitat = request.POST.get('habitat')
        foto = request.POST.get('foto', '')
        
        # Create new satwa
        new_satwa = {
            'id': get_next_satwa_id(),
            'nama': nama,
            'spesies': spesies,
            'asal': asal,
            'tanggal_lahir': tanggal_lahir,
            'status_kesehatan': status_kesehatan,
            'habitat': habitat,  # Store only the habitat name
            'foto': foto
        }
        
        # Add to list
        SATWA.append(new_satwa)
        
        # Redirect to list page
        return redirect('kuning:list_satwa')
    
    # GET request - show form
    # Pass only habitat names for the dropdown
    habitat_names = [h['nama'] for h in HABITAT]
    return render(request, 'tambah_satwa.html', {'habitats': habitat_names})

def edit_satwa(request, id):
    # Find satwa by id
    satwa = next((item for item in SATWA if item["id"] == id), None)
    
    if not satwa:
        return HttpResponse("Satwa tidak ditemukan", status=404)
    
    if request.method == 'POST':
        # Update data
        satwa['nama'] = request.POST.get('nama', '')
        satwa['spesies'] = request.POST.get('spesies')
        satwa['asal'] = request.POST.get('asal')
        satwa['tanggal_lahir'] = request.POST.get('tanggal_lahir', '')
        satwa['status_kesehatan'] = request.POST.get('status_kesehatan')
        # Get only the habitat name, not the full object
        satwa['habitat'] = request.POST.get('habitat')
        satwa['foto'] = request.POST.get('foto', '')
        
        # Redirect to list page
        return redirect('kuning:list_satwa')
    
    # GET request - show form with satwa data
    # Pass only habitat names for the dropdown
    habitat_names = [h['nama'] for h in HABITAT]
    return render(request, 'edit_satwa.html', {'satwa': satwa, 'habitats': habitat_names})

def hapus_satwa(request, id):
    global SATWA
    # Find satwa by id and remove
    SATWA = [item for item in SATWA if item["id"] != id]
    return redirect('kuning:list_satwa')

# HABITAT CRUD Operations
def list_habitat(request):
    return render(request, 'list_habitat.html', {'habitat': HABITAT})

def tambah_habitat(request):
    if request.method == 'POST':
        # Get form data
        nama = request.POST.get('nama')
        luas_area = request.POST.get('luas_area')
        kapasitas_maksimal = request.POST.get('kapasitas_maksimal')
        status_lingkungan = request.POST.get('status_lingkungan')
        
        # Create new habitat
        new_habitat = {
            'id': get_next_habitat_id(),
            'nama': nama,
            'luas_area': luas_area,
            'kapasitas_maksimal': kapasitas_maksimal,
            'status_lingkungan': status_lingkungan
        }
        
        # Add to list
        HABITAT.append(new_habitat)
        
        # Redirect to list page
        return redirect('kuning:list_habitat')
    
    # GET request - show form
    return render(request, 'tambah_habitat.html')

def edit_habitat(request, id):
    # Find habitat by id
    habitat = next((item for item in HABITAT if item["id"] == id), None)
    
    if not habitat:
        return HttpResponse("Habitat tidak ditemukan", status=404)
    
    if request.method == 'POST':
        # Update data
        habitat['nama'] = request.POST.get('nama')
        habitat['luas_area'] = request.POST.get('luas_area')
        habitat['kapasitas_maksimal'] = request.POST.get('kapasitas_maksimal')
        habitat['status_lingkungan'] = request.POST.get('status_lingkungan')
        
        # Redirect to list page
        return redirect('kuning:list_habitat')
    
    # GET request - show form with habitat data
    return render(request, 'edit_habitat.html', {'habitat': habitat})

def detail_habitat(request, id):
    # Find habitat by id
    habitat = next((item for item in HABITAT if item["id"] == id), None)
    
    if not habitat:
        return HttpResponse("Habitat tidak ditemukan", status=404)
    
    # Find all satwa in this habitat
    satwa_di_habitat = [s for s in SATWA if s['habitat'] == habitat['nama']]
    
    return render(request, 'detail_habitat.html', {'habitat': habitat, 'hewan_habitat': satwa_di_habitat})

def hapus_habitat(request, id):
    global HABITAT
    
    # Check if any animals are living in this habitat
    habitat = next((item for item in HABITAT if item["id"] == id), None)
    
    if habitat:
        # Check if any animals are in this habitat
        satwa_di_habitat = [s for s in SATWA if s['habitat'] == habitat['nama']]
        
        if satwa_di_habitat:
            # Return error message if habitat has animals
            return render(request, 'list_habitat.html', {
                'habitat': HABITAT,
                'error': f"Tidak dapat menghapus habitat {habitat['nama']} karena masih ada satwa yang tinggal di dalamnya."
            })
    
    # Remove habitat if no animals are living there
    HABITAT = [item for item in HABITAT if item["id"] != id]
    return redirect('kuning:list_habitat')