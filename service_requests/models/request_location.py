from django.db import models

class RequestLocation(models.Model):
    id_request_location = models.AutoField(primary_key=True)
    request = models.OneToOneField('service_requests.ServiceRequest', on_delete=models.PROTECT, null=False, blank=False, related_name='request_location')
    country = models.CharField(max_length=50, null=False, blank=False)
    department = models.CharField(max_length=50, null=False, blank=False)
    city_id = models.IntegerField(null=False, blank=False)
    place_name = models.CharField(max_length=255, null=False, blank=False)
    latitude = models.FloatField(null=False, blank=False)
    longitude = models.FloatField(null=False, blank=False)
    area = models.FloatField(null=False, blank=False)
    area_unit = models.ForeignKey('parameterization.Units', on_delete=models.PROTECT, null=False, blank=False, related_name='area_locations')
    soil_type = models.ForeignKey('parameterization.Types', on_delete=models.PROTECT, null=False, blank=False, related_name='soil_type_locations')
    humidity_level = models.FloatField(null=False, blank=False)
    altitude = models.FloatField(null=False, blank=False)
    altitude_unit = models.ForeignKey('parameterization.Units', on_delete=models.PROTECT, null=False, blank=False, related_name='altitude_locations')

    class Meta:
        db_table = 'request_locations'
