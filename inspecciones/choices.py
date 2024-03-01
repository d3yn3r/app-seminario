# choices.py
from django.db import models

class Caracteristicas(models.TextChoices):
    OPCION_1 = 'opcion_1', 'Opción 1'
    OPCION_2 = 'opcion_2', 'Opción 2'
    OPCION_3 = 'opcion_3', 'Opción 3'
