from django.db import models

class MachineryDocumentation(models.Model):
    id_machinery_documentation = models.AutoField(primary_key=True)
    id_machinery = models.ForeignKey('machinery.Machinery', on_delete=models.CASCADE, null=False)
    document = models.CharField(max_length=255, null=False)
    path = models.CharField(max_length=500, null=False)
    creation_date = models.DateField(null=False)
    id_responsible_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=False)
    justification = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        db_table = 'machinery_documentation'
        constraints = [
            models.UniqueConstraint(
                fields=['document', 'id_machinery'],
                name='uniq_document_name_per_machinery'
            )
        ]
