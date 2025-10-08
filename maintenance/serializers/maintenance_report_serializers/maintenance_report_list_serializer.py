from rest_framework import serializers
from maintenance.models import MaintenanceReport


class MaintenanceReportListSerializer(serializers.ModelSerializer):
    """
    Serializador para listar reportes de mantenimiento con la información solicitada:
    - id_maintenance_report
    - id_maintenance_scheduling
    - assigned_technician (nombre completo, resuelto vía servicio externo si está disponible)
    - registration_date
    - maintenance_names (nombres de los mantenimientos realizados separados por comas)
    - description
    - total_cost
    """

    id_maintenance_scheduling = serializers.CharField(
        source='id_maintenance_scheduling.id_maintenance_scheduling',
        read_only=True
    )

    assigned_technician = serializers.SerializerMethodField()
    maintenance_names = serializers.SerializerMethodField()

    def get_assigned_technician(self, obj):
        """Intenta resolver el nombre completo del técnico asignado al maintenance_scheduling.
        1) Si el viewset pasó technicians_map en el contexto, usarlo (evita llamadas HTTP por cada objeto)
        2) Si no existe technicians_map, usar atributos locales del objeto assigned_technician
        3) Siempre devuelve una cadena (o 'N/D')
        """
        try:
            sched = getattr(obj, 'id_maintenance_scheduling', None)
            if not sched:
                return 'N/D'

            tech = getattr(sched, 'assigned_technician', None)
            if not tech:
                return 'N/D'

            user_id = getattr(tech, 'id_user', None) or getattr(tech, 'id', None) or None
            if not user_id:
                return 'N/D'

            # 0) Intentar resolver usando mapping pasado por el viewset
            technicians_map = None
            try:
                technicians_map = self.context.get('technicians_map') if isinstance(self.context, dict) else None
            except Exception:
                technicians_map = None
            if technicians_map:
                # support keys as str or int
                key_str = str(user_id)
                if key_str in technicians_map:
                    return technicians_map[key_str]
                if user_id in technicians_map:
                    return technicians_map[user_id]

            # NOTA: la llamada HTTP al servicio externo se realiza en el viewset
            # para evitar N llamadas desde el serializador. Aquí sólo usamos
            # atributos locales como fallback.

            # Fallback: intentar atributos locales del objeto User relacionado
            given = (getattr(tech, 'name', None) or getattr(tech, 'first_name', None) or '')
            fln = (getattr(tech, 'first_last_name', None) or getattr(tech, 'last_name', None) or '')
            sln = (getattr(tech, 'second_last_name', None) or getattr(tech, 'secondLastName', None) or '')
            parts = [p for p in [given.strip(), fln.strip(), sln.strip()] if p]
            if parts:
                return ' '.join(parts)

            return str(user_id)
        except Exception:
            return 'N/D'

    def get_maintenance_names(self, obj):
        """Devuelve los nombres de los mantenimientos realizados en este reporte, separados por comas."""
        try:
            names = []
            for rel in getattr(obj, 'maintenance_relations').all():
                m = getattr(rel, 'id_maintenance', None)
                if m is not None:
                    name = getattr(m, 'name', None)
                    if name:
                        names.append(name)
            return ', '.join(names)
        except Exception:
            return ''

    class Meta:
        model = MaintenanceReport
        fields = [
            'id_maintenance_report',
            'id_maintenance_scheduling',
            'assigned_technician',
            'registration_date',
            'maintenance_names',
            'description',
            'total_cost'
        ]
