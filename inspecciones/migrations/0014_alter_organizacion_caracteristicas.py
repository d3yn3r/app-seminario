# Generated by Django 5.0.6 on 2024-05-13 01:04

import inspecciones.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inspecciones', '0013_alter_organizacion_caracteristicas'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organizacion',
            name='caracteristicas',
            field=inspecciones.models.MultiSelectField(blank=True, choices=[('reparaciones', 'Reparaciones'), ('planeacion', 'Planeacion')], max_length=1000),
        ),
    ]