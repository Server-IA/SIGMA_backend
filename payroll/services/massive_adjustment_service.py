
import pandas as pd
import uuid
from datetime import datetime
from django.db import transaction
from django.utils import timezone

from parameterization.models.types import Types
from ..models import Employee, TemporaryPayrollAdjustment
from parameterization.models import Types
import logging

logger = logging.getLogger(__name__)

class MassiveAdjustmentService:
    """Servicio para procesar carga masiva de ajustes desde Excel"""
    
    REQUIRED_COLUMNS = [
        'Identificación del empleado',
        'Nombre del empleado',
        'Nombre del ajuste',
        'Tipo de ajuste',
        'Tipo de monto',
        'Valor',
        'Aplicación',
        'Fecha de Inicio',
        'Fecha de Fin',
        'Cantidad',
        'Descripción',
    ]
    
    VALID_ADJUSTMENT_TYPES = ['deduccion', 'incremento', 'deducción']
    VALID_APPLICATION_TYPES = ['salario base', 'salario final']
    VALID_AMOUNT_TYPES = ['fijo', 'porcentaje']
    
    def __init__(self, file, start_date, end_date, employees_ids, user):
        self.file = file
        self.fecha_desde = start_date
        self.fecha_hasta = end_date
        self.empleados_ids = {e["id_employee"] for e in employees_ids}
        self.documentos_empleados = {str(e["document_number"]) for e in employees_ids}
        self.batch_id = uuid.uuid4()
        self.user = user
        self.results = []
    
    def process(self):
        """Procesa el archivo Excel y retorna resultados"""
        try:
            # 1. Leer Excel
            df = self._read_excel()
            
            # 2. Validar estructura
            self._validate_structure(df)
            
            # 3. Procesar cada fila
            accepted_adjustments = []
            
            for index, row in df.iterrows():
                result = self._process_row(index + 2, row)  # +2 porque Excel empieza en 1 y tiene header
                self.results.append(result)
                
                if result['status'] == 'pending':
                    accepted_adjustments.append(result['adjustment_data'])
            
            # 4. Guardar ajustes aceptados en BD
            temp_ids = []
            if accepted_adjustments:
                temp_ids = self._save_temporary_adjustments(accepted_adjustments)
            
            # 5. Retornar resultados
            return {
                'batch_id': self.batch_id, 
                'total_rows': len(self.results),
                'accepted_rows': len(accepted_adjustments),
                'rejected_rows': len(self.results) - len(accepted_adjustments),
                'results': self.results,
                'temporal_adjustment_ids': temp_ids
            }
            
        except Exception as e:
            logger.exception("Error procesando carga masiva")
            raise Exception(f"Error al procesar el archivo: {str(e)}")
    
    def _read_excel(self):
        """Lee el archivo Excel"""
        try:
            # Intentar con diferentes engines
            try:
                df = pd.read_excel(self.file, engine='openpyxl')
            except:
                df = pd.read_excel(self.file, engine='xlrd')
            
            if df.empty:
                raise ValueError("El archivo está vacío")
            
            return df
        except Exception as e:
            raise ValueError(f"Error al leer el archivo Excel: {str(e)}")
    
    def _validate_structure(self, df):
        """Valida que el Excel tenga las columnas requeridas"""
        missing_columns = []
        for col in self.REQUIRED_COLUMNS:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            raise ValueError(
                f"El archivo no tiene las columnas requeridas: {', '.join(missing_columns)}"
            )
    
    def _process_row(self, row_number, row):
        """Procesa una fila del Excel"""
        result = {
            'employee_identification': self.clean_value(row.get('Identificación del empleado')),
            'employee_name': self.clean_value(row.get('Nombre del empleado')),
            'adjustment_name': self.clean_value(row.get('Nombre del ajuste')),
            'adjustment_type': self.clean_value(row.get('Tipo de ajuste')).lower(),
            'amount_type': self.clean_value(row.get('Tipo de monto')).lower(),
            'amount_value': row.get('Valor', 0),
            'application_type': self.clean_value(row.get('Aplicación')).lower(),
            'start_date_adjustment': self.clean_value(row.get('Fecha de Inicio')),
            'end_date_adjustment': self.clean_value(row.get('Fecha de Fin')),
            'amount': row.get('Cantidad', 1),
            'description': self.clean_value(row.get('Descripción')),
            'status': 'Aceptado',
            'reason_rejection': '',
            'adjustment_data': None
        }

        
        # Validaciones
        errors = []
        
        # 1. Validar que el empleado existe y está en la lista
        employee = self._validate_employee(result['employee_identification'], errors)
        
        # 2. Validar que el tipo de ajuste exista
        novelty = self._validate_type(result['adjustment_name'], errors)
        
        # 3. Validar tipo de ajuste
        if result['adjustment_type'] not in self.VALID_ADJUSTMENT_TYPES:
            errors.append(f"Tipo de ajuste inválido: debe ser 'deduccion' o 'incremento'")

        # 4. Validar tipo de aplicación
        if result['application_type'] not in self.VALID_APPLICATION_TYPES:
            errors.append(f"Tipo de aplicación inválido: debe ser 'salario base' o 'salario final'")
        
        # 5. Validar tipo de monto
        if result['amount_type'] not in self.VALID_AMOUNT_TYPES:
            errors.append(f"Tipo de monto inválido: debe ser 'fijo' o 'porcentaje'")
        
        # 6. Validar valor
        try:
            value = float(result['amount_value'])
            if value < 0:
                errors.append("El valor debe ser positivo")
            
            # Validar porcentaje
            if result['amount_type'] == 'porcentaje' and value > 100:
                errors.append("El valor porcentual no puede superar el 100%")
        except (ValueError, TypeError):
            errors.append("El valor debe ser numérico")
            value = 0
        
        # 7. Validar cantidad
        try:
            amount = float(result['amount'])
            if amount < 0:
                errors.append("La cantidad debe ser positiva")
        except (ValueError, TypeError):
            errors.append("La cantidad debe ser numérica")
            amount = 1
        
        # 7. Validar fecha de inicio y fin
        start_date = self._validate_date(result['start_date_adjustment'], errors)
        end_date = self._validate_date(result['end_date_adjustment'], errors)
        if start_date and end_date and start_date > end_date:
            errors.append("La fecha de inicio no puede ser mayor a la fecha de fin")

        # 8. Validar que las fechas estén dentro del rango de la nómina
        if start_date and (start_date < self.fecha_desde or start_date > self.fecha_hasta):
            errors.append("La fecha de inicio está fuera del rango de la nómina")
        
        if end_date and (end_date < self.fecha_desde or end_date > self.fecha_hasta):
            errors.append("La fecha de fin está fuera del rango de la nómina")

        # 9. Validar longitud de descripción
        if len(result['description']) > 255:
            errors.append("La descripción no puede exceder 255 caracteres")
            
        # Si hay errores, marcar como rechazado
        if errors:
            result['status'] = 'Rechazado'
            result['reason_rejection'] = ' | '.join(errors)
        else:
            # Guardar datos para crear ajuste temporal
            result['adjustment_data'] = {
                'employee': employee,
                'adjustment_name': result['nombre_ajuste'],
                'adjustment_type': 'deduccion' if result['tipo_ajuste'] in ['deduccion', 'deducción'] else 'incremento',
                'amount_type': result['tipo_monto'],
                'amount_value': value,
                'application_type': result['application_type'],
                'start_date_adjustment': start_date,
                'end_date_adjustment': end_date,
                'amount': amount,
                "status": "pending",
                'description': result['description'],
            }
        
        return result
    
    def _validate_employee(self, identificacion, errors):
        """Valida que el empleado exista y esté en la lista"""
        if not identificacion:
            errors.append("Identificación del empleado es requerida")
            return None
        
        if identificacion not in self.documentos_empleados:
            errors.append(f"El empleado con documento {identificacion} no está en la lista de empleados aplicables")
            return None
        
        try:
            # Primero verificar que el empleado esté en la lista
            if not any(emp_id == employee.id_employee for emp_id in self.empleados_ids):
                errors.append("El empleado no está en la lista seleccionada")
                return None
            
            ## Obtener ID del empleado del listado
            employee_id = next(
                emp["id_employee"] for emp in self.empleados_ids
                if str(emp["document_number"]) == identificacion
            )
            
            # Luego validar que esté activo
            employee = Employee.objects.get(
                id_employee=employee_id,  # Usar el ID específico
                employee_status_id=1
            )
            return employee
        except Employee.DoesNotExist:
            errors.append(f"El empleado con documento {identificacion} no existe o no está activo")
            return None
        
    
    def _validate_type(self, adjustment_type, errors):
        """Valida que la novedad exista en parametrización"""
        if not adjustment_type:
            errors.append("El nombre del ajuste es requerido")
            return None
        
        try:
            adjustment = Types.objects.get(
                name__iexact=adjustment_type,
                id_types_categories__id_types_categories__in=[18, 19],  # Permitir categoría 18 o 19
                id_statues=1 # Activo
            )
            return adjustment
        except Types.DoesNotExist:
            errors.append(f"El ajuste '{adjustment_type}' no está registrado en el sistema")
            return None
    
    def _validate_date(self, fecha_str, errors):
        """Valida formato de fecha y que esté en el rango"""
        if not fecha_str or fecha_str.lower() in ['', 'nan', 'none']:
            return None
        
        # Intentar parsear fecha en formato DD/MM/AAAA
        try:
            fecha = datetime.strptime(fecha_str, '%d/%m/%Y').date()
            
            # Validar que esté dentro del rango
            if fecha < self.fecha_desde or fecha > self.fecha_hasta:
                errors.append(f"La fecha {fecha_str} está fuera del rango de la nómina")
                return None
            
            return fecha
        except ValueError:
            errors.append(f"Fecha inválida: debe tener formato DD/MM/AAAA")
            return None
    
    @transaction.atomic
    def _save_temporary_adjustments(self, adjustments_data):
        """Guarda los ajustes temporales en la BD"""
        temp_ids = []
        
        for adj_data in adjustments_data:
            temp_adj = TemporaryPayrollAdjustment.objects.create(
                employee=adj_data['employee'],
                user_creator=self.user,
                adjustment_name=adj_data['adjustment_name'],
                adjustment_type=adj_data['adjustment_type'],
                amount_type=adj_data['amount_type'],
                amount_value=adj_data['amount_value'],
                application_type=adj_data['application_type'],
                start_date_adjustment=adj_data['start_date_adjustment'],
                end_date_adjustment=adj_data['end_date_adjustment'],
                amount=adj_data['amount'],
                description=adj_data['description'],
                status='pending',
            )
            temp_ids.append(temp_adj.id_temp_adjustment)
        return temp_ids
    
    @staticmethod
    def clean_value(value):
        if pd.isna(value):
            return ''
        return str(value).strip()