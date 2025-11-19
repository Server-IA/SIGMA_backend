from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from django.db.models import Max
import re

from payroll.models import (
    EstablishedContract, 
    ContractPaymentsEstablishedContract,
    EstablishedDeduction,
    EstablishedIncrease
)
from parameterization.models import (
    EmployeeCharge, 
    Types, 
    Units, 
    Statues
)
from users.models import User

class ContractPaymentEstablishedContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractPaymentsEstablishedContract
        fields = ['date_payment', 'id_day_of_week']
        extra_kwargs = {
            'date_payment': {'required': False, 'allow_null': True},
            'id_day_of_week': {'required': False, 'allow_null': True}
        }

class EstablishedDeductionSerializer(serializers.ModelSerializer):
    deduction_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.filter(id_types_categories_id=18),
        error_messages={
            'does_not_exist': 'El tipo de deducción especificado no existe.',
            'incorrect_type': 'Se esperaba un ID de tipo de deducción válido.'
        }
    )
    
    def to_internal_value(self, data):
        if isinstance(data, dict):
            raw = data.get('deduction_type')
            if isinstance(raw, dict):
                for key in ('id', 'id_types', 'pk'):
                    if key in raw:
                        data['deduction_type'] = raw[key]
                        break
        return super().to_internal_value(data)
    
    class Meta:
        model = EstablishedDeduction
        fields = [
            'deduction_type', 'amount_type', 'amount_value', 
            'application_deduction_type', 'start_date_deduction', 
            'end_date_deductions', 'description', 'amount'
        ]
        extra_kwargs = {
            'start_date_deduction': {'required': False, 'allow_null': True},
            'end_date_deductions': {'required': False, 'allow_null': True},
            'description': {'required': False, 'allow_null': True},
            'amount_value': {'min_value': 0},
            'amount': {'min_value': 0}
        }
        
    def validate(self, data):
        # Mapear end_date_deduction a end_date_deductions si es necesario
        if 'end_date_deduction' in data and 'end_date_deductions' not in data:
            data['end_date_deductions'] = data.pop('end_date_deduction')

        sd = data.get('start_date_deduction')
        ed = data.get('end_date_deductions')

        # Validar presencia condicional de fechas (permitir ambos None)
        if sd is None and ed is None:
            pass
        elif sd is None and ed is not None:
            raise serializers.ValidationError({"start_date_deduction": "Este campo es obligatorio cuando se especifica end_date_deductions."})
        elif sd is not None and ed is None:
            raise serializers.ValidationError({"end_date_deductions": "Este campo es obligatorio cuando se especifica start_date_deduction."})
        else:
            # Ambos presentes: validar orden
            if sd >= ed:
                raise serializers.ValidationError({"end_date_deductions": "La fecha de fin debe ser posterior a la fecha de inicio."})
        
        if 'amount_value' in data and data['amount_value'] < 0:
            raise serializers.ValidationError({"amount_value": "El valor no puede ser negativo."})
            
        if 'amount' in data and data['amount'] is not None and data['amount'] < 0:
            raise serializers.ValidationError({"amount": "El monto no puede ser negativo."})
        
        if data.get('amount_type') == 'Porcentaje' and data.get('amount_value', 0) > 100:
            raise serializers.ValidationError({"amount_value": "El valor no puede ser mayor a 100 cuando el tipo es porcentaje."})
        
        return data

