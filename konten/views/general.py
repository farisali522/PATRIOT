from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Halaman SOP (Standard Operating Procedure)
@login_required
def sop_view(request):
    return render(request, 'sop.html')
