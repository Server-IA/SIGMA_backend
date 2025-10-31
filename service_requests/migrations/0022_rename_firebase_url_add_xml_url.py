# Generated migration for renaming firebase_url to invoice_pdf_url and adding invoice_xml_url

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('service_requests', '0021_invoice_total_withholding_taxes_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='invoice',
            old_name='firebase_url',
            new_name='invoice_pdf_url',
        ),
        migrations.AddField(
            model_name='invoice',
            name='invoice_xml_url',
            field=models.URLField(max_length=500, blank=True, null=True),
        ),
    ]
