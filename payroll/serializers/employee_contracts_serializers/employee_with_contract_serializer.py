from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from parameterization.models import EmployeeCharge, Statues, Types, Units
from payroll.models import (
    Employee,
    EmployeeNews,
    EmployeeContract,
    EmployeeContractDeduction,
    EmployeeContractIncrease,
    EmployeeContractPayment,
)
from users.models import User


class EmployeeContractPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeContractPayment
        fields = ["date_payment", "id_day_of_week"]
        extra_kwargs = {
            "date_payment": {"required": False, "allow_null": True},
            "id_day_of_week": {"required": False, "allow_null": True},
        }


class EmployeeContractDeductionSerializer(serializers.ModelSerializer):
    deduction_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.filter(id_types_categories_id=18),
        error_messages={
            "does_not_exist": "El tipo de deducción especificado no existe.",
            "incorrect_type": "Se esperaba un ID de tipo de deducción válido.",
        },
    )

    class Meta:
        model = EmployeeContractDeduction
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
            "amount": {"min_value": 0},
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
            raise serializers.ValidationError({"amount_value": "El valor no puede ser negativo."})

        if "amount" in data and data["amount"] is not None and data["amount"] < 0:
            raise serializers.ValidationError({"amount": "El monto no puede ser negativo."})

        if data.get("amount_type") == "Porcentaje" and data.get("amount_value", 0) > 100:
            raise serializers.ValidationError(
                {"amount_value": "El valor no puede ser mayor a 100 cuando el tipo es porcentaje."}
            )

        return data


