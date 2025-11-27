from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.db.models import Q
from rest_framework import serializers
from payroll.models import (
    Employee, EmployeeContract, Payroll, PayrollDeduction, PayrollIncrease,
    EmployeeContractDeduction, EmployeeContractIncrease, DaysOfWeek
)
from parameterization.models import Types
from users.models import User

class PayrollDeductionSerializer(serializers.ModelSerializer):
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
            "deduction_type", "amount_type", "amount_value",
            "application_deduction_type", "start_date_deduction",
            "end_date_deductions", "description", "amount"
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

        if sd is None and ed is not None:
            raise serializers.ValidationError(
                {"start_date_deduction": "Este campo es obligatorio cuando se especifica end_date_deductions."}
            )
        elif sd is not None and ed is None:
            raise serializers.ValidationError(
                {"end_date_deductions": "Este campo es obligatorio cuando se especifica start_date_deduction."}
            )
        elif sd and ed and sd >= ed:
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
        
        data.setdefault("amount", 1)
        return data


class PayrollIncreaseSerializer(serializers.ModelSerializer):
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
            "increase_type", "amount_type", "amount_value",
            "application_increase_type", "start_date_increase",
            "end_date_increase", "description", "amount"
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

        if si is None and ei is not None:
            raise serializers.ValidationError(
                {"start_date_increase": "Este campo es obligatorio cuando se especifica end_date_increase."}
            )
        elif si is not None and ei is None:
            raise serializers.ValidationError(
                {"end_date_increase": "Este campo es obligatorio cuando se especifica start_date_increase."}
            )
        elif si and ei and si >= ei:
            raise serializers.ValidationError(
                {"end_date_increase": "La fecha de fin debe ser posterior a la fecha de inicio."}
            )

        if "amount_value" in data and data["amount_value"] < 0:
            raise serializers.ValidationError(
                {"amount_value": "El valor no puede ser negativo."}
            )

        if data.get("amount_type") == "Porcentaje" and data.get("amount_value", 0) > 100:
            raise serializers.ValidationError(
                {"amount_value": "El valor no puede ser mayor a 100 cuando el tipo es porcentaje."}
            )
        
        data.setdefault("amount", 1)
        return data


