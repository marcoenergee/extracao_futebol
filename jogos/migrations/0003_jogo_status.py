# Generated by Django 5.1.5 on 2025-01-28 00:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jogos', '0002_campeonato_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='jogo',
            name='status',
            field=models.BooleanField(default=True),
        ),
    ]
