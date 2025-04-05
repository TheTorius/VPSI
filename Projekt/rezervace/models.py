from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone  # Add this import

# Create your models here.

# Enum choices for Role
ROLE_CHOICES = (
    ('user', 'User'),
    ('admin', 'Admin'),
)

# Enum choices for Customer Type
CUSTOMER_TYPE_CHOICES = (
    ('new', 'New'),
    ('long_term', 'Long Term'),
    ('vip', 'VIP'),
)

# Enum choices for Reservation Status
RESERVATION_STATUS_CHOICES = (
    ('nova', 'Nova'),
    ('potvrzena', 'Potvrzena'),
    ('zrusena', 'Zrušena'),
)

# Enum choices for Rental Type
RENTAL_TYPE_CHOICES = (
    ('pujcka', 'Půjčka'),
    ('prodej', 'Prodej'),
    ('oboji', 'Obojí'),
)

class TypZakaznika(models.Model):
    typ_zakaznika = models.CharField(
        max_length=20,
        choices=CUSTOMER_TYPE_CHOICES,
        primary_key=True,
        unique=True
    )
    sleva = models.IntegerField()  # Discount percentage

    def __str__(self):
        return self.typ_zakaznika

class Uzivatele(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='uzivatele')
    jmeno = models.CharField(max_length=50)
    prijmeni = models.CharField(max_length=50)
    email = models.EmailField(max_length=100, unique=True)
    telefon = models.CharField(max_length=20)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    datum_reg = models.DateTimeField(default=timezone.now)
    posledni_aktualizace = models.DateTimeField(auto_now=True)
    typ_zakaznika = models.ForeignKey(TypZakaznika, on_delete=models.SET_NULL, null=True, related_name='uzivatele')

    def __str__(self):
        return f"{self.jmeno} {self.prijmeni} {self.email} {self.telefon}"

class Hriste(models.Model):
    nazev = models.CharField(max_length=100)
    typ = models.CharField(max_length=50)
    popis = models.TextField()
    cena_hodina = models.DecimalField(max_digits=8, decimal_places=2)
    kapacita = models.IntegerField()
    aktivni = models.BooleanField(default=True)

    def __str__(self):
        return self.nazev

class Rezervace(models.Model):
    uzivatel = models.ForeignKey(Uzivatele, on_delete=models.CASCADE, related_name='rezervace')
    hriste = models.ForeignKey(Hriste, on_delete=models.CASCADE, related_name='rezervace')
    datum = models.DateField()
    cas_zacatku = models.TimeField()
    cas_konce = models.TimeField()
    stav = models.CharField(max_length=20, choices=RESERVATION_STATUS_CHOICES, default='nova')
    popis = models.TextField(blank=True, null=True)
    vytvoreno = models.DateTimeField(default=timezone.now)
    naposledy_upraveno = models.DateTimeField(auto_now=True)
    cena = models.FloatField()

    def __str__(self):
        return f"Rezervace {self.hriste.nazev} - {self.datum} ({self.uzivatel})"

class SezoniCena(models.Model):
    mesic_start = models.DateField()
    mesic_konec = models.DateField()
    naviseni_ceny = models.IntegerField()  # Price increase percentage

    def __str__(self):
        return f"Sezóní cena: {self.mesic_start} - {self.mesic_konec}"

class DenniCena(models.Model):
    hodina_start = models.DateField()
    hodina_konec = models.DateField()
    naviseni_ceny = models.IntegerField()  # Price increase percentage

    def __str__(self):
        return f"Denní cena: {self.hodina_start} - {self.hodina_konec}"

class Zapujcky(models.Model):
    nazev = models.CharField(max_length=100)
    popis = models.TextField()
    cena_pujceni = models.DecimalField(max_digits=8, decimal_places=2)
    cena_prodeje = models.DecimalField(max_digits=8, decimal_places=2)
    typ = models.CharField(max_length=20, choices=RENTAL_TYPE_CHOICES)
    aktivni = models.BooleanField(default=True)

    def __str__(self):
        return self.nazev

class RezervaceZapujcky(models.Model):
    rezervace = models.ForeignKey(Rezervace, on_delete=models.CASCADE, related_name='zapujcky')
    zapujcka = models.ForeignKey(Zapujcky, on_delete=models.CASCADE, related_name='rezervace')
    mnozstvi = models.IntegerField()
    cena_za_kus = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        unique_together = ('rezervace', 'zapujcka')  # Composite primary key

    def __str__(self):
        return f"{self.zapujcka.nazev} (x{self.mnozstvi}) - Rezervace {self.rezervace.id}"

class Novinky(models.Model):
    titulek = models.CharField(max_length=255)
    text = models.TextField()
    vytvoreno = models.DateTimeField(default=timezone.now)
    zverejneno = models.BooleanField(default=False)
    autor = models.ForeignKey(Uzivatele, on_delete=models.CASCADE, related_name='novinky')

    def __str__(self):
        return self.titulek