class EstablishedIncreaseSerializer(serializers.ModelSerializer):
    increase_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.filter(id_types_categories_id=19),
        error_messages={
            'does_not_exist': 'El tipo de incremento especificado no existe.',
            'incorrect_type': 'Se esperaba un ID de tipo de incremento válido.'
        }
    )
    
    def to_internal_value(self, data):
        if isinstance(data, dict):
            raw = data.get('increase_type')
            if isinstance(raw, dict):
                for key in ('id', 'id_types', 'pk'):
                    if key in raw:
                        data['increase_type'] = raw[key]
                        break
        return super().to_internal_value(data)
    
    class Meta:
        model = EstablishedIncrease
        fields = [
            'increase_type', 'amount_type', 'amount_value', 
            'application_increase_type', 'start_date_increase', 
            'end_date_increase', 'description', 'amount'
        ]
        extra_kwargs = {
            'start_date_increase': {'required': False, 'allow_null': True},
            'end_date_increase': {'required': False, 'allow_null': True},
            'description': {'required': False, 'allow_null': True},
            'amount_value': {'min_value': 0},
            'amount': {'min_value': 0}
        }
        
    def validate(self, data):
        si = data.get('start_date_increase')
        ei = data.get('end_date_increase')

        # Validar presencia condicional de fechas (permitir ambos None)
        if si is None and ei is None:
            pass
        elif si is None and ei is not None:
            raise serializers.ValidationError({"start_date_increase": "Este campo es obligatorio cuando se especifica end_date_increase."})
        elif si is not None and ei is None:
            raise serializers.ValidationError({"end_date_increase": "Este campo es obligatorio cuando se especifica start_date_increase."})
        else:
            # Ambos presentes: validar orden
            if si >= ei:
                raise serializers.ValidationError({"end_date_increase": "La fecha de fin debe ser posterior a la fecha de inicio."})
        
        if 'amount_value' in data and data['amount_value'] < 0:
            raise serializers.ValidationError({"amount_value": "El valor no puede ser negativo."})
            
        if 'amount' in data and data['amount'] is not None and data['amount'] < 0:
            raise serializers.ValidationError({"amount": "El monto no puede ser negativo."})
        
        if data.get('amount_type') == 'Porcentaje' and data.get('amount_value', 0) > 100:
            raise serializers.ValidationError({"amount_value": "El valor no puede ser mayor a 100 cuando el tipo es porcentaje."})
        
        return data

