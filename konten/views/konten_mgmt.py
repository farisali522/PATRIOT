from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from konten.models import Konten, KategoriKonten

# Daftar Konten (Gallery)
@login_required
def daftar_konten(request):
    konten_list = Konten.objects.prefetch_related('daftar_tugas').all().order_by('-tanggal_upload')
    kategori_list = KategoriKonten.objects.all().order_by('nama')
    
    # Filter Platform
    platform = request.GET.get('platform')
    if platform and platform != 'ALL':
        konten_list = konten_list.filter(platform=platform)

    return render(request, 'konten/konten.html', {
        'daftar_konten': konten_list,
        'active_platform': platform or 'ALL',
        'kategori_list': kategori_list
    })

# Tambah Konten (Frontend)
@login_required
def tambah_konten(request):
    if request.method == 'POST':
        judul = request.POST.get('judul')
        platform = request.POST.get('platform')
        link_konten = request.POST.get('link_konten')
        kategori_id = request.POST.get('kategori')
        nama_kategori_baru = request.POST.get('nama_kategori_baru')
        deskripsi = request.POST.get('deskripsi')
        
        # Handle kategori: Prioritas Input Baru
        kategori_obj = None
        if nama_kategori_baru:
            # Case insensitive get or create logic manual prevent duplicate error if distinct case
            # Disini pakai simple get_or_create
            kategori_obj, created = KategoriKonten.objects.get_or_create(nama=nama_kategori_baru.strip())
        elif kategori_id:
            try:
                kategori_obj = KategoriKonten.objects.get(id=kategori_id)
            except KategoriKonten.DoesNotExist:
                kategori_obj = None
        
        try:
            Konten.objects.create(
                judul=judul,
                platform=platform,
                link_konten=link_konten,
                kategori=kategori_obj,
                deskripsi=deskripsi
            )
            messages.success(request, 'Konten berhasil ditambahkan!')
        except IntegrityError:
            messages.error(request, 'Gagal! Link konten ini sudah terdaftar. Silakan cek kembali.')
            return redirect('daftar_konten')
        return redirect('daftar_konten')
    return redirect('daftar_konten')
