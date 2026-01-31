#!/bin/bash
echo "===================================="
echo "   Auto Push Git - PATRIOT (MAC/LINUX)"
echo "===================================="

# Cek apakah ada perubahan
git status -s

read -p "Masukkan pesan commit: " msg
if [ -z "$msg" ]; then
    msg="Update"
fi

echo "Menambahkan perubahan..."
git add .

echo "Melakukan commit dengan pesan: $msg"
git commit -m "$msg"

echo "Melakukan push ke branch main..."
git push origin main

echo ""
echo "===================================="
echo "   Push Selesai!"
echo "===================================="
