from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import Uzivatele, TypZakaznika

class RegistrationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    password = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class SignUpForm(forms.ModelForm):
    # Remove the duplicated fields (first_name, last_name, phone) since they're already in Meta.fields
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    password = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

    class Meta:
        model = Uzivatele
        fields = ['jmeno', 'prijmeni', 'email', 'telefon']
        widgets = {
            'jmeno': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Jméno'}),
            'prijmeni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Příjmení'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'telefon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telefon (e.g., +420123456789)'}),
        }
        labels = {
            'jmeno': 'Jméno',
            'prijmeni': 'Příjmení',
            'email': 'Email',
            'telefon': 'Telefon',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Uzivatele.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('telefon')  # Use 'telefon' since 'phone' is no longer a field
        if len(phone) < 5:  # Relaxed validation for now
            raise ValidationError("Phone number must be at least 5 characters long.")
        return phone