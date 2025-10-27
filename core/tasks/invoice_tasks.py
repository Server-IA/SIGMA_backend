try:
    from celery import shared_task
except Exception:
    def shared_task(func):
        func.delay = func
        return func

import logging


logger = logging.getLogger(__name__)


@shared_task
def download_and_upload_invoice(invoice_id: int):
    """
    Tarea que descarga el PDF de la factura desde Factus (usando invoice_number si está disponible,
    o CUFE como fallback), decodifica el base64, sube el PDF a Firebase y guarda la URL en el modelo Invoice.
    """
    try:
        from service_requests.models.invoice import Invoice
        from core.services.factus_service import FactusService, FactusServiceError
        from core.services.file_upload_service import upload_invoice_pdf

        invoice = Invoice.objects.get(id_invoice=invoice_id)

        # Preferir invoice_number (campo 'number' en Factus). Si no existe, usar cufe
        if invoice.invoice_number:
            file_data, filename = FactusService().get_invoice_pdf_by_number(invoice.invoice_number)
            key = invoice.invoice_number
        elif invoice.cufe:
            file_data, filename = FactusService().get_invoice_pdf(invoice.cufe)
            key = invoice.cufe
        else:
            logger.warning("Invoice %s no tiene invoice_number ni cufe; no se descargará PDF.", invoice_id)
            return None

        # Subir a Firebase
        firebase_url = upload_invoice_pdf(
            file_data=file_data,
            invoice_number=key,
            reference_code=invoice.reference_code
        )

        invoice.invoice_pdf_url = firebase_url
        invoice.save(update_fields=['invoice_pdf_url'])

        logger.info("Invoice %s: PDF subido a Firebase en %s", invoice_id, firebase_url)
        return firebase_url

    except Invoice.DoesNotExist:
        logger.warning("Invoice %s no encontrada al intentar descargar/subir PDF.", invoice_id)
        return None
    except FactusServiceError as e:
        logger.error("Error de Factus al descargar PDF para invoice %s: %s", invoice_id, str(e))
        return None
    except Exception as e:
        logger.exception("Error inesperado en download_and_upload_invoice para invoice %s: %s", invoice_id, str(e))
        return None
