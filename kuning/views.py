from django.shortcuts import render, redirect

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
        'foto': 'https://example.com/simba.jpg',
    },
    {
        'id': 2,
        'nama': 'Melly',
        'spesies': 'Gajah',
        'asal': 'Sumatra',
        'tanggal_lahir': '2015-09-22',
        'status_kesehatan': 'Dalam Pemantauan',
        'habitat': 'Hutan Tropis',
        'foto': 'https://example.com/melly.jpg',
    },
    {
        'id': 3,
        'nama': 'Rio',
        'spesies': 'Harimau',
        'asal': 'Kalimantan',
        'tanggal_lahir': '2015-09-22',
        'status_kesehatan': 'Sakit',
        'habitat': 'Hutan Tropis',
        'foto': 'https://example.com/rio.jpg',
    },
    {
        'id': 4,
        'nama': 'Nala',
        'spesies': 'Zebra',
        'asal': 'Afrika',
        'tanggal_lahir': '2020-03-01',
        'status_kesehatan': 'Sehat',
        'habitat': 'Savana',
        'foto': 'https://example.com/nala.jpg',
    },
    {
        'id': 5,
        'nama': 'Bimo',
        'spesies': 'Orangutan',
        'asal': 'Kalimantan',
        'tanggal_lahir': '2016-07-19',
        'status_kesehatan': 'Sehat',
        'habitat': 'Hutan Tropis',
        'foto': 'https://example.com/bimo.jpg',
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

# SATWA
def list_satwa(request):
    return render(request, 'kuning/list_satwa.html', {'satwa': SATWA})

def tambah_satwa(request):
    return render(request, 'kuning/tambah_satwa.html', {'habitats': HABITAT})

def edit_satwa(request, id):
    satwa = next((item for item in SATWA if item["id"] == id), None)
    return render(request, 'kuning/edit_satwa.html', {'satwa': satwa, 'habitats': HABITAT})

# HABITAT
def list_habitat(request):
    return render(request, 'kuning/list_habitat.html', {'habitat': HABITAT})

def tambah_habitat(request):
    return render(request, 'kuning/tambah_habitat.html')

def edit_habitat(request, id):
    habitat = next((item for item in HABITAT if item["id"] == id), None)
    return render(request, 'kuning/edit_habitat.html', {'habitat': habitat})

def detail_habitat(request, id):
    habitat = next((item for item in HABITAT if item["id"] == id), None)
    satwa_di_habitat = [s for s in SATWA if s['habitat'] == habitat['nama']]
    return render(request, 'kuning/detail_habitat.html', {'habitat': habitat, 'satwa': satwa_di_habitat})
