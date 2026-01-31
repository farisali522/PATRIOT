from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash

# Landing Page
def landing_page(request):
    # Set default role jika belum ada
    if 'active_role' not in request.session:
        if request.user.is_authenticated:
            # Jika user sudah login, arahkan ke role aslinya
            request.session['active_role'] = request.user.profile.role
        else:
            request.session['active_role'] = 'DCO'
    return render(request, 'landing.html')

@login_required
def switch_role(request, role_name):
    # Simpan role ke session
    request.session['active_role'] = role_name
    # Redirect kembali ke halaman sebelumnya
    return redirect(request.META.get('HTTP_REFERER', 'dashboard_uploader'))

# Login Page
def login_page(request):
    return render(request, 'login.html')

@login_required
def ubah_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validasi password lama
        if not request.user.check_password(old_password):
            messages.error(request, "Password lama tidak sesuai!")
            return redirect('ubah_password')
        
        # Validasi password baru dan konfirmasi
        if new_password != confirm_password:
            messages.error(request, "Password baru dan konfirmasi tidak cocok!")
            return redirect('ubah_password')
        
        # Validasi panjang password
        if len(new_password) < 8:
            messages.error(request, "Password minimal 8 karakter!")
            return redirect('ubah_password')
        
        # Update password
        request.user.set_password(new_password)
        request.user.save()
        
        # Update session agar tidak logout
        update_session_auth_hash(request, request.user)
        
        messages.success(request, "Password berhasil diubah!")
        return redirect('ubah_password')
    
    return render(request, 'password.html')
