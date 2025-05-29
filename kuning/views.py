from django.shortcuts import render, redirect
from django.http import HttpResponse
from utils.db_utils import get_db_connection
import uuid
from datetime import datetime

# SATWA CRUD Operations
def list_satwa(request):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Query untuk mengambil semua data hewan beserta habitat
        query = """
            SELECT h.id, h.nama, h.spesies, h.asal_hewan, h.tanggal_lahir, 
                   h.status_kesehatan, h.nama_habitat, h.url_foto
            FROM sizopi.hewan h
            ORDER BY h.nama
        """
        cursor.execute(query)
        satwa_data = cursor.fetchall()
        
        # Convert to list of dictionaries
        satwa = []
        for row in satwa_data:
            satwa.append({
                'id': row[0],
                'nama': row[1],
                'spesies': row[2],
                'asal': row[3],
                'tanggal_lahir': row[4],
                'status_kesehatan': row[5],
                'habitat': row[6],
                'foto': row[7]
            })
        
        return render(request, 'list_satwa.html', {'satwa': satwa})
    
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)
    finally:
        cursor.close()
        connection.close()

def tambah_satwa(request):
    if request.method == 'POST':
        connection = get_db_connection()
        cursor = connection.cursor()
        
        try:
            # Get form data
            nama = request.POST.get('nama', '')
            spesies = request.POST.get('spesies')
            asal = request.POST.get('asal')
            tanggal_lahir = request.POST.get('tanggal_lahir', None)
            status_kesehatan = request.POST.get('status_kesehatan')
            habitat = request.POST.get('habitat')
            foto = request.POST.get('foto', '')
            
            # Generate UUID for new hewan
            hewan_id = str(uuid.uuid4())
            
            # Convert empty string to None for date
            if tanggal_lahir == '':
                tanggal_lahir = None
            
            # Insert new hewan
            insert_query = """
                INSERT INTO sizopi.hewan 
                (id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                hewan_id, nama, spesies, asal, tanggal_lahir, 
                status_kesehatan, habitat, foto
            ))
            
            connection.commit()
            return redirect('kuning:list_satwa')
            
        except Exception as e:
            connection.rollback()
            error_message = str(e)
            
            # Clean up error message
            if "CONTEXT:" in error_message:
                error_message = error_message.split("CONTEXT:")[0]
            if "PL/pgSQL function" in error_message:
                error_message = error_message.split("PL/pgSQL function")[0]
            error_message = error_message.strip()
            
            # Get habitat names for dropdown (needed to re-render the form)
            cursor.execute("SELECT nama FROM sizopi.habitat ORDER BY nama")
            habitat_data = cursor.fetchall()
            habitat_names = [row[0] for row in habitat_data]
            
            # Re-render form with error message
            context = {
                'error_message': error_message,
                'habitats': habitat_names,
                'satwa': {
                    'nama': nama,
                    'spesies': spesies,
                    'asal': asal,
                    'tanggal_lahir': tanggal_lahir,
                    'status_kesehatan': status_kesehatan,
                    'habitat': habitat,
                    'foto': foto
                }
            }
            return render(request, 'tambah_satwa.html', context)
        finally:
            cursor.close()
            connection.close()
    
    # GET request - show form
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Get habitat names for dropdown
        cursor.execute("SELECT nama FROM sizopi.habitat ORDER BY nama")
        habitat_data = cursor.fetchall()
        habitat_names = [row[0] for row in habitat_data]
        
        return render(request, 'tambah_satwa.html', {'habitats': habitat_names})
    
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)
    finally:
        cursor.close()
        connection.close()

def edit_satwa(request, id):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Find satwa by id - convert string to UUID if needed
        if isinstance(id, str):
            hewan_id = id
        else:
            hewan_id = str(id)
            
        cursor.execute("SELECT id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto FROM sizopi.hewan WHERE id::text = %s", (hewan_id,))
        satwa_data = cursor.fetchone()
        
        if not satwa_data:
            return HttpResponse("Satwa tidak ditemukan", status=404)
        
        if request.method == 'POST':
            # Update data
            nama = request.POST.get('nama', '')
            spesies = request.POST.get('spesies')
            asal = request.POST.get('asal')
            tanggal_lahir = request.POST.get('tanggal_lahir', None)
            status_kesehatan = request.POST.get('status_kesehatan')
            habitat = request.POST.get('habitat')
            foto = request.POST.get('foto', '')
            
            # Convert empty string to None for date
            if tanggal_lahir == '':
                tanggal_lahir = None
            
            # Get old values for comparison
            old_status = satwa_data[5]
            old_habitat = satwa_data[6]
            
            update_query = """
                UPDATE sizopi.hewan 
                SET nama = %s, spesies = %s, asal_hewan = %s, tanggal_lahir = %s,
                    status_kesehatan = %s, nama_habitat = %s, url_foto = %s
                WHERE id::text = %s
            """
            cursor.execute(update_query, (
                nama, spesies, asal, tanggal_lahir, 
                status_kesehatan, habitat, foto, hewan_id
            ))
            
            connection.commit()
            
            # Check if status_kesehatan or habitat changed
            if old_status != status_kesehatan or old_habitat != habitat:
                success_message = f"SUKSES: Riwayat perubahan status kesehatan dari \"{old_status}\" menjadi \"{status_kesehatan}\" atau habitat dari \"{old_habitat}\" menjadi \"{habitat}\" telah dicatat."
                return render(request, 'edit_satwa.html', {
                    'success_message': success_message,
                    'satwa': {
                        'id': hewan_id,
                        'nama': nama,
                        'spesies': spesies,
                        'asal': asal,
                        'tanggal_lahir': tanggal_lahir,
                        'status_kesehatan': status_kesehatan,
                        'habitat': habitat,
                        'foto': foto
                    },
                    'habitats': habitat_names
                })
            
            return redirect('kuning:list_satwa')
        
        # GET request - show form with satwa data
        satwa = {
            'id': satwa_data[0],
            'nama': satwa_data[1],
            'spesies': satwa_data[2],
            'asal': satwa_data[3],
            'tanggal_lahir': satwa_data[4],
            'status_kesehatan': satwa_data[5],
            'habitat': satwa_data[6],
            'foto': satwa_data[7]
        }
        
        # Get habitat names for dropdown
        cursor.execute("SELECT nama FROM sizopi.habitat ORDER BY nama")
        habitat_data = cursor.fetchall()
        habitat_names = [row[0] for row in habitat_data]
        
        return render(request, 'edit_satwa.html', {'satwa': satwa, 'habitats': habitat_names})
    
    except Exception as e:
        connection.rollback()
        error_message = str(e)
        
        # Get habitat names for dropdown (needed to re-render the form)
        cursor.execute("SELECT nama FROM sizopi.habitat ORDER BY nama")
        habitat_data = cursor.fetchall()
        habitat_names = [row[0] for row in habitat_data]
        
        # Re-render form with error message
        context = {
            'error_message': error_message,
            'satwa': {
                'id': hewan_id,
                'nama': nama if 'nama' in locals() else satwa_data[1],
                'spesies': spesies if 'spesies' in locals() else satwa_data[2],
                'asal': asal if 'asal' in locals() else satwa_data[3],
                'tanggal_lahir': tanggal_lahir if 'tanggal_lahir' in locals() else satwa_data[4],
                'status_kesehatan': status_kesehatan if 'status_kesehatan' in locals() else satwa_data[5],
                'habitat': habitat if 'habitat' in locals() else satwa_data[6],
                'foto': foto if 'foto' in locals() else satwa_data[7]
            },
            'habitats': habitat_names
        }
        return render(request, 'edit_satwa.html', context)
    finally:
        cursor.close()
        connection.close()

def hapus_satwa(request, id):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Convert string to UUID if needed
        if isinstance(id, str):
            hewan_id = id
        else:
            hewan_id = str(id)
            
        # Delete satwa
        cursor.execute("DELETE FROM sizopi.hewan WHERE id::text = %s", (hewan_id,))
        connection.commit()
        
        return redirect('kuning:list_satwa')
    
    except Exception as e:
        connection.rollback()
        return HttpResponse(f"Error: {str(e)}", status=500)
    finally:
        cursor.close()
        connection.close()

# HABITAT CRUD Operations
def list_habitat(request):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Query untuk mengambil semua data habitat
        query = """
            SELECT nama, luas_area, kapasitas, status
            FROM sizopi.habitat
            ORDER BY nama
        """
        cursor.execute(query)
        habitat_data = cursor.fetchall()
        
        # Convert to list of dictionaries
        habitat = []
        for i, row in enumerate(habitat_data, 1):
            habitat.append({
                'id': i,  # Using index as ID for compatibility with templates
                'nama': row[0],
                'luas_area': str(row[1]),
                'kapasitas_maksimal': str(row[2]),
                'status_lingkungan': row[3]
            })
        
        return render(request, 'list_habitat.html', {'habitat': habitat})
    
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)
    finally:
        cursor.close()
        connection.close()

def tambah_habitat(request):
    if request.method == 'POST':
        connection = get_db_connection()
        cursor = connection.cursor()
        
        try:
            # Get form data
            nama = request.POST.get('nama')
            luas_area = float(request.POST.get('luas_area'))
            kapasitas_maksimal = int(request.POST.get('kapasitas_maksimal'))
            status_lingkungan = request.POST.get('status_lingkungan')
            
            # Insert new habitat
            insert_query = """
                INSERT INTO sizopi.habitat (nama, luas_area, kapasitas, status)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (nama, luas_area, kapasitas_maksimal, status_lingkungan))
            
            connection.commit()
            return redirect('kuning:list_habitat')
            
        except Exception as e:
            connection.rollback()
            return HttpResponse(f"Error: {str(e)}", status=500)
        finally:
            cursor.close()
            connection.close()
    
    # GET request - show form
    return render(request, 'tambah_habitat.html')

