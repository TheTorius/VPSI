from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import RegistrationForm,LoginForm,SignUpForm,UserUpdateForm
from django.contrib.auth import login,authenticate,logout,update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Uzivatele, TypZakaznika, Novinky
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from .models import Rezervace, Hriste, RezervaceZapujcky
from django.core.mail import send_mail

# Create your views here.
@login_required
def home(request):
    return render(request, 'rezervace/home.html') 

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user.uzivatele)
        form2 = PasswordChangeForm(request.user, request.POST)
        if 'change_info' in request.POST and form.is_valid():
            form.save()
            messages.success(request,"Informace byly změněny!")
            form = UserUpdateForm(instance=request.user.uzivatele)    
            form2 = PasswordChangeForm(request.user)
            return render(request,'rezervace/profile.html',{'form':form, 'form2':form2})
        if 'change_password' in request.POST and form2.is_valid():
            user = form2.save()
            update_session_auth_hash(request, user)  # Aby uživatel zůstal přihlášen po změně hesla
            messages.success(request, 'Heslo bylo úspěšně změněno!')
            form = UserUpdateForm(instance=request.user.uzivatele)    
            form2 = PasswordChangeForm(request.user)
            return render(request,'rezervace/profile.html',{'form':form, 'form2':form2})
        
    else:
        form = UserUpdateForm(instance=request.user.uzivatele)    
        form2 = PasswordChangeForm(request.user)

    return render(request,'rezervace/profile.html',{'form':form, 'form2':form2})

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
    #return render(request, 'rezervace/rezervace.html')
    #return render(request, 'rezervace/index.html')
    news = Novinky.objects.all().order_by('-vytvoreno')[:4]
    return render(request, 'rezervace/index.html', {'news': news})

def hriste(request):
    # Example hours and reserved times
    hours = [f"{h:02d}:00" for h in range(8, 21)]  # 08:00 to 20:00
    court1_reserved = ["10:00", "14:00"]  # Example reserved times for Court 1
    court2_reserved = ["09:00", "15:00"]  # Example reserved times for Court 2
    context = {
        "hours": hours,
        "court1_reserved": court1_reserved,
        "court2_reserved": court2_reserved,
    }
    return render(request, "rezervace/hriste.html", context)

def reserve_hour(request, court, hour):
    # Logic to save the reservation (e.g., to a database)
    # Redirect back to reservation page after saving
    return redirect("hriste")

@login_required
def rezervace(request):
    user = request.user.uzivatele  # vazba na náš model Uzivatele
    reservations = Rezervace.objects.filter(uzivatel=user).order_by('-datum', '-cas_zacatku')
    reservations_zapujcky = RezervaceZapujcky.objects.filter(rezervace__uzivatel=user).order_by('-rezervace__datum', '-rezervace__cas_zacatku')


    # --- Volitelné filtrování dle GET parametrů ---
    datum = request.GET.get('datum')
    typ_hriste = request.GET.get('typ_hriste')

    if datum:
        reservations = reservations.filter(datum=datum)
        reservations_zapujcky = reservations_zapujcky.filter(rezervace__datum=datum)
    if typ_hriste and typ_hriste != '':
        reservations = reservations.filter(hriste__typ=typ_hriste)
        reservations_zapujcky = reservations_zapujcky.filter(rezervace__hriste__typ=typ_hriste)


    return render(request, 'rezervace/rezervace.html', {
        'reservations': reservations,
        'reservations_zapujcky': reservations_zapujcky,
        'vybrane_datum': datum if datum else '',
        'vybrany_typ': typ_hriste if typ_hriste else '',
        'hriste_typy': Hriste.objects.values_list('typ', flat=True).distinct()
    })

def zrusit_rezervaci(request, rez_id):
    try:
        rezervace = get_object_or_404(Rezervace, id=rez_id, uzivatel=request.user.uzivatele)
        uzivatel = rezervace.uzivatel
        datum = rezervace.datum
        hriste = rezervace.hriste.nazev

        # Odeslání e-mailu
        send_mail(
            subject="Vaše rezervace byla zrušena",
            message=f"Dobrý den {uzivatel.jmeno},\n\nVaše rezervace na {hriste} dne {datum.strftime('%d.%m.%Y')} byla úspěšně zrušena.",
            from_email=None,  # použije DEFAULT_FROM_EMAIL
            recipient_list=[uzivatel.email],
            fail_silently=False,
        )
        rezervace.delete()

        news = Novinky.objects.all().order_by('-vytvoreno')[:4]
        context = {
            'news': news,
            'success': True,  # Přidáme informaci o úspěchu
            'message': "Rezervace byla úspěšně zrušena a e-mail odeslán."
        }

    except Exception as e:
        context = {'error': True, 'message': f"Došlo k chybě při odesílání e-mailu o zruseni rezervace"}
    
    return render(request, 'rezervace/index.html', context)

def zrusit_rezervaci_zapujcky(request, rez_id):
    try:
        rezervace = get_object_or_404(RezervaceZapujcky, id=rez_id, rezervace__uzivatel=request.user.uzivatele)
        uzivatel = rezervace.rezervace.uzivatel
        datum = rezervace.rezervace.datum
        hriste = rezervace.rezervace.hriste.nazev
        predmet = rezervace.zapujcka.nazev
        mnozstvi = rezervace.mnozstvi

        # Odeslání e-mailu
        send_mail(
            subject="Vaše zápůjčka byla zrušena",
            message=(
                f"Dobrý den {uzivatel.jmeno},\n\n"
                f"Vaše zápůjčka předmětu \"{predmet}\" (množství: {mnozstvi}) "
                f"k rezervaci hřiště {hriste} dne {datum.strftime('%d.%m.%Y')} byla úspěšně zrušena."
            ),
            from_email=None,  # použije DEFAULT_FROM_EMAIL
            recipient_list=[uzivatel.email],
            fail_silently=False,
        )

        rezervace.delete()

        news = Novinky.objects.all().order_by('-vytvoreno')[:4]
        context = {
            'news': news,
            'success': True,
            'message': "Zápůjčka byla úspěšně zrušena a e-mail odeslán."
        }

    except Exception as e:
        context = {
            'error': True,
            'message': "Došlo k chybě při odesílání e-mailu o zrušení zápůjčky."
        }

    return render(request, 'rezervace/index.html', context)



def tisk_rezervace(request, rez_id):
    rezervace = get_object_or_404(Rezervace, id=rez_id)
    zapujcky = RezervaceZapujcky.objects.filter(rezervace=rezervace)
    return render(request, 'rezervace/tisk.html', {'rezervace': rezervace, 'zapujcky': zapujcky})

def tisk_rezervace_zapujcka(request, rez_id):
    rezervace = get_object_or_404(RezervaceZapujcky, id=rez_id)
    return render(request, 'rezervace/tiskZapujcka.html', {'rez': rezervace})


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
