from typing import List, Dict, Any
from collections import defaultdict
from openpyxl import Workbook
from openpyxl.styles import PatternFill


def _build_report_data(queryset) -> list[Dict[str, Any]]:
    """Construye los datos del reporte a partir del queryset."""
    grouped_data = defaultdict(lambda: {"latitudes": [], "longitudes": [], "alerts": []})

    # --- 1️⃣ Agrupamos los datos por timestamp y dispositivo ---
    for record in queryset.select_related('id_parameter', 'id_device', 'id_machinery'):
        key = (record.registered_at, record.id_device)
        param_id = str(record.id_parameter.avl_id_parameter).strip()
        param_name = record.id_parameter.parameter_name

        # Guardamos coordenadas (latitud/longitud)
        if param_id == "387":
            if len(grouped_data[key]["latitudes"]) == len(grouped_data[key]["longitudes"]):
                grouped_data[key]["latitudes"].append(record.data)
            else:
                grouped_data[key]["longitudes"].append(record.data)
        else:
            grouped_data[key][param_id] = record.data

        # Si el registro tiene alerta, guardamos el nombre del parámetro
        if record.alert:
            grouped_data[key]["alerts"].append(param_name)

        grouped_data[key]['timestamp'] = record.registered_at
        grouped_data[key]['machinery'] = getattr(record.id_machinery, 'machinery_name', 'Desconocido')
        grouped_data[key]['device'] = getattr(record.id_device, 'name', 'Desconocido')
        grouped_data[key]['obd_fault'] = record.obd_fault

    # --- 2️⃣ Procesamos cada grupo para construir filas ---
    report_data = []

    for (timestamp, id_device), values in grouped_data.items():
        # Traducción de códigos a texto
        ignition_map = {"0": "Apagado", "1": "Encendido"}
        movement_map = {"0": "Detenido", "1": "En movimiento"}
        event_map = {"1": "Aceleración", "2": "Frenado", "3": "Curva"}
        logistic_map = {"1": "Ida", "2": "Trabajo", "3": "Vuelta"}

        ignition_state = ignition_map.get(str(values.get("239")), "N/A")
        movement_state = movement_map.get(str(values.get("240")), "N/A")
        logistic_state = logistic_map.get(str(values.get("-1")), "N/A")

        event_type_code = str(values.get("253")) if values.get("253") else None
        event_type = event_map.get(event_type_code, None)
        event_value = values.get("254") if event_type else None

        latitude = values["latitudes"][0] if values["latitudes"] else 0
        longitude = values["longitudes"][0] if values["longitudes"] else 0

        row_data = {
            "Fecha": values['timestamp'].date(),
            "Hora": values['timestamp'].time(),
            "Dispositivo": values.get("device"),
            "Maquinaria": values.get("machinery"),
            "Estado Ignición": ignition_state,
            "Estado Movimiento": movement_state,
            "Velocidad (km/h)": values.get("24", 0),
            "Revoluciones por Minuto (RPM)": values.get("36", 0),
            "Temperatura Motor (°C)": values.get("32", 0),
            "Carga Motor (%)": values.get("31", 0),
            "Nivel Aceite (%)": values.get("1159", 0),
            "Nivel Combustible (%)": values.get("48", 0),
            "Combustible Usado (L)": values.get("12", 0),
            "Consumo Instantáneo (L/h)": values.get("60", 0),
            "Odómetro Total (km)": values.get("16", 0),
            "Odómetro Viaje (km)": values.get("199", 0),
            "Tipo Evento Conducción": event_type or "N/A",
            "Valor G del Evento": event_value if event_type else None,
            "Fallas OBD": values.get("obd_fault") or "Sin fallas",
            "Latitud": latitude,
            "Longitud": longitude,
            "Estado Logístico": logistic_state,
            "Parámetros con alerta": ", ".join(values.get("alerts", [])) or "Sin alertas",
        }

        report_data.append(row_data)

    return report_data


def generate_excel_report(queryset) -> bytes:
    """Genera un reporte en formato Excel a partir del queryset."""
    report_data = _build_report_data(queryset)

    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte de Telemetría"

    # Encabezados
    headers = list(report_data[0].keys())
    for col_num, header in enumerate(headers, 1):
        ws.cell(row=1, column=col_num, value=header)

    red_fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")

    # --- 3️⃣ Filas ---
    for row_num, data_row in enumerate(report_data, 2):
        for col_num, (key, value) in enumerate(data_row.items(), 1):
            cell = ws.cell(row=row_num, column=col_num, value=value)

            # Si este parámetro está en la lista de alertas, píntalo en rojo
            alert_list = data_row.get("Parámetros con alerta", "")
            if key in alert_list:
                cell.fill = red_fill

    from io import BytesIO
    output = BytesIO()
    wb.save(output)
    return output.getvalue()


def generate_csv_report(queryset) -> str:
    """Genera un reporte en formato CSV a partir del queryset."""
    import csv
    from io import StringIO

    report_data = _build_report_data(queryset)

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=report_data[0].keys())
    writer.writeheader()

    for row in report_data:
        writer.writerow(row)

    return output.getvalue()
