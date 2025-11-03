import logging
import os
from typing import Optional

import requests
from django.db import transaction
from django.utils import timezone

from service_requests.models.customer import Customer
from users.models.user import User


logger = logging.getLogger(__name__)


def _build_users_service_url(document_number: int) -> Optional[str]:
    base_url = os.getenv('AUTH_SERVICE_URL', '').rstrip('/')
    if not base_url:
        logger.warning('AUTH_SERVICE_URL no configurado; se omite sincronización')
        return None
    return f"{base_url}/users/users/by-document-for-job/{document_number}"


def _fetch_external_user_by_document(document_number: int) -> Optional[dict]:
    url = _build_users_service_url(document_number)
    if not url:
        return None

    # GET simple, sin Authorization adicional
    try:
        resp = requests.get(url, timeout=8)
    except requests.exceptions.Timeout:
        logger.error('Timeout consultando by-document-for-job %s', document_number)
        return None
    except requests.exceptions.RequestException as e:
        logger.error('Error consultando by-document-for-job %s: %s', document_number, str(e))
        return None

    if resp.status_code != 200:
        # 404 u otros: no bloquear job
        logger.debug('by-document-for-job %s respondió %s', document_number, resp.status_code)
        return None

    try:
        payload = resp.json() if resp.content else {}
        # Verificar que success sea True
        if not payload.get('success'):
            logger.debug('by-document-for-job %s: success=false', document_number)
            return None
        
        data = (payload or {}).get('data') or {}
        if not isinstance(data, dict):
            logger.debug('by-document-for-job %s: data no es dict', document_number)
            return None
        
        # Verificar que data tenga id
        if 'id' not in data:
            logger.debug('by-document-for-job %s: data no contiene id', document_number)
            return None
        
        return data
    except Exception as e:
        logger.error('Respuesta inválida para documento %s: %s', document_number, str(e))
        return None


def sync_customers_users_job() -> None:
    """
    Sincroniza clientes con usuarios del servicio externo por número de documento.

    - Selecciona clientes con document_number no nulo y id_user nulo
    - Consulta /by-document-for-job/{document_number}
    - Si el documento coincide, vincula id_user_id al id externo y limpia campos locales
    """
    started_at = timezone.now()
    matched = 0
    updated = 0
    skipped = 0
    already_linked_conflict = 0
    users_created = 0
    errors = 0

    qs = Customer.objects.filter(document_number__isnull=False, id_user__isnull=True)

    for customer in qs.iterator():
        doc = customer.document_number
        if doc is None:
            skipped += 1
            continue

        ext = _fetch_external_user_by_document(doc)
        if not ext:
            skipped += 1
            logger.debug('No se encontró usuario externo para documento %s (customer %s)', doc, customer.id_customer)
            continue

        try:
            # La respuesta trae {"success": true, "data": {"id": 28}}
            # No incluye document_number, confiamos en que el endpoint devuelve el id correcto para el documento consultado
            ext_user_id = ext.get('id')
            if not ext_user_id:
                skipped += 1
                logger.warning('Respuesta sin id para documento %s (customer %s)', doc, customer.id_customer)
                continue

            matched += 1
            ext_user_id = int(ext_user_id)

            # Verificar conflicto de OneToOne: otro Customer ya vinculado al mismo user
            if Customer.objects.filter(id_user_id=ext_user_id).exclude(pk=customer.pk).exists():
                already_linked_conflict += 1
                logger.warning('User %s ya vinculado a otro Customer; omitiendo id_customer=%s', ext_user_id, customer.id_customer)
                continue

            with transaction.atomic():
                # Crear User si no existe en la tabla users
                user, created = User.objects.get_or_create(id_user=ext_user_id)
                if created:
                    users_created += 1
                    logger.info('User %s creado en tabla users', ext_user_id)

                # Vincular usuario y limpiar campos locales
                customer.id_user_id = ext_user_id
                customer.document_number = None
                customer.name = None
                customer.first_last_name = None
                customer.second_last_name = None
                customer.email = None
                customer.phone = None
                customer.address = None
                customer.type_document_id_id = None

                customer.save(update_fields=[
                    'id_user',
                    'document_number',
                    'name',
                    'first_last_name',
                    'second_last_name',
                    'email',
                    'phone',
                    'address',
                    'type_document_id',
                    'modification_date',
                ])

                updated += 1
                logger.info(
                    'Customer %s vinculado a user %s por documento %s; datos locales limpiados',
                    customer.id_customer,
                    ext_user_id,
                    doc,
                )

        except Exception as e:
            errors += 1
            logger.error('Error sincronizando customer %s: %s', getattr(customer, 'id_customer', 'unknown'), str(e), exc_info=True)

    logger.info(
        'sync_customers_users_job fin. started_at=%s matched=%s updated=%s skipped=%s conflicts=%s users_created=%s errors=%s',
        started_at.isoformat(), matched, updated, skipped, already_linked_conflict, users_created, errors
    )


