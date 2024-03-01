from django import forms
from django.contrib.auth.models import User
from django_registration.forms import RegistrationForm

from inspecciones.models import Perfil


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['celular', 'foto']


class UserForm(RegistrationForm):
    nombre = forms.CharField(label="Nombre")
    apellido = forms.CharField(label="Apellido")


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'is_active']


class PerfilEditForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['celular', 'foto', 'rol']

