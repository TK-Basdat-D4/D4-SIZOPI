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

# Updated pemberian_pakan_list function with raw SQL query and debug messages
def pemberian_pakan_list(request):
    print("=== DEBUG PEMBERIAN PAKAN LIST START ===")
    print(f"Request method: {request.method}")
    print(f"User in session: {'user' in request.session}")
    
    if not check_keeper_access(request):
        print("DEBUG: Access denied - redirecting to login")
        return redirect('register_login:login')
    
    try:
        # Get database connection
        connection = get_db_connection()
        cursor = connection.cursor()
        print("DEBUG: Database connection established")
        
        # Updated SQL query with JOIN to get animal and keeper information
        query = """
        SELECT 
            ROW_NUMBER() OVER (ORDER BY pakan.jadwal) AS row_id,
            pakan.id_hewan,
            hewan.nama AS nama_hewan,
            hewan.spesies AS spesies,
            pakan.jenis AS jenis_pakan,
            pakan.jumlah AS jumlah_pakan,
            pakan.jadwal AS jadwal,
            pakan.status AS status,
            memberi.username_jh AS penjaga_hewan
        FROM 
            pakan
        JOIN 
            hewan ON pakan.id_hewan = hewan.id
        LEFT JOIN 
            memberi ON pakan.id_hewan = memberi.id_hewan AND pakan.jadwal = memberi.jadwal
        ORDER BY 
            pakan.jadwal
        """
        
        print(f"DEBUG: Executing query: {query}")
        cursor.execute(query)
        rows = cursor.fetchall()
        print(f"DEBUG: Found {len(rows)} feeding records")
        
        # Convert query results to list of dictionaries
        feeding_schedules = []
        for i, row in enumerate(rows, 1):
            feeding_dict = {
                'id': row[0],  # ROW_NUMBER as ID for display purposes
                'id_hewan': row[1],  # Animal ID (UUID)
                'nama_hewan': row[2],  # Nama Hewan
                'spesies': row[3],  # Spesies
                'jenis': row[4],  # Jenis Pakan
                'jumlah': row[5],  # Jumlah Pakan (gram)
                'jadwal': row[6],  # Jadwal
                'status': row[7],  # Status
                'penjaga_hewan': row[8] if row[8] else 'Belum ditugaskan'  # Penjaga Hewan (handle NULL)
            }
            feeding_schedules.append(feeding_dict)
            if i <= 3:  # Only print first 3 to reduce log spam
                print(f"DEBUG: Feeding schedule {i}: {feeding_dict}")
        
        # Close database connection
        cursor.close()
        connection.close()
        print("DEBUG: Database connection closed")
        
        context = {
            'feeding_schedules': feeding_schedules
        }
        print(f"DEBUG: Context prepared with {len(feeding_schedules)} feeding schedules")
        print("=== DEBUG PEMBERIAN PAKAN LIST END ===")
        return render(request, 'hijau_kesehatan_satwa/pemberian_pakan_list.html', context)
        
    except Exception as e:
        # Handle database errors
        print(f"=== DEBUG ERROR - FEEDING LIST ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"Error details: {repr(e)}")
        
        messages.error(request, f'Terjadi kesalahan saat mengambil data pemberian pakan: {str(e)}')
        
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
            'feeding_schedules': []
        }
        print("DEBUG: Returning empty context due to error")
        return render(request, 'hijau_kesehatan_satwa/pemberian_pakan_list.html', context)
    
