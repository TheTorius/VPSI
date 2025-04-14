from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import RegistrationForm,LoginForm,SignUpForm,UserUpdateForm, HristeForm
from django.contrib.auth import login,authenticate,logout,update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Uzivatele, TypZakaznika, Novinky, Zapujcky
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from .models import Rezervace, Hriste, RezervaceZapujcky, SezoniCena, DenniCena
from django.core.mail import send_mail
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta

# Create your views here.
@login_required
def home(request):
    return render(request, 'rezervace/home.html') 

@login_required
def profile_view(request):
    # Check if user has a related Uzivatele object, create one if not
    try:
        request.user.uzivatele
    except:
        # If the user doesn't have a uzivatele, create one
        from .models import Uzivatele, TypZakaznika
        Uzivatele.objects.create(
            user=request.user,
            jmeno=request.user.username,
            prijmeni="",
            email=request.user.email or f"{request.user.username}@example.com",
            telefon="",
            typ_zakaznika=TypZakaznika.objects.get_or_create(typ_zakaznika='new', defaults={'sleva': 0})[0]
        )
        
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
    # Get date from query parameter; default to today
    datum_str = request.GET.get('datum')
    if datum_str:
        try:
            datum = datetime.strptime(datum_str, '%Y-%m-%d').date()
        except ValueError:
            datum = timezone.now().date()
    else:
        datum = timezone.now().date()

    # Get filter for court type
    vybrany_typ = request.GET.get('typ_hriste', '')

    # Fetch active courts, optionally filtered by type
    hriste_qs = Hriste.objects.filter(aktivni=True)
    if vybrany_typ:
        hriste_qs = hriste_qs.filter(typ=vybrany_typ)

    # Get all court types for filter dropdown
    hriste_typy = Hriste.objects.filter(aktivni=True).values_list('typ', flat=True).distinct()

    # Generate hours as time ranges (e.g., 08:00-09:00, 09:00-10:00, ..., 20:00-21:00)
    hours = []
    for h in range(8, 21):  # 08:00 to 20:00
        start_time = f"{h:02d}:00"
        end_time = f"{(h + 1):02d}:00"
        hours.append({'start': start_time, 'end': end_time})

    # Fetch reservations for the selected date
    reservations = Rezervace.objects.filter(datum=datum)

    # Prepare reserved times for each court
    courts_data = []
    for hriste in hriste_qs:
        # Get reserved hours for this court (based on start time)
        reserved_hours = []
        for res in reservations.filter(hriste=hriste):
            # Extract start hour from cas_zacatku (e.g., "08:00")
            hour = res.cas_zacatku.strftime('%H:%M')
            # Check if hour matches any start time in hours
            if any(h['start'] == hour for h in hours):
                reserved_hours.append(hour)
        courts_data.append({
            'id': hriste.id,
            'nazev': hriste.nazev,
            'reserved_hours': reserved_hours,
        })

    context = {
        'hours': hours,
        'courts_data': courts_data,
        'hriste_typy': hriste_typy,
        'vybrane_datum': datum.strftime('%Y-%m-%d'),
        'vybrany_typ': vybrany_typ,
    }
    return render(request, 'rezervace/hriste.html', context)

