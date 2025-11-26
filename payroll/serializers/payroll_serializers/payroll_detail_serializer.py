from rest_framework import serializers
import os
import requests
import logging
from typing import Dict, Optional, Any, List

from payroll.models import Payroll

logger = logging.getLogger(__name__)


class PayrollDetailSerializer(serializers.ModelSerializer):
    """Serializer para el detalle completo de una nómina."""
    
    document_number = serializers.SerializerMethodField()
    employee_full_name = serializers.SerializerMethodField()
    responsible_user_full_name = serializers.SerializerMethodField()
    payroll_deductions = serializers.SerializerMethodField()
    payroll_increases = serializers.SerializerMethodField()
    
    class Meta:
        model = Payroll
        fields = [
            'id_payroll',
            'start_date',
            'end_date',
            'id_employee',
            'id_employee_contract',
            'document_number',
            'employee_full_name',
            'base_salary',
            'time_worked',
            'total_deductions',
            'total_increments',
            'net_pay',
            'creation_date',
            'id_responsible_user',
            'responsible_user_full_name',
            'payroll_deductions',
            'payroll_increases',
        ]
        read_only_fields = ['id_payroll', 'start_date', 'end_date', 'id_employee', 
                          'id_employee_contract', 'base_salary', 'time_worked',
                          'total_deductions', 'total_increments', 'net_pay', 
                          'creation_date', 'id_responsible_user']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cache para datos de usuarios externos
        if not hasattr(self, '_ext_users_cache'):
            self._ext_users_cache = {}
        # Si se proporcionan usuarios en batch desde el contexto, usarlos
        context = kwargs.get('context', {})
        if isinstance(context, dict) and 'users_data' in context:
            self._ext_users_cache.update(context['users_data'])

    def _get_external_user(self, user_id: Optional[int]) -> Dict[str, Any]:
        """
        Obtiene información del usuario desde el servicio externo.
        
        Args:
            user_id: ID del usuario a consultar
            
        Returns:
            Diccionario con datos del usuario o diccionario vacío si no se encuentra
        """
        if not user_id:
            return {}

        # Verificar cache
        if user_id in self._ext_users_cache:
            return self._ext_users_cache[user_id]

        base_url = os.getenv('AUTH_SERVICE_URL', '').rstrip('/')
        if not base_url:
            logger.warning('AUTH_SERVICE_URL no configurado')
            return {}

        url = f"{base_url}/users/users/basic-user-list/by-ids"
        headers = {'Content-Type': 'application/json'}

        # Obtener header de autorización del request
        request = self.context.get('request') if isinstance(self.context, dict) else None
        if request is not None:
            auth_header = getattr(request, 'META', {}).get('HTTP_AUTHORIZATION') or (
                request.headers.get('Authorization') if hasattr(request, 'headers') else None
            )
            if auth_header:
                headers['Authorization'] = auth_header

        try:
            resp = requests.post(url, json={'ids': [user_id]}, headers=headers, timeout=10)
            if resp.status_code == 200 and resp.content:
                payload = resp.json() or {}
                data = payload.get('data') or []
                if isinstance(data, list):
                    for u in data:
                        try:
                            if u and str(u.get('id')) == str(user_id):
                                self._ext_users_cache[user_id] = u
                                return u
                        except Exception:
                            continue
        except Exception as e:
            logger.error(f'Error consultando servicio externo de usuarios: {str(e)}')

        return {}

    def get_document_number(self, obj: Payroll) -> Optional[str]:
        """Obtiene el número de documento del empleado desde el servicio externo."""
        # Obtener el empleado relacionado
        employee = getattr(obj, 'id_employee', None)
        if not employee:
            return None
        
        user_id = getattr(employee, 'id_user_id', None)
        if not user_id:
            return None

        user_data = self._get_external_user(user_id)
        if user_data:
            document_number = user_data.get('document_number')
            return str(document_number) if document_number else None

        return None

    def get_employee_full_name(self, obj: Payroll) -> Optional[str]:
        """Obtiene el nombre completo del empleado desde el servicio externo."""
        # Obtener el empleado relacionado
        employee = getattr(obj, 'id_employee', None)
        if not employee:
            return None
        
        user_id = getattr(employee, 'id_user_id', None)
        if not user_id:
            return None

        user_data = self._get_external_user(user_id)
        if user_data:
            name_parts = []
            name = user_data.get('name', '').strip() if user_data.get('name') else ''
            first_last_name = user_data.get('first_last_name', '').strip() if user_data.get('first_last_name') else ''
            second_last_name = user_data.get('second_last_name', '').strip() if user_data.get('second_last_name') else ''

            if name:
                name_parts.append(name)
            if first_last_name:
                name_parts.append(first_last_name)
            if second_last_name:
                name_parts.append(second_last_name)

            return ' '.join(name_parts) if name_parts else None

        return None

    def get_responsible_user_full_name(self, obj: Payroll) -> Optional[str]:
        """Obtiene el nombre completo del usuario responsable desde el servicio externo."""
        # Obtener el usuario responsable
        responsible_user = getattr(obj, 'id_responsible_user', None)
        if not responsible_user:
            return None
        
        # El id_responsible_user es un ForeignKey a users.User, donde id_user es la primary key
        user_id = getattr(responsible_user, 'id_user', None)
        if not user_id:
            return None

        user_data = self._get_external_user(user_id)
        if user_data:
            name_parts = []
            name = user_data.get('name', '').strip() if user_data.get('name') else ''
            first_last_name = user_data.get('first_last_name', '').strip() if user_data.get('first_last_name') else ''
            second_last_name = user_data.get('second_last_name', '').strip() if user_data.get('second_last_name') else ''

            if name:
                name_parts.append(name)
            if first_last_name:
                name_parts.append(first_last_name)
            if second_last_name:
                name_parts.append(second_last_name)

            return ' '.join(name_parts) if name_parts else None

        return None

    def get_payroll_deductions(self, obj: Payroll) -> List[Dict[str, Any]]:
        """Obtiene y serializa las deducciones de la nómina."""
        deductions = obj.payroll_deductions.all().select_related('deduction_type')
        result = []
        
        for deduction in deductions:
            deduction_data = {
                'id_payroll_deduction': deduction.id_payroll_deduction,
                'deduction_type': deduction.deduction_type.id_types if deduction.deduction_type else None,
                'deduction_type_name': deduction.deduction_type.name if deduction.deduction_type else None,
                'amount_type': deduction.amount_type,
                'amount_value': deduction.amount_value,
                'application_deduction_type': deduction.application_deduction_type,
                'start_date_deduction': None,
                'end_date_deductions': None,
                'description': deduction.description,
                'amount': deduction.amount,
                'calculated_amount': deduction.calculated_amount,
            }
            
            # Formatear fechas
            if deduction.start_date_deduction:
                deduction_data['start_date_deduction'] = deduction.start_date_deduction.strftime('%Y-%m-%d')
            if deduction.end_date_deductions:
                deduction_data['end_date_deductions'] = deduction.end_date_deductions.strftime('%Y-%m-%d')
            
            result.append(deduction_data)
        
        return result

    def get_payroll_increases(self, obj: Payroll) -> List[Dict[str, Any]]:
        """Obtiene y serializa los incrementos de la nómina."""
        increases = obj.payroll_increases.all().select_related('increase_type')
        result = []
        
        for increase in increases:
            increase_data = {
                'id_payroll_increase': increase.id_payroll_increase,
                'increase_type': increase.increase_type.id_types if increase.increase_type else None,
                'increase_type_name': increase.increase_type.name if increase.increase_type else None,
                'amount_type': increase.amount_type,
                'amount_value': increase.amount_value,
                'application_increase_type': increase.application_increase_type,
                'start_date_increase': None,
                'end_date_increase': None,
                'description': increase.description,
                'amount': increase.amount,
                'calculated_amount': increase.calculated_amount,
            }
            
            # Formatear fechas
            if increase.start_date_increase:
                increase_data['start_date_increase'] = increase.start_date_increase.strftime('%Y-%m-%d')
            if increase.end_date_increase:
                increase_data['end_date_increase'] = increase.end_date_increase.strftime('%Y-%m-%d')
            
            result.append(increase_data)
        
        return result
    
    def to_representation(self, instance):
        """Formatea las fechas correctamente y calcula base_salary."""
        representation = super().to_representation(instance)
        
        # Calcular base_salary * time_worked
        base_salary = representation.get('base_salary', 0) or 0
        time_worked = representation.get('time_worked', 0) or 0
        representation['base_salary'] = base_salary * time_worked
        
        # Formatear fechas
        date_fields = ['start_date', 'end_date']
        for field in date_fields:
            if representation.get(field):
                representation[field] = representation[field].split('T')[0] if 'T' in str(representation[field]) else str(representation[field])
        
        # Formatear creation_date (DateTimeField)
        if representation.get('creation_date'):
            creation_date = representation['creation_date']
            if 'T' in str(creation_date):
                representation['creation_date'] = creation_date.split('T')[0]
        
        return representation

