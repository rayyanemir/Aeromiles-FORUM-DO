# Aeromiles

Tugas Kelompok 03 - Mata Kuliah Basis Data (Fasilkom UI)

---

## Anggota Kelompok

| Nama | NPM |
| :--- | :--- |
| Rayyan Emir Muhammad | 2406345375 |
| Dylan Pirade Ponglabba | 2406496126 |
| Garuga Dewangga Putra Handikto | 2406437615 |
| Naufal Fadli Rabbani | 2406350785 |

---

**Tech Stack:**
*   **Framework:** Django (Python)
*   **Database:** Supabase (PostgreSQL)


Instalasi
```bash
# Clone repositori
git clone https://github.com/rayyanemir/Aeromiles-FORUM-DO.git
cd Aeromiles-FORUM-DO

# Buat virtual environment
python -m venv venv

# Aktivasi venv (Windows)
.\venv\Scripts\activate

# Aktivasi venv (MacOS)
source env/bin/activate

# Instalasi library
pip install -r requirements.txt
```

### 3. Konfigurasi Environment (`.env`)
Buat file `.env` di folder root (sejajar dengan `manage.py`) dan isi dengan kredensial database Anda:
```text
DATABASE_URL=
SECRET_KEY=
DEBUG=True
```
url dan key akan diberikan di file pengumpulan
### 4. Database Setup
Gunakan SQL Dump yang tersedia untuk membuat skema tabel manual di Supabase, kemudian jalankan migrasi sistem Django:
```bash
python manage.py migrate
```

### 5. Menjalankan Server
```bash
python manage.py runserver
```
Buka [http://localhost:8000](http://localhost:8000) di browser Anda.


