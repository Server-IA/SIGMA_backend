from django.db import models

class PersonType(models.Model):
    id_person_type = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'person_type'