from django.db import models

class Texture(models.Model):
    id = models.AutoField(primary_key=True)
    texture = models.CharField(max_length=50, null=False, blank=False)
    value = models.FloatField(null=True, blank=True)

    class Meta:

        db_table = 'textures'
