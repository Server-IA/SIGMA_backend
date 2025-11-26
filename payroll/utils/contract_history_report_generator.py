from io import BytesIO
from datetime import datetime, timezone
from typing import List, Dict, Any

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

from payroll.models import EmployeeContract, Employee
from parameterization.models import EmployeeCharge, EmployeeDepartment


def _resolve_logo_path() -> str | None:
    """Busca un logo institucional reutilizando la misma lógica usada en otros generadores."""
    try:
        from pathlib import Path
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent.parent  # payroll/ -> root
        candidates = [
            project_root / 'core' / 'assets' / 'logo.jpg',
            project_root / 'core' / 'assets' / 'logo.png',
        ]
        for c in candidates:
            if c.exists():
                return str(c)
    except Exception:
        return None
    return None


def _header(canvas, doc, title: str, logo_path: str | None):
    canvas.saveState()
    width, height = A4
    top_padding = 0.5 * cm
    if logo_path:
        try:
            img_width = 3 * cm
            ir = ImageReader(logo_path)
            iw, ih = ir.getSize()
            ratio = ih / float(iw) if iw else 1.0
            img_height = img_width * ratio
            x = doc.leftMargin
            y = height - img_height - top_padding
            canvas.drawImage(logo_path, x, y, width=img_width, height=img_height, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    canvas.setFont('Helvetica-Bold', 14)
    title_width = canvas.stringWidth(title, 'Helvetica-Bold', 14)
    canvas.drawString((width - title_width) / 2, height - 1 * cm, title)
    canvas.restoreState()


def generate_contract_history_pdf(
    employee: Employee,
    contracts: List[EmployeeContract],
    otrosi_entries: List[Dict[str, Any]],
    date_from,
    date_to,
    downloader_user: str | None,
    logo_path: str | None = None,
    employee_user_data: dict | None = None,
) -> bytes:
    """Construye el PDF de historial de contratos y cargos de un empleado."""
    if logo_path is None:
        logo_path = _resolve_logo_path()

    buffer = BytesIO()
    left_margin = 2 * cm
    right_margin = 2 * cm
    bottom_margin = 2 * cm
    top_margin = 2.5 * cm

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
    )

    styles = getSampleStyleSheet()
    small = ParagraphStyle('small', parent=styles['Normal'], fontSize=9, leading=11)
    cell_style = ParagraphStyle('cell', parent=styles['Normal'], fontSize=8, leading=10, wordWrap='LTR')
    story = []

    # Datos actuales del empleado
    charge: EmployeeCharge | None = getattr(employee, 'id_employee_charge', None)
    department: EmployeeDepartment | None = getattr(charge, 'id_employee_department', None) if charge else None

    # Obtener nombre y documento del empleado desde employee_user_data
    employee_name = 'N/D'
    employee_document = 'N/D'
    
    if employee_user_data:
        name_parts = []
        name = employee_user_data.get('name', '').strip()
        first_last_name = employee_user_data.get('first_last_name', '').strip()
        second_last_name = employee_user_data.get('second_last_name', '').strip()
        
        if name:
            name_parts.append(name)
        if first_last_name:
            name_parts.append(first_last_name)
        if second_last_name:
            name_parts.append(second_last_name)
        
        employee_name = ' '.join(name_parts) if name_parts else 'N/D'
        employee_document = str(employee_user_data.get('document_number', 'N/D'))

    # Usar zona horaria de Colombia
    from pytz import timezone as pytz_timezone
    colombia_tz = pytz_timezone('America/Bogota')
    now_str = datetime.now(colombia_tz).strftime('%Y-%m-%d %H:%M:%S')
    
    story.append(Paragraph('Informe de Historial Contractual', styles['Title']))
    story.append(Spacer(1, 6))

    story.append(Paragraph('Aspectos generales', styles['Heading2']))
    header_rows = [
        ['Nombre empleado', employee_name],
        ['Documento', employee_document],
        ['Departamento actual', str(getattr(department, 'name', 'N/D'))],
        ['Cargo actual', str(getattr(charge, 'name', 'N/D'))],
        ['Rango consultado', f"{date_from} - {date_to}"],
        ['Fecha generación', now_str],
    ]
    if downloader_user:
        header_rows.append(['Generado por', downloader_user])

    header_table = Table(header_rows, colWidths=[doc.width * 0.35, doc.width * 0.65], hAlign='LEFT')
    header_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 12))

    # Sección contratos
    story.append(Paragraph('Historial de Contratos', styles['Heading2']))
    contract_header = [
        Paragraph('Código', cell_style),
        Paragraph('Inicio', cell_style),
        Paragraph('Fin', cell_style),
        Paragraph('Departamento', cell_style),
        Paragraph('Cargo', cell_style),
        Paragraph('Estado', cell_style),
        Paragraph('Motivo fin', cell_style),
    ]
    contract_table_data = [contract_header]
    for c in contracts:
        dept = getattr(getattr(c, 'id_employee_department', None), 'name', 'N/D')
        chg = getattr(getattr(c, 'id_employee_charge', None), 'name', 'N/D')
        estado = getattr(getattr(c, 'contract_status', None), 'name', 'N/D')
        motivo = getattr(getattr(c, 'contract_termination_reason', None), 'name', '') or ''
        contract_table_data.append([
            Paragraph(str(c.contract_code), cell_style),
            Paragraph(str(c.start_date), cell_style),
            Paragraph(str(c.end_date) if c.end_date else '—', cell_style),
            Paragraph(str(dept), cell_style),
            Paragraph(str(chg), cell_style),
            Paragraph(str(estado), cell_style),
            Paragraph(motivo or '—', cell_style),
        ])

    contract_col_widths = [doc.width * 0.17, doc.width * 0.12, doc.width * 0.12, doc.width * 0.17, doc.width * 0.17, doc.width * 0.15, doc.width * 0.1]
    contracts_table = Table(contract_table_data, colWidths=contract_col_widths, hAlign='LEFT', repeatRows=1)
    contracts_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.4, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(contracts_table)
    story.append(Spacer(1, 12))

    # Sección Otrosí
    story.append(Paragraph('Otrosí Asociados', styles['Heading2']))
    if otrosi_entries:
        otrosi_header = [
            Paragraph('Código', cell_style),
            Paragraph('Fecha generación', cell_style),
            Paragraph('Tipo(s) modificación', cell_style),
            Paragraph('Versión', cell_style),
        ]
        otrosi_data = [otrosi_header]
        for o in otrosi_entries:
            tipos = ', '.join(o.get('mod_types', [])) or 'No determinado'
            otrosi_data.append([
                Paragraph(str(o.get('contract_code')), cell_style),
                Paragraph(str(o.get('creation_date')), cell_style),
                Paragraph(tipos, cell_style),
                Paragraph(str(o.get('version')), cell_style),
            ])
        otrosi_table = Table(otrosi_data, colWidths=[doc.width * 0.25, doc.width * 0.2, doc.width * 0.4, doc.width * 0.15], hAlign='LEFT', repeatRows=1)
        otrosi_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.4, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 7),
            ('LEFTPADDING', (0,0), (-1,-1), 3),
            ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ]))
        story.append(otrosi_table)
    else:
        story.append(Paragraph('No se encontraron Otrosí en el rango.', small))

    def on_page(canvas, d):
        _header(canvas, d, 'Historial Contractual', logo_path)
        # Pie de página
        canvas.saveState()
        page_num = canvas.getPageNumber()
        footer = f"Página {page_num}"
        canvas.setFont('Helvetica', 8)
        canvas.drawRightString(A4[0] - right_margin, bottom_margin / 2, footer)
        canvas.restoreState()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def build_otrosi_entries(contracts: List[EmployeeContract]) -> List[Dict[str, Any]]:
    """Genera lista de otrosí detectando versiones y tipos de modificación comparando con versión previa."""
    # Orden por creation_date para comparar secuencialmente
    ordered = sorted(contracts, key=lambda c: (c.creation_date, c.contract_code))
    entries: List[Dict[str, Any]] = []
    prev_map: Dict[str, EmployeeContract] = {}
    for c in ordered:
        # Detectar versión por sufijo -NN
        parts = str(c.contract_code).split('-')
        version_segment = parts[-1] if parts else '00'
        try:
            version_num = int(version_segment)
        except ValueError:
            version_num = 0
        base_code = '-'.join(parts[:-1]) if len(parts) > 1 else c.contract_code
        if version_num == 0:
            prev_map[base_code] = c
            continue  # versión inicial no es Otrosí
        previous = prev_map.get(base_code)
        mod_types: List[str] = []
        if previous:
            # Comparar campos clave
            if previous.salary_base != c.salary_base:
                mod_types.append('salario')
            if previous.id_employee_charge_id != c.id_employee_charge_id:
                mod_types.append('cargo')
            if previous.id_employee_department_id != getattr(c, 'id_employee_department_id', None):
                mod_types.append('departamento')
            if previous.payment_frequency_type != c.payment_frequency_type:
                mod_types.append('frecuencia_pago')
            if previous.working_hours != c.working_hours:
                mod_types.append('horas')
            if previous.work_mode_type_id != c.work_mode_type_id or previous.workday_type_id != c.workday_type_id:
                mod_types.append('condiciones_laborales')
        # Increments/deductions
        if c.employee_contract_increases.exists():
            mod_types.append('incrementos')
        if c.employee_contract_deductions.exists():
            mod_types.append('deducciones')
        if getattr(c, 'secundary_petition', False) and 'otrosi' not in mod_types:
            mod_types.append('otrosi')
        prev_map[base_code] = c
        entries.append({
            'contract_code': c.contract_code,
            'creation_date': c.creation_date.date(),
            'version': version_num,
            'mod_types': sorted(set(mod_types)) or ['cambio_no_clasificado'],
        })
    return entries
