@echo off
echo ====================================
echo    Auto Push Git - PATRIOT
echo ====================================

:: Cek apakah ada perubahan
git status -s

set /p msg="Masukkan pesan commit: "
if "%msg%"=="" set msg="Update"

echo Menambahkan perubahan...
git add .

echo Melakukan commit dengan pesan: %msg%
git commit -m "%msg%"

echo Melakukan push ke branch main...
git push origin main

echo.
echo ====================================
echo    Push Selesai!
echo ====================================
pause