def riwayat_pemberian_pakan(request):
    print("=== DEBUG RIWAYAT PEMBERIAN PAKAN START ===")
    print(f"Request method: {request.method}")
    print(f"User in session: {'user' in request.session}")
    
    if not check_keeper_access(request):
        print("DEBUG: Access denied - redirecting to login")
        return redirect('register_login:login')
    
    try:
        # Get database connection
        connection = get_db_connection()
        cursor = connection.cursor()
        print("DEBUG: Database connection established")
        
        # Updated SQL query to get feeding history with additional hewan table columns
        query = """
        SELECT
            ROW_NUMBER() OVER (ORDER BY pakan.jadwal DESC) AS row_id,
            pakan.id_hewan,
            hewan.nama AS "Nama Hewan",
            hewan.spesies AS "Spesies",
            hewan.asal_hewan AS "Asal Hewan",
            hewan.nama_habitat AS "Habitat",
            hewan.status_kesehatan AS "Status Kesehatan",
            pakan.jenis AS "Jenis Pakan",
            pakan.jumlah AS "Jumlah Pakan (gram)",
            pakan.jadwal AS "Jadwal",
            pakan.status AS "Status",
            memberi.username_jh AS "Penjaga Hewan"
        FROM
            pakan
        JOIN
            hewan ON pakan.id_hewan = hewan.id
        LEFT JOIN
            memberi ON pakan.id_hewan = memberi.id_hewan AND pakan.jadwal = memberi.jadwal
        WHERE
            pakan.status = 'Diberikan'
        ORDER BY
            pakan.jadwal DESC
        """
        
        print(f"DEBUG: Executing query: {query}")
        cursor.execute(query)
        rows = cursor.fetchall()
        print(f"DEBUG: Found {len(rows)} feeding history records with status 'Diberikan'")
        
        # Convert query results to list of dictionaries
        # Updated to match the new query with 12 columns
        feeding_history = []
        for i, row in enumerate(rows, 1):
            history_dict = {
                'id': row[0],  # ROW_NUMBER as ID for display purposes
                'id_hewan': row[1],  # Animal ID (UUID)
                'nama_individu': row[2],  # Nama Hewan (column 2)
                'spesies': row[3],  # Spesies (column 3)
                'asal_hewan': row[4] if row[4] else 'Tidak diketahui',  # Asal Hewan (column 4)
                'habitat': row[5] if row[5] else 'Tidak diketahui',  # Habitat/nama_habitat (column 5)
                'status_kesehatan': row[6] if row[6] else 'Tidak diketahui',  # Status Kesehatan (column 6)
                'jenis_pakan': row[7],  # Jenis Pakan (column 7)
                'jumlah': row[8],  # Jumlah Pakan (column 8)
                'jadwal': row[9],  # Jadwal (column 9)
                'status': row[10],  # Status (column 10)
                'penjaga_hewan': row[11] if row[11] else 'Belum ditugaskan'  # Penjaga Hewan (column 11)
            }
            feeding_history.append(history_dict)
            if i <= 3:  # Only print first 3 to reduce log spam
                print(f"DEBUG: Feeding history {i}: {history_dict}")
        
        # Close database connection
        cursor.close()
        connection.close()
        print("DEBUG: Database connection closed")
        
        context = {
            'feeding_history': feeding_history
        }
        print(f"DEBUG: Context prepared with {len(feeding_history)} feeding history records")
        print("=== DEBUG RIWAYAT PEMBERIAN PAKAN END ===")
        return render(request, 'hijau_kesehatan_satwa/riwayat_pemberian_pakan.html', context)
        
    except Exception as e:
        # Handle database errors
        print(f"=== DEBUG ERROR - FEEDING HISTORY ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"Error details: {repr(e)}")
        
        messages.error(request, f'Terjadi kesalahan saat mengambil riwayat pemberian pakan: {str(e)}')
        
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
            'feeding_history': []
        }
        print("DEBUG: Returning empty context due to error")
        return render(request, 'hijau_kesehatan_satwa/riwayat_pemberian_pakan.html', context)