@csrf_exempt
@login_required
def reserve_multiple(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            reservations = data.get('reservations', [])
            datum_str = data.get('datum')

            # Validate datum
            if datum_str:
                try:
                    datum = datetime.strptime(datum_str, '%Y-%m-%d').date()
                except ValueError:
                    return JsonResponse({'success': False, 'message': 'Neplatný formát data.'})
            else:
                datum = datetime.now().date()

            # Get Uzivatele instance
            try:
                uzivatel = request.user.uzivatele
            except AttributeError:
                return JsonResponse({'success': False, 'message': 'Uživatelský profil nenalezen.'})

            created_reservations = []

            for res in reservations:
                court_id = int(res['court'])
                hour = res['hour']  # e.g., "08:00"

                # Get Hriste instance
                try:
                    hriste = Hriste.objects.get(id=court_id, aktivni=True)
                except Hriste.DoesNotExist:
                    return JsonResponse({'success': False, 'message': f'Hřiště {court_id} neexistuje.'})

                # Parse start time
                try:
                    cas_zacatku = datetime.strptime(hour, '%H:%M').time()
                except ValueError:
                    return JsonResponse({'success': False, 'message': f'Neplatný čas: {hour}.'})

                # Calculate end time (1-hour slot)
                cas_zacatku_dt = datetime.combine(datum, cas_zacatku)
                cas_konce_dt = cas_zacatku_dt + timedelta(hours=1)
                cas_konce = cas_konce_dt.time()

                # Check for overlapping reservations
                if Rezervace.objects.filter(
                    hriste=hriste,
                    datum=datum,
                    cas_zacatku__lte=cas_konce,
                    cas_konce__gte=cas_zacatku
                ).exists():
                    return JsonResponse({
                        'success': False,
                        'message': f'Hřiště {hriste.nazev} v čase {hour} je již obsazeno.'
                    })

                # Calculate price
                base_price = float(hriste.cena_hodina)

                # Apply seasonal price increase (SezoniCena)
                seasonal_increase = 0
                seasonal_price = SezoniCena.objects.filter(
                    mesic_start__lte=datum,
                    mesic_konec__gte=datum
                ).first()
                if seasonal_price:
                    seasonal_increase = seasonal_price.naviseni_ceny

                # Apply daily price increase (DenniCena)
                daily_increase = 0
                daily_price = DenniCena.objects.filter(
                    hodina_start__lte=cas_zacatku_dt,
                    hodina_konec__gte=cas_zacatku_dt
                ).first()
                if daily_price:
                    daily_increase = daily_price.naviseni_ceny

                # Apply user discount (TypZakaznika)
                user_discount = 0
                if uzivatel.typ_zakaznika:  # Check if typ_zakaznika is not None
                    user_discount = uzivatel.typ_zakaznika.sleva

                # Validate percentages to prevent negative or excessive prices
                seasonal_increase = min(max(seasonal_increase, 0), 100)
                daily_increase = min(max(daily_increase, 0), 100)
                user_discount = min(max(user_discount, 0), 100)

                # Calculate final price
                # First, apply seasonal and daily increases
                price_with_increases = base_price * (1 + (seasonal_increase + daily_increase) / 100)
                # Then, apply user discount
                final_price = price_with_increases * (1 - user_discount / 100)

                # Create reservation
                rezervace = Rezervace(
                    uzivatel=uzivatel,
                    hriste=hriste,
                    datum=datum,
                    cas_zacatku=cas_zacatku,
                    cas_konce=cas_konce,
                    stav='nova',
                    popis='',
                    cena=final_price,
                    vytvoreno=timezone.now(),
                )
                created_reservations.append(rezervace)

            # Email message construction
            textmassage = f"Dobrý den {uzivatel.jmeno},\n\n"
            for res, rezervace in zip(reservations, created_reservations):
                hour = res['hour']
                cas_zacatku = datetime.strptime(hour, '%H:%M').time()
                cas_zacatku_dt = datetime.combine(datum, cas_zacatku)
                cas_konce_dt = cas_zacatku_dt + timedelta(hours=1)
                cas_konce = cas_konce_dt.time()
                textmassage += (
                    f"Vaše rezervace na {rezervace.hriste} dne {datum.strftime('%d.%m.%Y')} "
                    f"od {cas_zacatku} do {cas_konce} byla úspěšně vytvořena. Cena: {rezervace.cena:.2f} Kč\n"
                )

            # Try to send email
            try:
                send_mail(
                    subject="Vaše rezervace byly vytvořeny",
                    message=textmassage,
                    from_email=None,
                    recipient_list=[uzivatel.email],
                    fail_silently=True,
                )
            except Exception as email_error:
                print(f"Email sending error: {str(email_error)}")

            # Save reservations
            for rezervace in created_reservations:
                rezervace.save()

            # Return the first reservation's ID
            first_reservation_id = created_reservations[0].id if created_reservations else None
            
            return JsonResponse({
                'success': True,
                'message': 'Rezervace úspěšně vytvořeny.',
                'reservation_id': first_reservation_id
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Chyba: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Neplatná metoda požadavku.'})


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

        # Try to send email but don't fail the whole cancellation process if email sending fails
        try:
            send_mail(
                subject="Vaše rezervace byla zrušena",
                message=f"Dobrý den {uzivatel.jmeno},\n\nVaše rezervace na {hriste} dne {datum.strftime('%d.%m.%Y')} byla úspěšně zrušena.",
                from_email=None,  # použije DEFAULT_FROM_EMAIL
                recipient_list=[uzivatel.email],
                fail_silently=True,  # Set to True to prevent raising exceptions
            )
        except Exception as email_error:
            # Log the error but continue with the cancellation process
            print(f"Email sending error: {str(email_error)}")
            # You might want to log this to a file or monitoring system in production
            
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
        try:
            send_mail(
                subject="Vaše zápůjčka byla zrušena",
                message=(
                    f"Dobrý den {uzivatel.jmeno},\n\n"
                    f"Vaše zápůjčka předmětu \"{predmet}\" (množství: {mnozstvi}) "
                    f"k rezervaci hřiště {hriste} dne {datum.strftime('%d.%m.%Y')} byla úspěšně zrušena."
                ),
                from_email=None,  # použije DEFAULT_FROM_EMAIL
                recipient_list=[uzivatel.email],
                fail_silently=True,  # Set to True to prevent raising exceptions
            )
        except Exception as email_error:
            # Log the error but continue with the cancellation process
            print(f"Email sending error: {str(email_error)}")
            # You might want to log this to a file or monitoring system in production

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


@login_required
def zapujcky_k_rezervaci(request, rez_id):
    rezervace = get_object_or_404(Rezervace, id=rez_id, uzivatel=request.user.uzivatele)
    predmety = Zapujcky.objects.filter(aktivni=True)
    pujcovna = predmety.filter(typ__in=['pujcka', 'oboji'])
    prodej = predmety.filter(typ__in=['prodej', 'oboji'])

    session_cart = request.session.get('zapujcky_cart', {})
    cart = session_cart.get(str(rez_id), [])

    if request.method == 'POST':
        if 'rezervovat' in request.POST:
            for polozka in cart:
                zapujcka = get_object_or_404(Zapujcky, id=polozka['predmet_id'])
                cena = zapujcka.cena_pujceni if zapujcka.typ != 'prodej' else zapujcka.cena_prodeje

                # Zkontroluj, jestli záznam už existuje
                existing = RezervaceZapujcky.objects.filter(rezervace=rezervace, zapujcka=zapujcka).first()
                if existing:
                    existing.mnozstvi += polozka['mnozstvi']
                    existing.save()
                else:
                    RezervaceZapujcky.objects.create(
                        rezervace=rezervace,
                        zapujcka=zapujcka,
                        mnozstvi=polozka['mnozstvi'],
                        cena_za_kus=cena
                    )

            # Vyčištění košíku
            session_cart[str(rez_id)] = []
            request.session['zapujcky_cart'] = session_cart

            return redirect('rezervace')

        elif 'odebrat' in request.POST:
            odebrat_id = int(request.POST.get('odebrat'))
            cart = [item for item in cart if item['predmet_id'] != odebrat_id]
            session_cart[str(rez_id)] = cart
            request.session['zapujcky_cart'] = session_cart
            return redirect('zapujcky_k_rezervaci', rez_id=rez_id)

        else:
            predmet_id = int(request.POST.get('predmet'))
            mnozstvi = int(request.POST.get('mnozstvi', 1))

            if str(rez_id) not in session_cart:
                session_cart[str(rez_id)] = []

            found = False
            for item in session_cart[str(rez_id)]:
                if item['predmet_id'] == predmet_id:
                    item['mnozstvi'] += mnozstvi
                    found = True
                    break

            if not found:
                session_cart[str(rez_id)].append({
                    'predmet_id': predmet_id,
                    'mnozstvi': mnozstvi
                })

            request.session['zapujcky_cart'] = session_cart
            return redirect('zapujcky_k_rezervaci', rez_id=rez_id)

    # Kontext pro šablonu
    cart_items = []
    for polozka in cart:
        zapujcka = get_object_or_404(Zapujcky, id=polozka['predmet_id'])
        cart_items.append({
            'id': zapujcka.id,
            'nazev': zapujcka.nazev,
            'mnozstvi': polozka['mnozstvi'],
            'typ': zapujcka.typ,
            'cena': zapujcka.cena_pujceni if zapujcka.typ != 'prodej' else zapujcka.cena_prodeje
        })

    return render(request, 'rezervace/zapujcky_k_rezervaci.html', {
        'rezervace': rezervace,
        'predmety': predmety,
        'cenik_zapujcek': pujcovna,
        'cenik_prodeje': prodej,
        'cart_items': cart_items
    })



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

def novinky(request):
    news = Novinky.objects.all().order_by('-vytvoreno')
    return render(request, 'rezervace/novinky.html', {'news': news})

def is_admin(user):
    """Helper function to check if user is an admin"""
    try:
        return user.is_authenticated and (user.is_staff or user.is_superuser)
    except:
        return False

@login_required
def hriste_management(request):
    """View to list all sports facilities for admin management"""
    # Check if user is admin
    if not is_admin(request.user):
        messages.error(request, "Tato stránka je přístupná pouze pro administrátory.")
        return redirect('profile')
    
    # Get all sports facilities
    hriste_list = Hriste.objects.all().order_by('nazev')
    
    return render(request, 'rezervace/hriste_management.html', {
        'hriste_list': hriste_list
    })

@login_required
def hriste_create(request):
    """View to create a new sports facility"""
    # Check if user is admin
    if not is_admin(request.user):
        messages.error(request, "Tato funkce je přístupná pouze pro administrátory.")
        return redirect('profile')
    
    if request.method == 'POST':
        form = HristeForm(request.POST)
        if form.is_valid():
            hriste = form.save()
            messages.success(request, f"Sportoviště {hriste.nazev} bylo úspěšně vytvořeno.")
            return redirect('hriste_management')
    else:
        form = HristeForm()
    
    return render(request, 'rezervace/hriste_form.html', {
        'form': form
    })

@login_required
def hriste_update(request, pk):
    """View to update an existing sports facility"""
    # Check if user is admin
    if not is_admin(request.user):
        messages.error(request, "Tato funkce je přístupná pouze pro administrátory.")
        return redirect('profile')
    
    hriste = get_object_or_404(Hriste, pk=pk)
    
    if request.method == 'POST':
        form = HristeForm(request.POST, instance=hriste)
        if form.is_valid():
            hriste = form.save()
            messages.success(request, f"Sportoviště {hriste.nazev} bylo úspěšně aktualizováno.")
            return redirect('hriste_management')
    else:
        form = HristeForm(instance=hriste)
    
    return render(request, 'rezervace/hriste_form.html', {
        'form': form,
        'hriste': hriste
    })

@login_required
def hriste_detail(request, pk):
    """View to show detailed information about a sports facility"""
    # Check if user is admin
    if not is_admin(request.user):
        messages.error(request, "Tato stránka je přístupná pouze pro administrátory.")
        return redirect('profile')
    
    hriste = get_object_or_404(Hriste, pk=pk)
    
    return render(request, 'rezervace/hriste_detail.html', {
        'hriste': hriste
    })

@login_required
def hriste_delete(request, pk):
    """View to delete a sports facility"""
    # Check if user is admin
    if not is_admin(request.user):
        messages.error(request, "Tato funkce je přístupná pouze pro administrátory.")
        return redirect('profile')
    
    hriste = get_object_or_404(Hriste, pk=pk)
    
    if request.method == 'POST':
        nazev = hriste.nazev
        hriste.delete()
        messages.success(request, f"Sportoviště {nazev} bylo úspěšně smazáno.")
        return redirect('hriste_management')
    
    return render(request, 'rezervace/hriste_delete.html', {
        'hriste': hriste
    })

@login_required
def hriste_public_list(request):
    """View to show a list of active sports facilities for all users"""
    # Get active sports facilities
    hriste_list = Hriste.objects.filter(aktivni=True)
    
    # Apply filtering if set
    typ = request.GET.get('typ', '')
    if typ:
        hriste_list = hriste_list.filter(typ=typ)
    
    # Order by name
    hriste_list = hriste_list.order_by('nazev')
    
    # Get all court types for filter dropdown
    hriste_typy = Hriste.objects.filter(aktivni=True).values_list('typ', flat=True).distinct()
    
    return render(request, 'rezervace/hriste_public_list.html', {
        'hriste_list': hriste_list,
        'hriste_typy': hriste_typy
    })

@login_required
def rezervace_detail(request, rez_id):
    """View to show detailed information about a reservation"""
    # Check if the user has access to this reservation (is owner or admin)
    try:
        rezervace = Rezervace.objects.get(id=rez_id)
        if rezervace.uzivatel.user != request.user and not is_admin(request.user):
            messages.error(request, "Nemáte oprávnění zobrazit tuto rezervaci.")
            return redirect('rezervace')
            
        zapujcky = RezervaceZapujcky.objects.filter(rezervace=rezervace)
        
        return render(request, 'rezervace/rezervace_detail.html', {
            'rezervace': rezervace,
            'zapujcky': zapujcky
        })
    except Rezervace.DoesNotExist:
        messages.error(request, "Požadovaná rezervace neexistuje.")
        return redirect('rezervace')

@login_required
def rezervace_update(request, rez_id):
    """View to update an existing reservation"""
    try:
        # Get the reservation 
        if is_admin(request.user):
            rezervace = get_object_or_404(Rezervace, id=rez_id)
        else:
            rezervace = get_object_or_404(Rezervace, id=rez_id, uzivatel__user=request.user)
        
        # Check if reservation is in the future and more than 24 hours away
        now = timezone.now()
        rezervace_datetime = datetime.combine(rezervace.datum, rezervace.cas_zacatku)
        rezervace_datetime = timezone.make_aware(rezervace_datetime)
        
        # For regular users, enforce the 1-day rule
        if not is_admin(request.user) and (rezervace_datetime - now) < timedelta(days=1):
            messages.error(request, "Rezervaci lze upravit pouze více než 24 hodin před jejím začátkem.")
            return redirect('rezervace_detail', rez_id=rez_id)
            
        # Process form submission
        if request.method == 'POST':
            # Validate form data
            try:
                datum_str = request.POST.get('datum')
                cas_zacatku_str = request.POST.get('cas_zacatku')
                cas_konce_str = request.POST.get('cas_konce')
                
                # Parse the date and times
                datum = datetime.strptime(datum_str, '%Y-%m-%d').date()
                cas_zacatku = datetime.strptime(cas_zacatku_str, '%H:%M').time()
                cas_konce = datetime.strptime(cas_konce_str, '%H:%M').time()
                
                # Update reservation
                rezervace.datum = datum
                rezervace.cas_zacatku = cas_zacatku
                rezervace.cas_konce = cas_konce
                
                # Update description
                if 'popis' in request.POST:
                    rezervace.popis = request.POST.get('popis')
                
                # Update court if user is staff
                if is_admin(request.user) and 'hriste' in request.POST:
                    hriste_id = request.POST.get('hriste')
                    try:
                        hriste = Hriste.objects.get(id=hriste_id, aktivni=True)
                        rezervace.hriste = hriste
                    except Hriste.DoesNotExist:
                        messages.error(request, "Vybrané hřiště neexistuje nebo není aktivní.")
                        dostupna_hriste = Hriste.objects.filter(aktivni=True)
                        return render(request, 'rezervace/rezervace_update.html', {
                            'rezervace': rezervace,
                            'dostupna_hriste': dostupna_hriste
                        })
                
                # Update status if user is staff
                if is_admin(request.user) and 'stav' in request.POST:
                    stav = request.POST.get('stav')
                    if stav in ['nova', 'potvrzena', 'zrusena']:
                        rezervace.stav = stav
                
                # Check for conflicts (skip the current reservation when checking)
                conflicts = Rezervace.objects.filter(
                    hriste=rezervace.hriste,
                    datum=datum,
                    cas_zacatku__lt=cas_konce,
                    cas_konce__gt=cas_zacatku
                ).exclude(id=rez_id)
                
                if conflicts.exists():
                    messages.error(request, "Vybraný termín koliduje s jinou rezervací.")
                    dostupna_hriste = Hriste.objects.filter(aktivni=True)
                    return render(request, 'rezervace/rezervace_update.html', {
                        'rezervace': rezervace,
                        'dostupna_hriste': dostupna_hriste
                    })
                
                # Save changes
                rezervace.save()
                
                # Try to send email notification
                try:
                    send_mail(
                        subject="Vaše rezervace byla upravena",
                        message=f"Dobrý den {rezervace.uzivatel.jmeno},\n\nVaše rezervace na {rezervace.hriste.nazev} byla upravena na {datum.strftime('%d.%m.%Y')} od {cas_zacatku} do {cas_konce}.",
                        from_email=None,
                        recipient_list=[rezervace.uzivatel.email],
                        fail_silently=True,
                    )
                except Exception as email_error:
                    print(f"Email sending error: {str(email_error)}")
                
                messages.success(request, "Rezervace byla úspěšně upravena.")
                return redirect('rezervace_detail', rez_id=rez_id)
                
            except ValueError:
                messages.error(request, "Neplatný formát data nebo času.")
                dostupna_hriste = Hriste.objects.filter(aktivni=True)
                return render(request, 'rezervace/rezervace_update.html', {
                    'rezervace': rezervace,
                    'dostupna_hriste': dostupna_hriste
                })
        
        # Display form
        dostupna_hriste = Hriste.objects.filter(aktivni=True)
        return render(request, 'rezervace/rezervace_update.html', {
            'rezervace': rezervace,
            'dostupna_hriste': dostupna_hriste
        })
        
    except Rezervace.DoesNotExist:
        messages.error(request, "Požadovaná rezervace neexistuje.")
        return redirect('rezervace')

@login_required
def admin_reservations(request):
    """View for administrators to manage all reservations"""
    # Check if user is admin
    if not is_admin(request.user):
        messages.error(request, "Tato stránka je přístupná pouze pro administrátory.")
        return redirect('profile')
    
    # Get all reservations ordered by date, newest first
    reservations = Rezervace.objects.all().order_by('-datum', '-cas_zacatku')
    
    # Filter by date, user or court if provided
    datum = request.GET.get('datum')
    user_id = request.GET.get('user_id')
    hriste_id = request.GET.get('hriste_id')
    
    if datum:
        reservations = reservations.filter(datum=datum)
    if user_id:
        reservations = reservations.filter(uzivatel__id=user_id)
    if hriste_id:
        reservations = reservations.filter(hriste__id=hriste_id)
    
    # Get all users and courts for filter dropdowns
    users = Uzivatele.objects.all().order_by('prijmeni', 'jmeno')
    courts = Hriste.objects.all().order_by('nazev')
    
    return render(request, 'rezervace/admin_reservations.html', {
        'reservations': reservations,
        'users': users,
        'courts': courts,
        'vybrane_datum': datum if datum else '',
        'vybrany_user': int(user_id) if user_id else None,
        'vybrane_hriste': int(hriste_id) if hriste_id else None
    })
