from django.db import models

class VisualParameterization(models.Model):
    id_visual_parameterization = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    background_color = models.CharField(max_length=255, null=True, blank=True)
    text_color = models.CharField(max_length=255, null=True, blank=True)
    font = models.CharField(max_length=255, null=True, blank=True)
    font_size = models.CharField(max_length=255, null=True, blank=True)
    border_thickness = models.CharField(max_length=255, null=True, blank=True)
    border_color = models.CharField(max_length=255, null=True, blank=True)
    visual_parameterization_status = models.ForeignKey('parameterization.Statues', on_delete=models.PROTECT)
    modification_date = models.DateTimeField(null=True, blank=True)
    creation_date = models.DateTimeField()
    id_responsible_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=True)

    class Meta:
        db_table = 'visual_parameterization'
