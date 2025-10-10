from django.db import models

class DocumentType(models.Model):
    id_document_type = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'document_type'
