# Generated by Django 5.0.1 on 2024-03-30 10:18

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_rename_profilepicurl_user_profilepic_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ParkSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True, editable=False)),
                ('status', models.CharField(choices=[('Available', 'Available'), ('Booked', 'Booked'), ('Reserved', 'Reserved')], default='available', max_length=32)),
                ('price', models.FloatField()),
                ('address', models.CharField(max_length=255)),
                ('coordinates', models.CharField(blank=True, max_length=64, null=True)),
                ('description', models.TextField()),
                ('type', models.CharField(choices=[('Bike', 'Bike'), ('Car', 'Car'), ('Van', 'Van'), ('Bus', 'Bus'), ('Truck', 'Truck')], max_length=255)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='slot_owner', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
