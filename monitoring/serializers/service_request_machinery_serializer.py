from rest_framework import serializers
import os
import requests
from service_requests.models import ServiceRequest, RequestMachineryUser
from monitoring.serializers.data_serializer import get_machinery_data

class ServiceRequestMachineryDataSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source="id_request", read_only=True)
    customer_id = serializers.IntegerField(source="customer.id_customer", read_only=True)
    legal_entity_name = serializers.CharField(source="customer.legal_entity_name", read_only=True)
    customer_name = serializers.SerializerMethodField()
    request_status_name = serializers.SerializerMethodField()
    request_status_id = serializers.IntegerField(source="request_status.id_statues", read_only=True)
    scheduled_date = serializers.DateField(source="scheduled_start_date", read_only=True)
    completion_date = serializers.SerializerMethodField()
    maquinarias = serializers.SerializerMethodField()
    operadores = serializers.SerializerMethodField()
    distancia_recorrida = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = [
            "code",
            "customer_id",
            "legal_entity_name",
            "customer_name",
            "request_status_id",
            "request_status_name",
            "scheduled_date",
            "completion_date",
            "maquinarias",
            "operadores",
            "distancia_recorrida"
        ]

    def get_queryset(self):
        return super().get_queryset().filter(
            request_status_id__in=[20, 21, 22]
        )

    def get_customer_name(self, obj):
        try:
            customer = getattr(obj, "customer", None)
            if not customer:
                return None

            if not hasattr(self, "_ext_users_cache"):
                self._ext_users_cache = {}

            user_id = getattr(customer, "id_user_id", None)
            ext_data = {}
            if user_id:
                if user_id in self._ext_users_cache:
                    ext_data = self._ext_users_cache[user_id]
                else:
                    base_url = os.getenv("AUTH_SERVICE_URL", "").rstrip("/")
                    if base_url:
                        url = f"{base_url}/users/users/basic-user-list/by-ids"
                        headers = {}
                        request = self.context.get("request") if isinstance(self.context, dict) else None
                        if request is not None:
                            auth_header = getattr(request, "META", {}).get("HTTP_AUTHORIZATION") or (request.headers.get("Authorization") if hasattr(request, "headers") else None)
                            if auth_header:
                                headers["Authorization"] = auth_header
                        try:
                            resp = requests.post(url, json={"ids": [user_id]}, headers=headers, timeout=10)
                            if resp.status_code == 200 and resp.content:
                                payload = resp.json() or {}
                                data = payload.get("data") or []
                                if isinstance(data, list):
                                    for u in data:
                                        try:
                                            if u and str(u.get("id")) == str(user_id):
                                                ext_data = u
                                                self._ext_users_cache[user_id] = u
                                                break
                                        except Exception:
                                            continue
                        except Exception:
                            pass

            name = (ext_data.get("name") if isinstance(ext_data, dict) else None) or getattr(customer, "name", None)
            fln = (ext_data.get("first_last_name") if isinstance(ext_data, dict) else None) or getattr(customer, "first_last_name", None)
            sln = (ext_data.get("second_last_name") if isinstance(ext_data, dict) else None) or getattr(customer, "second_last_name", None)
            parts = [p for p in [name, fln, sln] if p]
            return " ".join(parts) if parts else None
        except Exception:
            return None

    def get_request_status_name(self, obj):
        try:
            return obj.request_status.name if obj.request_status else None
        except Exception:
            return None

    def get_completion_date(self, obj):
        try:
            if obj.request_status and getattr(obj.request_status, 'id_statues', None) == 22:
                if obj.completion_cancellation_datetime:
                    return obj.completion_cancellation_datetime.date()
            return None
        except Exception:
            return None

    def get_maquinarias(self, obj):
        try:
            # Obtener filtros del contexto
            filters = self.context.get('filters', {})
            machinery_id = filters.get('machinery_id')
            operator_id = filters.get('operator_id')
            
            # Obtener las maquinarias de la solicitud
            request_machineries = RequestMachineryUser.objects.filter(request=obj).select_related('machinery')
            
            # Aplicar filtros si existen
            if machinery_id is not None:
                request_machineries = request_machineries.filter(machinery_id=machinery_id)
            if operator_id is not None:
                request_machineries = request_machineries.filter(user_id=operator_id)
            
            # Construir lista de maquinarias
            machinery_list = []
            for rm in request_machineries:
                machinery_list.append({
                    'id_machinery': rm.machinery.id_machinery,
                    'machinery_name': rm.machinery.machinery_name,
                    'serial_number': rm.machinery.serial_number
                })
            
            # Si no hay maquinarias después de aplicar los filtros, devolver None
            if not machinery_list:
                return None
                
            # Siempre devolver un string unificado separado por ;
            return "; ".join([f"{m['machinery_name']} ({m['serial_number']})" for m in machinery_list])
        except Exception as e:
            print(f"Error en get_maquinarias: {str(e)}")
            return None

    def get_operadores(self, obj):
        try:
            # Obtener filtros del contexto
            filters = self.context.get('filters', {})
            machinery_id = filters.get('machinery_id')
            operator_id = filters.get('operator_id')
            
            # Obtener las asignaciones de maquinaria-operador
            request_operators = RequestMachineryUser.objects.filter(request=obj)
            
            # Aplicar filtros si existen
            if machinery_id is not None:
                request_operators = request_operators.filter(machinery_id=machinery_id)
            if operator_id is not None:
                request_operators = request_operators.filter(user_id=operator_id)
            
            # Obtener la lista de maquinarias para mantener el mismo orden
            machinery_list = []
            if hasattr(self, '_machinery_list'):
                machinery_list = self._machinery_list
            else:
                # Si no se ha generado la lista de maquinarias, usar las del request
                machinery_list = [rm.machinery for rm in request_operators.select_related('machinery').distinct('machinery')]
            
            # Obtener operadores ordenados por maquinaria
            operator_names = []
            processed_operators = set()  # Para evitar duplicados
            
            for machinery in machinery_list:
                # Obtener operadores para esta maquinaria
                operators_for_machinery = request_operators.filter(
                    machinery=machinery,
                    user__isnull=False
                ).select_related('user')
                
                for assignment in operators_for_machinery:
                    if not assignment.user:
                        continue
                        
                    # Obtener información del usuario desde el servicio externo
                    users_info = self._get_users_info([assignment.user.id_user])
                    if not users_info:
                        continue
                        
                    user_info = users_info[0]
                    name = user_info.get('name', '')
                    first_last_name = user_info.get('first_last_name', '')
                    second_last_name = user_info.get('second_last_name', '')
                    full_name = ' '.join(filter(None, [name, first_last_name, second_last_name]))
                    
                    # Solo agregar si no lo hemos procesado ya
                    if full_name and assignment.user.id_user not in processed_operators:
                        operator_names.append(full_name)
                        processed_operators.add(assignment.user.id_user)
            
            # Si no se encontraron operadores después de aplicar los filtros
            if not operator_names:
                return None
                
            # Devolver la lista de operadores
            return "; ".join(operator_names)
        except Exception as e:
            print(f"Error en get_operadores: {str(e)}")
            return None

    def get_distancia_recorrida(self, obj):
        try:
            # Obtener filtros del contexto
            filters = self.context.get('filters', {})
            machinery_id = filters.get('machinery_id')
            operator_id = filters.get('operator_id')
            
            # Obtener datos de maquinaria para la solicitud
            request = self.context.get('request')
            machinery_data = get_machinery_data(obj.id_request, request=request)
            
            # Filtrar por maquinaria/operador si es necesario
            filtered_data = []
            for data in machinery_data:
                # Si hay un filtro de maquinaria, verificar que coincida
                if machinery_id is not None and data.get('id_machinery') != machinery_id:
                    continue
                    
                # Si hay un filtro de operador, verificar que coincida
                if operator_id is not None and data.get('id_user') != operator_id:
                    continue
                    
                filtered_data.append(data)
            
            # Extraer distancias de cada máquina
            distances = []
            for data in filtered_data:
                if 'total_distance_km' in data and data['total_distance_km'] is not None:
                    # Formatear el número para mostrar hasta 3 decimales sin redondear
                    distance = float(data['total_distance_km'])
                    # Usar format para evitar redondeo y eliminar ceros innecesarios
                    formatted_distance = '{0:.10f}'.format(distance).rstrip('0').rstrip('.')
                    distances.append(f"{formatted_distance} km")
            
            # Unificar distancias en un string separado por ;
            if distances:
                return "; ".join(distances)
            return None
        except Exception as e:
            print(f"Error en get_distancia_recorrida: {str(e)}")
            return None

    def _get_users_info(self, user_ids):
        """Obtiene información de usuarios desde el servicio externo"""
        if not user_ids:
            return []
            
        try:
            base_url = os.getenv("AUTH_SERVICE_URL", "").rstrip("/")
            if not base_url:
                return []
                
            url = f"{base_url}/users/users/basic-user-list/by-ids"
            headers = {}
            
            request = self.context.get("request")
            if request is not None:
                auth_header = getattr(request, "META", {}).get("HTTP_AUTHORIZATION") or \
                            (request.headers.get("Authorization") if hasattr(request, "headers") else None)
                if auth_header:
                    headers["Authorization"] = auth_header
                    
            resp = requests.post(
                url,
                json={"ids": user_ids},
                headers=headers,
                timeout=10
            )
            
            if resp.status_code == 200:
                payload = resp.json() or {}
                return payload.get("data") or []
                
        except Exception as e:
            print(f"Error al obtener información de usuarios: {str(e)}")
            
        return []
