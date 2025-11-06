from django.db import models

class RequestMachineryUser(models.Model):
    id_request_machinery_user = models.AutoField(primary_key=True)
    request = models.ForeignKey('service_requests.ServiceRequest', on_delete=models.PROTECT, related_name='machinery_users')
    machinery = models.ForeignKey('machinery.Machinery', on_delete=models.PROTECT, related_name='request_assignments')
    user = models.ForeignKey('users.User', on_delete=models.PROTECT, related_name='request_assignments')
    soil_type = models.ForeignKey('service_requests.SoilType', on_delete=models.PROTECT, null=True, blank=True, related_name='soil_type')
    texture = models.ForeignKey('service_requests.Texture', on_delete=models.PROTECT, null=True, blank=True, related_name='machinery_texture_assignments')
    humidity_level = models.FloatField(null=True, blank=True)
    implementation = models.ForeignKey('service_requests.Implementation', on_delete=models.PROTECT, null=True, blank=True, related_name='machinery_implementation')
    implement_width = models.FloatField(null=True, blank=True, verbose_name='implement_width')
    depth = models.FloatField(null=True, blank=True, verbose_name='depth')
    slope = models.FloatField(null=True, blank=True, verbose_name='slope')
    work_duration = models.FloatField(null=True, blank=True, verbose_name='work_duration')

    class Meta:
        db_table = 'request_machinery_users'
        unique_together = ('request', 'machinery')