def pemberian_pakan_form(request):
    print("=== DEBUG PEMBERIAN PAKAN FORM START ===")
    print(f"Request method: {request.method}")
    print(f"User in session: {'user' in request.session}")
    
    if not check_keeper_access(request):
        print("DEBUG: Access denied - redirecting to login")
        return redirect('register_login:login')
    
    if request.method == 'POST':
        print("=== DEBUG POST REQUEST - PAKAN FORM ===")
        connection = None
        cursor = None
        
        try:
            # Get database connection
            connection = get_db_connection()
            cursor = connection.cursor()
            print("DEBUG: Database connection established")
            
            # Get current user (keeper)
            current_user = request.session.get('user', {})
            username = current_user.get('username', '')
            print(f"DEBUG: Current user: {current_user}")
            print(f"DEBUG: Username: {username}")
            
            # Get form data
            animal_id = request.POST.get('animal_id')
            jenis_pakan = request.POST.get('jenis')
            jumlah = request.POST.get('jumlah')
            jadwal = request.POST.get('jadwal')
            
            print("=== DEBUG FORM DATA - PAKAN ===")
            print(f"animal_id: {animal_id}")
            print(f"jenis_pakan: {jenis_pakan}")
            print(f"jumlah: {jumlah}")
            print(f"jadwal: {jadwal}")
            
            # Convert and validate jumlah
            try:
                jumlah = float(jumlah)
                print(f"DEBUG: Jumlah converted to float: {jumlah}")
            except (ValueError, TypeError):
                print("DEBUG: Invalid jumlah value")
                messages.error(request, 'Jumlah pakan harus berupa angka!')
                return redirect('hijau_kesehatan_satwa:pemberian_pakan_form')
            
            # Validate required fields
            if not animal_id:
                print("DEBUG: Validation failed - animal_id is empty")
                messages.error(request, 'Silahkan pilih hewan untuk pemberian pakan!')
                return redirect('hijau_kesehatan_satwa:pemberian_pakan_form')
            
            if not jenis_pakan:
                print("DEBUG: Validation failed - jenis_pakan is empty")
                messages.error(request, 'Jenis pakan wajib diisi!')
                return redirect('hijau_kesehatan_satwa:pemberian_pakan_form')
            
            if not jadwal:
                print("DEBUG: Validation failed - jadwal is empty")
                messages.error(request, 'Jadwal pemberian wajib diisi!')
                return redirect('hijau_kesehatan_satwa:pemberian_pakan_form')
            
            # Validate UUID format for animal_id
            try:
                import uuid
                uuid.UUID(animal_id)
                print("DEBUG: UUID validation passed")
            except ValueError:
                print("DEBUG: Invalid UUID format")
                messages.error(request, 'Format ID hewan tidak valid!')
                return redirect('hijau_kesehatan_satwa:pemberian_pakan_form')
            
            print("DEBUG: Form validation passed")
            
            # Start transaction
            connection.autocommit = False
            print("DEBUG: Autocommit disabled, starting transaction")
            
            # Verify the animal exists
            verify_query = "SELECT COUNT(*) FROM hewan WHERE id = %s"
            print(f"DEBUG: Verifying animal exists: {verify_query}")
            cursor.execute(verify_query, [animal_id])
            animal_count = cursor.fetchone()[0]
            
            if animal_count == 0:
                print("DEBUG: Animal not found")
                connection.rollback()
                messages.error(request, 'Hewan yang dipilih tidak ditemukan!')
                return redirect('hijau_kesehatan_satwa:pemberian_pakan_form')
            
            print(f"DEBUG: Animal found, count: {animal_count}")
            
            # Check if this feeding schedule already exists
            check_duplicate_query = """
            SELECT COUNT(*) FROM pakan 
            WHERE id_hewan = %s AND jadwal = %s
            """
            cursor.execute(check_duplicate_query, [animal_id, jadwal])
            duplicate_count = cursor.fetchone()[0]
            
            if duplicate_count > 0:
                print("DEBUG: Duplicate feeding schedule found")
                connection.rollback()
                messages.error(request, 'Jadwal pemberian pakan untuk hewan ini sudah ada!')
                return redirect('hijau_kesehatan_satwa:pemberian_pakan_form')
            
            # Insert new feeding record
            insert_pakan_query = """
            INSERT INTO pakan (
                id_hewan, 
                jenis, 
                jumlah, 
                jadwal,
                status
            ) VALUES (%s, %s, %s, %s, %s)
            """
            
            # Set default status as 'Dijadwalkan'
            status = 'Dijadwalkan'
            
            print("=== DEBUG SQL EXECUTION - PAKAN INSERT ===")
            print(f"SQL Query: {insert_pakan_query}")
            print(f"Parameters: [{animal_id}, {jenis_pakan}, {jumlah}, {jadwal}, {status}]")
            
            cursor.execute(insert_pakan_query, [animal_id, jenis_pakan, jumlah, jadwal, status])
            print("DEBUG: Pakan record inserted successfully")
            
            # Insert into memberi table to track who assigned this feeding
            insert_memberi_query = """
            INSERT INTO memberi (
                id_hewan,
                jadwal,
                username_jh
            ) VALUES (%s, %s, %s)
            """
            
            print("=== DEBUG SQL EXECUTION - MEMBERI INSERT ===")
            print(f"SQL Query: {insert_memberi_query}")
            print(f"Parameters: [{animal_id}, {jadwal}, {username}]")
            
            cursor.execute(insert_memberi_query, [animal_id, jadwal, username])
            print("DEBUG: Memberi record inserted successfully")
            
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
                messages.success(request, f'Jadwal pemberian pakan berhasil disimpan! {trigger_message}')
                print("DEBUG: Success message with trigger")
            else:
                messages.success(request, 'Jadwal pemberian pakan berhasil disimpan!')
                print("DEBUG: Success message without trigger")
            
            print("=== DEBUG: Redirecting to pakan list ===")
            return redirect('hijau_kesehatan_satwa:pemberian_pakan_list')
            
        except Exception as e:
            # Handle database errors
            print(f"=== DEBUG ERROR - PAKAN FORM ===")
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
    print("=== DEBUG GET REQUEST - Fetching animals for pakan ===")
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
        
        # Convert to dictionary format for template compatibility
        # Based on the HTML template, it expects animals.items()
        animals = {}
        for i, animal in enumerate(animals_data):
            animal_id = str(animal[0])  # Convert UUID to string
            animals[animal_id] = {
                'nama_individu': animal[1],
                'spesies': animal[2],
                'asal_hewan': animal[3],
                'tanggal_lahir': animal[4].strftime('%Y-%m-%d') if animal[4] else '',
                'nama_habitat': animal[5],
                'status_kesehatan': animal[6]
            }
            if i < 5:  # Only print first 5 to reduce log spam
                print(f"DEBUG: Animal {i+1}: ID={animal_id}, Data={animals[animal_id]}")

        print("DEBUG: Animals data fetched successfully")
        
        cursor.close()
        connection.close()
        print("DEBUG: Database connection closed")
        
        context = {'animals': animals}
        print(f"DEBUG: Context prepared with {len(animals)} animals")
        print("=== DEBUG PEMBERIAN PAKAN FORM END ===")
        return render(request, 'hijau_kesehatan_satwa/pemberian_pakan_form.html', context)
        
    except Exception as e:
        # Handle database errors when fetching animals
        print(f"=== DEBUG ERROR FETCHING ANIMALS - PAKAN ===")
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
        
        context = {'animals': {}}
        print("DEBUG: Returning empty animals context due to error")
        return render(request, 'hijau_kesehatan_satwa/pemberian_pakan_form.html', context)

