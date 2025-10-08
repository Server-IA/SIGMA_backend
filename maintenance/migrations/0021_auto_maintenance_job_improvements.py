# Generated manually for HU-SM-002 compliance

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0020_remove_maintenancereport_creation_date'),
        ('machinery', '0016_merge_20251004_0033'),
    ]

    operations = [
        migrations.AlterField(
            model_name='maintenancerequest',
            name='detected_at',
            field=models.DateTimeField(db_column='detected_at'),
        ),
        migrations.AddField(
            model_name='maintenancerequest',
            name='is_automatic',
            field=models.BooleanField(default=False, db_column='is_automatic', help_text='Indica si la solicitud fue generada automáticamente'),
        ),
        migrations.CreateModel(
            name='SensorReadingIncident',
            fields=[
                ('id_sensor_incident', models.AutoField(primary_key=True, serialize=False)),
                ('incident_type', models.CharField(db_column='incident_type', help_text='Tipo de incidente: sensor_error, telemetry_error, data_validation_error, etc.', max_length=50)),
                ('description', models.TextField(db_column='description', help_text='Descripción detallada del error o incidente')),
                ('error_details', models.TextField(blank=True, db_column='error_details', help_text='Detalles técnicos del error (stack trace, código de error, etc.)', null=True)),
                ('notified', models.BooleanField(db_column='notified', default=False, help_text='Indica si se notificó al jefe de mantenimiento')),
                ('notification_date', models.DateTimeField(blank=True, db_column='notification_date', help_text='Fecha y hora en que se envió la notificación', null=True)),
                ('detected_at', models.DateTimeField(auto_now_add=True, db_column='detected_at', help_text='Fecha y hora de detección del incidente')),
                ('registration_date', models.DateTimeField(auto_now_add=True, db_column='registration_date')),
                ('modification_date', models.DateTimeField(auto_now=True, db_column='modification_date')),
                ('id_machinery', models.ForeignKey(db_column='id_machinery', on_delete=django.db.models.deletion.PROTECT, related_name='sensor_incidents', to='machinery.machinery')),
            ],
            options={
                'db_table': 'sensor_reading_incident',
                'ordering': ['-detected_at'],
            },
        ),
        migrations.AddIndex(
            model_name='sensorreadingincident',
            index=models.Index(fields=['id_machinery', '-detected_at'], name='sensor_read_id_mach_idx'),
        ),
        migrations.AddIndex(
            model_name='sensorreadingincident',
            index=models.Index(fields=['notified', '-detected_at'], name='sensor_read_notifie_idx'),
        ),
    ]
