from django.db import models

class DaysOfWeek(models.Model):
    id_day_of_week = models.AutoField(primary_key=True, db_column="id_day_of_week")
    name = models.CharField(max_length=255, null=True, blank=True, db_column="name")

    class Meta:
        db_table = "days_of_week"