def pemberian_pakan_edit(request, id):
    if not check_keeper_access(request):
        return redirect('register_login:login')
    
    connection = None
    cursor = None
    
    try:
        # Get database connection
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get the feeding record to edit
        get_feeding_query = """
        WITH numbered_pakan AS (
            SELECT
                ROW_NUMBER() OVER (ORDER BY pakan.jadwal) AS row_id,
                pakan.id_hewan,
                hewan.nama AS nama_hewan,
                hewan.spesies AS spesies,
                pakan.jenis AS jenis_pakan,
                pakan.jumlah AS jumlah_pakan,
                pakan.jadwal AS jadwal,
                pakan.status AS status,
                memberi.username_jh AS penjaga_hewan
            FROM
                pakan
            JOIN
                hewan ON pakan.id_hewan = hewan.id
            LEFT JOIN
                memberi ON pakan.id_hewan = memberi.id_hewan AND pakan.jadwal = memberi.jadwal
            ORDER BY
                pakan.jadwal
        )
        SELECT 
            id_hewan,
            nama_hewan,
            spesies,
            jenis_pakan,
            jumlah_pakan,
            jadwal,
            status,
            penjaga_hewan
        FROM numbered_pakan 
        WHERE row_id = %s
        """
        
        cursor.execute(get_feeding_query, [id])
        feeding_data = cursor.fetchone()
        
        if not feeding_data:
            messages.error(request, 'Data pemberian pakan tidak ditemukan!')
            return redirect('hijau_kesehatan_satwa:pemberian_pakan_list')
        
        # Convert feeding data to dictionary
        feeding_record = {
            'animal_id': str(feeding_data[0]),
            'nama_hewan': feeding_data[1],
            'spesies': feeding_data[2],
            'jenis_pakan': feeding_data[3],
            'jumlah': feeding_data[4],
            'jadwal': feeding_data[5],
            'status': feeding_data[6],
            'penjaga_hewan': feeding_data[7] if feeding_data[7] else 'Belum ditugaskan'
        }
        
        if request.method == 'POST':
            # Get current user
            current_user = request.session.get('user', {})
            username = current_user.get('username', '')
            
            # Get form data
            new_animal_id = request.POST.get('animal_id', '').strip()
            new_jenis_pakan = request.POST.get('jenis', '').strip()
            new_jumlah = request.POST.get('jumlah', '').strip()
            new_jadwal = request.POST.get('jadwal', '').strip()
            
            # Validation
            errors = []
            
            if not new_animal_id:
                errors.append('Silahkan pilih hewan untuk pemberian pakan!')
            
            if not new_jenis_pakan:
                errors.append('Jenis pakan wajib diisi!')
            
            if not new_jadwal:
                errors.append('Jadwal pemberian wajib diisi!')
            
            # Validate jumlah
            try:
                new_jumlah_float = float(new_jumlah) if new_jumlah else 0
                if new_jumlah_float <= 0:
                    errors.append('Jumlah pakan harus lebih dari 0!')
            except (ValueError, TypeError):
                errors.append('Jumlah pakan harus berupa angka!')
                new_jumlah_float = 0
            
            # Validate UUID format for animal_id
            if new_animal_id:
                try:
                    import uuid
                    uuid.UUID(new_animal_id)
                except ValueError:
                    errors.append('Format ID hewan tidak valid!')
            
            # If there are validation errors, show them and return to form
            if errors:
                for error in errors:
                    messages.error(request, error)
                
                # Get animals for dropdown
                animals_query = """
                    SELECT id, nama, spesies, asal_hewan, tanggal_lahir, nama_habitat, status_kesehatan
                    FROM hewan ORDER BY nama
                """
                cursor.execute(animals_query)
                animals_data = cursor.fetchall()
                
                animals = {}
                for animal in animals_data:
                    animal_id = str(animal[0])
                    animals[animal_id] = {
                        'nama_individu': animal[1],
                        'spesies': animal[2],
                        'asal_hewan': animal[3],
                        'tanggal_lahir': animal[4].strftime('%Y-%m-%d') if animal[4] else '',
                        'nama_habitat': animal[5],
                        'status_kesehatan': animal[6]
                    }
                
                # Update feeding_record with user input to preserve form data
                feeding_record.update({
                    'animal_id': new_animal_id,
                    'jenis_pakan': new_jenis_pakan,
                    'jumlah': new_jumlah,
                    'jadwal': new_jadwal
                })
                
                context = {
                    'feeding': feeding_record,
                    'animals': animals
                }
                return render(request, 'hijau_kesehatan_satwa/pemberian_pakan_form.html', context)
            
            # Start transaction
            connection.autocommit = False
            
            try:
                # Verify the new animal exists
                cursor.execute("SELECT COUNT(*) FROM hewan WHERE id = %s", [new_animal_id])
                animal_count = cursor.fetchone()[0]
                
                if animal_count == 0:
                    messages.error(request, 'Hewan yang dipilih tidak ditemukan!')
                    return redirect('hijau_kesehatan_satwa:pemberian_pakan_edit', id=id)
                
                # Check for duplicate if animal or jadwal changed
                if (new_animal_id != feeding_record['animal_id'] or 
                    str(new_jadwal) != str(feeding_record['jadwal'])):
                    
                    check_duplicate_query = """
                    SELECT COUNT(*) FROM pakan 
                    WHERE id_hewan = %s AND jadwal = %s
                    AND NOT (id_hewan = %s AND jadwal = %s)
                    """
                    cursor.execute(check_duplicate_query, [
                        new_animal_id, new_jadwal,
                        feeding_record['animal_id'], feeding_record['jadwal']
                    ])
                    duplicate_count = cursor.fetchone()[0]
                    
                    if duplicate_count > 0:
                        connection.rollback()
                        messages.error(request, 'Jadwal pemberian pakan untuk hewan ini sudah ada!')
                        return redirect('hijau_kesehatan_satwa:pemberian_pakan_edit', id=id)
                
                # Update the feeding record in pakan table
                update_pakan_query = """
                UPDATE pakan 
                SET id_hewan = %s, jenis = %s, jumlah = %s, jadwal = %s
                WHERE id_hewan = %s AND jadwal = %s
                """
                
                cursor.execute(update_pakan_query, [
                    new_animal_id, new_jenis_pakan, new_jumlah_float, new_jadwal,
                    feeding_record['animal_id'], feeding_record['jadwal']
                ])
                
                pakan_rows_affected = cursor.rowcount
                
                if pakan_rows_affected == 0:
                    connection.rollback()
                    messages.error(request, 'Data tidak dapat diperbarui. Mungkin data telah diubah oleh pengguna lain.')
                    return redirect('hijau_kesehatan_satwa:pemberian_pakan_list')
                
                # Handle memberi table
                # Check if memberi record exists
                cursor.execute("""
                    SELECT COUNT(*) FROM memberi 
                    WHERE id_hewan = %s AND jadwal = %s
                """, [feeding_record['animal_id'], feeding_record['jadwal']])
                
                memberi_exists = cursor.fetchone()[0] > 0
                
                if memberi_exists:
                    # Update existing memberi record
                    cursor.execute("""
                        UPDATE memberi 
                        SET id_hewan = %s, jadwal = %s, username_jh = %s
                        WHERE id_hewan = %s AND jadwal = %s
                    """, [
                        new_animal_id, new_jadwal, username,
                        feeding_record['animal_id'], feeding_record['jadwal']
                    ])
                else:
                    # Insert new memberi record
                    cursor.execute("""
                        INSERT INTO memberi (id_hewan, jadwal, username_jh)
                        VALUES (%s, %s, %s)
                    """, [new_animal_id, new_jadwal, username])
                
                # Commit the transaction
                connection.commit()
                
                # Success message
                messages.success(request, 'Data pemberian pakan berhasil diperbarui!')
                return redirect('hijau_kesehatan_satwa:pemberian_pakan_list')
                
            except Exception as transaction_error:
                connection.rollback()
                messages.error(request, f'Terjadi kesalahan saat memperbarui data: {str(transaction_error)}')
                return redirect('hijau_kesehatan_satwa:pemberian_pakan_edit', id=id)
        
        # GET request - fetch animals for dropdown
        animals_query = """
            SELECT id, nama, spesies, asal_hewan, tanggal_lahir, nama_habitat, status_kesehatan
            FROM hewan ORDER BY nama
        """
        
        cursor.execute(animals_query)
        animals_data = cursor.fetchall()
        
        # Convert to dictionary format
        animals = {}
        for animal in animals_data:
            animal_id = str(animal[0])
            animals[animal_id] = {
                'nama_individu': animal[1],
                'spesies': animal[2],
                'asal_hewan': animal[3],
                'tanggal_lahir': animal[4].strftime('%Y-%m-%d') if animal[4] else '',
                'nama_habitat': animal[5],
                'status_kesehatan': animal[6]
            }
        
        context = {
            'feeding': feeding_record,
            'animals': animals
        }
        return render(request, 'hijau_kesehatan_satwa/pemberian_pakan_form.html', context)
        
    except Exception as e:
        # Handle general errors
        if connection:
            try:
                connection.rollback()
            except:
                pass
        
        messages.error(request, f'Terjadi kesalahan: {str(e)}')
        return redirect('hijau_kesehatan_satwa:pemberian_pakan_list')
        
    finally:
        # Always close connections
        try:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        except:
            pass

