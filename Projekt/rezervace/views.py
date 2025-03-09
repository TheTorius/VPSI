from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import RegistrationForm
from django.contrib.auth import login
from django.contrib.auth.models import User

# Create your views here.
@login_required
def home(request):
    return render(request, 'rezervace/home.html') 


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Automaticky přihlásí uživatele po registraci
            return redirect('login')  # Můžeš přesměrovat na domovskou stránku nebo jinou stránku
    else:
        form = RegistrationForm()
    return render(request, 'rezervace/register.html', {'form': form})
