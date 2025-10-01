from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
import requests
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


def _header(canvas, doc, logo_path: str | None):
    """Dibuja encabezado en cada página (logo a la derecha)."""
    canvas.saveState()
    width, height = A4
    if logo_path:
        try:
            # 3 cm de ancho, calculamos alto proporcional
            img_width = 3 * cm
            ir = ImageReader(logo_path)
            iw, ih = ir.getSize()
            ratio = ih / float(iw) if iw else 1.0
            img_height = img_width * ratio
            margin = 1.5 * cm
            # Posicionar en la esquina superior IZQUIERDA
            x = margin
            y = height - img_height - margin
            canvas.drawImage(logo_path, x, y, width=img_width, height=img_height, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    canvas.restoreState()


def build_maintenance_report_pdf(report, maintenance_items, spare_parts, downloader_user_id=None, logo_path: str | None = None, technician_name: str | None = None) -> bytes:
    """
    Genera un PDF en memoria con los datos del reporte de mantenimiento.

    Parámetros:
      - report: instancia de MaintenanceReport (con select_related ya resuelto)
      - maintenance_items: lista de dicts de mantenimientos realizados
      - spare_parts: lista de dicts de repuestos usados
      - downloader_user_id: opcional, para imprimir quién descarga

    Retorna:
      - bytes del PDF
    """

    # Resolver logo si no fue provisto
    if logo_path is None:
        try:
            from pathlib import Path
            current_dir = Path(__file__).resolve().parent  # .../core/services
            core_dir = current_dir.parent                  # .../core
            project_root = core_dir.parent                 # .../AppMachineryPayrollBackend

            # 1) Sibling assets to services: core/assets/logo.jpg
            candidates = [
                core_dir / 'assets' / 'logo.jpg',
                core_dir / 'assets' / 'logo.png',
                # 2) Root/core/assets as fallback (equivalente al 1, por compatibilidad)
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
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Encabezado
    story.append(Paragraph("Reporte de Mantenimiento", styles['Title']))
    story.append(Spacer(1, 12))

    # Datos generales
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    story.append(Paragraph(f"Fecha de generación: {now_str}", styles['Normal']))
    if downloader_user_id is not None:
        story.append(Paragraph(f"Usuario que descarga: {downloader_user_id}", styles['Normal']))
    story.append(Spacer(1, 12))

    # Maquinaria
    scheduling = report.id_maintenance_scheduling
    machinery = scheduling.id_machinery
    
    # Crear tabla con imagen de la maquinaria
    story.append(Paragraph("Datos de la Maquinaria", styles['Heading2']))
    
    # Intentar cargar imagen de Firebase
    machinery_image = None
    image_path = getattr(machinery, 'image_path', None)
    if image_path:
        try:
            logger.info(f"Intentando descargar imagen de maquinaria desde: {image_path}")
            # Descargar imagen desde Firebase
            response = requests.get(image_path, timeout=10)
            if response.status_code == 200:
                # Crear ImageReader desde bytes para obtener dimensiones
                img_reader = ImageReader(BytesIO(response.content))
                # Redimensionar imagen (máximo 5cm de ancho, más pequeña)
                img_width = 5 * cm
                iw, ih = img_reader.getSize()
                ratio = ih / float(iw) if iw else 1.0
                img_height = img_width * ratio
                # Limitar altura máxima
                if img_height > 4 * cm:
                    img_height = 4 * cm
                    img_width = img_height / ratio
                # Crear Image con BytesIO directamente
                machinery_image = Image(BytesIO(response.content), width=img_width, height=img_height)
                logger.info(f"Imagen de maquinaria cargada exitosamente. Dimensiones: {img_width:.1f}cm x {img_height:.1f}cm")
            else:
                logger.warning(f"No se pudo descargar imagen de maquinaria. Status code: {response.status_code}, URL: {image_path}")
        except requests.exceptions.Timeout:
            logger.error(f"Timeout al descargar imagen de maquinaria desde: {image_path}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión al descargar imagen de maquinaria desde {image_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado al procesar imagen de maquinaria desde {image_path}: {str(e)}")
    else:
        logger.info(f"Maquinaria {getattr(machinery, 'machinery_name', 'N/D')} no tiene image_path configurado")
    
    # Crear tabla con datos de maquinaria
    machinery_rows = [
        ["Serial", str(getattr(machinery, 'serial_number', 'N/D'))],
        ["Nombre", str(getattr(machinery, 'machinery_name', 'N/D'))],
        ["Tipo", str(getattr(getattr(machinery, 'machinery_type', None), 'name', 'N/D'))],
        ["Ubicación", f"{getattr(machinery,'id_country', 'N/D')}-{getattr(machinery,'id_department','N/D')}-{getattr(machinery,'id_city','N/D')}"]
    ]
    
    # Si hay imagen, crear tabla de dos columnas
    if machinery_image:
        # Crear tabla con datos a la izquierda e imagen a la derecha
        machinery_table_data = [
            [Table(machinery_rows, hAlign='LEFT'), machinery_image]
        ]
        machinery_table = Table(machinery_table_data, colWidths=[10*cm, 6*cm])
        machinery_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (0, 0), 0),
            ('RIGHTPADDING', (1, 0), (1, 0), 0),
            # Marco para la imagen
            ('BOX', (1, 0), (1, 0), 1, colors.grey),
            ('PADDING', (1, 0), (1, 0), 5),
        ]))
        story.append(machinery_table)
    else:
        # Sin imagen, tabla normal
        story.append(Table(machinery_rows, hAlign='LEFT'))
    
    story.append(Spacer(1, 12))

    # Detalles del mantenimiento
    # Nombre del técnico (si fue provisto desde el caller)
    tech_display = technician_name or str(getattr(getattr(scheduling, 'assigned_technician', None), 'id_user', 'N/D'))

    # Formatear fecha de mantenimiento
    scheduled_at = getattr(scheduling, 'scheduled_at', None)
    if scheduled_at:
        # Convertir datetime a string sin zona horaria
        if hasattr(scheduled_at, 'strftime'):
            formatted_date = scheduled_at.strftime("%Y-%m-%d %H:%M")
        else:
            formatted_date = str(scheduled_at)
    else:
        formatted_date = 'N/D'
    
    detail_rows = [
        ["Fecha mantenimiento", formatted_date],
        ["Tipo mantenimiento", str(getattr(getattr(scheduling, 'maintenance_type', None), 'name', 'N/D'))],
        ["Descripción", report.description or ""],
        ["Tiempo invertido", f"{report.time_invested_hours}h {report.time_invested_minutes}m"],
        ["Técnico asignado", tech_display],
    ]
    story.append(Paragraph("Detalles del Mantenimiento", styles['Heading2']))
    story.append(Table(detail_rows, hAlign='LEFT'))
    story.append(Spacer(1, 12))

    # Mantenimientos realizados
    story.append(Paragraph("Mantenimientos Realizados", styles['Heading2']))
    maint_table_data = [["Mantenimiento", "Tipo", "Técnico", "Costo"]]
    for item in maintenance_items:
        maint_table_data.append([
            item.get('name', 'N/D'),
            item.get('type', 'N/D'),
            item.get('technician', 'N/D'),
            item.get('cost', 'N/D'),
        ])
    maint_table = Table(maint_table_data, hAlign='LEFT')
    maint_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    story.append(maint_table)
    story.append(Spacer(1, 12))

    # Repuestos usados
    story.append(Paragraph("Repuestos Utilizados", styles['Heading2']))
    parts_table_data = [["Repuesto", "Marca", "Cantidad", "Costo Unitario", "Costo Total"]]
    for sp in spare_parts:
        parts_table_data.append([
            sp.get('name','N/D'),
            sp.get('brand','N/D'),
            sp.get('quantity', 0),
            sp.get('unit_cost', 0),
            sp.get('total', 0),
        ])
    parts_table = Table(parts_table_data, hAlign='LEFT')
    parts_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    story.append(parts_table)
    story.append(Spacer(1, 12))

    # Recomendaciones
    story.append(Paragraph("Recomendaciones", styles['Heading2']))
    story.append(Paragraph(report.recommendations or "", styles['Normal']))
    story.append(Spacer(1, 12))

    # Resumen económico
    story.append(Paragraph("Resumen Económico", styles['Heading2']))
    # Calcular total de mantenimientos desde los items recibidos
    try:
        maint_total = 0.0
        for it in maintenance_items:
            value = it.get('cost', 0) if isinstance(it, dict) else 0
            try:
                maint_total += float(value)
            except (TypeError, ValueError):
                pass
    except Exception:
        maint_total = 0.0

    total_general = maint_total + float(getattr(report, 'spare_parts_total_cost', 0) or 0)
    econ_rows = [
        ["Total mantenimientos", f"{maint_total}"],
        ["Total repuestos", f"{report.spare_parts_total_cost}"],
        ["Total general", f"{total_general}"],
    ]
    story.append(Table(econ_rows, hAlign='LEFT'))

    # Encabezado en todas las páginas
    def on_page(canvas, d):
        _header(canvas, d, logo_path)

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


