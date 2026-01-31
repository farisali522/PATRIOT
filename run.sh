#!/bin/bash
echo "===================================="
echo "   Memulai Server PATRIOT (MAC/LINUX)"
echo "===================================="

# 1. Cek folder venv
if [ ! -d "venv" ]; then
    echo "[ERROR] Folder venv tidak ditemukan!"
    echo "Silahkan buat venv dulu dengan: python3 -m venv venv"
    exit 1
fi

# 2. Aktifkan venv
echo "Mengaktifkan Virtual Environment..."
source venv/bin/activate

# 3. Install requirements
echo "Mengecek dan menginstall requirements..."
pip install -r requirements.txt

# 4. Run Server
echo "Menjalankan server di 0.0.0.0:8000..."
python manage.py runserver 0.0.0.0:8000
