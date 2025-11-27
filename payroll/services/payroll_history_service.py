from datetime import datetime
from typing import Any, Dict, List, Tuple

from django.db.models import Prefetch, QuerySet
from django.utils import timezone
from django.conf import settings
import os
import logging
import requests

from payroll.models import Employee, Payroll, PayrollIncrease, PayrollDeduction

logger = logging.getLogger(__name__)


class EmployeeNotFoundError(Exception):
    """Se lanza cuando el documento no está registrado en el sistema."""


class PayrollHistoryService:
    """Servicio para construir la data del historial de nóminas de un empleado."""

    @classmethod
    def _get_auth_base_url(cls) -> str:
        return os.getenv("AUTH_SERVICE_URL", "").rstrip("/")

    @classmethod
    def resolve_employee_by_identification(
        cls,
        document_number: str,
        request,
    ) -> Tuple[Employee, Dict[str, Any]]:
        """Resuelve el empleado y datos de usuario externo a partir del documento.

        Retorna una tupla (employee, user_data_ext).
        Lanza EmployeeNotFoundError si no se encuentra.
        """
        base_url = cls._get_auth_base_url()
        if not base_url:
            raise EmployeeNotFoundError("Servicio de autenticación no configurado")

        url = f"{base_url}/users/users/by-document/{document_number}"
        headers = {"Content-Type": "application/json"}

        # Copiar header de autorización del request
        auth_header = getattr(request, "META", {}).get("HTTP_AUTHORIZATION") or (
            request.headers.get("Authorization") if hasattr(request, "headers") else None
        )
        if auth_header:
            headers["Authorization"] = auth_header

        try:
            resp = requests.get(url, headers=headers, timeout=10)
        except Exception as exc:
            logger.error("Error llamando a servicio externo by-document: %s", exc, exc_info=True)
            raise EmployeeNotFoundError("No fue posible validar el documento en el servicio de autenticación")

        if resp.status_code == 404:
            raise EmployeeNotFoundError("El documento ingresado no se encuentra registrado en el sistema.")

        if resp.status_code != 200 or not resp.content:
            logger.warning("Respuesta inesperada de servicio by-document: %s %s", resp.status_code, resp.text)
            raise EmployeeNotFoundError("El documento ingresado no se encuentra registrado en el sistema.")

        try:
            data = resp.json() or {}
        except Exception:
            data = {}

        # La respuesta puede venir envuelta en "data" o directa
        user_data = data.get("data", data) if isinstance(data, dict) else {}
        if not isinstance(user_data, dict) or not user_data:
            raise EmployeeNotFoundError("El documento ingresado no se encuentra registrado en el sistema.")

        user_id = user_data.get("id")
        if not user_id:
            raise EmployeeNotFoundError("El documento ingresado no se encuentra registrado en el sistema.")

        try:
            employee = Employee.objects.select_related(
                "id_employee_charge",
                "id_employee_charge__id_employee_department",
                "employee_status",
            ).get(id_user_id=user_id)
        except Employee.DoesNotExist:
            raise EmployeeNotFoundError("El documento ingresado no se encuentra registrado en el sistema.")

        return employee, user_data

    @classmethod
    def get_payrolls_for_employee(
        cls,
        employee: Employee,
        date_from,
        date_to,
    ) -> QuerySet:
        """Obtiene las nóminas del empleado filtradas por rango de fechas."""
        qs = (
            Payroll.objects.select_related(
                "id_employee",
                "id_employee_contract",
                "id_employee_contract__contract_type",
                "id_employee_contract__workday_type",
                "id_employee_contract__work_mode_type",
                "id_employee_contract__currency_type",
                "id_responsible_user",
            )
            .prefetch_related(
                Prefetch("payroll_increases", queryset=PayrollIncrease.objects.select_related("increase_type")),
                Prefetch("payroll_deductions", queryset=PayrollDeduction.objects.select_related("deduction_type")),
            )
            .filter(id_employee=employee, creation_date__date__gte=date_from, creation_date__date__lte=date_to)
            .order_by("creation_date")
        )
        return qs

    @classmethod
    def _classify_increases(cls, increases: List[PayrollIncrease]) -> Dict[str, List[Dict[str, Any]]]:
        fixed: List[Dict[str, Any]] = []
        additional: List[Dict[str, Any]] = []

        for inc in increases or []:
            row = {
                "type_name": getattr(getattr(inc, "increase_type", None), "name", None),
                "amount_type": inc.amount_type,
                "application_type": inc.application_increase_type,
                "amount_value": inc.amount_value,
                "amount": inc.amount,
                "calculated_amount": inc.calculated_amount,
                "start_date": inc.start_date_increase,
                "end_date": inc.end_date_increase,
                "description": inc.description,
            }
            # Heurística: tratamos como "fijo" los que aplican sobre salario base/por hora
            if inc.application_increase_type in ("SalarioBase", "SalarioPorHora"):
                fixed.append(row)
            else:
                additional.append(row)

        return {"fixed": fixed, "additional": additional}

    @classmethod
    def _classify_deductions(cls, deductions: List[PayrollDeduction]) -> Dict[str, List[Dict[str, Any]]]:
        fixed: List[Dict[str, Any]] = []
        additional: List[Dict[str, Any]] = []

        for ded in deductions or []:
            row = {
                "type_name": getattr(getattr(ded, "deduction_type", None), "name", None),
                "amount_type": ded.amount_type,
                "application_type": ded.application_deduction_type,
                "amount_value": ded.amount_value,
                "amount": ded.amount,
                "calculated_amount": ded.calculated_amount,
                "start_date": ded.start_date_deduction,
                "end_date": ded.end_date_deductions,
                "description": ded.description,
            }
            # Heurística similar: base = fijo, resto = adicional
            if ded.application_deduction_type == "SalarioBase":
                fixed.append(row)
            else:
                additional.append(row)

        return {"fixed": fixed, "additional": additional}

    @classmethod
    def build_history_payload(
        cls,
        employee: Employee,
        user_data: Dict[str, Any],
        payrolls: QuerySet,
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Construye la estructura de datos para el PDF.

        Retorna (employee_info, payroll_items).
        """
        # Datos del empleado
        charge = getattr(employee, "id_employee_charge", None)
        department = getattr(charge, "id_employee_department", None) if charge else None

        full_name_parts: List[str] = []
        name = (user_data.get("name") or "").strip()
        fln = (user_data.get("first_last_name") or "").strip()
        sln = (user_data.get("second_last_name") or "").strip()
        for p in (name, fln, sln):
            if p:
                full_name_parts.append(p)
        full_name = " ".join(full_name_parts) if full_name_parts else None

        employee_info = {
            "id_employee": employee.id_employee,
            "identification": str(user_data.get("document_number")) if user_data.get("document_number") else None,
            "full_name": full_name,
            "department_name": getattr(department, "name", None) if department else None,
            "charge_name": getattr(charge, "name", None) if charge else None,
        }

        payroll_items: List[Dict[str, Any]] = []

        global_total_increments = 0.0
        global_total_deductions = 0.0
        global_total_net = 0.0
        currency_symbol = ""

        for p in payrolls:
            increases = list(getattr(p, "payroll_increases", []).all()) if hasattr(p, "payroll_increases") else []
            deductions = list(getattr(p, "payroll_deductions", []).all()) if hasattr(p, "payroll_deductions") else []

            inc_grouped = cls._classify_increases(increases)
            ded_grouped = cls._classify_deductions(deductions)

            contract = getattr(p, "id_employee_contract", None)
            contract_code = getattr(contract, "contract_code", None)

            author_user = getattr(p, "id_responsible_user", None)
            author_name = None
            if author_user is not None:
                # El nombre completo real vendría de servicio externo; aquí solo ID
                author_name = str(getattr(author_user, "id_user", author_user))

            global_total_increments += float(p.total_increments or 0)
            global_total_deductions += float(p.total_deductions or 0)
            global_total_net += float(p.net_pay or 0)

            if not currency_symbol and contract is not None:
                try:
                    currency_symbol = getattr(getattr(contract, "currency_type", None), "symbol", "") or ""
                except Exception:
                    currency_symbol = ""

            item = {
                "id_payroll": p.id_payroll,
                "generation_date": p.creation_date,
                "period_from": p.start_date,
                "period_to": p.end_date,
                "contract_code": contract_code,
                "base_salary": p.base_salary,
                "author": author_name,
                # TODO: estado de nómina si se agrega en modelo
                "status": None,
                "summary": {
                    "total_increments": p.total_increments,
                    "total_deductions": p.total_deductions,
                    "net_pay": p.net_pay,
                    # En este contexto neto final = net_pay (si luego se diferencia, se puede ajustar)
                    "net_final": p.net_pay,
                },
                "increases": inc_grouped,
                "deductions": ded_grouped,
            }
            payroll_items.append(item)

        employee_info["currency_symbol"] = currency_symbol
        employee_info["global_summary"] = {
            "total_increments": global_total_increments,
            "total_deductions": global_total_deductions,
            "total_net": global_total_net,
        }

        return employee_info, payroll_items
