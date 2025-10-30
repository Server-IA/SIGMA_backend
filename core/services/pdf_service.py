from io import BytesIO
from datetime import datetime, timezone
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
import requests
import logging
from core.services import csc_service

logger = logging.getLogger(__name__)


def _header(canvas, doc, logo_path: str | None):
    """Dibuja encabezado en cada página (logo a la derecha)."""
    canvas.saveState()
    width, height = A4
    if logo_path:
        try:
            img_width = 3 * cm
            ir = ImageReader(logo_path)
            iw, ih = ir.getSize()
            ratio = ih / float(iw) if iw else 1.0
            img_height = img_width * ratio
            # Small padding from the top edge so the image is inside the top margin
            top_padding = 0.5 * cm
            x = getattr(doc, 'leftMargin', 1.5 * cm)
            y = height - img_height - top_padding
            # Draw within the page top area; top_margin calculation guarantees no overlap
            canvas.drawImage(logo_path, x, y, width=img_width, height=img_height, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    canvas.restoreState()


def build_maintenance_report_pdf(report, maintenance_items, spare_parts, downloader_user: str | None = None, logo_path: str | None = None, technician_name: str | None = None, technicians_list: list | None = None) -> bytes:
    """
    Genera PDF del reporte de mantenimiento con soporte para múltiples técnicos,
    subtotal en mantenimientos, costo total en repuestos y símbolo de moneda.

    Parámetros:
      - report: instancia de MaintenanceReport
      - maintenance_items: lista de dicts {'name','type','technician','cost'}
      - spare_parts: lista de dicts {'name','brand','quantity','unit_cost','total'}
      - downloader_user: nombre del usuario que descarga (string)
      - technicians_list: lista de nombres de técnicos (opcional)

    Retorna bytes del PDF.
    """

    # Resolver logo si no fue provisto
    if logo_path is None:
        try:
            current_dir = Path(__file__).resolve().parent
            core_dir = current_dir.parent
            project_root = core_dir.parent
            candidates = [
                core_dir / 'assets' / 'logo.jpg',
                core_dir / 'assets' / 'logo.png',
                project_root / 'core' / 'assets' / 'logo.jpg',
                project_root / 'core' / 'assets' / 'logo.png',
            ]
            for c in candidates:
                if c.exists():
                    logo_path = str(c)
                    break
        except Exception:
            logo_path = None

    buffer = BytesIO()
    # Márgenes base
    left_margin = 2 * cm
    right_margin = 2 * cm
    bottom_margin = 2 * cm

    # Calcular altura del logo si existe para reservar espacio en el top margin
    logo_height = 0
    header_margin = 1.5 * cm
    if logo_path:
        try:
            # Usar el mismo ancho que en el header (3 cm) y calcular altura proporcional
            img_width = 3 * cm
            ir = ImageReader(logo_path)
            iw, ih = ir.getSize()
            ratio = ih / float(iw) if iw else 1.0
            logo_height = img_width * ratio
        except Exception:
            logo_height = 0

    # Definir top margin suficientemente grande para que el logo no solape el contenido
    # Usar el mismo margin que el header y agregar padding extra para evitar solapamiento en páginas siguientes
    top_margin = max(2 * cm, logo_height + header_margin + (1.0 * cm))

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
    )
    styles = getSampleStyleSheet()
    # Use doc.width (content width) as the available width for tables
    available_width = None

    # Estilos: fuente más pequeña para tablas y wrapping
    small = ParagraphStyle('small', parent=styles['Normal'], fontSize=9, leading=11)
    table_cell_style = ParagraphStyle('table_cell', parent=styles['Normal'], fontSize=8, leading=10, wordWrap='LTR')

    story = []

    # Título
    story.append(Paragraph("Reporte de Mantenimiento", styles['Title']))
    story.append(Spacer(1, 6))

    # Subtítulo "Detalle del mantenimiento" encima de la fecha
    story.append(Paragraph("Detalle del reporte", styles['Heading2']))
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"Fecha de generación: {now_str}", small))
    # Mostrar nombre completo del usuario que descarga (nombre + apellidos). El
    # parámetro downloader_user puede ser un str, dict o un objeto con atributos.
    if downloader_user:
        downloader_display = None
        # Si ya es string, usarlo directamente
        if isinstance(downloader_user, str):
            downloader_display = downloader_user
        # Si es mapping/dict, extraer campos posibles
        elif isinstance(downloader_user, dict):
            name = (downloader_user.get('name') or downloader_user.get('first_name') or "").strip()
            fln = (downloader_user.get('first_last_name') or downloader_user.get('last_name') or "").strip()
            sln = (downloader_user.get('second_last_name') or "").strip()
            parts = [p for p in [name, fln, sln] if p]
            downloader_display = ' '.join(parts) if parts else str(downloader_user)
        else:
            # Intentar leer atributos del objeto
            try:
                name = (getattr(downloader_user, 'name', None) or getattr(downloader_user, 'first_name', '') or '').strip()
                fln = (getattr(downloader_user, 'first_last_name', None) or getattr(downloader_user, 'last_name', '') or '').strip()
                sln = (getattr(downloader_user, 'second_last_name', '') or '').strip()
                parts = [p for p in [name, fln, sln] if p]
                downloader_display = ' '.join(parts) if parts else str(downloader_user)
            except Exception:
                downloader_display = str(downloader_user)

        if downloader_display:
            story.append(Paragraph(f"Usuario que descarga: {downloader_display}", small))
    story.append(Spacer(1, 12))

    # Datos de la maquinaria
    scheduling = getattr(report, 'id_maintenance_scheduling', None)
    machinery = getattr(scheduling, 'id_machinery', None) if scheduling else None

    story.append(Paragraph("Datos de la Maquinaria", styles['Heading2']))

    # Imagen de maquinaria (opcional)
    machinery_image = None
    image_path = getattr(machinery, 'image_path', None) if machinery else None
    if image_path:
        try:
            resp = requests.get(image_path, timeout=10)
            if resp.status_code == 200:
                img_reader = ImageReader(BytesIO(resp.content))
                img_w = 5 * cm
                iw, ih = img_reader.getSize()
                ratio = ih / float(iw) if iw else 1.0
                img_h = img_w * ratio
                if img_h > 4 * cm:
                    img_h = 4 * cm
                    img_w = img_h / ratio
                machinery_image = Image(BytesIO(resp.content), width=img_w, height=img_h)
        except Exception:
            machinery_image = None

    # Resolver ubicación legible con CSC API
    raw_country = getattr(machinery, 'id_country', None)
    raw_state = getattr(machinery, 'id_department', None)
    raw_city = getattr(machinery, 'id_city', None)

    country_iso2 = csc_service.get_country_iso2(raw_country) if raw_country else None
    state_iso2 = csc_service.get_state_iso2(country_iso2 or raw_country, raw_state) if raw_state else None
    country_name = csc_service.resolve_country_name(raw_country) if raw_country else 'N/D'
    state_name = csc_service.resolve_state_name(country_iso2 or raw_country, raw_state) if raw_state else 'N/D'
    city_name = csc_service.resolve_city_name(country_iso2 or raw_country, state_iso2 or (raw_state or ''), raw_city) if raw_city is not None else 'N/D'
    location_display = f"{country_name} - {state_name} - {city_name}"

    machinery_rows = [
        ["Serial", str(getattr(machinery, 'serial_number', 'N/D'))],
        ["Nombre", str(getattr(machinery, 'machinery_name', 'N/D'))],
        ["Tipo", str(getattr(getattr(machinery, 'machinery_type', None), 'name', 'N/D'))],
        ["Ubicación", location_display]
    ]

    if machinery_image:
        machinery_table = Table([[Table(machinery_rows, hAlign='LEFT'), machinery_image]], colWidths=[10 * cm, 6 * cm])
        machinery_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        story.append(machinery_table)
    else:
        story.append(Table(machinery_rows, hAlign='LEFT'))
    story.append(Spacer(1, 12))

    # Detalles del mantenimiento
    # Preparar lista de técnicos como Paragraph para wrapping
    if technicians_list:
        tech_text = ', '.join([t for t in technicians_list if t])
    else:
        tech_text = technician_name or ''
    tech_par = Paragraph(tech_text or 'N/D', table_cell_style)

    scheduled_at = getattr(scheduling, 'scheduled_at', None) if scheduling else None
    if scheduled_at and hasattr(scheduled_at, 'strftime'):
        formatted_date = scheduled_at.strftime("%Y-%m-%d %H:%M:%S")
    else:
        formatted_date = 'N/D'

    hours = int(getattr(report, 'time_invested_hours', 0) or 0)
    minutes = int(getattr(report, 'time_invested_minutes', 0) or 0)
    seconds = int(getattr(report, 'time_invested_seconds', 0) or 0)
    time_str = f"{hours}h {minutes}m {seconds}s"

    story.append(Paragraph("Detalle del mantenimiento", styles['Heading2']))
    detail_rows = [
        ["Fecha mantenimiento", formatted_date],
        ["Tipo mantenimiento", str(getattr(getattr(scheduling, 'maintenance_type', None), 'name', 'N/D'))],
        ["Descripción", Paragraph(str(getattr(report, 'description', '') or ''), table_cell_style)],
        ["Tiempo invertido", time_str],
        ["Técnicos asignados", tech_par],
    ]

    # if available_width wasn't set yet, use doc.width
    if available_width is None:
        try:
            available_width = doc.width
        except Exception:
            available_width = A4[0] - left_margin - right_margin

    detail_table = Table(detail_rows, colWidths=[available_width * 0.35, available_width * 0.65], hAlign='LEFT')
    detail_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 12))

    # Obtener símbolo de moneda
    try:
        currency_symbol = getattr(getattr(report, 'currency_unit', None), 'symbol', '') or ''
    except Exception:
        currency_symbol = ''

    # Mantenimientos realizados - tabla con subtotal
    story.append(Paragraph("Mantenimientos Realizados", styles['Heading2']))
    maint_header = [
        Paragraph("Mantenimiento", table_cell_style),
        Paragraph("Tipo", table_cell_style),
        Paragraph("Técnico", table_cell_style),
        Paragraph(f"Costo {f'({currency_symbol})' if currency_symbol else ''}", table_cell_style),
    ]

    maint_table_data = [maint_header]
    maint_total = 0.0
    for it in maintenance_items or []:
        name = it.get('name', 'N/D')
        ttype = it.get('type', 'N/D')
        tech = it.get('technician', 'N/D')
        cost_raw = it.get('cost', 0) or 0
        try:
            cost_value = float(cost_raw)
        except Exception:
            cost_value = 0.0
        maint_total += cost_value
        maint_table_data.append([
            Paragraph(str(name), table_cell_style),
            Paragraph(str(ttype), table_cell_style),
            Paragraph(str(tech), table_cell_style),
            Paragraph(f"{currency_symbol}{cost_value:,.2f}", table_cell_style),
        ])
    # Subtotal row
    maint_table_data.append([
        Paragraph("Subtotal", table_cell_style), '', '', Paragraph(f"{currency_symbol}{maint_total:,.2f}", table_cell_style)
    ])

    # Column widths proporcionales al ancho disponible para evitar overflow
    maint_col_widths = [available_width * 0.5, available_width * 0.2, available_width * 0.2, available_width * 0.1]
    maint_table = Table(maint_table_data, colWidths=maint_col_widths, hAlign='LEFT', repeatRows=1)
    maint_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-2, -1), 0.5, colors.grey),
        ('GRID', (-1, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('ALIGN', (-1,1), (-1,-1), 'RIGHT'),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
    ]))
    story.append(maint_table)
    story.append(Spacer(1, 12))

    # Repuestos utilizados - tabla con fila final
    story.append(Paragraph("Repuestos Utilizados", styles['Heading2']))
    parts_header = [
        Paragraph("Repuesto", table_cell_style),
        Paragraph("Marca", table_cell_style),
        Paragraph("Cantidad", table_cell_style),
        Paragraph(f"Costo Unitario {f'({currency_symbol})' if currency_symbol else ''}", table_cell_style),
        Paragraph(f"Costo Total {f'({currency_symbol})' if currency_symbol else ''}", table_cell_style),
    ]

    parts_table_data = [parts_header]
    spare_total = 0.0
    for sp in spare_parts or []:
        name = sp.get('name', 'N/D')
        brand = sp.get('brand', 'N/D')
        qty = sp.get('quantity', 0)
        unit = sp.get('unit_cost', 0) or 0
        total_raw = sp.get('total', 0) or 0
        try:
            total_value = float(total_raw)
        except Exception:
            total_value = 0.0
        try:
            unit_value = float(unit)
        except Exception:
            unit_value = 0.0
        spare_total += total_value
        parts_table_data.append([
            Paragraph(str(name), table_cell_style),
            Paragraph(str(brand), table_cell_style),
            Paragraph(str(qty), table_cell_style),
            Paragraph(f"{currency_symbol}{unit_value:,.2f}", table_cell_style),
            Paragraph(f"{currency_symbol}{total_value:,.2f}", table_cell_style),
        ])
    # Fila final: costo total de los repuestos
    parts_table_data.append([
        Paragraph("Costo total de los repuestos", table_cell_style), '', '', '', Paragraph(f"{currency_symbol}{spare_total:,.2f}", table_cell_style)
    ])

    parts_col_widths = [available_width * 0.35, available_width * 0.2, available_width * 0.12, available_width * 0.165, available_width * 0.165]
    parts_table = Table(parts_table_data, colWidths=parts_col_widths, hAlign='LEFT', repeatRows=1)
    parts_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('ALIGN', (3,1), (4,-1), 'RIGHT'),
        ('ALIGN', (0,0), (1,-1), 'LEFT'),
    ]))
    story.append(parts_table)
    story.append(Spacer(1, 12))

    # Recomendaciones (si existen)
    recommendations_text = getattr(report, 'recommendations', None)
    if recommendations_text and str(recommendations_text).strip():
        story.append(Paragraph("Recomendaciones", styles['Heading2']))
        story.append(Paragraph(str(recommendations_text), table_cell_style))
        story.append(Spacer(1, 12))

    # Resumen económico
    story.append(Paragraph("Resumen Económico", styles['Heading2']))
    try:
        total_general = maint_total + float(getattr(report, 'spare_parts_total_cost', spare_total) or spare_total)
    except Exception:
        total_general = maint_total + spare_total

    # Resumen económico como líneas de texto (no tabla), con símbolo de unidad y paréntesis al final
    try:
        total_general = maint_total + float(getattr(report, 'spare_parts_total_cost', spare_total) or spare_total)
    except Exception:
        total_general = maint_total + spare_total

    # Mostrar símbolo también entre paréntesis al final de cada total si existe
    symbol_paren = f" ({currency_symbol})" if currency_symbol else ""
    story.append(Paragraph(f"Total mantenimientos: {currency_symbol}{maint_total:,.2f}{symbol_paren}", small))
    story.append(Paragraph(f"Total repuestos: {currency_symbol}{spare_total:,.2f}{symbol_paren}", small))
    story.append(Paragraph(f"Total general: {currency_symbol}{total_general:,.2f}{symbol_paren}", small))
    story.append(Spacer(1, 12))

    # Encabezado en todas las páginas
    def on_page(canvas, d):
        _header(canvas, d, logo_path)

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
