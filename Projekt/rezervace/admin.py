from django.contrib import admin
from .models import Uzivatele, TypZakaznika, Hriste, Rezervace, SezoniCena, DenniCena, Zapujcky, RezervaceZapujcky, Novinky

admin.site.register(Uzivatele)
admin.site.register(TypZakaznika)
admin.site.register(Hriste)
admin.site.register(Rezervace)
admin.site.register(SezoniCena)
admin.site.register(DenniCena)
admin.site.register(Zapujcky)
admin.site.register(RezervaceZapujcky)
admin.site.register(Novinky)
# Register your models here.
