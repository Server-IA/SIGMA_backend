from django.db import models

class VisualParameterization(models.Model):
    id_visual_parameterization = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    
    # Colores del sistema de diseño
    primary_color = models.CharField(max_length=255, null=True, blank=True)
    secondary_color = models.CharField(max_length=255, null=True, blank=True)
    accent_color = models.CharField(max_length=255, null=True, blank=True)
    background_color = models.CharField(max_length=255, null=True, blank=True)
    surface_color = models.CharField(max_length=255, null=True, blank=True)
    text_color = models.CharField(max_length=255, null=True, blank=True)
    text_secondary_color = models.CharField(max_length=255, null=True, blank=True)
    border_color = models.CharField(max_length=255, null=True, blank=True)
    hover_color = models.CharField(max_length=255, null=True, blank=True)
    error_color = models.CharField(max_length=255, null=True, blank=True)
    success_color = models.CharField(max_length=255, null=True, blank=True)
    warning_color = models.CharField(max_length=255, null=True, blank=True)
    
    # Tipografía
    font = models.CharField(max_length=255, null=True, blank=True)
    title_size = models.CharField(max_length=10, null=True, blank=True)  # xs, sm, base, lg, xl, 2xl, 3xl
    paragraph_size = models.CharField(max_length=10, null=True, blank=True)  # xs, sm, base, lg, xl, 2xl, 3xl
    
    visual_parameterization_status = models.ForeignKey('parameterization.Statues', on_delete=models.PROTECT)
    modification_date = models.DateTimeField(null=True, blank=True)
    creation_date = models.DateTimeField()
    id_responsible_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=True)

    class Meta:
        db_table = 'visual_parameterization'
