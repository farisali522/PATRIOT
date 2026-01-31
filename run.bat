@echo off
echo ====================================
echo    Memulai Server PATRIOT (Windows)
echo ====================================

:: 1. Cek folder venv
if not exist venv (
    echo [ERROR] Folder venv tidak ditemukan!
    echo Silahkan buat venv dulu dengan: python -m venv venv
    pause
    exit
)

:: 2. Aktifkan venv
echo Mengaktifkan Virtual Environment...
call venv\Scripts\activate

:: 3. Install requirements
echo Mengecek dan menginstall requirements...
pip install -r requirements.txt

:: 4. Run Server
echo Menjalankan server di 0.0.0.0:8000...
python manage.py runserver 0.0.0.0:8000

pause
