from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('maintenance', '0013_maintenancemaintenancereports_maintenance_cost'),
        ('parameterization', '0013_remove_units_description_units_id_types_units_symbol_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='MaintenanceReportSpareParts',
            fields=[
                ('id_maintenance_report_spare_part', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(db_column='name', max_length=255)),
                ('spare_parts_cost', models.FloatField(db_column='spare_parts_cost')),
                ('quantity_used', models.IntegerField(db_column='quantity_used', default=1)),
                ('cost_at_time', models.FloatField(db_column='cost_at_time')),
                ('registration_date', models.DateTimeField(auto_now=True, db_column='registration_date')),
                ('modification_date', models.DateTimeField(auto_now=True, db_column='modification_date')),
                ('id_maintenance_report', models.ForeignKey(db_column='id_maintenance_report', on_delete=django.db.models.deletion.CASCADE, related_name='spare_parts_used', to='maintenance.maintenancereport')),
                ('spare_part_brand', models.ForeignKey(db_column='spare_part_brand', on_delete=django.db.models.deletion.PROTECT, related_name='maintenance_report_spare_parts_by_brand', to='parameterization.brands')),
            ],
            options={
                'db_table': 'maintenance_report_spare_parts',
            },
        ),
    ]