def pemberian_pakan_delete(request, id):
    if not check_keeper_access(request):
        return redirect('register_login:login')
    
    connection = None
    cursor = None
    
    try:
        print(f"[DEBUG] Attempting to delete feeding record with id: {id}")
        
        # Get database connection without setting autocommit initially
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get the feeding record to delete using the same numbered query as edit
        get_feeding_query = """
        WITH numbered_pakan AS (
            SELECT
                ROW_NUMBER() OVER (ORDER BY pakan.jadwal) AS row_id,
                pakan.id_hewan,
                pakan.jadwal
            FROM
                pakan
            JOIN
                hewan ON pakan.id_hewan = hewan.id
            ORDER BY
                pakan.jadwal
        )
        SELECT 
            id_hewan,
            jadwal
        FROM numbered_pakan 
        WHERE row_id = %s
        """
        
        print(f"[DEBUG] Executing query to find feeding record")
        cursor.execute(get_feeding_query, [id])
        feeding_data = cursor.fetchone()
        
        print(f"[DEBUG] Query result: {feeding_data}")
        
        if not feeding_data:
            print(f"[DEBUG] No feeding data found for id: {id}")
            messages.error(request, 'Data pemberian pakan tidak ditemukan!')
            return redirect('hijau_kesehatan_satwa:pemberian_pakan_list')
        
        animal_id = feeding_data[0]
        jadwal = feeding_data[1]
        
        print(f"[DEBUG] Found feeding record - Animal ID: {animal_id}, Jadwal: {jadwal}")
        
        # Close the current connection and create a fresh one for the delete operation
        cursor.close()
        connection.close()
        print(f"[DEBUG] Closed initial connection, creating new one for delete")
        
        # Create new connection for delete operations
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Set autocommit to False for transaction
        connection.autocommit = False
        print(f"[DEBUG] Set autocommit to False, starting transaction")
        
        # Delete from memberi table first
        print(f"[DEBUG] Deleting from memberi table")
        cursor.execute("DELETE FROM memberi WHERE id_hewan = %s AND jadwal = %s", [animal_id, jadwal])
        memberi_affected = cursor.rowcount
        print(f"[DEBUG] Memberi rows affected: {memberi_affected}")
        
        # Delete from pakan table
        print(f"[DEBUG] Deleting from pakan table")
        cursor.execute("DELETE FROM pakan WHERE id_hewan = %s AND jadwal = %s", [animal_id, jadwal])
        pakan_affected = cursor.rowcount
        print(f"[DEBUG] Pakan rows affected: {pakan_affected}")
        
        if pakan_affected == 0:
            print(f"[DEBUG] No rows affected, rolling back")
            connection.rollback()
            messages.error(request, 'Data tidak dapat dihapus. Mungkin data telah dihapus oleh pengguna lain.')
            return redirect('hijau_kesehatan_satwa:pemberian_pakan_list')
        
        # Commit the transaction
        connection.commit()
        print(f"[DEBUG] Transaction committed successfully")
        
        messages.success(request, 'Data pemberian pakan berhasil dihapus!')
        return redirect('hijau_kesehatan_satwa:pemberian_pakan_list')
        
    except Exception as e:
        print(f"[DEBUG] Exception occurred: {str(e)}")
        print(f"[DEBUG] Exception type: {type(e).__name__}")
        
        if connection:
            try:
                connection.rollback()
                print(f"[DEBUG] Rolled back transaction")
            except Exception as rollback_error:
                print(f"[DEBUG] Rollback error: {str(rollback_error)}")
        
        messages.error(request, f'Terjadi kesalahan: {str(e)}')
        return redirect('hijau_kesehatan_satwa:pemberian_pakan_list')
        
    finally:
        print(f"[DEBUG] Cleaning up connections")
        try:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
        except Exception as cleanup_error:
            print(f"[DEBUG] Cleanup error: {str(cleanup_error)}")

