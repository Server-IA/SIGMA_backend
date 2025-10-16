from django.db import models

class RequestMachineryUser(models.Model):
    id_request_machinery_user = models.AutoField(primary_key=True)
    request = models.ForeignKey('service_requests.ServiceRequest', on_delete=models.PROTECT, related_name='machinery_users')
    machinery = models.ForeignKey('machinery.Machinery', on_delete=models.PROTECT, related_name='request_assignments')
    user = models.ForeignKey('users.User', on_delete=models.PROTECT, related_name='request_assignments')

    class Meta:
        db_table = 'request_machinery_users'
        unique_together = ('request', 'machinery', 'user')