class EstablishedContractCreateSerializer(serializers.ModelSerializer):
    contract_payments = ContractPaymentEstablishedContractSerializer(many=True, required=False)
    established_deductions = EstablishedDeductionSerializer(many=True, required=False)
    established_increases = EstablishedIncreaseSerializer(many=True, required=False)

    class Meta:
        model = EstablishedContract
        fields = [
            'contract_code', 'id_employee_charge', 'description', 'contract_type', 
            'start_date', 'end_date', 'payment_frequency_type', 'contract_payments',
            'minimum_hours', 'workday_type', 'work_mode_type', 'salary_type',
            'salary_base', 'currency_type', 'trial_period_days', 'vacation_days',
            'cumulative_vacation', 'start_cumulative_vacation', 'vacation_frequency_days',
            'maximum_disability_days', 'overtime', 'overtime_period', 'notice_period_days',
            'established_deductions', 'established_increases'
        ]
        read_only_fields = ['contract_code', 'creation_date', 'modification_date', 'id_responsible_user', 'established_contract_status']
        extra_kwargs = {
            'description': {'required': False, 'allow_blank': True, 'allow_null': True},
            'minimum_hours': {'required': False, 'allow_null': True},
            'trial_period_days': {'required': False, 'allow_null': True},
            'vacation_frequency_days': {'required': False, 'allow_null': True},
            'overtime_period': {'required': False, 'allow_null': True},
            'notice_period_days': {'required': False, 'allow_null': True},
            'end_date': {'required': False, 'allow_null': True}
        }

    def validate_id_employee_charge(self, value):
        try:
            employee_charge = EmployeeCharge.objects.get(pk=value.pk)
            return value
        except EmployeeCharge.DoesNotExist:
            raise serializers.ValidationError("El cargo de empleado especificado no existe.")

    def validate_contract_type(self, value):
        if value.id_types_categories_id != 15:
            raise serializers.ValidationError("El tipo de contrato no es válido.")
        return value

    def validate_workday_type(self, value):
        if value.id_types_categories_id != 16:
            raise serializers.ValidationError("El tipo de jornada no es válido.")
        return value

    def validate_work_mode_type(self, value):
        if value.id_types_categories_id != 17:
            raise serializers.ValidationError("El modo de trabajo no es válido.")
        return value

    def validate_currency_type(self, value):
        if value.id_units_categories_id != 10:
            raise serializers.ValidationError("El tipo de moneda no es válido.")
        return value
        
    def validate_minimum_hours(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Las horas mínimas no pueden ser negativas.")
        return value
        
    def validate_salary_base(self, value):
        if value < 0:
            raise serializers.ValidationError("El salario base no puede ser negativo.")
        return value
        
    def validate_trial_period_days(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("El período de prueba no puede ser negativo.")
        return value
        
    def validate_vacation_days(self, value):
        if value < 0:
            raise serializers.ValidationError("Los días de vacaciones no pueden ser negativos.")
        return value
        
    def validate_vacation_frequency_days(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("La frecuencia de vacaciones no puede ser negativa.")
        return value
        
    def validate_maximum_disability_days(self, value):
        if value < 0:
            raise serializers.ValidationError("Los días máximos de incapacidad no pueden ser negativos.")
        return value
        
    def validate_overtime(self, value):
        if value < 0:
            raise serializers.ValidationError("El valor de horas extras no puede ser negativo.")
        return value
        
    def validate_notice_period_days(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("El período de preaviso no puede ser negativo.")
        return value

    def validate_start_date(self, value):
        return value

    def validate(self, data):
        # Validar fechas
        if 'start_date' in data and 'end_date' in data and data['end_date'] is not None:
            if data['start_date'] >= data['end_date']:
                raise serializers.ValidationError({"end_date": "La fecha de fin debe ser posterior a la fecha de inicio."})
                
        # Validar campos numéricos en el contexto general
        numeric_fields = {
            'minimum_hours': "Las horas mínimas no pueden ser negativas.",
            'salary_base': "El salario base no puede ser negativo.",
            'trial_period_days': "El período de prueba no puede ser negativo.",
            'vacation_days': "Los días de vacaciones no pueden ser negativos.",
            'vacation_frequency_days': "La frecuencia de vacaciones no puede ser negativa.",
            'maximum_disability_days': "Los días máximos de incapacidad no pueden ser negativos.",
            'overtime': "El valor de horas extras no puede ser negativo.",
            'notice_period_days': "El período de preaviso no puede ser negativo."
        }
        
        for field, error_message in numeric_fields.items():
            if field in data and data[field] is not None and data[field] < 0:
                raise serializers.ValidationError({field: error_message})
        
        # Validar fechas de vacaciones acumulativas
        if 'cumulative_vacation' in data:
            if data['cumulative_vacation']:
                if 'start_cumulative_vacation' not in data or not data['start_cumulative_vacation']:
                    raise serializers.ValidationError({
                        "start_cumulative_vacation": "Este campo es obligatorio cuando las vacaciones son acumulativas."
                    })
                
                if 'start_date' in data and data['start_cumulative_vacation'] < data['start_date']:
                    raise serializers.ValidationError({
                        "start_cumulative_vacation": f"La fecha de inicio de acumulación no puede ser anterior a la fecha de inicio del contrato ({data['start_date']})."
                    })
                
                if 'end_date' in data and data['end_date'] is not None and data['start_cumulative_vacation'] > data['end_date']:
                    raise serializers.ValidationError({
                        "start_cumulative_vacation": f"La fecha de inicio de acumulación no puede ser posterior a la fecha de finalización del contrato ({data['end_date']})."
                    })
            else:
                # Si cumulative_vacation es False, ignorar cualquier valor en start_cumulative_vacation
                if 'start_cumulative_vacation' in data:
                    data['start_cumulative_vacation'] = None
        
        # Validar payment_frequency_type y contract_payments
        if 'payment_frequency_type' in data:
            payment_items = self.initial_data.get('contract_payments') or []
            freq = data['payment_frequency_type']

            # Reglas de cantidad de elementos
            if freq in ('diario', 'semanal', 'mensual'):
                if len(payment_items) != 1:
                    raise serializers.ValidationError({"contract_payments": "Debe existir exactamente 1 registro de pago para frecuencia diaria, semanal o mensual."})
            elif freq == 'quincenal':
                if len(payment_items) != 2:
                    raise serializers.ValidationError({"contract_payments": "Para pago quincenal deben existir exactamente 2 registros de pago."})

            # Reglas por tipo de frecuencia
            if freq == 'diario':
                item = payment_items[0]
                if item.get('date_payment') is not None or item.get('id_day_of_week') is not None:
                    raise serializers.ValidationError({"contract_payments": "Para pago diario, no se deben especificar fecha de pago ni día de la semana."})

            elif freq == 'semanal':
                item = payment_items[0]
                if not item.get('id_day_of_week'):
                    raise serializers.ValidationError({"contract_payments": "Para pago semanal, se debe especificar el día de la semana (id_day_of_week)."})
                if item.get('date_payment') is not None:
                    raise serializers.ValidationError({"contract_payments": "Para pago semanal, no se debe especificar fecha de pago."})

            elif freq == 'quincenal':
                d1 = payment_items[0]
                d2 = payment_items[1]
                # id_day_of_week debe ser null en ambos
                if d1.get('id_day_of_week') is not None or d2.get('id_day_of_week') is not None:
                    raise serializers.ValidationError({"contract_payments": "Para pago quincenal, id_day_of_week debe ser nulo en ambos registros."})
                # date_payment requerido en ambos
                if d1.get('date_payment') is None or d2.get('date_payment') is None:
                    raise serializers.ValidationError({"contract_payments": "Para pago quincenal, ambos registros deben especificar date_payment."})
                # valores deben ser distintos
                if d1.get('date_payment') == d2.get('date_payment'):
                    raise serializers.ValidationError({"contract_payments": "Para pago quincenal, los dos date_payment deben ser distintos."})
                # validar rango permitido por modelo (1..31)
                v1 = d1.get('date_payment')
                v2 = d2.get('date_payment')
                for v in (v1, v2):
                    if not isinstance(v, int) or v < 1 or v > 31:
                        raise serializers.ValidationError({"contract_payments": "Para pago quincenal, cada date_payment debe estar entre 1 y 31."})

                # Validar que uno esté en 1-15 y el otro en 16-31
                low = min(v1, v2)
                high = max(v1, v2)
                if not (1 <= low <= 15 and 16 <= high <= 31):
                    raise serializers.ValidationError({
                        "contract_payments": "Para pago quincenal, un date_payment debe estar entre 1-15 y el otro entre 16-31."
                    })

                # Validar diferencia mínima de 15 días entre ambos
                if abs(v1 - v2) < 15:
                    raise serializers.ValidationError({
                        "contract_payments": "Para pago quincenal, la diferencia entre ambos date_payment debe ser de al menos 15 días."
                    })

            elif freq == 'mensual':
                item = payment_items[0]
                v = item.get('date_payment')
                if item.get('id_day_of_week') is not None:
                    raise serializers.ValidationError({"contract_payments": "Para pago mensual, no se debe especificar día de la semana."})
                if not isinstance(v, int) or v < 1 or v > 31:
                    raise serializers.ValidationError({"contract_payments": "Para pago mensual, la fecha de pago debe estar entre 1 y 31."})
        
        # Validar deducciones
        if 'established_deductions' in self.initial_data:
            deduction_types = set()
            for deduction in self.initial_data['established_deductions']:
                if 'deduction_type' in deduction:
                    if deduction['deduction_type'] in deduction_types:
                        raise serializers.ValidationError({"established_deductions": f"No puede haber dos deducciones con el mismo tipo: {deduction['deduction_type']}."})
                    deduction_types.add(deduction['deduction_type'])
        # Validar rangos de fechas de deducciones con respecto al contrato
        contract_start = data.get('start_date')
        contract_end = data.get('end_date')
        if data.get('established_deductions'):
            ded_errors = []
            for d in data.get('established_deductions', []):
                sd = d.get('start_date_deduction')
                ed = d.get('end_date_deductions')
                e = {}
                if sd and not ed:
                    e['end_date_deductions'] = ["Este campo es obligatorio cuando se especifica start_date_deduction."]
                if ed and not sd:
                    e['start_date_deduction'] = ["Este campo es obligatorio cuando se especifica end_date_deductions."]
                if sd and ed:
                    # Validaciones de inicio (prioritarias)
                    if contract_start and sd < contract_start:
                        e['start_date_deduction'] = [f"La fecha de inicio de la deducción no puede ser anterior a la fecha de inicio del contrato ({contract_start})."]
                    elif contract_end and sd > contract_end:
                        e['start_date_deduction'] = [f"La fecha de inicio de la deducción no puede ser posterior a la fecha de finalización del contrato ({contract_end})."]

                    # Solo si no hubo error de inicio, validar fin
                    if 'start_date_deduction' not in e:
                        if contract_start and ed < contract_start:
                            e['end_date_deductions'] = [f"La fecha de fin de la deducción no puede ser anterior a la fecha de inicio del contrato ({contract_start})."]
                        elif contract_end and ed > contract_end:
                            e['end_date_deductions'] = [f"La fecha de fin de la deducción no puede ser posterior a la fecha de finalización del contrato ({contract_end})."]

                    # Solo si no hubo error de inicio ni de fin, validar orden
                    if 'start_date_deduction' not in e and 'end_date_deductions' not in e:
                        if sd >= ed:
                            e['end_date_deductions'] = ["La fecha de fin debe ser posterior a la fecha de inicio."]
                if e:
                    ded_errors.append(e)
            if ded_errors:
                raise serializers.ValidationError({'established_deductions': ded_errors})
        
        # Validar incrementos
        if 'established_increases' in self.initial_data:
            increase_types = set()
            for increase in self.initial_data['established_increases']:
                if 'increase_type' in increase:
                    if increase['increase_type'] in increase_types:
                        raise serializers.ValidationError({"established_increases": f"No puede haber dos incrementos con el mismo tipo: {increase['increase_type']}."})
                    increase_types.add(increase['increase_type'])
        # Validar rangos de fechas de incrementos con respecto al contrato
        if data.get('established_increases'):
            inc_errors = []
            for inc in data.get('established_increases', []):
                si = inc.get('start_date_increase')
                ei = inc.get('end_date_increase')
                e = {}
                if si and not ei:
                    e['end_date_increase'] = ["Este campo es obligatorio cuando se especifica start_date_increase."]
                if ei and not si:
                    e['start_date_increase'] = ["Este campo es obligatorio cuando se especifica end_date_increase."]
                if si and ei:
                    # Validaciones de inicio (prioritarias)
                    if contract_start and si < contract_start:
                        e['start_date_increase'] = [f"La fecha de inicio del incremento no puede ser anterior a la fecha de inicio del contrato ({contract_start})."]
                    elif contract_end and si > contract_end:
                        e['start_date_increase'] = [f"La fecha de inicio del incremento no puede ser posterior a la fecha de finalización del contrato ({contract_end})."]

                    # Solo si no hubo error de inicio, validar fin
                    if 'start_date_increase' not in e:
                        if contract_start and ei < contract_start:
                            e['end_date_increase'] = [f"La fecha de fin del incremento no puede ser anterior a la fecha de inicio del contrato ({contract_start})."]
                        elif contract_end and ei > contract_end:
                            e['end_date_increase'] = [f"La fecha de fin del incremento no puede ser posterior a la fecha de finalización del contrato ({contract_end})."]

                    # Solo si no hubo error de inicio ni de fin, validar orden
                    if 'start_date_increase' not in e and 'end_date_increase' not in e:
                        if si >= ei:
                            e['end_date_increase'] = ["La fecha de fin debe ser posterior a la fecha de inicio."]
                if e:
                    inc_errors.append(e)
            if inc_errors:
                raise serializers.ValidationError({'established_increases': inc_errors})
        
        return data

    def generate_contract_code(self, employee_charge):
        # Obtener el nombre del cargo sin espacios y en mayúsculas
        charge_name = re.sub(r'\s+', '', employee_charge.name).upper() if employee_charge.name else 'CARGO'
        
        # Obtener el último contrato con el mismo prefijo
        last_contract = EstablishedContract.objects.filter(
            contract_code__startswith=f'CON-{charge_name}-'
        ).order_by('-contract_code').first()
        
        if last_contract:
            # Extraer el número y sumar 1
            match = re.search(r'-(\d+)$', last_contract.contract_code)
            if match:
                next_num = int(match.group(1)) + 1
                return f'CON-{charge_name}-{next_num:04d}'
        
        # Si no hay contratos previos, empezar con 1
        return f'CON-{charge_name}-0001'

    @transaction.atomic
    def create(self, validated_data):
        # Extraer los datos de los nested serializers
        contract_payments_data = validated_data.pop('contract_payments', [])
        deductions_data = validated_data.pop('established_deductions', [])
        increases_data = validated_data.pop('established_increases', [])
        
        # Generar el código de contrato
        employee_charge = validated_data['id_employee_charge']
        validated_data['contract_code'] = self.generate_contract_code(employee_charge)
        
        # Establecer valores por defecto
        validated_data['creation_date'] = timezone.now()
        validated_data['modification_date'] = timezone.now()
        
        # Obtener el usuario autenticado
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            from users.models import User
            try:
                # Try to get the actual User instance from the JWTUser
                if hasattr(request.user, 'id'):
                    validated_data['id_responsible_user'] = User.objects.get(pk=request.user.id)
            except User.DoesNotExist:
                # If user doesn't exist, use a default user or raise an error
                validated_data['id_responsible_user'] = None
        
        # Establecer el estado del contrato como activo (1)
        try:
            status = Statues.objects.get(pk=1)
            validated_data['established_contract_status'] = status
        except Statues.DoesNotExist:
            raise serializers.ValidationError({"established_contract_status": "El estado del contrato no es válido."})
        
        # Crear el contrato
        contract = EstablishedContract.objects.create(**validated_data)
        
        # Procesar pagos del contrato según la frecuencia
        self.process_contract_payments(contract, contract_payments_data, validated_data['payment_frequency_type'])
        
        # Crear deducciones
        if deductions_data:
            for d in deductions_data:
                EstablishedDeduction.objects.create(
                    established_contracts_contract_code=contract,
                    **d
                )
        
        # Crear incrementos
        if increases_data:
            for inc in increases_data:
                EstablishedIncrease.objects.create(
                    established_contracts_contract_code=contract,
                    **inc
                )
        
        return contract
    
    def process_contract_payments(self, contract, payments_data, payment_frequency_type):
        if payment_frequency_type == 'diario':
            # Debe haber exactamente 1 item; crear registro con ambos campos en null
            ContractPaymentsEstablishedContract.objects.create(
                established_contracts_contract_code=contract,
                date_payment=None,
                id_day_of_week=None
            )
        elif payment_frequency_type == 'semanal':
            # Debe haber exactamente 1 item; crear registro con el día de la semana
            payment_data = payments_data[0]
            ContractPaymentsEstablishedContract.objects.create(
                established_contracts_contract_code=contract,
                date_payment=None,
                id_day_of_week=payment_data['id_day_of_week']
            )
        elif payment_frequency_type == 'quincenal':
            # Deben existir exactamente 2 items; crear registros con los date_payment provistos
            for payment_data in payments_data:
                ContractPaymentsEstablishedContract.objects.create(
                    established_contracts_contract_code=contract,
                    date_payment=payment_data['date_payment'],
                    id_day_of_week=None
                )
        elif payment_frequency_type == 'mensual':
            # Debe haber exactamente 1 item; crear registro con ese día del mes
            payment_data = payments_data[0]
            ContractPaymentsEstablishedContract.objects.create(
                established_contracts_contract_code=contract,
                date_payment=payment_data['date_payment'],
                id_day_of_week=None
            )