def beri_pakan(request, id):
    print("=== DEBUG BERI PAKAN START ===")
    print(f"Request method: {request.method}")
    print(f"Feeding ID: {id}")
    print(f"User in session: {'user' in request.session}")
    
    if not check_keeper_access(request):
        print("DEBUG: Access denied - redirecting to login")
        return redirect('register_login:login')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Get database connection
        connection = get_db_connection()
        cursor = connection.cursor()
        print("DEBUG: Database connection established")
        
        # Get current user (keeper)
        current_user = request.session.get('user', {})
        username = current_user.get('username', '')
        print(f"DEBUG: Current user: {current_user}")
        
        # PERBAIKAN 1: Gunakan query yang sama seperti di list untuk konsistensi
        get_feeding_query = """
        WITH numbered_pakan AS (
            SELECT 
                ROW_NUMBER() OVER (ORDER BY pakan.jadwal) as row_id,
                pakan.id_hewan,
                pakan.jenis,
                pakan.jumlah,
                pakan.jadwal,
                pakan.status
            FROM pakan
            ORDER BY pakan.jadwal
        )
        SELECT 
            id_hewan,
            jenis,
            jumlah,
            jadwal,
            status
        FROM numbered_pakan 
        WHERE row_id = %s
        """
        
        print(f"DEBUG: Getting feeding record with ID: {id}")
        cursor.execute(get_feeding_query, [id])
        feeding_data = cursor.fetchone()
        
        if not feeding_data:
            print("DEBUG: Feeding record not found")
            messages.error(request, 'Data pemberian pakan tidak ditemukan!')
            return redirect('hijau_kesehatan_satwa:pemberian_pakan_list')
        
        # Convert feeding data to dictionary
        feeding_record = {
            'animal_id': feeding_data[0],  # Tetap sebagai UUID object
            'jenis_pakan': feeding_data[1],
            'jumlah': feeding_data[2],
            'jadwal': feeding_data[3],
            'status': feeding_data[4]
        }
        print(f"DEBUG: Found feeding record: {feeding_record}")
        
        # Check if status allows feeding (only 'Dijadwalkan')
        if feeding_record['status'] != 'Dijadwalkan':
            print(f"DEBUG: Feeding not allowed with current status: {feeding_record['status']}")
            messages.warning(request, f'Pemberian pakan ini tidak dapat dilakukan! Status saat ini: {feeding_record["status"]}')
            return redirect('hijau_kesehatan_satwa:pemberian_pakan_list')
        
        print(f"DEBUG: Status allows feeding: {feeding_record['status']}")
        
        # Start transaction
        connection.autocommit = False
        print("DEBUG: Autocommit disabled, starting transaction")
        
        # PERBAIKAN 2: Update dengan kondisi yang lebih spesifik dan handle timestamp
        update_query = """
        UPDATE pakan 
        SET status = 'Diberikan'
        WHERE 
            id_hewan = %s 
            AND jenis = %s 
            AND jumlah = %s 
            AND DATE(jadwal) = DATE(%s)
            AND TIME(jadwal) = TIME(%s)
            AND status = 'Dijadwalkan'
        """
        
        print("=== DEBUG SQL EXECUTION - UPDATE STATUS ===")
        print(f"SQL Query: {update_query}")
        print(f"Parameters: [{feeding_record['animal_id']}, {feeding_record['jenis_pakan']}, {feeding_record['jumlah']}, {feeding_record['jadwal']}, {feeding_record['jadwal']}]")
        
        cursor.execute(update_query, [
            feeding_record['animal_id'], 
            feeding_record['jenis_pakan'], 
            feeding_record['jumlah'], 
            feeding_record['jadwal'],
            feeding_record['jadwal']
        ])
        
        rows_affected = cursor.rowcount
        print(f"DEBUG: Rows affected: {rows_affected}")
        
        if rows_affected == 0:
            print("DEBUG: No rows updated - checking if record still exists")
            
            # PERBAIKAN 3: Cek ulang apakah record masih ada dan statusnya
            check_query = """
            SELECT status FROM pakan 
            WHERE id_hewan = %s AND jenis = %s AND jumlah = %s 
            AND jadwal = %s
            """
            cursor.execute(check_query, [
                feeding_record['animal_id'], 
                feeding_record['jenis_pakan'], 
                feeding_record['jumlah'], 
                feeding_record['jadwal'],
                feeding_record['jadwal']
            ])
            current_status = cursor.fetchone()
            
            if current_status:
                status = current_status[0]
                if status == 'Diberikan':
                    connection.rollback()
                    messages.info(request, 'Pemberian pakan ini sudah dilakukan sebelumnya!')
                else:
                    connection.rollback()
                    messages.error(request, f'Status pemberian pakan sudah berubah menjadi: {status}')
            else:
                connection.rollback()
                messages.error(request, 'Data pemberian pakan tidak ditemukan!')
            
            return redirect('hijau_kesehatan_satwa:pemberian_pakan_list')
        
        # PERBAIKAN 4: Tambahkan record ke tabel memberi jika belum ada
        # Cek apakah sudah ada record di tabel memberi
        check_memberi_query = """
        SELECT COUNT(*) FROM memberi 
        WHERE id_hewan = %s AND jadwal = %s
        """
        cursor.execute(check_memberi_query, [
            feeding_record['animal_id'],
            feeding_record['jadwal'],
            feeding_record['jadwal']
        ])
        memberi_exists = cursor.fetchone()[0]
        
        if memberi_exists == 0:
            # Tambahkan record ke tabel memberi
            insert_memberi_query = """
            INSERT INTO memberi (username_jh, id_hewan, jadwal)
            VALUES (%s, %s, %s)
            """
            cursor.execute(insert_memberi_query, [
                username,
                feeding_record['animal_id'],
                feeding_record['jadwal']
            ])
            print(f"DEBUG: Added record to memberi table for keeper: {username}")
        
        # Commit the transaction
        connection.commit()
        print("DEBUG: Transaction committed successfully")
        
        # Display success message
        messages.success(request, f'Status pemberian pakan berhasil diubah menjadi "Diberikan"!')
        print("DEBUG: Success message displayed")
        
        print("=== DEBUG: Redirecting to pakan list ===")
        return redirect('hijau_kesehatan_satwa:pemberian_pakan_list')
        
    except Exception as e:
        # Handle database errors
        print(f"=== DEBUG ERROR - BERI PAKAN ===")
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
        
        messages.error(request, f'Terjadi kesalahan saat mengubah status pemberian pakan: {str(e)}')
        return redirect('hijau_kesehatan_satwa:pemberian_pakan_list')
        
    finally:
        # Always close connection
        try:
            if cursor:
                cursor.close()
                print("DEBUG: Cursor closed in cleanup")
            if connection:
                connection.close()
                print("DEBUG: Connection closed in cleanup")
        except Exception as cleanup_error:
            print(f"DEBUG: Error in cleanup: {cleanup_error}")


