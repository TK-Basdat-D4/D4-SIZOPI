from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from utils.db_utils import get_db_connection

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
    
    try:
        # Get database connection
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Execute the SQL query
        query = """
        SELECT
          cm.id_hewan,
          CONCAT_WS(' ', p.nama_depan, p.nama_tengah, p.nama_belakang) AS nama_dokter,
          cm.tanggal_pemeriksaan,
          cm.diagnosis,
          cm.pengobatan,
          cm.status_kesehatan,
          cm.catatan_tindak_lanjut
        FROM
          catatan_medis cm
        JOIN
          dokter_hewan dh ON cm.username_dh = dh.username_dh
        JOIN
          pengguna p ON dh.username_dh = p.username
        ORDER BY
          cm.tanggal_pemeriksaan DESC;
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Convert query results to list of dictionaries
        rekam_medis_list = []
        for i, row in enumerate(rows, 1):
            rekam_medis_list.append({
                'id': i,  # Generate sequential ID for template compatibility
                'id_hewan': row[0],
                'dokter': row[1],
                'tanggal': row[2].strftime('%Y-%m-%d') if row[2] else '',
                'diagnosa': row[3],
                'pengobatan': row[4],
                'status': row[5],
                'catatan_tindak_lanjut': row[6]
            })
        
        # Close database connection
        cursor.close()
        connection.close()
        
        context = {
            'rekam_medis_list': rekam_medis_list
        }
        return render(request, 'hijau_kesehatan_satwa/rekam_medis_list.html', context)
        
    except Exception as e:
        # Handle database errors
        messages.error(request, f'Terjadi kesalahan saat mengambil data: {str(e)}')
        
        # Close connection if it exists
        try:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()
        except:
            pass
        
        # Return empty list on error
        context = {
            'rekam_medis_list': []
        }
        return render(request, 'hijau_kesehatan_satwa/rekam_medis_list.html', context)

def rekam_medis_form(request):
    print("=== DEBUG REKAM MEDIS FORM START ===")
    print(f"Request method: {request.method}")
    print(f"User in session: {'user' in request.session}")
    
    if not check_doctor_access(request):
        print("DEBUG: Access denied - redirecting to login")
        return redirect('register_login:login')
    
    if request.method == 'POST':
        print("=== DEBUG POST REQUEST ===")
        connection = None
        cursor = None
        
        try:
            # Get database connection
            connection = get_db_connection()
            cursor = connection.cursor()
            print("DEBUG: Database connection established")
            
            # Get current user (doctor)
            current_user = request.session.get('user', {})
            username_dh = current_user.get('username', '')
            print(f"DEBUG: Current user: {current_user}")
            print(f"DEBUG: Username DH: {username_dh}")
            
            # Get form data
            id_hewan = request.POST.get('id_hewan')
            tanggal_pemeriksaan = request.POST.get('tanggal')
            diagnosis = request.POST.get('diagnosa')
            pengobatan = request.POST.get('pengobatan')
            status_kesehatan = request.POST.get('status')
            catatan_tindak_lanjut = request.POST.get('catatan_tindak_lanjut', '')
            
            print("=== DEBUG FORM DATA ===")
            print(f"id_hewan: {id_hewan}")
            print(f"tanggal_pemeriksaan: {tanggal_pemeriksaan}")
            print(f"diagnosis: {diagnosis}")
            print(f"pengobatan: {pengobatan}")
            print(f"status_kesehatan: {status_kesehatan}")
            print(f"catatan_tindak_lanjut: {catatan_tindak_lanjut}")
            
            # Validate required fields
            if not id_hewan:
                print("DEBUG: Validation failed - id_hewan is empty")
                messages.error(request, 'Silahkan pilih hewan yang akan diperiksa!')
                return redirect('hijau_kesehatan_satwa:rekam_medis_form')
            
            if not tanggal_pemeriksaan:
                print("DEBUG: Validation failed - tanggal_pemeriksaan is empty")
                messages.error(request, 'Tanggal pemeriksaan wajib diisi!')
                return redirect('hijau_kesehatan_satwa:rekam_medis_form')
            
            # Validate UUID format for id_hewan
            try:
                import uuid
                uuid.UUID(id_hewan)
                print("DEBUG: UUID validation passed")
            except ValueError:
                print("DEBUG: Invalid UUID format")
                messages.error(request, 'Format ID hewan tidak valid!')
                return redirect('hijau_kesehatan_satwa:rekam_medis_form')
            
            print("DEBUG: Form validation passed")
            
            # Start fresh transaction
            connection.autocommit = False
            print("DEBUG: Autocommit disabled, starting transaction")
            
            # Verify the animal exists first
            verify_query = "SELECT COUNT(*) FROM hewan WHERE id = %s"
            print(f"DEBUG: Verifying animal exists: {verify_query}")
            cursor.execute(verify_query, [id_hewan])
            animal_count = cursor.fetchone()[0]
            
            if animal_count == 0:
                print("DEBUG: Animal not found")
                connection.rollback()
                messages.error(request, 'Hewan yang dipilih tidak ditemukan!')
                return redirect('hijau_kesehatan_satwa:rekam_medis_form')
            
            print(f"DEBUG: Animal found, count: {animal_count}")
            
            # Insert new medical record using raw SQL
            insert_query = """
            INSERT INTO catatan_medis (
                id_hewan, 
                username_dh, 
                tanggal_pemeriksaan, 
                diagnosis, 
                pengobatan, 
                status_kesehatan, 
                catatan_tindak_lanjut
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            print("=== DEBUG SQL EXECUTION ===")
            print(f"SQL Query: {insert_query}")
            print(f"Parameters: [{id_hewan}, {username_dh}, {tanggal_pemeriksaan}, {diagnosis}, {pengobatan}, {status_kesehatan}, {catatan_tindak_lanjut}]")
            
            cursor.execute(insert_query, [
                id_hewan,
                username_dh,
                tanggal_pemeriksaan,
                diagnosis,
                pengobatan,
                status_kesehatan,
                catatan_tindak_lanjut
            ])
            print("DEBUG: SQL executed successfully")
            
            # Commit the transaction
            connection.commit()
            print("DEBUG: Transaction committed successfully")
            
            # Check for trigger messages after commit (optional)
            trigger_message = ""
            try:
                cursor.execute("SELECT current_setting('trigger_message', true)")
                result = cursor.fetchone()
                if result and result[0] and result[0] != '':
                    trigger_message = result[0]
                print(f"DEBUG: Trigger message: {trigger_message}")
            except Exception as trigger_error:
                print(f"DEBUG: No trigger message or error getting it: {trigger_error}")
                trigger_message = ""
            
            # Display success message
            if trigger_message and trigger_message.strip():
                messages.success(request, f'Data rekam medis hewan berhasil disimpan! {trigger_message}')
                print("DEBUG: Success message with trigger")
            else:
                messages.success(request, 'Data rekam medis hewan berhasil disimpan!')
                print("DEBUG: Success message without trigger")
            
            print("=== DEBUG: Redirecting to list ===")
            return redirect('hijau_kesehatan_satwa:rekam_medis_list')
            
        except Exception as e:
            # Handle database errors
            print(f"=== DEBUG ERROR ===")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print(f"Error details: {repr(e)}")
            
            # Rollback transaction on error
            if connection:
                try:
                    connection.rollback()
                    print("DEBUG: Transaction rolled back")
                except Exception as rollback_error:
                    print(f"DEBUG: Error during rollback: {rollback_error}")
            
            messages.error(request, f'Terjadi kesalahan saat menyimpan data: {str(e)}')
            
        finally:
            # Always close connection
            try:
                if cursor:
                    cursor.close()
                    print("DEBUG: Cursor closed")
                if connection:
                    connection.close()
                    print("DEBUG: Connection closed")
            except Exception as cleanup_error:
                print(f"DEBUG: Error in cleanup: {cleanup_error}")
    
    # For GET request, fetch available animals from database
    print("=== DEBUG GET REQUEST - Fetching animals ===")
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        print("DEBUG: Database connection for animals established")
        
        # Query to get all animals with correct field names
        animals_query = """
            SELECT 
                id,
                nama,
                spesies,
                asal_hewan,
                tanggal_lahir,
                nama_habitat,
                status_kesehatan
            FROM hewan
            ORDER BY nama;
        """
        
        print(f"DEBUG: Animals query: {animals_query}")
        cursor.execute(animals_query)
        animals_data = cursor.fetchall()
        print(f"DEBUG: Found {len(animals_data)} animals")
        
        # Convert to list of dictionaries
        animals = []
        for i, animal in enumerate(animals_data):
            animal_dict = {
                'id_hewan': str(animal[0]),  # Convert UUID to string for template
                'nama_individu': animal[1],
                'spesies': animal[2],
                'asal_hewan': animal[3],
                'tanggal_lahir': animal[4].strftime('%Y-%m-%d') if animal[4] else '',
                'habitat_id': animal[5],
                'status_kesehatan': animal[6]
            }
            animals.append(animal_dict)
            if i < 5:  # Only print first 5 to reduce log spam
                print(f"DEBUG: Animal {i+1}: {animal_dict}")

        print("DEBUG: Animals data fetched successfully")
        
        context = {'animals': animals}
        print(f"DEBUG: Context prepared with {len(animals)} animals")
        print("=== DEBUG REKAM MEDIS FORM END ===")
        return render(request, 'hijau_kesehatan_satwa/rekam_medis_form.html', context)
        
    except Exception as e:
        # Handle database errors when fetching animals
        print(f"=== DEBUG ERROR FETCHING ANIMALS ===")
        print(f"Error: {str(e)}")
        messages.error(request, f'Terjadi kesalahan saat mengambil data hewan: {str(e)}')
        
        context = {'animals': []}
        return render(request, 'hijau_kesehatan_satwa/rekam_medis_form.html', context)
        
    finally:
        # Always close connection for GET request too
        try:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
            print("DEBUG: GET request - Database connection closed")
        except Exception as cleanup_error:
            print(f"DEBUG: Error in GET cleanup: {cleanup_error}")

def rekam_medis_edit(request, id):
    print(f"=== DEBUG REKAM MEDIS EDIT START - ID: {id} ===")
    print(f"Request method: {request.method}")
    
    if not check_doctor_access(request):
        print("DEBUG: Access denied - redirecting to login")
        return redirect('register_login:login')
    
    try:
        # Get database connection
        connection = get_db_connection()
        cursor = connection.cursor()
        print("DEBUG: Database connection established")
        
        if request.method == 'POST':
            print("=== DEBUG POST REQUEST - EDIT ===")
            
            # Get form data
            id_hewan = request.POST.get('id_hewan')
            tanggal_pemeriksaan = request.POST.get('tanggal')
            diagnosis = request.POST.get('diagnosa')
            pengobatan = request.POST.get('pengobatan')
            status_kesehatan = request.POST.get('status')
            catatan_tindak_lanjut = request.POST.get('catatan_tindak_lanjut', '')
            
            print("=== DEBUG FORM DATA - EDIT ===")
            print(f"id_hewan: {id_hewan}")
            print(f"tanggal_pemeriksaan: {tanggal_pemeriksaan}")
            print(f"diagnosis: {diagnosis}")
            print(f"pengobatan: {pengobatan}")
            print(f"status_kesehatan: {status_kesehatan}")
            print(f"catatan_tindak_lanjut: {catatan_tindak_lanjut}")
            
            # Get the specific record to update based on sequential ID
            get_record_query = """
            SELECT id_hewan, tanggal_pemeriksaan
            FROM catatan_medis
            ORDER BY tanggal_pemeriksaan DESC
            LIMIT 1 OFFSET %s
            """
            
            offset = int(id) - 1
            print(f"DEBUG: Getting record with offset: {offset}")
            cursor.execute(get_record_query, [offset])
            record = cursor.fetchone()
            print(f"DEBUG: Found record: {record}")
            
            if record:
                old_id_hewan, old_tanggal = record
                print(f"DEBUG: Old record - id_hewan: {old_id_hewan}, tanggal: {old_tanggal}")
                
                update_query = """
                UPDATE catatan_medis 
                SET 
                    tanggal_pemeriksaan = %s,
                    diagnosis = %s,
                    pengobatan = %s,
                    status_kesehatan = %s,
                    catatan_tindak_lanjut = %s
                WHERE id_hewan = %s AND tanggal_pemeriksaan = %s
                """
                
                print("=== DEBUG UPDATE SQL ===")
                print(f"SQL Query: {update_query}")
                print(f"Parameters: [{tanggal_pemeriksaan}, {diagnosis}, {pengobatan}, {status_kesehatan}, {catatan_tindak_lanjut}, {old_id_hewan}, {old_tanggal}]")
                
                cursor.execute(update_query, [
                    tanggal_pemeriksaan,
                    diagnosis,
                    pengobatan,
                    status_kesehatan,
                    catatan_tindak_lanjut,
                    old_id_hewan,
                    old_tanggal
                ])
                print(f"DEBUG: Rows affected: {cursor.rowcount}")
                
                # Commit the transaction
                connection.commit()
                print("DEBUG: Transaction committed")
                
                # Check for trigger messages using a more robust approach
                trigger_message = ""
                try:
                    # Try to get custom message first
                    cursor.execute("SELECT COALESCE(current_setting('trigger_message', true), '')")
                    result = cursor.fetchone()
                    if result and result[0]:
                        trigger_message = result[0]
                    print(f"DEBUG: Trigger message: {trigger_message}")
                except Exception as trigger_error:
                    print(f"DEBUG: Error getting trigger message: {trigger_error}")
                    # If trigger message fails, just continue without it
                
                # Display success message and any trigger messages
                if trigger_message and trigger_message.strip():
                    messages.success(request, f'Data rekam medis hewan berhasil diperbarui! {trigger_message}')
                    print("DEBUG: Success message with trigger")
                else:
                    messages.success(request, 'Data rekam medis hewan berhasil diperbarui!')
                    print("DEBUG: Success message without trigger")
            else:
                print("DEBUG: Record not found for update")
                messages.error(request, 'Data tidak ditemukan!')
            
            # Close database connection
            cursor.close()
            connection.close()
            print("DEBUG: Database connection closed")
            
            return redirect('hijau_kesehatan_satwa:rekam_medis_list')
            
        else:
            # GET request - fetch the record to edit and available animals
            print("=== DEBUG GET REQUEST - EDIT ===")
            fetch_query = """
            SELECT
              cm.id_hewan,
              CONCAT_WS(' ', p.nama_depan, p.nama_tengah, p.nama_belakang) AS nama_dokter,
              cm.tanggal_pemeriksaan,
              cm.diagnosis,
              cm.pengobatan,
              cm.status_kesehatan,
              cm.catatan_tindak_lanjut
            FROM
              catatan_medis cm
            JOIN
              dokter_hewan dh ON cm.username_dh = dh.username_dh
            JOIN
              pengguna p ON dh.username_dh = p.username
            ORDER BY
              cm.tanggal_pemeriksaan DESC
            LIMIT 1 OFFSET %s
            """
            
            offset = int(id) - 1
            print(f"DEBUG: Fetching record with offset: {offset}")
            cursor.execute(fetch_query, [offset])
            row = cursor.fetchone()
            print(f"DEBUG: Fetched record: {row}")
            
            if row:
                record_to_edit = {
                    'id_hewan': str(row[0]),  # Convert UUID to string
                    'dokter': row[1],
                    'tanggal': row[2].strftime('%Y-%m-%d') if row[2] else '',
                    'diagnosa': row[3],
                    'pengobatan': row[4],
                    'status': row[5],
                    'catatan_tindak_lanjut': row[6]
                }
                print(f"DEBUG: Record to edit: {record_to_edit}")
                
                # Also fetch available animals for dropdown
                animals_query = """
                    SELECT 
                        id, nama, spesies, asal_hewan, tanggal_lahir, nama_habitat, status_kesehatan
                    FROM hewan
                    ORDER BY nama;
                """
                
                cursor.execute(animals_query)
                animals_data = cursor.fetchall()
                print(f"DEBUG: Found {len(animals_data)} animals for dropdown")
                
                animals = []
                for animal in animals_data:
                    animals.append({
                        'id_hewan': str(animal[0]),
                        'nama_individu': animal[1],
                        'spesies': animal[2],
                        'asal_hewan': animal[3],
                        'tanggal_lahir': animal[4].strftime('%Y-%m-%d') if animal[4] else '',
                        'habitat_id': animal[5],
                        'status_kesehatan': animal[6]
                    })

                cursor.close()
                connection.close()
                print("DEBUG: Database connection closed")
                
                context = {
                    'rekam_medis': record_to_edit,
                    'animals': animals
                }
                print("=== DEBUG REKAM MEDIS EDIT END ===")
                return render(request, 'hijau_kesehatan_satwa/rekam_medis_form.html', context)
            else:
                cursor.close()
                connection.close()
                print("DEBUG: Record not found for edit")
                messages.error(request, 'Data tidak ditemukan!')
                return redirect('hijau_kesehatan_satwa:rekam_medis_list')
            
    except Exception as e:
        # Handle database errors
        print(f"=== DEBUG ERROR - EDIT ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"Error details: {repr(e)}")
        
        # Rollback transaction if still active
        try:
            if 'connection' in locals():
                connection.rollback()
                print("DEBUG: Transaction rolled back")
        except Exception as rollback_error:
            print(f"DEBUG: Error in rollback: {rollback_error}")
        
        messages.error(request, f'Terjadi kesalahan: {str(e)}')
        
        # Close connection if it exists
        try:
            if 'cursor' in locals():
                cursor.close()
                print("DEBUG: Cursor closed in error handling")
            if 'connection' in locals():
                connection.close()
                print("DEBUG: Connection closed in error handling")
        except Exception as cleanup_error:
            print(f"DEBUG: Error in cleanup: {cleanup_error}")
        
        return redirect('hijau_kesehatan_satwa:rekam_medis_list')
    
def rekam_medis_delete(request, id):
    print(f"=== DEBUG REKAM MEDIS DELETE START - ID: {id} ===")
    
    if not check_doctor_access(request):
        print("DEBUG: Access denied - redirecting to login")
        return redirect('register_login:login')
    
    try:
        # Get database connection
        connection = get_db_connection()
        cursor = connection.cursor()
        print("DEBUG: Database connection established")
        
        # Delete medical record using raw SQL
        # First, get the record details for proper deletion
        fetch_query = """
        SELECT id_hewan, tanggal_pemeriksaan
        FROM catatan_medis
        ORDER BY tanggal_pemeriksaan DESC
        LIMIT 1 OFFSET %s
        """
        
        offset = int(id) - 1
        print(f"DEBUG: Getting record to delete with offset: {offset}")
        cursor.execute(fetch_query, [offset])
        record = cursor.fetchone()
        print(f"DEBUG: Found record to delete: {record}")
        
        if record:
            id_hewan, tanggal_pemeriksaan = record
            print(f"DEBUG: Deleting record - id_hewan: {id_hewan}, tanggal: {tanggal_pemeriksaan}")
            
            # Delete the specific record
            delete_query = """
            DELETE FROM catatan_medis 
            WHERE id_hewan = %s AND tanggal_pemeriksaan = %s
            """
            
            print("=== DEBUG DELETE SQL ===")
            print(f"SQL Query: {delete_query}")
            print(f"Parameters: [{id_hewan}, {tanggal_pemeriksaan}]")
            
            cursor.execute(delete_query, [id_hewan, tanggal_pemeriksaan])
            print(f"DEBUG: Rows affected: {cursor.rowcount}")
            
            # Check if there are any notices from triggers
            try:
                cursor.execute("SELECT get_trigger_message()")
                trigger_result = cursor.fetchone()
                print(f"DEBUG: Trigger result: {trigger_result}")
            except Exception as trigger_error:
                print(f"DEBUG: Error getting trigger message: {trigger_error}")
                trigger_result = None
            
            # Commit the transaction
            connection.commit()
            print("DEBUG: Transaction committed")
            
            # Display success message and any trigger messages
            if trigger_result and trigger_result[0]:
                messages.success(request, f'Data rekam medis hewan berhasil dihapus! {trigger_result[0]}')
                print("DEBUG: Success message with trigger")
            else:
                messages.success(request, 'Data rekam medis hewan berhasil dihapus!')
                print("DEBUG: Success message without trigger")
        else:
            print("DEBUG: Record not found for deletion")
            messages.error(request, 'Data tidak ditemukan!')
        
        # Close database connection
        cursor.close()
        connection.close()
        print("DEBUG: Database connection closed")
        
    except Exception as e:
        # Handle database errors
        print(f"=== DEBUG ERROR - DELETE ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"Error details: {repr(e)}")
        
        messages.error(request, f'Terjadi kesalahan saat menghapus data: {str(e)}')
        
        # Close connection if it exists
        try:
            if 'cursor' in locals():
                cursor.close()
                print("DEBUG: Cursor closed in error handling")
            if 'connection' in locals():
                connection.rollback()
                connection.close()
                print("DEBUG: Connection rolled back and closed in error handling")
        except Exception as cleanup_error:
            print(f"DEBUG: Error in cleanup: {cleanup_error}")
    
    print("=== DEBUG REKAM MEDIS DELETE END ===")
    return redirect('hijau_kesehatan_satwa:rekam_medis_list')

# Updated jadwal_pemeriksaan_list function with debug messages
def jadwal_pemeriksaan_list(request):
    print("=== DEBUG JADWAL PEMERIKSAAN LIST START ===")
    print(f"Request method: {request.method}")
    print(f"User in session: {'user' in request.session}")
    
    if not check_doctor_access(request):
        print("DEBUG: Access denied - redirecting to login")
        return redirect('register_login:login')
    
    try:
        # Get database connection
        connection = get_db_connection()
        cursor = connection.cursor()
        print("DEBUG: Database connection established")
        
        # Get filter parameter from request
        selected_animal = request.GET.get('filter_hewan', '')
        print(f"DEBUG: Selected animal filter: {selected_animal}")
        
        # Base SQL query
        base_query = """
        SELECT
            jpk.id_hewan,
            h.nama,
            h.spesies,
            h.asal_hewan,
            h.nama_habitat,
            h.status_kesehatan,
            jpk.tgl_pemeriksaan_selanjutnya,
            jpk.freq_pemeriksaan_rutin
        FROM
            jadwal_pemeriksaan_kesehatan jpk
        JOIN
            hewan h ON jpk.id_hewan = h.id
        """
        
        # Add WHERE clause if animal is selected
        if selected_animal:
            query = base_query + " WHERE jpk.id_hewan = %s ORDER BY jpk.tgl_pemeriksaan_selanjutnya ASC"
            print(f"DEBUG: Filtered query: {query}")
            print(f"DEBUG: Filter parameter: {selected_animal}")
            cursor.execute(query, [selected_animal])
        else:
            query = base_query + " ORDER BY jpk.tgl_pemeriksaan_selanjutnya ASC"
            print(f"DEBUG: Unfiltered query: {query}")
            cursor.execute(query)
        
        rows = cursor.fetchall()
        print(f"DEBUG: Found {len(rows)} schedule records")
        
        # Convert query results to list of dictionaries
        jadwal_list = []
        for i, row in enumerate(rows, 1):
            schedule_dict = {
                'id': i,  # Generate sequential ID for template compatibility
                'id_hewan': str(row[0]),  # Convert UUID to string
                'nama_hewan': row[1],
                'spesies': row[2],
                'asal_hewan': row[3],
                'habitat': row[4],
                'status_kesehatan': row[5],
                'tanggal': row[6].strftime('%Y-%m-%d') if row[6] else '',
                'frequency': row[7]
            }
            jadwal_list.append(schedule_dict)
            if i <= 3:  # Only print first 3 to reduce log spam
                print(f"DEBUG: Schedule {i}: {schedule_dict}")
        
        # Get all animals that have schedules for dropdown
        animals_query = """
        SELECT DISTINCT
            jpk.id_hewan,
            h.nama,
            h.spesies
        FROM
            jadwal_pemeriksaan_kesehatan jpk
        JOIN
            hewan h ON jpk.id_hewan = h.id
        ORDER BY
            h.nama ASC
        """
        
        print(f"DEBUG: Animals dropdown query: {animals_query}")
        cursor.execute(animals_query)
        animals_rows = cursor.fetchall()
        print(f"DEBUG: Found {len(animals_rows)} animals for dropdown")
        
        # Convert to list of dictionaries for dropdown
        animals_for_dropdown = []
        for animal_row in animals_rows:
            animal_dict = {
                'id_hewan': str(animal_row[0]),
                'nama': animal_row[1],
                'spesies': animal_row[2]
            }
            animals_for_dropdown.append(animal_dict)
        
        # Close database connection
        cursor.close()
        connection.close()
        print("DEBUG: Database connection closed")
        
        # Get the default frequency (you can make this configurable later)
        examination_frequency = 3  # Default 3 days
        print(f"DEBUG: Default examination frequency: {examination_frequency}")
        
        context = {
            'jadwal_list': jadwal_list,
            'frequency': examination_frequency,
            'animals_dropdown': animals_for_dropdown,
            'selected_animal': selected_animal
        }
        print(f"DEBUG: Context prepared with {len(jadwal_list)} schedules and {len(animals_for_dropdown)} dropdown animals")
        print("=== DEBUG JADWAL PEMERIKSAAN LIST END ===")
        return render(request, 'hijau_kesehatan_satwa/jadwal_pemeriksaan_list.html', context)
        
    except Exception as e:
        # Handle database errors
        print(f"=== DEBUG ERROR - JADWAL LIST ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"Error details: {repr(e)}")
        
        messages.error(request, f'Terjadi kesalahan saat mengambil data: {str(e)}')
        
        # Close connection if it exists
        try:
            if 'cursor' in locals():
                cursor.close()
                print("DEBUG: Cursor closed in error handling")
            if 'connection' in locals():
                connection.close()
                print("DEBUG: Connection closed in error handling")
        except Exception as cleanup_error:
            print(f"DEBUG: Error in cleanup: {cleanup_error}")
        
        # Return empty list on error
        context = {
            'jadwal_list': [],
            'frequency': 3,  # Default frequency
            'animals_dropdown': [],
            'selected_animal': ''
        }
        print("DEBUG: Returning empty context due to error")
        return render(request, 'hijau_kesehatan_satwa/jadwal_pemeriksaan_list.html', context)

# Updated update_frequency function with debug messages
def update_frequency(request):
    print("=== DEBUG UPDATE FREQUENCY START ===")
    print(f"Request method: {request.method}")
    print(f"User in session: {'user' in request.session}")
    
    if not check_doctor_access(request):
        print("DEBUG: Access denied - redirecting to login")
        return redirect('register_login:login')
    
    if request.method == 'POST':
        print("=== DEBUG POST REQUEST - UPDATE FREQUENCY ===")
        connection = None
        cursor = None
        
        try:
            new_frequency = int(request.POST.get('frequency', 3))
            print(f"DEBUG: New frequency from form: {new_frequency}")
            
            # Validate frequency
            if new_frequency < 1:
                print("DEBUG: Validation failed - frequency less than 1")
                messages.error(request, 'Frekuensi harus lebih dari atau sama dengan 1 hari!')
                return redirect('hijau_kesehatan_satwa:jadwal_pemeriksaan_list')
            
            print("DEBUG: Frequency validation passed")
            
            # Get database connection
            connection = get_db_connection()
            cursor = connection.cursor()
            print("DEBUG: Database connection established")
            
            # Update all examination schedules with new frequency
            # You might want to make this more selective based on your business logic
            update_query = """
            UPDATE jadwal_pemeriksaan_kesehatan 
            SET freq_pemeriksaan_rutin = %s
            """
            
            print("=== DEBUG SQL EXECUTION - UPDATE FREQUENCY ===")
            print(f"SQL Query: {update_query}")
            print(f"Parameters: [{new_frequency}]")
            
            cursor.execute(update_query, [new_frequency])
            affected_rows = cursor.rowcount
            print(f"DEBUG: Rows affected: {affected_rows}")
            
            # Commit the transaction
            connection.commit()
            print("DEBUG: Transaction committed successfully")
            
            # Close database connection
            cursor.close()
            connection.close()
            print("DEBUG: Database connection closed")
            
            messages.success(request, f'Frekuensi pemeriksaan berhasil diubah menjadi {new_frequency} hari untuk {affected_rows} jadwal!')
            print("DEBUG: Success message set")
            
        except ValueError as ve:
            print(f"=== DEBUG VALUE ERROR ===")
            print(f"Error: {str(ve)}")
            messages.error(request, 'Frekuensi harus berupa angka!')
        except Exception as e:
            # Handle database errors
            print(f"=== DEBUG ERROR - UPDATE FREQUENCY ===")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print(f"Error details: {repr(e)}")
            
            messages.error(request, f'Terjadi kesalahan saat mengubah frekuensi: {str(e)}')
            
            # Close connection if it exists
            try:
                if cursor:
                    cursor.close()
                    print("DEBUG: Cursor closed in error handling")
                if connection:
                    connection.rollback()
                    connection.close()
                    print("DEBUG: Connection rolled back and closed in error handling")
            except Exception as cleanup_error:
                print(f"DEBUG: Error in cleanup: {cleanup_error}")
    else:
        print("DEBUG: Not a POST request - redirecting")
    
    print("=== DEBUG UPDATE FREQUENCY END ===")
    return redirect('hijau_kesehatan_satwa:jadwal_pemeriksaan_list')

# Updated jadwal_pemeriksaan_form function with debug messages
def jadwal_pemeriksaan_form(request):
    print("=== DEBUG JADWAL PEMERIKSAAN FORM START ===")
    print(f"Request method: {request.method}")
    print(f"User in session: {'user' in request.session}")
    
    if not check_doctor_access(request):
        print("DEBUG: Access denied - redirecting to login")
        return redirect('register_login:login')
    
    if request.method == 'POST':
        print("=== DEBUG POST REQUEST - JADWAL FORM ===")
        connection = None
        cursor = None
        
        try:
            # Get database connection
            connection = get_db_connection()
            cursor = connection.cursor()
            print("DEBUG: Database connection established")
            
            # Get current user (doctor)
            current_user = request.session.get('user', {})
            username_dh = current_user.get('username', '')
            print(f"DEBUG: Current user: {current_user}")
            print(f"DEBUG: Username DH: {username_dh}")
            
            # Get form data
            id_hewan = request.POST.get('id_hewan')
            tanggal_pemeriksaan = request.POST.get('tanggal')
            frequency = request.POST.get('frequency', 3)
            
            print("=== DEBUG FORM DATA - JADWAL ===")
            print(f"id_hewan: {id_hewan}")
            print(f"tanggal_pemeriksaan: {tanggal_pemeriksaan}")
            print(f"frequency: {frequency}")
            
            # Convert and validate frequency
            try:
                frequency = int(frequency)
                print(f"DEBUG: Frequency converted to int: {frequency}")
            except ValueError:
                print("DEBUG: Invalid frequency value")
                messages.error(request, 'Frekuensi harus berupa angka!')
                return redirect('hijau_kesehatan_satwa:jadwal_pemeriksaan_form')
            
            # Validate required fields
            if not id_hewan:
                print("DEBUG: Validation failed - id_hewan is empty")
                messages.error(request, 'Silahkan pilih hewan yang akan dijadwalkan!')
                return redirect('hijau_kesehatan_satwa:jadwal_pemeriksaan_form')
            
            if not tanggal_pemeriksaan:
                print("DEBUG: Validation failed - tanggal_pemeriksaan is empty")
                messages.error(request, 'Tanggal pemeriksaan wajib diisi!')
                return redirect('hijau_kesehatan_satwa:jadwal_pemeriksaan_form')
            
            # Validate UUID format for id_hewan
            try:
                import uuid
                uuid.UUID(id_hewan)
                print("DEBUG: UUID validation passed")
            except ValueError:
                print("DEBUG: Invalid UUID format")
                messages.error(request, 'Format ID hewan tidak valid!')
                return redirect('hijau_kesehatan_satwa:jadwal_pemeriksaan_form')
            
            print("DEBUG: Form validation passed")
            
            # Start transaction
            connection.autocommit = False
            print("DEBUG: Autocommit disabled, starting transaction")
            
            # Verify the animal exists
            verify_query = "SELECT COUNT(*) FROM hewan WHERE id = %s"
            print(f"DEBUG: Verifying animal exists: {verify_query}")
            cursor.execute(verify_query, [id_hewan])
            animal_count = cursor.fetchone()[0]
            
            if animal_count == 0:
                print("DEBUG: Animal not found")
                connection.rollback()
                messages.error(request, 'Hewan yang dipilih tidak ditemukan!')
                return redirect('hijau_kesehatan_satwa:jadwal_pemeriksaan_form')
            
            print(f"DEBUG: Animal found, count: {animal_count}")
            
            # Insert new examination schedule
            insert_query = """
            INSERT INTO jadwal_pemeriksaan_kesehatan (
                id_hewan, 
                tgl_pemeriksaan_selanjutnya, 
                freq_pemeriksaan_rutin
            ) VALUES (%s, %s, %s)
            ON CONFLICT (id_hewan, tgl_pemeriksaan_selanjutnya) 
            DO UPDATE SET freq_pemeriksaan_rutin = EXCLUDED.freq_pemeriksaan_rutin
            """
            
            print("=== DEBUG SQL EXECUTION - JADWAL INSERT ===")
            print(f"SQL Query: {insert_query}")
            print(f"Parameters: [{id_hewan}, {tanggal_pemeriksaan}, {frequency}]")
            
            cursor.execute(insert_query, [id_hewan, tanggal_pemeriksaan, frequency])
            print("DEBUG: SQL executed successfully")
            
            # Commit the transaction
            connection.commit()
            print("DEBUG: Transaction committed successfully")
            
            # Check for trigger messages after commit (optional)
            trigger_message = ""
            try:
                cursor.execute("SELECT current_setting('trigger_message', true)")
                result = cursor.fetchone()
                if result and result[0] and result[0] != '':
                    trigger_message = result[0]
                print(f"DEBUG: Trigger message: {trigger_message}")
            except Exception as trigger_error:
                print(f"DEBUG: No trigger message or error getting it: {trigger_error}")
                trigger_message = ""
            
            # Display success message
            if trigger_message and trigger_message.strip():
                messages.success(request, f'Jadwal pemeriksaan berhasil disimpan! {trigger_message}')
                print("DEBUG: Success message with trigger")
            else:
                messages.success(request, 'Jadwal pemeriksaan berhasil disimpan!')
                print("DEBUG: Success message without trigger")
            
            print("=== DEBUG: Redirecting to jadwal list ===")
            return redirect('hijau_kesehatan_satwa:jadwal_pemeriksaan_list')
            
        except Exception as e:
            # Handle database errors
            print(f"=== DEBUG ERROR - JADWAL FORM ===")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print(f"Error details: {repr(e)}")
            
            # Rollback transaction on error
            if connection:
                try:
                    connection.rollback()
                    print("DEBUG: Transaction rolled back")
                except Exception as rollback_error:
                    print(f"DEBUG: Error during rollback: {rollback_error}")
            
            messages.error(request, f'Terjadi kesalahan saat menyimpan data: {str(e)}')
            
        finally:
            # Always close connection
            try:
                if cursor:
                    cursor.close()
                    print("DEBUG: Cursor closed")
                if connection:
                    connection.close()
                    print("DEBUG: Connection closed")
            except Exception as cleanup_error:
                print(f"DEBUG: Error in cleanup: {cleanup_error}")
    
    # For GET request, fetch available animals from database
    print("=== DEBUG GET REQUEST - Fetching animals for jadwal ===")
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        print("DEBUG: Database connection for animals established")
        
        # Query to get all animals
        animals_query = """
            SELECT 
                id,
                nama,
                spesies,
                asal_hewan,
                tanggal_lahir,
                nama_habitat,
                status_kesehatan
            FROM hewan
            ORDER BY nama;
        """
        
        print(f"DEBUG: Animals query: {animals_query}")
        cursor.execute(animals_query)
        animals_data = cursor.fetchall()
        print(f"DEBUG: Found {len(animals_data)} animals")
        
        # Convert to list of dictionaries
        animals = []
        for i, animal in enumerate(animals_data):
            animal_dict = {
                'id_hewan': str(animal[0]),  # Convert UUID to string for template
                'nama_individu': animal[1],
                'spesies': animal[2],
                'asal_hewan': animal[3],
                'tanggal_lahir': animal[4].strftime('%Y-%m-%d') if animal[4] else '',
                'habitat': animal[5],
                'status_kesehatan': animal[6]
            }
            animals.append(animal_dict)
            if i < 5:  # Only print first 5 to reduce log spam
                print(f"DEBUG: Animal {i+1}: {animal_dict}")

        print("DEBUG: Animals data fetched successfully")
        
        cursor.close()
        connection.close()
        print("DEBUG: Database connection closed")
        
        context = {'animals': animals}
        print(f"DEBUG: Context prepared with {len(animals)} animals")
        print("=== DEBUG JADWAL PEMERIKSAAN FORM END ===")
        return render(request, 'hijau_kesehatan_satwa/jadwal_pemeriksaan_form.html', context)
        
    except Exception as e:
        # Handle database errors when fetching animals
        print(f"=== DEBUG ERROR FETCHING ANIMALS - JADWAL ===")
        print(f"Error: {str(e)}")
        messages.error(request, f'Terjadi kesalahan saat mengambil data hewan: {str(e)}')
        
        # Close connection if it exists
        try:
            if cursor:
                cursor.close()
                print("DEBUG: Cursor closed in error handling")
            if connection:
                connection.close()
                print("DEBUG: Connection closed in error handling")
        except Exception as cleanup_error:
            print(f"DEBUG: Error in cleanup: {cleanup_error}")
        
        context = {'animals': []}
        print("DEBUG: Returning empty animals context due to error")
        return render(request, 'hijau_kesehatan_satwa/jadwal_pemeriksaan_form.html', context)

# Updated jadwal_pemeriksaan_edit function with debug messages
def jadwal_pemeriksaan_edit(request, id):
    print(f"=== DEBUG JADWAL PEMERIKSAAN EDIT START - ID: {id} ===")
    print(f"Request method: {request.method}")
    print(f"User in session: {'user' in request.session}")
    
    if not check_doctor_access(request):
        print("DEBUG: Access denied - redirecting to login")
        return redirect('register_login:login')
    
    try:
        # Get database connection
        connection = get_db_connection()
        cursor = connection.cursor()
        print("DEBUG: Database connection established")
        
        if request.method == 'POST':
            print("=== DEBUG POST REQUEST - JADWAL EDIT ===")
            
            # Get form data
            tanggal = request.POST.get('tanggal')
            frequency = request.POST.get('frequency', 3)
            
            print("=== DEBUG FORM DATA - JADWAL EDIT ===")
            print(f"tanggal: {tanggal}")
            print(f"frequency: {frequency}")
            
            # Convert and validate frequency
            try:
                frequency = int(frequency)
                print(f"DEBUG: Frequency converted to int: {frequency}")
            except ValueError:
                print("DEBUG: Invalid frequency value")
                messages.error(request, 'Frekuensi harus berupa angka!')
                return redirect('hijau_kesehatan_satwa:jadwal_pemeriksaan_list')
            
            # Get the specific record to update based on sequential ID
            get_record_query = """
            SELECT id_hewan, tgl_pemeriksaan_selanjutnya
            FROM jadwal_pemeriksaan_kesehatan jpk
            JOIN hewan h ON jpk.id_hewan = h.id
            ORDER BY jpk.tgl_pemeriksaan_selanjutnya ASC
            LIMIT 1 OFFSET %s
            """
            
            offset = int(id) - 1
            print(f"DEBUG: Getting record with offset: {offset}")
            cursor.execute(get_record_query, [offset])
            record = cursor.fetchone()
            print(f"DEBUG: Found record: {record}")
            
            if record:
                old_id_hewan, old_tanggal = record
                print(f"DEBUG: Old record - id_hewan: {old_id_hewan}, tanggal: {old_tanggal}")
                
                # Update the schedule
                update_query = """
                UPDATE jadwal_pemeriksaan_kesehatan 
                SET 
                    tgl_pemeriksaan_selanjutnya = %s,
                    freq_pemeriksaan_rutin = %s
                WHERE id_hewan = %s AND tgl_pemeriksaan_selanjutnya = %s
                """
                
                print("=== DEBUG UPDATE SQL - JADWAL ===")
                print(f"SQL Query: {update_query}")
                print(f"Parameters: [{tanggal}, {frequency}, {old_id_hewan}, {old_tanggal}]")
                
                cursor.execute(update_query, [tanggal, frequency, old_id_hewan, old_tanggal])
                print(f"DEBUG: Rows affected: {cursor.rowcount}")
                
                # Commit the transaction
                connection.commit()
                print("DEBUG: Transaction committed")
                
                # Check for trigger messages using a more robust approach
                trigger_message = ""
                try:
                    # Try to get custom message first
                    cursor.execute("SELECT COALESCE(current_setting('trigger_message', true), '')")
                    result = cursor.fetchone()
                    if result and result[0]:
                        trigger_message = result[0]
                    print(f"DEBUG: Trigger message: {trigger_message}")
                except Exception as trigger_error:
                    print(f"DEBUG: Error getting trigger message: {trigger_error}")
                    # If trigger message fails, just continue without it
                
                # Display success message and any trigger messages
                if trigger_message and trigger_message.strip():
                    messages.success(request, f'Jadwal pemeriksaan berhasil diperbarui! {trigger_message}')
                    print("DEBUG: Success message with trigger")
                else:
                    messages.success(request, 'Jadwal pemeriksaan berhasil diperbarui!')
                    print("DEBUG: Success message without trigger")
            else:
                print("DEBUG: Record not found for update")
                messages.error(request, 'Data tidak ditemukan!')
            
            # Close database connection
            cursor.close()
            connection.close()
            print("DEBUG: Database connection closed")
            
            return redirect('hijau_kesehatan_satwa:jadwal_pemeriksaan_list')
            
        else:
            # GET request - fetch the record to edit
            print("=== DEBUG GET REQUEST - JADWAL EDIT ===")
            fetch_query = """
            SELECT
                jpk.id_hewan,
                h.nama,
                h.spesies,
                jpk.tgl_pemeriksaan_selanjutnya,
                jpk.freq_pemeriksaan_rutin
            FROM
                jadwal_pemeriksaan_kesehatan jpk
            JOIN
                hewan h ON jpk.id_hewan = h.id
            ORDER BY
                jpk.tgl_pemeriksaan_selanjutnya ASC
            LIMIT 1 OFFSET %s
            """
            
            offset = int(id) - 1
            print(f"DEBUG: Fetching record with offset: {offset}")
            cursor.execute(fetch_query, [offset])
            row = cursor.fetchone()
            print(f"DEBUG: Fetched record: {row}")
            
            if row:
                schedule_to_edit = {
                    'id': id,
                    'id_hewan': str(row[0]),
                    'nama_hewan': row[1],
                    'spesies': row[2],
                    'tanggal': row[3].strftime('%Y-%m-%d') if row[3] else '',
                    'frequency': row[4]
                }
                print(f"DEBUG: Schedule to edit: {schedule_to_edit}")
                
                cursor.close()
                connection.close()
                print("DEBUG: Database connection closed")
                
                context = {
                    'schedule': schedule_to_edit
                }
                print("=== DEBUG JADWAL PEMERIKSAAN EDIT END ===")
                return render(request, 'hijau_kesehatan_satwa/jadwal_pemeriksaan_edit.html', context)
            else:
                cursor.close()
                connection.close()
                print("DEBUG: Record not found for edit")
                messages.error(request, 'Data tidak ditemukan!')
                return redirect('hijau_kesehatan_satwa:jadwal_pemeriksaan_list')
            
    except Exception as e:
        # Handle database errors
        print(f"=== DEBUG ERROR - JADWAL EDIT ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"Error details: {repr(e)}")
        
        # Rollback transaction if still active
        try:
            if 'connection' in locals():
                connection.rollback()
                print("DEBUG: Transaction rolled back")
        except Exception as rollback_error:
            print(f"DEBUG: Error in rollback: {rollback_error}")
        
        messages.error(request, f'Terjadi kesalahan: {str(e)}')
        
        # Close connection if it exists
        try:
            if 'cursor' in locals():
                cursor.close()
                print("DEBUG: Cursor closed in error handling")
            if 'connection' in locals():
                connection.close()
                print("DEBUG: Connection closed in error handling")
        except Exception as cleanup_error:
            print(f"DEBUG: Error in cleanup: {cleanup_error}")
        
        return redirect('hijau_kesehatan_satwa:jadwal_pemeriksaan_list')

# Updated jadwal_pemeriksaan_delete function to work with database
def jadwal_pemeriksaan_delete(request, id):
    if not check_doctor_access(request):
        return redirect('register_login:login')
    
    try:
        # Get database connection
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get the specific record to delete based on sequential ID
        get_record_query = """
        SELECT id_hewan, tgl_pemeriksaan_selanjutnya
        FROM jadwal_pemeriksaan_kesehatan jpk
        JOIN hewan h ON jpk.id_hewan = h.id
        ORDER BY jpk.tgl_pemeriksaan_selanjutnya ASC
        LIMIT 1 OFFSET %s
        """
        
        offset = int(id) - 1
        cursor.execute(get_record_query, [offset])
        record = cursor.fetchone()
        
        if record:
            id_hewan, tanggal_pemeriksaan = record
            print(f"DEBUG: Deleting record - id_hewan: {id_hewan}, tanggal: {tanggal_pemeriksaan}")
            
            # Delete the specific record
            delete_query = """
            DELETE FROM jadwal_pemeriksaan_kesehatan 
            WHERE id_hewan = %s AND tgl_pemeriksaan_selanjutnya = %s
            """
            
            cursor.execute(delete_query, [id_hewan, tanggal_pemeriksaan])
            print(f"DEBUG: Rows affected: {cursor.rowcount}")
            
            # Commit the transaction
            connection.commit()
            
            messages.success(request, 'Jadwal pemeriksaan berhasil dihapus!')
        else:
            messages.error(request, 'Data tidak ditemukan!')
        
        # Close database connection
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"DEBUG: Error in jadwal_pemeriksaan_delete: {str(e)}")
        
        # Handle database errors
        messages.error(request, f'Terjadi kesalahan saat menghapus data: {str(e)}')
        
        # Close connection if it exists
        try:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.rollback()
                connection.close()
        except:
            pass
    
    return redirect('hijau_kesehatan_satwa:jadwal_pemeriksaan_list')
            
# Tambahkan juga fungsi debug untuk melihat semua URL patterns
def debug_urls(request):
    """Debug function to check URL patterns"""
    if request.method == 'GET':
        from django.urls import reverse
        try:
            # Test URL generation
            test_url = reverse('hijau_kesehatan_satwa:jadwal_pemeriksaan_edit', args=[1])
            return HttpResponse(f"Test URL for edit: {test_url}")
        except Exception as e:
            return HttpResponse(f"URL Error: {str(e)}")
    return HttpResponse("Debug URL function")

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