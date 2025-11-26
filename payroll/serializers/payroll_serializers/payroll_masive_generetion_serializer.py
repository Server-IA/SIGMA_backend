import os
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
import requests
from rest_framework import serializers

from payroll.models.employee import Employee
from payroll.models.employee_contract import EmployeeContract
from payroll.models.employee_contract_deduction import EmployeeContractDeduction
from payroll.models.employee_contract_increase import EmployeeContractIncrease
from payroll.models.employee_news import EmployeeNews
from payroll.models.temporary_payroll_adjustment import TemporaryPayrollAdjustment

from payroll.models import (
    Payroll,
    PayrollDeduction,
    PayrollIncrease
)
from parameterization.models import Types
from users.models import User


class EmployeeAdditionalDeductionSerializer(serializers.ModelSerializer):
    deduction_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.filter(id_types_categories_id=18),
        error_messages={
            "does_not_exist": "El tipo de deducción especificado no existe.",
            "incorrect_type": "El valor proporcionado para el tipo de deducción es incorrecto."
        }
    )

    class Meta:
        model = PayrollDeduction
        fields = [
            "deduction_type",
            "amount_type",
            "amount_value",
            "application_deduction_type",
            "start_date_deduction",
            "end_date_deductions",
            "description",
            "amount",
        ]
        extra_kwargs = {
            "start_date_deduction": {"required": False, "allow_null": True},
            "end_date_deductions": {"required": False, "allow_null": True},
            "description": {"required": False, "allow_null": True},
            "amount_value": {"min_value": 0},
            "amount": {"required": False, "allow_null": True, "min_value": 0},
        }
    
    def validate(self, data):
        sd = data.get("start_date_deduction")
        ed = data.get("end_date_deductions")

        if sd is None and ed is None:
            pass
        elif sd is None and ed is not None:
            raise serializers.ValidationError(
                {"start_date_deduction": "Este campo es obligatorio cuando se especifica end_date_deductions."}
            )
        elif sd is not None and ed is None:
            raise serializers.ValidationError(
                {"end_date_deductions": "Este campo es obligatorio cuando se especifica start_date_deduction."}
            )
        else:
            if sd >= ed:
                raise serializers.ValidationError(
                    {"end_date_deductions": "La fecha de fin debe ser posterior a la fecha de inicio."}
                )
        
        if "amount_value" in data and data["amount_value"] < 0:
            raise serializers.ValidationError(
                {"amount_value": "El valor del monto no puede ser negativo."}
            )
        
        if data.get("amount_type") == "Porcentaje" and data.get("amount_value", 0) > 100:
            raise serializers.ValidationError(
                {"amount_value": "El valor del porcentaje no puede ser mayor a 100."}
            )
        
        # Asegurar que amount tenga un valor por defecto
        data.setdefault("amount", 1)
        return data
    

class EmployeeAdditionalIncreaseSerializer(serializers.ModelSerializer):
    increase_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.filter(id_types_categories_id=19),
        error_messages={
            "does_not_exist": "El tipo de incremento especificado no existe.",
            "incorrect_type": "Se esperaba un ID de tipo de incremento válido.",
        },
    )

    class Meta:
        model = PayrollIncrease
        fields = [
            "employee_name",
            "increase_type",
            "amount_type",
            "amount_value",
            "application_increase_type",
            "start_date_increase",
            "end_date_increase",
            "description",
            "amount",
        ]
        extra_kwargs = {
            "start_date_increase": {"required": False, "allow_null": True},
            "end_date_increase": {"required": False, "allow_null": True},
            "description": {"required": False, "allow_null": True},
            "amount_value": {"min_value": 0},
            "amount": {"required": False, "allow_null": True, "min_value": 0},
        }

    def validate(self, data):
        si = data.get("start_date_increase")
        ei = data.get("end_date_increase")

        if si is None and ei is None:
            pass
        elif si is None and ei is not None:
            raise serializers.ValidationError(
                {"start_date_increase": "Este campo es obligatorio cuando se especifica end_date_increase."}
            )
        elif si is not None and ei is None:
            raise serializers.ValidationError(
                {"end_date_increase": "Este campo es obligatorio cuando se especifica start_date_increase."}
            )
        else:
            if si >= ei:
                raise serializers.ValidationError(
                    {"end_date_increase": "La fecha de fin debe ser posterior a la fecha de inicio."}
                )

        if "amount_value" in data and data["amount_value"] < 0:
            raise serializers.ValidationError({"amount_value": "El valor no puede ser negativo."})

        if data.get("amount_type") == "Porcentaje" and data.get("amount_value", 0) > 100:
            raise serializers.ValidationError(
                {"amount_value": "El valor no puede ser mayor a 100 cuando el tipo es porcentaje."}
            )
        
        # Asegurar que amount tenga un valor por defecto
        data.setdefault("amount", 1)
        return data


class EmployeePayrollDataSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField()
    increases = EmployeeAdditionalIncreaseSerializer(many=True, required=False)
    deductions = EmployeeAdditionalDeductionSerializer(many=True, required=False)

    def validate(self, data):
        # Evitar listas vacías
        data.setdefault("increases", [])
        data.setdefault("deductions", [])
        return data


class PayrollMasiveGenerationSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    id_employee_department = serializers.IntegerField()
    id_employee_charge = serializers.IntegerField()
    exclude_conflicts = serializers.BooleanField(default=False, required=False)
    batch_id = serializers.UUIDField(required=False, allow_null=True)
    employees = EmployeePayrollDataSerializer(many=True)

    def validate(self, data):
        start = data["start_date"]
        end = data["end_date"]

        request = self.context.get('request') if isinstance(self.context, dict) else None


        # Validar fechas
        if start > end:
            raise serializers.ValidationError({
                "end_date": "La fecha de fin debe ser igual o posterior a la fecha de inicio."
            })

        # Validar que haya empleados
        if not data.get("employees", []):
            raise serializers.ValidationError({
                "employees": "Debe proporcionar al menos un empleado."
            })
        
        # Validar que batch_id exista y tenga ajustes vigentes
        batch_id = data.get("batch_id")
        if batch_id:
            adjustments = TemporaryPayrollAdjustment.objects.filter(
                batch_id=batch_id,
                status='pending',
                expires_at__gt=timezone.now()
            )
            
            if not adjustments.exists():
                raise serializers.ValidationError({
                    "batch_id": "El lote de ajustes especificado no existe, ya expiró o fue procesado."
                })
        
        employee_ids = [emp_data["employee_id"] for emp_data in data["employees"]]
        existing_employee_ids = set(Employee.objects.filter(id_employee__in=employee_ids).values_list('id_employee', flat=True))
        
        # Diccionario para acumular todos los conflictos/rechazos
        rejected_employees = {}
        
        # Validar existencia de empleados
        for emp_id in employee_ids:
            if emp_id not in existing_employee_ids:
                employee_name = f"ID {emp_id}"
                rejected_employees[emp_id] = {
                    "employee_id": emp_id,
                    "employee_name": employee_name,
                    "reason": "El empleado no existe en el sistema."
                }

        base_auth_url = os.getenv('AUTH_SERVICE_URL', '').rstrip('/')
        if base_auth_url:
            url = f"{base_auth_url}/users/users/basic-user-list/by-ids"
            headers = {}
            
            auth_header = getattr(request, 'META', {}).get('HTTP_AUTHORIZATION') if request is not None else None
            if not auth_header and hasattr(request, 'headers'):
                auth_header = request.headers.get('Authorization')
            if auth_header:
                headers['Authorization'] = auth_header
            try:
                resp = requests.post(url, json={'ids': employee_ids}, headers=headers, timeout=10)
                if resp.status_code == 200:
                    payload = resp.json()
                    users_data = payload.get('data', []) or []
                    
                    names_map = {}
                    for u in users_data:
                        id = u.get('id')
                        name = u.get('name') or ''
                        fln = u.get('first_last_name') or ''
                        sln = u.get('second_last_name') or ''
                        full = ' '.join([p for p in [name, fln, sln] if p]).strip()
                        names_map[id] = full

                    # Actualizar employees_data con full_name
                    for emp in data:
                        emp_id = emp.get("employee_id")
                        if emp_id in names_map:
                            emp["full_name"] = names_map[emp_id]

                else:
                    for emp in data.get("employees", []):
                        emp.setdefault("full_name", "")
            except Exception:
                for emp in data.get("employees", []):
                    emp.setdefault("full_name", "")
        
        employees_map = {emp["employee_id"]: emp for emp in data.get("employees", [])}
        
        # Validar contratos activos en cargo/departamento
        for emp_id in employee_ids:
            if emp_id in rejected_employees:
                continue  # Ya fue rechazado
            is_active = Employee.objects.filter(
                id_employee=emp_id,
                employee_status=1
            ).exists()

            if not is_active:
                emp_data = employees_map.get(emp_id, {})
                employee_name = emp_data.get("full_name") or emp_data.get("employee_name") or f"ID {emp_id}"

                rejected_employees[emp_id] = {
                    "employee_id": emp_id,
                    "employee_name": employee_name,
                    "reason": "El empleado está inactivo en el sistema."
                }


            has_valid_contract = EmployeeContract.objects.filter(
                id_employee=emp_id,
                id_employee_charge=data['id_employee_charge'],
                id_employee_department=data['id_employee_department'],
                contract_status=28,
                start_date__lte=end,
            ).filter(
                Q(end_date__gte=start) | Q(end_date__isnull=True)
            ).exists()

            if not has_valid_contract:
                emp_data = employees_map.get(emp_id, {})
                employee_name = emp_data.get("full_name") or emp_data.get("employee_name") or f"ID {emp_id}"

                rejected_employees[emp_id] = {
                    "employee_id": emp_id,
                    "employee_name": employee_name,
                    "reason": "No tiene un contrato activo en el cargo/departamento especificado durante el periodo seleccionado."
                }
        
        # Verificar nóminas con fechas solapadas
        for emp_id in employee_ids:
            if emp_id in rejected_employees:
                continue
            
            conflicting = Payroll.objects.filter(
                id_employee_id=emp_id,
            ).filter(
                Q(start_date__lte=end, end_date__gte=start) 
            ).exists()
            
            if conflicting:
                emp_data = employees_map.get(emp_id, {})
                employee_name = emp_data.get("full_name") or emp_data.get("employee_name") or f"ID {emp_id}"

                rejected_employees[emp_id] = {
                    "employee_id": emp_id,
                    "employee_name": employee_name,
                    "reason": "Ya tiene una nómina que se solapa con el periodo seleccionado."
                }
        
        # Si hay empleados rechazados y no se ha solicitado excluirlos
        if rejected_employees and not data.get("exclude_conflicts", False):
            raise serializers.ValidationError({
                "employees": {
                    "rejected": list(rejected_employees.values()),
                    "message": "Los siguientes empleados no pueden ser procesados. Puede descartarlos y reenviar la solicitud.",
                    "action_required": "Envíe nuevamente la solicitud con 'exclude_conflicts: true' para procesar solo los empleados válidos."
                }
            })
        
        # Si se solicitó excluir conflictos, filtrar empleados rechazados
        if data.get("exclude_conflicts", False):
            data["employees"] = [
                emp_data for emp_data in data["employees"]
                if emp_data["employee_id"] not in rejected_employees
            ]
            
            # Validar que queden empleados después de filtrar
            if not data["employees"]:
                raise serializers.ValidationError({
                    "employees": "Después de excluir los empleados rechazados, no quedan empleados válidos para procesar.",
                    "rejected": list(rejected_employees.values())
                })
        
        return data

    @transaction.atomic
    def create(self, validated_data):
        employees_data = validated_data.pop('employees', [])
        id_employee_department = validated_data.pop('id_employee_department', None)
        id_employee_charge = validated_data.pop('id_employee_charge', None)
        exclude_conflicts = validated_data.pop('exclude_conflicts', False)
        batch_id = validated_data.pop('batch_id', None)

        start_date = validated_data['start_date']
        end_date = validated_data['end_date']

        # Obtener el usuario autenticado
        request = self.context.get('request')
        id_responsible_user = None
        if request and hasattr(request, 'user'):
            try:
                if hasattr(request.user, 'id'):
                    id_responsible_user = User.objects.get(pk=request.user.id)
            except User.DoesNotExist:
                pass
        
        created_payrolls = []
        rejected_employees = {}
        
        for emp_data in employees_data:
            if emp_data["employee_id"] in rejected_employees:
                continue
            employee_id = emp_data["employee_id"]
            employee_full_name = emp_data["full_name"]
            
            try:
                employee_contract = self._get_valid_contract(
                    employee_id, start_date, end_date, 
                    id_employee_charge, id_employee_department
                )
                if not employee_contract:
                    rejected_employees[employee_id] = {
                        "employee_id": employee_id,
                        "employee_name": employee_full_name,
                        "reason": "No tiene un contrato activo en el periodo seleccionado."
                    }
                
                time_worked = self._calculate_time_worked(employee_contract, start_date, end_date)
                
                # Crear nómina
                payroll = Payroll.objects.create(
                    id_employee_id=employee_id,
                    id_employee_contract=employee_contract,
                    base_salary=employee_contract.salary_base,
                    start_date=start_date,
                    end_date=end_date,
                    creation_date=timezone.now(),
                    time_worked=time_worked,
                    currency_type = employee_contract.currency_type,
                    id_responsible_user=id_responsible_user,
                )

                # Procesar incrementos y deducciones del contrato
                contract_increases = self._get_applicable_contract_increases(
                    employee_contract, start_date, end_date
                )
                contract_deductions = self._get_applicable_contract_deductions(
                    employee_contract, start_date, end_date
                )

                # Crear incrementos del contrato
                for contract_inc in contract_increases:
                    PayrollIncrease.objects.create(
                        payroll=payroll,
                        increase_type=contract_inc.increase_type,
                        amount_type=contract_inc.amount_type,
                        amount_value=contract_inc.amount_value,
                        application_increase_type=contract_inc.application_increase_type,
                        start_date_increase=contract_inc.start_date_increase,
                        end_date_increase=contract_inc.end_date_increase,
                        description=contract_inc.description,
                        amount=contract_inc.amount,
                        calculated_amount=0.0,
                    )

                # Crear deducciones del contrato
                for contract_ded in contract_deductions:
                    PayrollDeduction.objects.create(
                        payroll=payroll,
                        deduction_type=contract_ded.deduction_type,
                        amount_type=contract_ded.amount_type,
                        amount_value=contract_ded.amount_value,
                        application_deduction_type=contract_ded.application_deduction_type,
                        start_date_deduction=contract_ded.start_date_deduction,
                        end_date_deductions=contract_ded.end_date_deductions,
                        description=contract_ded.description,
                        amount=contract_ded.amount,
                        calculated_amount=0.0,
                    )

                # Procesar ajustes temporales del batch_id
                if batch_id:
                    temp_adjustments = TemporaryPayrollAdjustment.objects.filter(
                        batch_id=batch_id,
                        id_employee_id=employee_id,
                        status='pending',
                        expires_at__gt=timezone.now()
                    )
                    
                    for adj in temp_adjustments:
                        if adj.adjustment_type == 'incremento':
                            # Obtener el tipo de incremento basado en adjustment_name
                            try:
                                increase_type = Types.objects.get(
                                    id_types_categories_id=19,
                                    name=adj.adjustment_name
                                )
                            except Types.DoesNotExist:
                                continue
                            
                            PayrollIncrease.objects.create(
                                payroll=payroll,
                                increase_type=increase_type,
                                amount_type=adj.amount_type,
                                amount_value=adj.amount_value,
                                application_increase_type=adj.application_type,
                                start_date_increase=adj.start_date_adjustment,
                                end_date_increase=adj.end_date_adjustment,
                                description=adj.description,
                                amount=adj.amount,
                                calculated_amount=0.0,
                            )
                        
                        elif adj.adjustment_type == 'deduccion':
                            try:
                                deduction_type = Types.objects.get(
                                    id_types_categories_id=18,
                                    name=adj.adjustment_name
                                )
                            except Types.DoesNotExist:
                                continue
                            
                            PayrollDeduction.objects.create(
                                payroll=payroll,
                                deduction_type=deduction_type,
                                amount_type=adj.amount_type,
                                amount_value=adj.amount_value,
                                application_deduction_type=adj.application_type,
                                start_date_deduction=adj.start_date_adjustment,
                                end_date_deductions=adj.end_date_adjustment,
                                description=adj.description,
                                amount=adj.amount,
                                calculated_amount=0.0,
                            )
                        
                        # Marcar ajuste como confirmado
                        adj.status = 'confirmed'
                        adj.save()
                
                # Crear incrementos y deducciones adicionales del request
                increases_data = emp_data.get('increases', [])
                deductions_data = emp_data.get('deductions', [])
                
                for inc_data in increases_data:
                    PayrollIncrease.objects.create(
                        payroll=payroll,
                        calculated_amount=0.0,
                        **inc_data
                    )
                
                for ded_data in deductions_data:
                    PayrollDeduction.objects.create(
                        payroll=payroll,
                        calculated_amount=0.0,
                        **ded_data
                    )
                
                # Calcular totales
                payroll = self._calculate_payroll_totals(payroll)
                
                # Validar pago neto
                if payroll.net_pay < 0:
                    # eliminar aumentos
                    PayrollIncrease.objects.filter(payroll=payroll).delete()

                    # eliminar deducciones
                    PayrollDeduction.objects.filter(payroll=payroll).delete()
                    payroll.delete()
                    
                    rejected_employees[employee_id] = {
                        "employee_id": employee_id,
                        "employee_name": employee_full_name,
                        "reason": f"El cálculo resulta en un pago neto negativo (${payroll.net_pay:.2f})."
                    }
                
                payroll.save()
                
                # Registrar novedad de generación de nómina
                employee = Employee.objects.get(id_employee=employee_id)
                
                observation = (
                    f"Nómina masiva generada para {employee_full_name}"
                    f"({start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}). "
                )
                
                if batch_id:
                    observation += f" Ajustes aplicados desde lote: {batch_id}."
                
                EmployeeNews.objects.create(
                    id_employee=employee,
                    observation=observation,
                    news_type='GENERACION_NOMINA',  # Asumiendo que agregarás este tipo
                    id_responsible_user=id_responsible_user
                )
                
                created_payrolls.append(payroll)
                
            except Exception as e:
                # Capturar cualquier otro error inesperado
                
                rejected_employees[employee_id] ={
                    "employee_id": employee_id,
                    "employee_name": employee_full_name,
                    "reason": f"Error durante la generación: {str(e)}"
                }

        if rejected_employees and not exclude_conflicts:
            raise serializers.ValidationError({
                "employees": {
                    "rejected": list(rejected_employees.values()),
                    "message": "Los siguientes empleados no pueden ser procesados. Puede descartarlos y reenviar la solicitud.",
                    "action_required": "Envíe nuevamente la solicitud con 'exclude_conflicts: true' para procesar solo los empleados válidos."
                }
            })
        
        return created_payrolls

    def _get_valid_contract(self, employee_id, start, end, charge_id, dept_id):
        contract = EmployeeContract.objects.filter(
            id_employee_id=employee_id,
            id_employee_charge=charge_id,
            id_employee_department=dept_id,
            contract_status=28,
            start_date__lte=end,
        ).filter(
            Q(end_date__gte=start) | Q(end_date__isnull=True)
        ).first()

        return contract
    
    def _get_applicable_contract_increases(self, contract, start_date, end_date):
        """Obtiene los incrementos del contrato que aplican para el periodo de nómina."""
        increases = EmployeeContractIncrease.objects.filter(
            employee_contracts_contract_code=contract.contract_code,
        )

        applicable_increases = []
        for increase in increases:
            # Si no tiene fechas, siempre aplica
            if increase.start_date_increase is None and increase.end_date_increase is None:
                applicable_increases.append(increase)
                continue
            
            if increase.start_date_increase and increase.end_date_increase:
                if (increase.start_date_increase <= end_date and 
                    increase.end_date_increase >= start_date):
                    applicable_increases.append(increase)
            elif increase.start_date_increase:
                if increase.start_date_increase <= end_date:
                    applicable_increases.append(increase)
            elif increase.end_date_increase:
                if increase.end_date_increase >= start_date:
                    applicable_increases.append(increase)

        return applicable_increases
    
    def _get_applicable_contract_deductions(self, contract, start_date, end_date):
        """Obtiene las deducciones del contrato que aplican para el periodo de nómina."""
        deductions = EmployeeContractDeduction.objects.filter(
            employee_contracts_contract_code=contract.contract_code,
        )

        applicable_deductions = []
        for deduction in deductions:
            # Si no tiene fechas, siempre aplica
            if deduction.start_date_deduction is None and deduction.end_date_deductions is None:
                applicable_deductions.append(deduction)
                continue
            # Si tiene fechas, verificar que el periodo de nómina esté dentro del rango
            if deduction.start_date_deduction and deduction.end_date_deductions:
                if (deduction.start_date_deduction <= end_date and 
                    deduction.end_date_deductions >= start_date):
                    applicable_deductions.append(deduction)
            elif deduction.start_date_deduction:
                if deduction.start_date_deduction <= end_date:
                    applicable_deductions.append(deduction)
            elif deduction.end_date_deductions:
                if deduction.end_date_deductions >= start_date:
                    applicable_deductions.append(deduction)

        return applicable_deductions
    
    def _calculate_time_worked(self, contract, start_date, end_date):
        """
        Calcula tiempo trabajado según tipo de salario:
        - Por horas: suma horas de días laborables
        - Por días: cuenta días laborables
        - Mensual fijo: fracción del mes (días/30)
        """
        time_worked = 0.0
        days_of_week = contract.days_of_week.all().values_list('id_day_of_week', flat=True)
        total_days = (end_date - start_date).days + 1

        for day_offset in range(total_days):
            current_date = start_date + timezone.timedelta(days=day_offset)
            if current_date.isoweekday() in days_of_week:
                if contract.salary_type == 'Por horas':
                    time_worked += contract.working_hours if contract.working_hours else 8
                elif contract.salary_type == 'Por días':
                    time_worked += 1
                elif contract.salary_type == 'Mensual fijo':
                    time_worked = total_days / 30
                    break

        return time_worked

    def _calculate_payroll_totals(self, payroll):
        """
        Calcula totales de nómina en 4 fases:
        1. Incrementos sobre salario base
        2. Deducciones sobre salario base
        3. Incrementos sobre salario ajustado
        4. Deducciones sobre salario ajustado
        """
        base_salary = payroll.base_salary * payroll.time_worked

        # Fase 1: Incrementos sobre salario base
        increases_base = payroll.payroll_increases.filter(
            application_increase_type='SalarioBase'
        )

        total_increases_base = 0
        for increase in increases_base:
            amount = getattr(increase, 'amount', 1) or 1

            if increase.amount_type == 'Porcentaje':
                calculated_amount = (base_salary * increase.amount_value / 100) * amount
            else:
                calculated_amount = increase.amount_value * amount

            increase.calculated_amount = calculated_amount
            increase.save()
            total_increases_base += calculated_amount

        # Fase 2: Deducciones sobre salario base
        deductions_base = payroll.payroll_deductions.filter(
            application_deduction_type='SalarioBase'
        )

        total_deductions_base = 0
        for deduction in deductions_base:
            amount = getattr(deduction, 'amount', 1) or 1

            if deduction.amount_type == 'Porcentaje':
                calculated_amount = (base_salary * deduction.amount_value / 100) * amount
            else:
                calculated_amount = deduction.amount_value * amount

            deduction.calculated_amount = calculated_amount
            deduction.save()
            total_deductions_base += calculated_amount

        # Salario después de ajustes base
        salary_after_base_adjustments = base_salary + total_increases_base - total_deductions_base

        # Fase 3: Incrementos sobre salario final
        increases_final = payroll.payroll_increases.filter(
            application_increase_type='SalarioFinal'
        )

        total_increases_final = 0
        for increase in increases_final:
            amount = getattr(increase, 'amount', 1) or 1

            if increase.amount_type == 'Porcentaje':
                calculated_amount = (salary_after_base_adjustments * increase.amount_value / 100) * amount
            else:
                calculated_amount = increase.amount_value * amount
            
            increase.calculated_amount = calculated_amount
            increase.save()
            total_increases_final += calculated_amount

        # Fase 4: Deducciones sobre salario final
        deductions_final = payroll.payroll_deductions.filter(
            application_deduction_type='SalarioFinal'
        )

        total_deductions_final = 0
        for deduction in deductions_final:
            amount = getattr(deduction, 'amount', 1) or 1

            if deduction.amount_type == 'Porcentaje':
                calculated_amount = (salary_after_base_adjustments * deduction.amount_value / 100) * amount
            else:
                calculated_amount = deduction.amount_value * amount

            deduction.calculated_amount = calculated_amount
            deduction.save()
            total_deductions_final += calculated_amount

        # Totales finales
        payroll.total_increments = total_increases_base + total_increases_final
        payroll.total_deductions = total_deductions_base + total_deductions_final
        payroll.net_pay = base_salary + payroll.total_increments - payroll.total_deductions
        
        return payroll