class EmployeeContractIncreaseSerializer(serializers.ModelSerializer):
    increase_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.filter(id_types_categories_id=19),
        error_messages={
            "does_not_exist": "El tipo de incremento especificado no existe.",
            "incorrect_type": "Se esperaba un ID de tipo de incremento válido.",
        },
    )

    class Meta:
        model = EmployeeContractIncrease
        fields = [
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
            "amount": {"min_value": 0},
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

        if "amount" in data and data["amount"] is not None and data["amount"] < 0:
            raise serializers.ValidationError({"amount": "El monto no puede ser negativo."})

        if data.get("amount_type") == "Porcentaje" and data.get("amount_value", 0) > 100:
            raise serializers.ValidationError(
                {"amount_value": "El valor no puede ser mayor a 100 cuando el tipo es porcentaje."}
            )

        return data


class EmployeeContractCreateSerializer(serializers.ModelSerializer):
    contract_payments = EmployeeContractPaymentSerializer(many=True, required=False)
    established_deductions = EmployeeContractDeductionSerializer(many=True, required=False)
    established_increases = EmployeeContractIncreaseSerializer(many=True, required=False)
    days_of_week = serializers.ListField(
        child=serializers.IntegerField(min_value=1, max_value=7),
        required=False,
        allow_empty=True
    )

    class Meta:
        model = EmployeeContract
        fields = [
            "contract_code",
            "description",
            "contract_type",
            "start_date",
            "end_date",
            "payment_frequency_type",
            "contract_payments",
            "minimum_hours",
            "workday_type",
            "work_mode_type",
            "salary_type",
            "working_hours",
            "salary_base",
            "currency_type",
            "trial_period_days",
            "vacation_days",
            "vacation_frequency_days",
            "cumulative_vacation",
            "start_cumulative_vacation",
            "maximum_disability_days",
            "overtime",
            "overtime_period",
            "notice_period_days",
            "established_deductions",
            "established_increases",
            "days_of_week"
        ]
        read_only_fields = ["contract_code"]
        extra_kwargs = {
            "description": {"required": False, "allow_blank": True, "allow_null": True},
            "minimum_hours": {"required": False, "allow_null": True},
            "trial_period_days": {"required": False, "allow_null": True},
            "vacation_frequency_days": {"required": False, "allow_null": True},
            "overtime_period": {"required": False, "allow_null": True},
            "notice_period_days": {"required": False, "allow_null": True},
            "working_hours": {"required": False, "allow_null": True},
            "end_date": {"required": False, "allow_null": True},
        }

    def validate_contract_type(self, value):
        if value.id_types_categories_id != 15:
            raise serializers.ValidationError("El tipo de contrato no es válido.")
        return value

    def validate_workday_type(self, value):
        if value and value.id_types_categories_id != 16:
            raise serializers.ValidationError("El tipo de jornada no es válido.")
        return value

    def validate_work_mode_type(self, value):
        if value and value.id_types_categories_id != 17:
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

    def validate_deductions(self, data):
        """
        Validates the deductions according to the specified rules:
        1. For 'Porcentaje' and 'SalarioBase' deductions, sum of amount_value <= 100
        2. For 'Porcentaje' and 'SalarioFinal' deductions, sum of amount_value <= 100
        3. For 'fijo' and 'SalarioBase' deductions, sum of amount_value <= salary_base
        """
        deductions = data.get('established_deductions', [])
        salary_base = data.get('salary_base')

        # Group deductions by amount_type and application_deduction_type
        percentage_salario_base = []
        percentage_salario_final = []
        fijo_salario_base = []

        for deduction in deductions:
            amount_type = deduction.get('amount_type')
            app_type = deduction.get('application_deduction_type')
            amount_value = deduction.get('amount_value', 0)

            if amount_type == 'Porcentaje' and app_type == 'SalarioBase':
                percentage_salario_base.append(amount_value)
            elif amount_type == 'Porcentaje' and app_type == 'SalarioFinal':
                percentage_salario_final.append(amount_value)
            elif amount_type == 'fijo' and app_type == 'SalarioBase':
                fijo_salario_base.append(amount_value)

        # Validate percentage SalarioBase deductions
        total_percentage_sb = sum(percentage_salario_base)
        if total_percentage_sb > 100:
            raise serializers.ValidationError({
                'established_deductions': f"La suma de los porcentajes para deducciones de tipo 'Porcentaje' y 'SalarioBase' no puede exceder el 100%. Total actual: {total_percentage_sb}%"
            })

        # Validate percentage SalarioFinal deductions
        total_percentage_sf = sum(percentage_salario_final)
        if total_percentage_sf > 100:
            raise serializers.ValidationError({
                'established_deductions': f"La suma de los porcentajes para deducciones de tipo 'Porcentaje' y 'SalarioFinal' no puede exceder el 100%. Total actual: {total_percentage_sf}%"
            })

        # Validate fixed SalarioBase deductions
        total_fixed_sb = sum(fijo_salario_base)
        if salary_base is not None and total_fixed_sb > salary_base:
            raise serializers.ValidationError({
                'established_deductions': f"La suma de los montos fijos para deducciones de tipo 'fijo' y 'SalarioBase' no puede exceder el salario base (${salary_base:.2f}). Total actual: ${total_fixed_sb:.2f}"
            })

        return data

    def validate(self, data):
        if "start_date" in data and "end_date" in data and data["end_date"] is not None:
            if data["start_date"] >= data["end_date"]:
                raise serializers.ValidationError(
                    {"end_date": "La fecha de fin debe ser posterior a la fecha de inicio."}
                )

        numeric_fields = {
            "minimum_hours": "Las horas mínimas no pueden ser negativas.",
            "salary_base": "El salario base no puede ser negativo.",
            "trial_period_days": "El período de prueba no puede ser negativo.",
            "vacation_days": "Los días de vacaciones no pueden ser negativos.",
            "vacation_frequency_days": "La frecuencia de vacaciones no puede ser negativa.",
            "maximum_disability_days": "Los días máximos de incapacidad no pueden ser negativos.",
            "overtime": "El valor de horas extras no puede ser negativo.",
            "notice_period_days": "El período de preaviso no puede ser negativo.",
        }
        for field, message in numeric_fields.items():
            if field in data and data[field] is not None and data[field] < 0:
                raise serializers.ValidationError({field: message})

        if data.get("cumulative_vacation"):
            if not data.get("start_cumulative_vacation"):
                raise serializers.ValidationError(
                    {"start_cumulative_vacation": "Este campo es obligatorio cuando las vacaciones son acumulativas."}
                )
            if data.get("start_cumulative_vacation") < data.get("start_date"):
                raise serializers.ValidationError(
                    {
                        "start_cumulative_vacation": "La fecha de inicio de acumulación no puede ser anterior a la fecha de inicio del contrato ({}).".format(
                            data["start_date"]
                        )
                    }
                )
            if (
                data.get("end_date")
                and data.get("start_cumulative_vacation") > data.get("end_date")
            ):
                raise serializers.ValidationError(
                    {
                        "start_cumulative_vacation": "La fecha de inicio de acumulación no puede ser posterior a la fecha de finalización del contrato ({}).".format(
                            data["end_date"]
                        )
                    }
                )
        else:
            if "start_cumulative_vacation" in data:
                data["start_cumulative_vacation"] = None

        payment_items = self.initial_data.get("contract_payments") or []
        freq = data.get("payment_frequency_type")
        if freq:
            if freq in ("diario", "semanal", "mensual") and len(payment_items) != 1:
                raise serializers.ValidationError(
                    {
                        "contract_payments": "Debe existir exactamente 1 registro de pago para frecuencia diaria, semanal o mensual.",
                    }
                )
            if freq == "quincenal" and len(payment_items) != 2:
                raise serializers.ValidationError(
                    {"contract_payments": "Para pago quincenal deben existir exactamente 2 registros de pago."}
                )

            if freq == "diario" and payment_items:
                item = payment_items[0]
                if item.get("date_payment") is not None or item.get("id_day_of_week") is not None:
                    raise serializers.ValidationError(
                        {"contract_payments": "Para pago diario, no se deben especificar fecha de pago ni día de la semana."}
                    )

            if freq == "semanal" and payment_items:
                item = payment_items[0]
                if not item.get("id_day_of_week"):
                    raise serializers.ValidationError(
                        {"contract_payments": "Para pago semanal, se debe especificar el día de la semana (id_day_of_week)."}
                    )
                if item.get("date_payment") is not None:
                    raise serializers.ValidationError(
                        {"contract_payments": "Para pago semanal, no se debe especificar fecha de pago."}
                    )

            if freq == "quincenal" and payment_items:
                d1, d2 = payment_items
                if d1.get("id_day_of_week") is not None or d2.get("id_day_of_week") is not None:
                    raise serializers.ValidationError(
                        {"contract_payments": "Para pago quincenal, id_day_of_week debe ser nulo en ambos registros."}
                    )
                if d1.get("date_payment") is None or d2.get("date_payment") is None:
                    raise serializers.ValidationError(
                        {"contract_payments": "Para pago quincenal, ambos registros deben especificar date_payment."}
                    )
                if d1.get("date_payment") == d2.get("date_payment"):
                    raise serializers.ValidationError(
                        {"contract_payments": "Para pago quincenal, los dos date_payment deben ser distintos."}
                    )
                for v in (d1.get("date_payment"), d2.get("date_payment")):
                    if not isinstance(v, int) or v < 1 or v > 31:
                        raise serializers.ValidationError(
                            {"contract_payments": "Para pago quincenal, cada date_payment debe estar entre 1 y 31."}
                        )
                low, high = sorted([d1.get("date_payment"), d2.get("date_payment")])
                if not (1 <= low <= 15 and 16 <= high <= 31):
                    raise serializers.ValidationError(
                        {
                            "contract_payments": "Para pago quincenal, un date_payment debe estar entre 1-15 y el otro entre 16-31.",
                        }
                    )
                if abs(d1.get("date_payment") - d2.get("date_payment")) < 15:
                    raise serializers.ValidationError(
                        {
                            "contract_payments": "Para pago quincenal, la diferencia entre ambos date_payment debe ser de al menos 15 días.",
                        }
                    )

            if freq == "mensual" and payment_items:
                item = payment_items[0]
                if item.get("id_day_of_week") is not None:
                    raise serializers.ValidationError(
                        {"contract_payments": "Para pago mensual, no se debe especificar día de la semana."}
                    )
                v = item.get("date_payment")
                if not isinstance(v, int) or v < 1 or v > 31:
                    raise serializers.ValidationError(
                        {"contract_payments": "Para pago mensual, la fecha de pago debe estar entre 1 y 31."}
                    )

        # Validate working_hours based on salary_type
        salary_type = data.get('salary_type')
        working_hours = data.get('working_hours')

        if salary_type == 'Por horas':
            if working_hours is None:
                raise serializers.ValidationError({
                    "working_hours": "Este campo es obligatorio cuando el tipo de salario es 'Por horas'."
                })
            if working_hours <= 0 or working_hours >= 24:
                raise serializers.ValidationError({
                    "working_hours": "Las horas de trabajo deben ser mayores que 0 y menores que 24 cuando el tipo de salario es 'Por horas'."
                })
        else:
            # Remove working_hours if salary_type is not 'Por horas'
            if 'working_hours' in data:
                data.pop('working_hours')

        # Validate deductions if they exist in the data
        if 'established_deductions' in data:
            self.validate_deductions(data)

        if "established_deductions" in self.initial_data:
            deduction_types = set()
            for deduction in self.initial_data.get("established_deductions", []):
                dtype = deduction.get("deduction_type")
                if dtype in deduction_types:
                    raise serializers.ValidationError(
                        {
                            "established_deductions": f"No puede haber dos deducciones con el mismo tipo: {dtype}.",
                        }
                    )
                deduction_types.add(dtype)

        contract_start = data.get("start_date")
        contract_end = data.get("end_date")
        if data.get("established_deductions"):
            ded_errors = []
            for d in data.get("established_deductions", []):
                sd = d.get("start_date_deduction")
                ed = d.get("end_date_deductions")
                e = {}
                if sd and not ed:
                    e["end_date_deductions"] = [
                        "Este campo es obligatorio cuando se especifica start_date_deduction."
                    ]
                if ed and not sd:
                    e["start_date_deduction"] = [
                        "Este campo es obligatorio cuando se especifica end_date_deductions."
                    ]
                if sd and ed:
                    if contract_start and sd < contract_start:
                        e["start_date_deduction"] = [
                            f"La fecha de inicio de la deducción no puede ser anterior a la fecha de inicio del contrato ({contract_start})."
                        ]
                    elif contract_end and sd > contract_end:
                        e["start_date_deduction"] = [
                            f"La fecha de inicio de la deducción no puede ser posterior a la fecha de finalización del contrato ({contract_end})."
                        ]
                    if "start_date_deduction" not in e:
                        if contract_start and ed < contract_start:
                            e["end_date_deductions"] = [
                                f"La fecha de fin de la deducción no puede ser anterior a la fecha de inicio del contrato ({contract_start})."
                            ]
                        elif contract_end and ed > contract_end:
                            e["end_date_deductions"] = [
                                f"La fecha de fin de la deducción no puede ser posterior a la fecha de finalización del contrato ({contract_end})."
                            ]
                    if "start_date_deduction" not in e and "end_date_deductions" not in e and sd >= ed:
                        e["end_date_deductions"] = ["La fecha de fin debe ser posterior a la fecha de inicio."]
                if e:
                    ded_errors.append(e)
            if ded_errors:
                raise serializers.ValidationError({"established_deductions": ded_errors})

        if "established_increases" in self.initial_data:
            increase_types = set()
            for increase in self.initial_data.get("established_increases", []):
                itype = increase.get("increase_type")
                if itype in increase_types:
                    raise serializers.ValidationError(
                        {
                            "established_increases": f"No puede haber dos incrementos con el mismo tipo: {itype}.",
                        }
                    )
                increase_types.add(itype)

        if data.get("established_increases"):
            inc_errors = []
            for inc in data.get("established_increases", []):
                si = inc.get("start_date_increase")
                ei = inc.get("end_date_increase")
                e = {}
                if si and not ei:
                    e["end_date_increase"] = [
                        "Este campo es obligatorio cuando se especifica start_date_increase."
                    ]
                if ei and not si:
                    e["start_date_increase"] = [
                        "Este campo es obligatorio cuando se especifica end_date_increase."
                    ]
                if si and ei:
                    if contract_start and si < contract_start:
                        e["start_date_increase"] = [
                            f"La fecha de inicio del incremento no puede ser anterior a la fecha de inicio del contrato ({contract_start})."
                        ]
                    elif contract_end and si > contract_end:
                        e["start_date_increase"] = [
                            f"La fecha de inicio del incremento no puede ser posterior a la fecha de finalización del contrato ({contract_end})."
                        ]
                    if "start_date_increase" not in e:
                        if contract_start and ei < contract_start:
                            e["end_date_increase"] = [
                                f"La fecha de fin del incremento no puede ser anterior a la fecha de inicio del contrato ({contract_start})."
                            ]
                        elif contract_end and ei > contract_end:
                            e["end_date_increase"] = [
                                f"La fecha de fin del incremento no puede ser posterior a la fecha de finalización del contrato ({contract_end})."
                            ]
                    if "start_date_increase" not in e and "end_date_increase" not in e and si >= ei:
                        e["end_date_increase"] = ["La fecha de fin debe ser posterior a la fecha de inicio."]
                if e:
                    inc_errors.append(e)
            if inc_errors:
                raise serializers.ValidationError({"established_increases": inc_errors})

        # Validar días de la semana
        days_of_week = data.get('days_of_week', [])
        if days_of_week and len(days_of_week) != len(set(days_of_week)):
            raise serializers.ValidationError({"days_of_week": "No se permiten días duplicados."})
        if days_of_week and any(day < 1 or day > 7 for day in days_of_week):
            raise serializers.ValidationError({"days_of_week": "Los días de la semana deben estar entre 1 y 7."})

        return data

    def generate_contract_code(self):
        current_year = timezone.now().year
        prefix = f"CON-{current_year}-"
        last_contract = (
            EmployeeContract.objects.filter(contract_code__startswith=prefix)
            .order_by("-contract_code")
            .first()
        )
        if last_contract:
            parts = last_contract.contract_code.split("-")
            try:
                sequence = int(parts[2]) + 1
            except (IndexError, ValueError):
                sequence = 1
        else:
            sequence = 1
        return f"CON-{current_year}-{sequence:04d}-00"

    def get_contract_status(self):
        try:
            return Statues.objects.get(pk=28)
        except Statues.DoesNotExist:
            raise serializers.ValidationError(
                {"contract_status": "No se encontró el estado 28 para los contratos de empleados."}
            )

    @transaction.atomic
    def create(self, validated_data):
        payments_data = validated_data.pop("contract_payments", [])
        deductions_data = validated_data.pop("established_deductions", [])
        increases_data = validated_data.pop("established_increases", [])
        days_of_week = validated_data.pop('days_of_week', [1, 2, 3, 4, 5])  # Default to Monday-Friday

        employee = validated_data.pop("employee", None)
        employee_charge = validated_data.pop("employee_charge", None)
        responsible_user = validated_data.pop("responsible_user", None)

        if not employee:
            raise serializers.ValidationError("No se proporcionó el empleado para el contrato.")
        if not employee_charge:
            raise serializers.ValidationError("No se proporcionó el cargo para el contrato.")
        if not employee_charge.id_employee_department:
            raise serializers.ValidationError(
                {"id_employee_charge": "El cargo seleccionado no tiene un departamento asociado."}
            )
        if not responsible_user:
            raise serializers.ValidationError("No se pudo determinar el usuario responsable autenticado.")

        validated_data["id_employee"] = employee
        validated_data["id_employee_charge"] = employee_charge
        validated_data["id_employee_department"] = employee_charge.id_employee_department
        validated_data["contract_status"] = self.get_contract_status()
        validated_data["secundary_petition"] = False
        validated_data["creation_date"] = timezone.now()
        validated_data["id_responsible_user"] = responsible_user
        validated_data["contract_code"] = self.generate_contract_code()

        contract = EmployeeContract.objects.create(**validated_data)

        # Asignar días de la semana
        if days_of_week:
            from payroll.models import DaysOfWeek
            days = DaysOfWeek.objects.filter(id_day_of_week__in=days_of_week)
            contract.days_of_week.set(days)

        self.process_contract_payments(contract, payments_data, contract.payment_frequency_type)

        for deduction in deductions_data:
            EmployeeContractDeduction.objects.create(
                employee_contracts_contract_code=contract, **deduction
            )

        for increase in increases_data:
            EmployeeContractIncrease.objects.create(
                employee_contracts_contract_code=contract, **increase
            )

        return contract

    def process_contract_payments(self, contract, payments_data, payment_frequency_type):
        if payment_frequency_type == "diario":
            EmployeeContractPayment.objects.create(
                employee_contracts_contract_code=contract,
                date_payment=None,
                id_day_of_week=None,
            )
        elif payment_frequency_type == "semanal" and payments_data:
            payment_data = payments_data[0]
            EmployeeContractPayment.objects.create(
                employee_contracts_contract_code=contract,
                date_payment=None,
                id_day_of_week=payment_data.get("id_day_of_week"),
            )
        elif payment_frequency_type == "quincenal":
            for payment_data in payments_data:
                EmployeeContractPayment.objects.create(
                    employee_contracts_contract_code=contract,
                    date_payment=payment_data.get("date_payment"),
                    id_day_of_week=None,
                )
        elif payment_frequency_type == "mensual" and payments_data:
            payment_data = payments_data[0]
            EmployeeContractPayment.objects.create(
                employee_contracts_contract_code=contract,
                date_payment=payment_data.get("date_payment"),
                id_day_of_week=None,
            )


class EmployeeWithContractCreateSerializer(serializers.Serializer):
    id_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        help_text="ID del usuario que se vinculará al empleado.",
    )
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    observation = serializers.CharField(allow_blank=False)
    id_employee_charge = serializers.PrimaryKeyRelatedField(
        queryset=EmployeeCharge.objects.all()
    )
    contract = serializers.ListField(child=serializers.DictField(), write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._contract_serializer = None

    def validate_email(self, value):
        if value and Employee.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ya existe un empleado con este correo electrónico.")
        return value

    def validate_id_user(self, value):
        if Employee.objects.filter(id_user=value).exists():
            raise serializers.ValidationError("Este usuario ya está asociado a otro empleado.")
        return value

    def validate(self, attrs):
        contracts_payload = self.initial_data.get("contract")
        if not isinstance(contracts_payload, list) or not contracts_payload:
            raise serializers.ValidationError(
                {"contract": "Debe proporcionar una lista con la información del contrato."}
            )
        if len(contracts_payload) != 1:
            raise serializers.ValidationError(
                {"contract": "Por ahora solo se admite la creación de un contrato por solicitud."}
            )

        contract_serializer = EmployeeContractCreateSerializer(
            data=contracts_payload[0],
            context={"request": self.context.get("request")},
        )
        contract_serializer.is_valid(raise_exception=True)
        self._contract_serializer = contract_serializer
        return attrs

    def _get_responsible_user(self):
        request = self.context.get("request")
        if request and hasattr(request, "user") and getattr(request.user, "id", None):
            try:
                return User.objects.get(pk=request.user.id)
            except User.DoesNotExist:
                pass
        raise serializers.ValidationError(
            {"id_responsible_user": "No se pudo determinar el usuario autenticado."}
        )

    def _get_employee_status(self):
        try:
            return Statues.objects.get(pk=1)
        except Statues.DoesNotExist:
            raise serializers.ValidationError(
                {"employee_status": "No se encontró el estado 1 para los empleados."}
            )

    @transaction.atomic
    def create(self, validated_data):
        if not self._contract_serializer:
            raise serializers.ValidationError("La información del contrato no fue validada correctamente.")

        id_user = validated_data["id_user"]
        email = validated_data["email"]
        observation = validated_data["observation"]
        employee_charge = validated_data["id_employee_charge"]
        responsible_user = self._get_responsible_user()
        employee_status = self._get_employee_status()
        now = timezone.now()

        employee = Employee.objects.create(
            id_user=id_user,
            email=email,
            id_employee_charge=employee_charge,
            employee_status=employee_status,
            creation_date=now,
            modification_date=now,
            id_responsible_user=responsible_user,
        )

        EmployeeNews.objects.create(
            id_employee=employee,
            observation=observation,
            news_type="CREACION_EMPLEADO",
            id_responsible_user=responsible_user,
        )

        contract = self._contract_serializer.save(
            employee=employee,
            employee_charge=employee_charge,
            responsible_user=responsible_user,
        )

        return {"employee_id": employee.id_employee, "contract_code": contract.contract_code}
