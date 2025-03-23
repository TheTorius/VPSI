from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import RegistrationForm,LoginForm,SignUpForm
from django.contrib.auth import login,authenticate,logout
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Uzivatele, TypZakaznika, Novinky

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

def index(request):
    #return render(request, 'rezervace/index.html')
    news = Novinky.objects.all().order_by('-vytvoreno')[:4]
    return render(request, 'rezervace/index.html', {'news': news})

def main(request):
    #return render(request, 'rezervace/index.html')
    news = Novinky.objects.all().order_by('-vytvoreno')[:4]
    return render(request, 'rezervace/index.html', {'news': news})

def hriste(request):
    return render(request, 'rezervace/hriste.html')

def rezervace(request):
    return render(request, 'rezervace/rezervace.html')

def cennik(request):
    return render(request, 'rezervace/cennik.html')

def nastaveni(request):
    return render(request, 'rezervace/nastaveni.html')

def signup_view(request):
    if request.method == 'POST':
        print("POST data:", request.POST)
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data.get('email'),
                email=form.cleaned_data.get('email'),
                password=form.cleaned_data.get('password'),
            )
            uzivatele = Uzivatele.objects.create(
                user=user,
                jmeno=form.cleaned_data.get('jmeno'),  # Updated to match form field
                prijmeni=form.cleaned_data.get('prijmeni'),  # Updated to match form field
                email=form.cleaned_data.get('email'),
                telefon=form.cleaned_data.get('telefon'),  # Updated to match form field
                typ_zakaznika=TypZakaznika.objects.get_or_create(typ_zakaznika='new', defaults={'sleva': 0})[0]
            )
            login(request, user)
            messages.success(request, "Successfully signed up!")
            return redirect('index')
        else:
            print("Form errors:", form.errors)
    else:
        form = SignUpForm()
    return render(request, 'rezervace/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            try:
                uzivatele = Uzivatele.objects.get(email=email)
                user = authenticate(request, username=uzivatele.user.username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, "Successfully logged in!")
                    return redirect('index')
                else:
                    messages.error(request, "Invalid email or password.")
            except Uzivatele.DoesNotExist:
                messages.error(request, "Invalid email or password.")
    else:
        form = LoginForm()
    return render(request, 'rezervace/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, "Successfully logged out!")
    return redirect('home')
