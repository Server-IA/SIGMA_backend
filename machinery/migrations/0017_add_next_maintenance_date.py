# Generated manually for HU-SM-002 compliance

from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ('machinery', '0016_merge_20251004_0033'),
    ]

    operations = [
        migrations.AddField(
            model_name='periodicmaintenancescheduling',
            name='next_maintenance_date',
            field=models.DateField(blank=True, db_column='next_maintenance_date', help_text='Fecha programada para el próximo mantenimiento preventivo', null=True),
        ),
        # Update constraint to allow date-based maintenance
        migrations.RemoveConstraint(
            model_name='periodicmaintenancescheduling',
            name='pm_exactly_one_trigger',
        ),
        migrations.AddConstraint(
            model_name='periodicmaintenancescheduling',
            constraint=models.CheckConstraint(
                name='pm_at_least_one_trigger',
                check=(
                    Q(usage_hours__isnull=False) |
                    Q(distance_km__isnull=False) |
                    Q(next_maintenance_date__isnull=False)
                ),
            ),
        ),
        migrations.AddConstraint(
            model_name='periodicmaintenancescheduling',
            constraint=models.UniqueConstraint(
                fields=['machinery', 'maintenance', 'next_maintenance_date'],
                name='uniq_pm_by_mach_maint_date',
                condition=Q(next_maintenance_date__isnull=False),
            ),
        ),
    ]
