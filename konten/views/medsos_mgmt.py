from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from konten.models import AkunMedsos
from .utils import generate_profile_link

# Halaman Manajemen Akun Medsos (Role: Commander)
@login_required
def manajemen_akun_medsos(request):
    active_role = request.session.get('active_role', 'COMMANDER')
    
    if request.method == 'POST':
        platform = request.POST.get('platform')
        raw_username = request.POST.get('username').strip()
        
        # Normalisasi: Pastikan username selalu diawali @ saat disimpan ke DB
        username = raw_username if raw_username.startswith('@') else f"@{raw_username}"
        
        if platform and username:
            # Cek apakah akun ini sudah pernah didaftarkan oleh SIAPAPUN di sistem (Global & Case Insensitive)
            exists = AkunMedsos.objects.filter(platform=platform, username__iexact=username).exists()
            
            if exists:
                messages.error(request, f"Gagal! Akun {platform} {username} sudah diklaim oleh personil lain.")
            else:
                link_profil = generate_profile_link(platform, username)
                AkunMedsos.objects.create(
                    owner=request.user,
                    role_pemegang='COMMANDER', # Simpan sebagai aset Commander
                    platform=platform,
                    username=username,
                    link_profil=link_profil,
                    status='PENDING'
                )
                messages.success(request, f"Aset wilayah {platform} {username} berhasil ditambahkan!")
            
            # Redirect kembali ke halaman yang sama untuk mencegah re-submit saat refresh
            return redirect('akun_medsos')
            
    # Akun milik Commander sendiri (Hanya yang didaftarkan sebagai COMMANDER)
    akun_list = AkunMedsos.objects.filter(owner=request.user, role_pemegang='COMMANDER')
    
    # Statistik Dinamis (Hanya akun milik user ini sebagai Commander)
    stats = {
        'total': akun_list.count(),
        'ig': akun_list.filter(platform='INSTAGRAM').count(),
        'tt': akun_list.filter(platform='TIKTOK').count(),
        'fb': akun_list.filter(platform='FACEBOOK').count(),
    }
    
    # Akun milik Cadre bawahan (Subordinates)
    cadre_sub_ids = request.user.subordinates.values_list('user_id', flat=True)
    akun_cadre_list = AkunMedsos.objects.filter(owner_id__in=cadre_sub_ids)
    
    context = {
        'akun_list': akun_list,
        'akun_cadre_list': akun_cadre_list,
        'stats': stats,
    }
    return render(request, 'dewandpc/akun_medsos.html', context)

# Halaman Verifikasi Akun Medsos (Role: DCO)
@login_required
def verifikasi_akun_medsos(request):
    # Ambil semua akun yang statusnya PENDING
    akun_pending = AkunMedsos.objects.filter(status='PENDING').order_by('-tanggal_daftar')
    context = {
        'akun_pending': akun_pending,
    }
    return render(request, 'konten/verifikasi_akun.html', context)

@login_required
def proses_verifikasi_akun(request, akun_id, action):
    try:
        akun = AkunMedsos.objects.get(id=akun_id)
        if action == 'approve':
            akun.status = 'VERIFIED'
            messages.success(request, f"Akun {akun.username} ({akun.platform}) berhasil diverifikasi!")
        elif action == 'reject':
            akun.status = 'REJECTED'
            messages.warning(request, f"Pendaftaran akun {akun.username} ({akun.platform}) telah ditolak.")
        akun.save()
    except AkunMedsos.DoesNotExist:
        messages.error(request, "Akun tidak ditemukan.")
    
    return redirect('verifikasi_akun')
