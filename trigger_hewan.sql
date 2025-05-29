-- Membuat tabel RIWAYAT_SATWA jika belum ada
CREATE TABLE IF NOT EXISTS sizopi.RIWAYAT_SATWA (
    id SERIAL PRIMARY KEY,
    id_hewan UUID REFERENCES sizopi.hewan(id),
    tanggal_perubahan TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    kolom_diubah VARCHAR(50),
    nilai_lama VARCHAR(255),
    nilai_baru VARCHAR(255)
);

-- Trigger untuk memeriksa duplikasi data satwa
CREATE OR REPLACE FUNCTION check_duplicate_animal()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM sizopi.hewan
        WHERE LOWER(nama_individu) = LOWER(NEW.nama_individu)
        AND LOWER(spesies) = LOWER(NEW.spesies)
        AND LOWER(asal_hewan) = LOWER(NEW.asal_hewan)
        AND id != COALESCE(NEW.id, '00000000-0000-0000-0000-000000000000'::uuid)
    ) THEN
        RAISE EXCEPTION 'Data satwa atas nama "%", spesies "%", dan berasal dari "%" sudah terdaftar.',
            INITCAP(NEW.nama_individu), INITCAP(NEW.spesies), INITCAP(NEW.asal_hewan);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER tr_check_duplicate_animal
BEFORE INSERT OR UPDATE ON sizopi.hewan
FOR EACH ROW
EXECUTE FUNCTION check_duplicate_animal();

-- Trigger untuk mencatat perubahan status kesehatan dan habitat
CREATE OR REPLACE FUNCTION log_animal_changes()
RETURNS TRIGGER AS $$
BEGIN
    -- Mencatat perubahan status kesehatan
    IF NEW.status_kesehatan IS DISTINCT FROM OLD.status_kesehatan THEN
        INSERT INTO sizopi.RIWAYAT_SATWA (id_hewan, kolom_diubah, nilai_lama, nilai_baru)
        VALUES (NEW.id, 'status_kesehatan', OLD.status_kesehatan, NEW.status_kesehatan);
    END IF;

    -- Mencatat perubahan habitat
    IF NEW.nama_habitat IS DISTINCT FROM OLD.nama_habitat THEN
        INSERT INTO sizopi.RIWAYAT_SATWA (id_hewan, kolom_diubah, nilai_lama, nilai_baru)
        VALUES (NEW.id, 'nama_habitat', OLD.nama_habitat, NEW.nama_habitat);
    END IF;

    -- Menampilkan pesan sukses
    IF NEW.status_kesehatan IS DISTINCT FROM OLD.status_kesehatan OR 
       NEW.nama_habitat IS DISTINCT FROM OLD.nama_habitat THEN
        RAISE NOTICE 'SUKSES: Riwayat perubahan status kesehatan dari "%" menjadi "%" atau habitat dari "%" menjadi "%" telah dicatat.',
            OLD.status_kesehatan, NEW.status_kesehatan, OLD.nama_habitat, NEW.nama_habitat;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER tr_log_animal_changes
AFTER UPDATE ON sizopi.hewan
FOR EACH ROW
EXECUTE FUNCTION log_animal_changes(); 