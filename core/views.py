# core/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def choose_app(request):
    return render(request, 'core/choose_app.html')