def edit_habitat(request, id):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Get all habitats to find the one at the specified index
        cursor.execute("SELECT nama, luas_area, kapasitas, status FROM sizopi.habitat ORDER BY nama")
        habitat_data = cursor.fetchall()
        
        if id > len(habitat_data) or id < 1:
            return HttpResponse("Habitat tidak ditemukan", status=404)
        
        # Get the habitat at index (id-1)
        habitat_row = habitat_data[id-1]
        habitat_nama = habitat_row[0]
        
        if request.method == 'POST':
            # Update data
            nama_baru = request.POST.get('nama')
            luas_area = float(request.POST.get('luas_area'))
            kapasitas_maksimal = int(request.POST.get('kapasitas_maksimal'))
            status_lingkungan = request.POST.get('status_lingkungan')
            
            update_query = """
                UPDATE sizopi.habitat 
                SET nama = %s, luas_area = %s, kapasitas = %s, status = %s
                WHERE nama = %s
            """
            cursor.execute(update_query, (nama_baru, luas_area, kapasitas_maksimal, status_lingkungan, habitat_nama))
            
            connection.commit()
            return redirect('kuning:list_habitat')
        
        # GET request - show form with habitat data
        habitat = {
            'id': id,
            'nama': habitat_row[0],
            'luas_area': str(habitat_row[1]),
            'kapasitas_maksimal': str(habitat_row[2]),
            'status_lingkungan': habitat_row[3]
        }
        
        return render(request, 'edit_habitat.html', {'habitat': habitat})
    
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)
    finally:
        cursor.close()
        connection.close()

