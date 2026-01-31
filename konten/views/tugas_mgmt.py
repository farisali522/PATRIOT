from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta, datetime
from konten.models import Konten, TugasKonten

@login_required
def tambah_tugas(request, konten_id):
    if request.method == 'POST':
        konten = Konten.objects.get(id=konten_id)
        jenis_tugas_list = request.POST.getlist('jenis_tugas[]')
        instruksi = request.POST.get('instruksi')
        
        # Validasi Timezone Aware
        today = timezone.localdate()
        tgl_mulai = request.POST.get('tanggal_mulai')
        tgl_selesai = request.POST.get('tanggal_selesai')
        
        # Konversi string ke date object untuk komparasi
        if tgl_mulai:
            tgl_mulai_obj = datetime.strptime(tgl_mulai, '%Y-%m-%d').date()
            if tgl_mulai_obj < today:
                tgl_mulai = today # Paksa jadi hari ini jika mundur
        else:
            tgl_mulai = today

        if not tgl_selesai:
            tgl_selesai = today + timedelta(days=3)

        poin = request.POST.get('poin') or 10

        # Tentukan boolean flags berdasarkan checkbox
        is_like = 'LIKE' in jenis_tugas_list
        is_komen = 'KOMEN' in jenis_tugas_list
        is_share = 'SHARE' in jenis_tugas_list
        is_follow = 'FOLLOW' in jenis_tugas_list
        is_reply = 'REPLY' in jenis_tugas_list
        
        # Buat SATU tugas dengan multiselect action
        if jenis_tugas_list: # Hanya simpan jika ada minimal 1 tugas dipilih
            TugasKonten.objects.create(
                konten=konten,
                is_like=is_like,
                is_komen=is_komen,
                is_share=is_share,
                is_follow=is_follow,
                is_reply=is_reply,
                instruksi=instruksi,
                tanggal_mulai=tgl_mulai,
                tanggal_selesai=tgl_selesai,
                poin=poin
            )
            
        return redirect('daftar_konten')
    return redirect('daftar_konten')

# Daftar Tugas (Manajemen)
@login_required
def daftar_tugas(request):
    today = timezone.localdate()
    
    # Tugas Aktif: Tanggal Selesai >= Hari Ini
    tugas_aktif = TugasKonten.objects.filter(
        tanggal_selesai__gte=today
    ).select_related('konten').order_by('tanggal_selesai')
    
    # Tugas Selesai/Riwayat: Tanggal Selesai < Hari Ini
    tugas_selesai = TugasKonten.objects.filter(
        tanggal_selesai__lt=today
    ).select_related('konten').order_by('-tanggal_selesai')[:20] 

    konten_list = Konten.objects.all().order_by('-tanggal_upload')
    
    context = {
        'tugas_aktif': tugas_aktif,
        'tugas_selesai': tugas_selesai,
        'konten_list': konten_list,
        'today': today
    }
    return render(request, 'konten/tugas.html', context)