class PayrollCreateSerializer(serializers.ModelSerializer):
    id_employee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.filter(employee_status=1),
        error_messages={
            "does_not_exist": "El empleado especificado no existe o no está activo.",
            "incorrect_type": "Se esperaba un ID de empleado válido.",
        }
    )
    contract_code = serializers.CharField(write_only=True)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    additional_deductions = PayrollDeductionSerializer(many=True, required=False, default=list)
    additional_increases = PayrollIncreaseSerializer(many=True, required=False, default=list)

    class Meta:
        model = Payroll
        fields = [
            "id_employee", "contract_code", "start_date", "end_date",
            "additional_deductions", "additional_increases"
        ]

    def validate_deductions(self, data):
        """
        Validates the deductions according to the specified rules:
        1. For 'Porcentaje' and 'SalarioBase' deductions, sum of amount_value <= 100
        2. For 'Porcentaje' and 'SalarioFinal' deductions, sum of amount_value <= 100
        3. For 'fijo' and 'SalarioBase' deductions, sum of amount_value <= salary_base
        """
        deductions = data.get('additional_deductions', [])
        contract = data.get('contract')
        
        if not contract or not deductions:
            return data
            
        # Group deductions by application type and amount type
        base_percent_deductions = []
        final_percent_deductions = []
        fixed_base_deductions = []
        
        for d in deductions:
            if not isinstance(d, dict):
                d = d.initial_data if hasattr(d, 'initial_data') else {}
                
            amount_type = d.get('amount_type')
            app_type = d.get('application_deduction_type')
            amount_value = float(d.get('amount_value', 0))
            
            if amount_type == 'Porcentaje':
                if app_type == 'SalarioBase':
                    base_percent_deductions.append(amount_value)
                elif app_type == 'SalarioFinal':
                    final_percent_deductions.append(amount_value)
            elif amount_type == 'fijo' and app_type == 'SalarioBase':
                amount = float(d.get('amount', 1))
                fixed_base_deductions.append(amount_value * amount)
        
        # Validate SalarioBase percentage deductions
        total_base_percent = sum(base_percent_deductions)
        if total_base_percent > 100:
            raise serializers.ValidationError({
                "additional_deductions": [{
                    "amount_value": f"La suma de los porcentajes de deducción para SalarioBase no puede superar el 100%. "
                                  f"Total actual: {total_base_percent}%"
                }]
            })
        
        # Validate SalarioFinal percentage deductions
        total_final_percent = sum(final_percent_deductions)
        if total_final_percent > 100:
            raise serializers.ValidationError({
                "additional_deductions": [{
                    "amount_value": f"La suma de los porcentajes de deducción para SalarioFinal no puede superar el 100%. "
                                  f"Total actual: {total_final_percent}%"
                }]
            })
        
        # Validate fixed amount deductions against salary base
        if fixed_base_deductions and hasattr(contract, 'salary_base'):
            total_fixed_deductions = sum(fixed_base_deductions)
            if total_fixed_deductions > contract.salary_base:
                raise serializers.ValidationError({
                    "additional_deductions": [{
                        "amount_value": f"La suma de las deducciones fijas para SalarioBase no puede superar el salario base. "
                                      f"Total deducciones: {total_fixed_deductions}, Salario base: {contract.salary_base}"
                    }]
                })
        
        return data

    def validate(self, data):
        start_date = data["start_date"]
        end_date = data["end_date"]
        contract_code = data["contract_code"]
        employee = data["id_employee"]
        
        # Get contract first to validate deductions
        contract_code = data["contract_code"]
        employee = data["id_employee"]
        base_code = "-".join(contract_code.split("-")[:3])
        contracts = EmployeeContract.objects.filter(
            contract_code__startswith=base_code,
            id_employee=employee
        ).order_by("-contract_code")

        if not contracts.exists():
            raise serializers.ValidationError({
                "contract_code": f"No se encontró un contrato con el código {contract_code} para el empleado."
            })

        contract = contracts.first()
        data["contract"] = contract
        
        # Validate deductions with contract data
        if 'additional_deductions' in data:
            self.validate_deductions({
                'additional_deductions': data['additional_deductions'],
                'contract': contract
            })

        # Validar fechas
        if start_date > end_date:
            raise serializers.ValidationError({"end_date": "La fecha de fin debe ser posterior a la fecha de inicio"})
            
        # Validar que no haya tipos de deducción duplicados
        additional_deductions = data.get('additional_deductions', [])
        deduction_types = set()
        for i, deduction in enumerate(additional_deductions):
            if isinstance(deduction, dict):
                ded_type = deduction.get('deduction_type')
                if ded_type in deduction_types:
                    raise serializers.ValidationError({
                        'additional_deductions': f'No se permite tener más de una deducción del mismo tipo (Error en la deducción #{i+1})'
                    })
                deduction_types.add(ded_type)
        
        # Validar que no haya tipos de incremento duplicados
        additional_increases = data.get('additional_increases', [])
        increase_types = set()
        for i, increase in enumerate(additional_increases):
            if isinstance(increase, dict):
                inc_type = increase.get('increase_type')
                if inc_type in increase_types:
                    raise serializers.ValidationError({
                        'additional_increases': f'No se permite tener más de un incremento del mismo tipo (Error en el incremento #{i+1})'
                    })
                increase_types.add(inc_type)

        # Obtener el contrato más reciente que coincida con el código base
        base_code = "-".join(contract_code.split("-")[:3])  # Obtener todo hasta antes del número de versión
        contracts = EmployeeContract.objects.filter(
            contract_code__startswith=base_code,
            id_employee=employee
        ).order_by("-contract_code")

        if not contracts.exists():
            raise serializers.ValidationError({
                "contract_code": f"No se encontró un contrato con el código {contract_code} para el empleado."
            })

        contract = contracts.first()
        data["contract"] = contract

        # Validar que las fechas estén dentro del rango del contrato
        if start_date < contract.start_date:
            raise serializers.ValidationError({
                "start_date": f"La fecha de inicio no puede ser anterior a la fecha de inicio del contrato ({contract.start_date})."
            })

        if contract.end_date and end_date > contract.end_date:
            raise serializers.ValidationError({
                "end_date": f"La fecha de fin no puede ser posterior a la fecha de fin del contrato ({contract.end_date})."
            })

        # Validar que no se cruce con otra nómina del mismo empleado y contrato
        existing_payrolls = Payroll.objects.filter(
            id_employee=employee,
            id_employee_contract=contract,
            start_date__lte=end_date,
            end_date__gte=start_date
        )

        if existing_payrolls.exists():
            raise serializers.ValidationError({
                "start_date": "Ya existe una nómina para este empleado en el rango de fechas especificado."
            })

        # Validar fechas de deducciones adicionales
        for i, deduction in enumerate(data.get('additional_deductions', [])):
            deduction_start = deduction.get('start_date_deduction')
            deduction_end = deduction.get('end_date_deductions')
            
            if deduction_start and deduction_end:  # Solo validar si ambas fechas están presentes
                if deduction_start < start_date or deduction_end > end_date:
                    raise serializers.ValidationError({
                        f"additional_deductions.{i}.start_date_deduction": 
                            f"Las fechas de la deducción deben estar dentro del rango de fechas de la nómina ({start_date} - {end_date})."
                    })
            
            # Asegurar que las fechas de deducción sean consistentes
            if deduction_start and not deduction_end:
                raise serializers.ValidationError({
                    f"additional_deductions.{i}.end_date_deductions": 
                        "Este campo es obligatorio cuando se especifica start_date_deduction."
                })
            
            if deduction_start and deduction_end and deduction_start > deduction_end:
                raise serializers.ValidationError({
                    f"additional_deductions.{i}.end_date_deductions": 
                        "La fecha de fin debe ser posterior a la fecha de inicio."
                })

        # Validar fechas de incrementos adicionales
        for i, increase in enumerate(data.get('additional_increases', [])):
            increase_start = increase.get('start_date_increase')
            increase_end = increase.get('end_date_increase')
            
            if increase_start and increase_end:  # Solo validar si ambas fechas están presentes
                if increase_start < start_date or increase_end > end_date:
                    raise serializers.ValidationError({
                        f"additional_increases.{i}.start_date_increase": 
                            f"Las fechas del incremento deben estar dentro del rango de fechas de la nómina ({start_date} - {end_date})."
                    })
            
            # Asegurar que las fechas de incremento sean consistentes
            if increase_start and not increase_end:
                raise serializers.ValidationError({
                    f"additional_increases.{i}.end_date_increase": 
                        "Este campo es obligatorio cuando se especifica start_date_increase."
                })
            
            if increase_start and increase_end and increase_start > increase_end:
                raise serializers.ValidationError({
                    f"additional_increases.{i}.end_date_increase": 
                        "La fecha de fin debe ser posterior a la fecha de inicio."
                })

        return data

    def calculate_time_worked(self, contract, start_date, end_date):
        """Calcula el tiempo trabajado según el tipo de salario."""
        if contract.salary_type == 'Mensual fijo':
            # Para salario mensual fijo, contar todos los días en el rango
            delta = end_date - start_date
            return delta.days / 30.0  # Convertir a meses
        
        # Para los demás tipos, necesitamos los días de la semana laborales
        work_days = contract.days_of_week.values_list('day_number', flat=True)
        
        if not work_days:
            return 0
        
        # Contar cuántos días laborales hay en el rango
        current_date = start_date
        workday_count = 0
        
        while current_date <= end_date:
            if current_date.weekday() + 1 in work_days:  # weekday() returns 0=Monday, 6=Sunday
                workday_count += 1
            current_date += timedelta(days=1)
        
        if contract.salary_type == 'Por horas':
            # Para pago por horas, multiplicar por las horas de trabajo diarias
            return workday_count * (contract.working_hours or 0)
        else:  # 'Por días'
            return workday_count

    def calculate_payroll_amounts(self, contract, time_worked, start_date, end_date, additional_deductions, additional_increases):
        """Calcula los montos de la nómina."""
        # Calcular salario base
        base_salary = contract.salary_base * time_worked
        
        # Obtener deducciones e incrementos del contrato
        contract_deductions = EmployeeContractDeduction.objects.filter(
            employee_contracts_contract_code=contract.contract_code,
            start_date_deduction__lte=end_date,
            end_date_deductions__gte=start_date
        )
        
        contract_increases = EmployeeContractIncrease.objects.filter(
            employee_contracts_contract_code=contract.contract_code,
            start_date_increase__lte=end_date,
            end_date_increase__gte=start_date
        )
        
        # Inicializar totales
        total_deductions = 0
        total_increases = 0
        
        # Procesar deducciones e incrementos del contrato
        for deduction in contract_deductions:
            amount = 1 if deduction.amount is None else float(deduction.amount)
            if deduction.amount_type == 'Porcentaje':
                calculated_amount = (deduction.amount_value * base_salary / 100) * amount
            else:  # 'fijo'
                calculated_amount = deduction.amount_value * amount
            
            if deduction.application_deduction_type == 'SalarioBase':
                if deduction.amount_type == 'Porcentaje':
                    total_deductions += (deduction.amount_value * base_salary / 100) * amount
                else:  # 'fijo'
                    total_deductions += deduction.amount_value * amount
        
        for increase in contract_increases:
            amount = 1 if increase.amount is None else float(increase.amount)
            if increase.application_increase_type in ['SalarioBase', 'SalarioFinal']:
                if increase.amount_type == 'Porcentaje':
                    calculated_amount = (increase.amount_value * base_salary / 100) * amount
                else:  # 'fijo'
                    calculated_amount = increase.amount_value * amount
                
                if increase.application_increase_type == 'SalarioBase':
                    total_increases += calculated_amount
        
        # Procesar deducciones e incrementos adicionales
        for deduction in additional_deductions:
            amount = 1 if deduction.get('amount') is None else float(deduction['amount'])
            if deduction['amount_type'] == 'Porcentaje':
                calculated_amount = (deduction['amount_value'] * base_salary / 100) * amount
            else:  # 'fijo'
                calculated_amount = deduction['amount_value'] * amount
            
            if deduction['application_deduction_type'] == 'SalarioBase':
                total_deductions += calculated_amount
        
        for increase in additional_increases:
            amount = 1 if increase.get('amount') is None else float(increase['amount'])
            if increase['amount_type'] == 'Porcentaje':
                calculated_amount = (increase['amount_value'] * base_salary / 100) * amount
            else:  # 'fijo'
                calculated_amount = increase['amount_value'] * amount
            
            if increase['application_increase_type'] == 'SalarioBase':
                total_increases += calculated_amount
        
        # Calcular salario base con incrementos y deducciones
        net_pay_salary_base = (base_salary + total_increases) - total_deductions
        
        # Si el salario base es negativo, lanzar error
        if net_pay_salary_base < 0:
            raise serializers.ValidationError({
                "non_field_errors": ["El salario neto no puede ser negativo."]
            })
        
        # Procesar deducciones e incrementos de SalarioFinal
        salary_final_deductions = 0
        salary_final_increases = 0
        
        for deduction in contract_deductions:
            if deduction.application_deduction_type == 'SalarioFinal':
                amount = 1 if deduction.amount is None else float(deduction.amount)
                if deduction.amount_type == 'Porcentaje':
                    salary_final_deductions += (deduction.amount_value * net_pay_salary_base / 100) * amount
                else:  # 'fijo'
                    salary_final_deductions += deduction.amount_value * amount
        
        for increase in contract_increases:
            if increase.application_increase_type == 'SalarioFinal':
                amount = 1 if increase.amount is None else float(increase.amount)
                if increase.amount_type == 'Porcentaje':
                    salary_final_increases += (increase.amount_value * net_pay_salary_base / 100) * amount
                else:  # 'fijo'
                    salary_final_increases += increase.amount_value * amount
        
        for deduction in additional_deductions:
            if deduction['application_deduction_type'] == 'SalarioFinal':
                amount = 1 if deduction.get('amount') is None else float(deduction['amount'])
                if deduction['amount_type'] == 'Porcentaje':
                    salary_final_deductions += (deduction['amount_value'] * net_pay_salary_base / 100) * amount
                else:  # 'fijo'
                    salary_final_deductions += deduction['amount_value'] * amount
        
        for increase in additional_increases:
            if increase['application_increase_type'] == 'SalarioFinal':
                amount = 1 if increase.get('amount') is None else float(increase['amount'])
                if increase['amount_type'] == 'Porcentaje':
                    salary_final_increases += (increase['amount_value'] * net_pay_salary_base / 100) * amount
                else:  # 'fijo'
                    salary_final_increases += increase['amount_value'] * amount
        
        # Calcular salario final
        net_pay = (net_pay_salary_base + salary_final_increases) - salary_final_deductions
        
        # Validar que el salario final no sea negativo
        if net_pay < 0:
            raise serializers.ValidationError({
                "non_field_errors": ["El salario neto final no puede ser negativo."]
            })
        
        # Actualizar totales
        total_deductions += salary_final_deductions
        total_increases += salary_final_increases
        
        return {
            'base_salary': contract.salary_base,
            'time_worked': time_worked,
            'total_deductions': total_deductions,
            'total_increases': total_increases,
            'net_pay': net_pay,
            'currency_type': contract.currency_type
        }

    @transaction.atomic
    def create(self, validated_data):
        # Extraer datos
        employee = validated_data['id_employee']
        contract = validated_data.pop('contract')
        start_date = validated_data['start_date']
        end_date = validated_data['end_date']
        additional_deductions = validated_data.pop('additional_deductions', [])
        additional_increases = validated_data.pop('additional_increases', [])
        
        # Calcular tiempo trabajado
        time_worked = self.calculate_time_worked(contract, start_date, end_date)
        
        # Calcular montos de la nómina
        amounts = self.calculate_payroll_amounts(
            contract, time_worked, start_date, end_date,
            additional_deductions, additional_increases
        )
        
        # Crear la nómina
        payroll = Payroll.objects.create(
            id_employee=employee,
            id_employee_contract=contract,
            start_date=start_date,
            end_date=end_date,
            base_salary=amounts['base_salary'],
            time_worked=time_worked,
            total_deductions=amounts['total_deductions'],
            total_increments=amounts['total_increases'],
            net_pay=amounts['net_pay'],
            currency_type=amounts['currency_type'],
            creation_date=timezone.now(),
            # Create a User instance with the id_user from the JWTUser object
            id_responsible_user=User(id_user=self.context['request'].user.id)
        )
        
        # Obtener deducciones e incrementos del contrato que caen dentro del período de la nómina
        from payroll.models.employee_contract_deduction import EmployeeContractDeduction
        from payroll.models.employee_contract_increase import EmployeeContractIncrease
        
        contract_deductions = EmployeeContractDeduction.objects.filter(
            employee_contracts_contract_code=contract.contract_code,
            start_date_deduction__lte=end_date,
            end_date_deductions__gte=start_date
        )
        
        contract_increases = EmployeeContractIncrease.objects.filter(
            employee_contracts_contract_code=contract.contract_code,
            start_date_increase__lte=end_date,
            end_date_increase__gte=start_date
        )
        
        # Crear deducciones de nómina a partir de las deducciones del contrato
        for deduction in contract_deductions:
            amount = deduction.amount or 1
            base_for_calculation = amounts['base_salary'] if deduction.application_deduction_type == 'SalarioBase' else amounts['net_pay']
            
            if deduction.amount_type == 'Porcentaje':
                calculated_amount = (deduction.amount_value * base_for_calculation / 100) * amount
            else:  # 'fijo'
                calculated_amount = deduction.amount_value * amount
            
            PayrollDeduction.objects.create(
                deduction_type=deduction.deduction_type,
                amount_type=deduction.amount_type,
                amount_value=deduction.amount_value,
                application_deduction_type=deduction.application_deduction_type,
                start_date_deduction=max(deduction.start_date_deduction, start_date),
                end_date_deductions=min(deduction.end_date_deductions, end_date),
                description=deduction.description or "",
                amount=amount,
                calculated_amount=calculated_amount,
                payroll=payroll
            )
        
        # Crear incrementos de nómina a partir de los incrementos del contrato
        for increase in contract_increases:
            amount = increase.amount or 1
            base_for_calculation = amounts['base_salary'] if increase.application_increase_type == 'SalarioBase' else amounts['net_pay']
            
            if increase.amount_type == 'Porcentaje':
                calculated_amount = (increase.amount_value * base_for_calculation / 100) * amount
            else:  # 'fijo'
                calculated_amount = increase.amount_value * amount
            
            PayrollIncrease.objects.create(
                increase_type=increase.increase_type,
                amount_type=increase.amount_type,
                amount_value=increase.amount_value,
                application_increase_type=increase.application_increase_type,
                start_date_increase=max(increase.start_date_increase, start_date),
                end_date_increase=min(increase.end_date_increase, end_date),
                description=increase.description or "",
                amount=amount,
                calculated_amount=calculated_amount,
                payroll=payroll
            )
        
        # Crear registros de deducciones adicionales
        for deduction_data in additional_deductions:
            amount = 1 if deduction_data.get('amount') is None else float(deduction_data['amount'])
            base_for_calculation = amounts['base_salary'] if deduction_data['application_deduction_type'] == 'SalarioBase' else amounts['net_pay']
            
            if deduction_data['amount_type'] == 'Porcentaje':
                calculated_amount = (deduction_data['amount_value'] * base_for_calculation / 100) * amount
            else:  # 'fijo'
                calculated_amount = deduction_data['amount_value'] * amount
            
            PayrollDeduction.objects.create(
                **deduction_data,
                calculated_amount=calculated_amount,
                payroll=payroll
            )
        
        # Crear registros de incrementos adicionales
        for increase_data in additional_increases:
            amount = 1 if increase_data.get('amount') is None else float(increase_data['amount'])
            base_for_calculation = amounts['base_salary'] if increase_data['application_increase_type'] == 'SalarioBase' else amounts['net_pay']
            
            if increase_data['amount_type'] == 'Porcentaje':
                calculated_amount = (increase_data['amount_value'] * base_for_calculation / 100) * amount
            else:  # 'fijo'
                calculated_amount = increase_data['amount_value'] * amount
            
            PayrollIncrease.objects.create(
                **increase_data,
                calculated_amount=calculated_amount,
                payroll=payroll
            )
        
        return payroll