def detail_habitat(request, id):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Get all habitats to find the one at the specified index
        cursor.execute("SELECT nama, luas_area, kapasitas, status FROM sizopi.habitat ORDER BY nama")
        habitat_data = cursor.fetchall()
        
        if id > len(habitat_data) or id < 1:
            return HttpResponse("Habitat tidak ditemukan", status=404)
        
        # Get the habitat at index (id-1)
        habitat_row = habitat_data[id-1]
        habitat_nama = habitat_row[0]
        
        habitat = {
            'id': id,
            'nama': habitat_row[0],
            'luas_area': str(habitat_row[1]),
            'kapasitas_maksimal': str(habitat_row[2]),
            'status_lingkungan': habitat_row[3]
        }
        
        # Find all satwa in this habitat
        cursor.execute("""
            SELECT id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, url_foto
            FROM sizopi.hewan 
            WHERE nama_habitat = %s
        """, (habitat_nama,))
        
        satwa_data = cursor.fetchall()
        satwa_di_habitat = []
        for row in satwa_data:
            satwa_di_habitat.append({
                'id': row[0],
                'nama': row[1],
                'spesies': row[2],
                'asal': row[3],
                'tanggal_lahir': row[4],
                'status_kesehatan': row[5],
                'foto': row[6]
            })
        
        return render(request, 'detail_habitat.html', {'habitat': habitat, 'hewan_habitat': satwa_di_habitat})
    
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)
    finally:
        cursor.close()
        connection.close()

def hapus_habitat(request, id):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Get all habitats to find the one at the specified index
        cursor.execute("SELECT nama FROM sizopi.habitat ORDER BY nama")
        habitat_data = cursor.fetchall()
        
        if id > len(habitat_data) or id < 1:
            return HttpResponse("Habitat tidak ditemukan", status=404)
        
        habitat_nama = habitat_data[id-1][0]
        
        # Check if any animals are living in this habitat
        cursor.execute("SELECT COUNT(*) FROM sizopi.hewan WHERE nama_habitat = %s", (habitat_nama,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            # Get all habitats for display
            cursor.execute("SELECT nama, luas_area, kapasitas, status FROM sizopi.habitat ORDER BY nama")
            all_habitat_data = cursor.fetchall()
            
            habitat = []
            for i, row in enumerate(all_habitat_data, 1):
                habitat.append({
                    'id': i,
                    'nama': row[0],
                    'luas_area': str(row[1]),
                    'kapasitas_maksimal': str(row[2]),
                    'status_lingkungan': row[3]
                })
            
            return render(request, 'list_habitat.html', {
                'habitat': habitat,
                'error': f"Tidak dapat menghapus habitat {habitat_nama} karena masih ada satwa yang tinggal di dalamnya."
            })
        
        # Delete habitat if no animals are living there
        cursor.execute("DELETE FROM sizopi.habitat WHERE nama = %s", (habitat_nama,))
        connection.commit()
        
        return redirect('kuning:list_habitat')
    
    except Exception as e:
        connection.rollback()
        return HttpResponse(f"Error: {str(e)}", status=500)
    finally:
        cursor.close()
        connection.close()