# TAMBAHAN: Fungsi helper untuk debug
def debug_pakan_data(connection, animal_id, jenis, jumlah, jadwal):
    """Helper function untuk debug data pakan"""
    cursor = connection.cursor()
    
    print("=== DEBUG PAKAN DATA ===")
    
    # Cek semua data pakan untuk hewan ini
    debug_query = """
    SELECT id_hewan, jenis, jumlah, jadwal, status 
    FROM pakan 
    WHERE id_hewan = %s
    ORDER BY jadwal
    """
    cursor.execute(debug_query, [animal_id])
    all_records = cursor.fetchall()
    
    print(f"All pakan records for animal {animal_id}:")
    for i, record in enumerate(all_records):
        print(f"  {i+1}. ID: {record[0]}, Jenis: {record[1]}, Jumlah: {record[2]}, Jadwal: {record[3]}, Status: {record[4]}")
    
    # Cek exact match
    exact_query = """
    SELECT COUNT(*) FROM pakan 
    WHERE id_hewan = %s AND jenis = %s AND jumlah = %s AND jadwal = %s
    """
    cursor.execute(exact_query, [animal_id, jenis, jumlah, jadwal])
    exact_count = cursor.fetchone()[0]
    print(f"Exact matches found: {exact_count}")
    
    cursor.close()
    return all_records