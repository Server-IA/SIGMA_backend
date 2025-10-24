from rest_framework import serializers
import os
import requests
import logging

from maintenance.models import MaintenanceReport

logger = logging.getLogger(__name__)


class MaintenanceReportDetailSerializer(serializers.ModelSerializer):
    """
    Serializador que contiene la lógica completa para representar el detalle
    de un reporte de mantenimiento en el mismo formato JSON que se usa para
    el PDF/endpoint detail. Se encapsula aquí para mantener la view limpia.
    """

    class Meta:
        model = MaintenanceReport
        # No confiar en auto campos; to_representation construye la salida
        fields = []

    def to_representation(self, obj):
        request = self.context.get('request') if isinstance(self.context, dict) else None

        try:
            # Preparar scheduling y maquinaria
            scheduling = getattr(obj, 'id_maintenance_scheduling', None)
            scheduling_id = getattr(scheduling, 'id_maintenance_scheduling', None) if scheduling else None
            machinery = getattr(scheduling, 'id_machinery', None) if scheduling else None

            machinery_image = getattr(machinery, 'image_path', None) if machinery else None
            try:
                machinery_id_val = getattr(machinery, 'id_machinery', None) or getattr(machinery, 'id', None)
            except Exception:
                machinery_id_val = None
            machinery_serial = getattr(machinery, 'serial_number', None) if machinery else None
            machinery_name = getattr(machinery, 'machinery_name', None) if machinery else None
            machinery_type_name = getattr(getattr(machinery, 'machinery_type', None), 'name', None) if machinery else None
            machinery_location = None
            try:
                if machinery:
                    country = getattr(machinery, 'id_country', None) or ''
                    dept = getattr(machinery, 'id_department', None) or ''
                    city = getattr(machinery, 'id_city', None) or ''
                    machinery_location = f"{country}-{dept}-{city}"
            except Exception:
                machinery_location = None

            # Fecha y tipo del mantenimiento
            scheduled_at = getattr(scheduling, 'scheduled_at', None) if scheduling else None
            if scheduled_at and hasattr(scheduled_at, 'strftime'):
                maintenance_date = scheduled_at.strftime("%Y-%m-%d %H:%M:%S")
            else:
                maintenance_date = None
            maintenance_type_name_sched = getattr(getattr(scheduling, 'maintenance_type', None), 'name', None) if scheduling else None

            # Tiempo invertido (formateado)
            try:
                hours = int(getattr(obj, 'time_invested_hours', 0) or 0)
            except Exception:
                hours = 0
            try:
                minutes = int(getattr(obj, 'time_invested_minutes', 0) or 0)
            except Exception:
                minutes = 0
            try:
                seconds = int(getattr(obj, 'time_invested_seconds', 0) or 0)
            except Exception:
                seconds = 0
            time_invested_str = f"{hours}h {minutes}m {seconds}s"

            # Resolver técnicos: coletar ids relevantes
            technicians_map = {}
            technicians_list = []
            try:
                tech_ids = set()
                # assigned users
                try:
                    for uid in obj.assigned_users.values_list('id_user', flat=True):
                        if uid:
                            tech_ids.add(uid)
                except Exception:
                    pass

                # técnicos que realizaron cada mantenimiento
                maintenance_tech_ids = []
                try:
                    for rel in getattr(obj, 'maintenance_relations').all():
                        try:
                            tid = getattr(getattr(rel, 'id_technician', None), 'id_user', None)
                        except Exception:
                            tid = None
                        if tid:
                            tech_ids.add(tid)
                            maintenance_tech_ids.append(tid)
                except Exception:
                    maintenance_tech_ids = []

                # scheduling assigned tech
                sched_tech_uid = None
                try:
                    sched_tech_uid = getattr(getattr(scheduling, 'assigned_technician', None), 'id_user', None)
                    if sched_tech_uid:
                        tech_ids.add(sched_tech_uid)
                except Exception:
                    sched_tech_uid = None

                tech_ids_list = list(tech_ids)
                if tech_ids_list:
                    base_url = os.getenv('AUTH_SERVICE_URL', '').rstrip('/')
                    if base_url:
                        url = f"{base_url}/users/users/basic-user-list/by-ids"
                        headers = {}
                        auth_header = getattr(request, 'META', {}).get('HTTP_AUTHORIZATION') if request is not None else None
                        if not auth_header and hasattr(request, 'headers'):
                            auth_header = request.headers.get('Authorization')
                        if auth_header:
                            headers['Authorization'] = auth_header
                        try:
                            resp = requests.post(url, json={'ids': tech_ids_list}, headers=headers, timeout=10)
                            if resp.status_code == 200:
                                payload = resp.json()
                                data = payload.get('data', []) or []
                                for u in data:
                                    uid = u.get('id')
                                    name = u.get('name') or ''
                                    fln = u.get('first_last_name') or ''
                                    sln = u.get('second_last_name') or ''
                                    full = ' '.join([p for p in [name, fln, sln] if p]).strip()
                                    if uid is not None:
                                        technicians_map[str(uid)] = full or str(uid)
                            else:
                                for uid in tech_ids_list:
                                    technicians_map[str(uid)] = str(uid)
                        except Exception:
                            for uid in tech_ids_list:
                                technicians_map[str(uid)] = str(uid)

                # construir technicians_list ordered
                seen = set()
                for tid in maintenance_tech_ids:
                    key = str(tid)
                    if key in technicians_map and key not in seen:
                        technicians_list.append(technicians_map[key])
                        seen.add(key)
                try:
                    if sched_tech_uid:
                        key = str(sched_tech_uid)
                        if key in technicians_map and key not in seen:
                            technicians_list.append(technicians_map[key])
                            seen.add(key)
                except Exception:
                    pass

            except Exception:
                technicians_map = {}
                technicians_list = []

            # Construir maintenance_entries
            maintenance_entries = []
            maintenance_total = 0.0
            try:
                for rel in getattr(obj, 'maintenance_relations').all():
                    m = getattr(rel, 'id_maintenance', None)
                    name = getattr(m, 'name', None) if m else None
                    try:
                        cost_raw = getattr(rel, 'maintenance_cost', 0) or 0
                        cost_val = float(cost_raw)
                    except Exception:
                        cost_val = 0.0
                    maintenance_total += cost_val

                    # técnico
                    tech_obj = getattr(rel, 'id_technician', None)
                    tech_name = None
                    if tech_obj is not None:
                        tech_id = getattr(tech_obj, 'id_user', None) or getattr(tech_obj, 'id', None)
                        if tech_id is not None:
                            tech_name = technicians_map.get(str(tech_id)) if technicians_map else None
                        if not tech_name:
                            tech_name_parts = [
                                getattr(tech_obj, 'name', '') or getattr(tech_obj, 'first_name', '') or '',
                                getattr(tech_obj, 'first_last_name', '') or getattr(tech_obj, 'last_name', ''),
                                getattr(tech_obj, 'second_last_name', '') or getattr(tech_obj, 'secondLastName', '')
                            ]
                            tech_name = ' '.join([p for p in [p.strip() for p in tech_name_parts] if p]) or (str(tech_id) if tech_id is not None else 'N/D')

                    maintenance_entries.append({
                        'name': name or 'N/D',
                        'type': getattr(getattr(m, 'maintenance_type', None), 'name', 'N/D'),
                        'technician': tech_name or 'N/D',
                        'cost': cost_val
                    })
            except Exception:
                maintenance_entries = []

            # Spare parts
            spare_parts = []
            spare_total = 0.0
            try:
                for sp in getattr(obj, 'spare_parts_used').all():
                    try:
                        qty = float(getattr(sp, 'quantity_used', 0) or 0)
                    except Exception:
                        qty = 0.0
                    try:
                        unit_cost = float(getattr(sp, 'cost_at_time', 0) or 0)
                    except Exception:
                        unit_cost = 0.0
                    total = qty * unit_cost
                    spare_total += total
                    spare_parts.append({
                        'name': getattr(sp, 'name', 'N/D'),
                        'brand': getattr(getattr(sp, 'spare_part_brand', None), 'name', 'N/D'),
                        'quantity': qty,
                        'unit_cost': unit_cost,
                        'total': total
                    })
            except Exception:
                spare_parts = []
                spare_total = 0.0

            # currency symbol and totals
            try:
                currency_symbol = getattr(getattr(obj, 'currency_unit', None), 'symbol', '') or ''
            except Exception:
                currency_symbol = ''
            try:
                total_general = float(getattr(obj, 'total_cost', maintenance_total + spare_total) or (maintenance_total + spare_total))
            except Exception:
                total_general = maintenance_total + spare_total

            technicians_text = ', '.join(technicians_list) if technicians_list else ''

            data = {
                'id_maintenance_report': getattr(obj, 'id_maintenance_report', None),
                'id_maintenance_scheduling': scheduling_id,
                'machinery_id': machinery_id_val,
                'machinery_serial': machinery_serial,
                'machinery_name': machinery_name,
                'machinery_type': machinery_type_name,
                'machinery_location': machinery_location,
                'machinery_image': machinery_image,
                'maintenance_date': maintenance_date,
                'maintenance_type': maintenance_type_name_sched,
                'description': getattr(obj, 'description', '') or '',
                'recommendations': getattr(obj, 'recommendations', '') or '',
                'time_invested': time_invested_str,
                'technicians': technicians_text,
                'maintenance_entries': maintenance_entries,
                'spare_parts': spare_parts,
                'currency_symbol': currency_symbol,
                'maintenance_total': maintenance_total,
                'spare_parts_total': spare_total,
                'total_cost': total_general,
            }

            return data

        except Exception as e:
            logger.exception("Error serializing MaintenanceReport detail: %s", e)
            return {
                'id_maintenance_report': getattr(obj, 'id_maintenance_report', None),
                'error': 'Error building representation'
            }
