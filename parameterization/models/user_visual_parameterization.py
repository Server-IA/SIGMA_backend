from django.db import models

class UserVisualParameterization(models.Model):
    id_user_visual_parameterization = models.AutoField(primary_key=True)
    id_user = models.ForeignKey('users.User', on_delete=models.PROTECT, related_name='user_visual_parameterizations')
    id_visual_parameterization = models.ForeignKey('parameterization.VisualParameterization', on_delete=models.PROTECT, related_name='user_assignments')
    user_visual_parameterization_status = models.ForeignKey('parameterization.Statues', on_delete=models.PROTECT, related_name='user_visual_parameterization_statuses')
    registration_date = models.DateTimeField()
    modification_date = models.DateTimeField(null=True, blank=True)
    id_responsible_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=True, related_name='responsible_user_visual_parameterizations')

    class Meta:
        db_table = 'user_visual_parameterization'
