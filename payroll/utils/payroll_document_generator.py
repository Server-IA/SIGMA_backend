from io import BytesIO
from datetime import datetime, timezone
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
import logging

logger = logging.getLogger(__name__)


class PayrollDocumentGenerator:
    """Generador de documentos PDF para nóminas de empleados."""

    @staticmethod
    def _resolve_logo_path():
        """Resuelve la ruta del logo institucional."""
        try:
            current_dir = Path(__file__).resolve().parent
            payroll_dir = current_dir.parent
            project_root = payroll_dir.parent
            candidates = [
                project_root / 'core' / 'assets' / 'logo.jpg',
                project_root / 'core' / 'assets' / 'logo.png',
                payroll_dir / 'assets' / 'logo.jpg',
                payroll_dir / 'assets' / 'logo.png',
            ]
            for candidate in candidates:
                if candidate.exists():
                    return str(candidate)
        except Exception as e:
            logger.warning(f"Error al resolver logo: {str(e)}")
        return None

    @staticmethod
    def _format_user_name(user):
        """Formatea el nombre del usuario para mostrar."""
        if not user:
            return "Sistema"

        if isinstance(user, str):
            return user

        if isinstance(user, dict):
            name = (user.get('name') or user.get('first_name') or '').strip()
            fln = (user.get('first_last_name') or user.get('last_name') or '').strip()
            sln = (user.get('second_last_name') or '').strip()
            parts = [p for p in [name, fln, sln] if p]
            return ' '.join(parts) if parts else str(user)

        try:
            name = (getattr(user, 'name', None) or getattr(user, 'first_name', '') or '').strip()
            fln = (getattr(user, 'first_last_name', None) or getattr(user, 'last_name', '') or '').strip()
            sln = (getattr(user, 'second_last_name', '') or '').strip()
            parts = [p for p in [name, fln, sln] if p]
            return ' '.join(parts) if parts else str(user)
        except Exception:
            return str(user)

    @staticmethod
    def _format_date(date_obj):
        """Formatea una fecha a string."""
        if not date_obj:
            return "N/A"
        if hasattr(date_obj, 'strftime'):
            return date_obj.strftime("%Y-%m-%d")
        return str(date_obj)

    @staticmethod
    def _format_datetime(dt_obj):
        """Formatea datetime a string."""
        if not dt_obj:
            return "N/A"
        if hasattr(dt_obj, 'strftime'):
            return dt_obj.strftime("%Y-%m-%d %H:%M:%S")
        return str(dt_obj)

    @staticmethod
    def _format_currency(value, symbol=''):
        """Formatea un valor numérico como moneda."""
        try:
            return f"{symbol}{float(value):,.2f}"
        except (ValueError, TypeError):
            return f"{symbol}0.00"

    @staticmethod
    def _get_salary_type_label(salary_type):
        """Obtiene la etiqueta para el tipo de salario."""
        labels = {
            'Por horas': 'horas',
            'Por días': 'días',
            'Mensual fijo': 'meses'
        }
        return labels.get(salary_type, 'unidades')

    @staticmethod
    def generate_pdf(
        payroll,
        employee_data,
        contract,
        contract_increases,
        contract_deductions,
        author_name=None,
        downloader_user=None,
        logo_path=None
    ):
        """
        Genera un PDF de la nómina del empleado.

        Args:
            payroll: Instancia del modelo Payroll
            employee_data: Dict con datos del empleado (document_number, name, first_last_name, etc.)
            contract: Instancia del modelo EmployeeContract
            contract_increases: QuerySet de EmployeeContractIncrease (devengos fijos del contrato)
            contract_deductions: QuerySet de EmployeeContractDeduction (deducciones fijas del contrato)
            author_name: Nombre del autor/responsable de la nómina
            downloader_user: Usuario que descarga (str, dict u objeto)
            logo_path: Ruta al logo (opcional)

        Returns:
            bytes: Contenido del PDF
        """
        if logo_path is None:
            logo_path = PayrollDocumentGenerator._resolve_logo_path()

        buffer = BytesIO()
        left_margin = 2 * cm
        right_margin = 2 * cm
        bottom_margin = 2 * cm

        # Calcular top margin considerando logo
        logo_height = 0
        header_margin = 1.5 * cm
        if logo_path:
            try:
                img_width = 3 * cm
                ir = ImageReader(logo_path)
                iw, ih = ir.getSize()
                ratio = ih / float(iw) if iw else 1.0
                logo_height = img_width * ratio
            except Exception:
                logo_height = 0

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
        small = ParagraphStyle('small', parent=styles['Normal'], fontSize=9, leading=11)
        table_cell_style = ParagraphStyle('table_cell', parent=styles['Normal'], fontSize=8, leading=10, wordWrap='LTR')

        # Obtener símbolo de moneda
        currency_symbol = ''
        try:
            currency_symbol = getattr(payroll.currency_type, 'symbol', '') or ''
        except Exception:
            pass

        # Contador de páginas para mostrar total
        page_info = [0]

        # Encabezado con logo y título
        def header_footer(canvas, doc_content, total_pages=None):
            canvas.saveState()
            width, height = A4

            # Actualizar contador de páginas
            current_page = canvas.getPageNumber()
            if total_pages is None:
                if current_page > page_info[0]:
                    page_info[0] = current_page

            # Logo en la parte superior derecha
            if logo_path:
                try:
                    img_width = 3 * cm
                    ir = ImageReader(logo_path)
                    iw, ih = ir.getSize()
                    ratio = ih / float(iw) if iw else 1.0
                    img_height = img_width * ratio
                    top_padding = 0.5 * cm
                    x = width - img_width - right_margin
                    y = height - img_height - top_padding
                    canvas.drawImage(logo_path, x, y, width=img_width, height=img_height, preserveAspectRatio=True, mask='auto')
                except Exception:
                    pass

            # Título del documento
            canvas.setFont('Helvetica-Bold', 16)
            title = "NÓMINA DE PAGO"
            title_width = canvas.stringWidth(title, 'Helvetica-Bold', 16)
            canvas.drawString((width - title_width) / 2, height - 1 * cm, title)

            # Fecha y hora de generación
            canvas.setFont('Helvetica', 9)
            gen_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            date_width = canvas.stringWidth(f"Generado: {gen_date}", 'Helvetica', 9)
            canvas.drawString((width - date_width) / 2, height - 1.5 * cm, f"Generado: {gen_date}")

            # Pie de página con paginación completa
            page_num = current_page
            total = total_pages if total_pages is not None else page_info[0]
            user_name = PayrollDocumentGenerator._format_user_name(downloader_user)

            if total > 0 and total_pages is not None:
                footer_text = f"Descargado por: {user_name} | Página {page_num} / {total}"
            else:
                footer_text = f"Descargado por: {user_name} | Página {page_num}"

            canvas.setFont('Helvetica', 8)
            footer_width = canvas.stringWidth(footer_text, 'Helvetica', 8)
            canvas.drawString((width - footer_width) / 2, bottom_margin / 2, footer_text)

            canvas.restoreState()

        def on_page_first(canvas, doc_content):
            header_footer(canvas, doc_content, total_pages=None)

        def on_page_final(canvas, doc_content):
            header_footer(canvas, doc_content, total_pages=page_info[0])

        def create_story(available_width):
            story = []

            # Título principal
            story.append(Spacer(1, 0.5 * cm))
            story.append(Paragraph("NÓMINA DE PAGO", styles['Title']))
            story.append(Spacer(1, 0.3 * cm))

            # ==========================================
            # Sección 1: Datos del Empleado
            # ==========================================
            story.append(Paragraph("1. DATOS DEL EMPLEADO", styles['Heading2']))
            story.append(Spacer(1, 0.2 * cm))

            # Extraer datos del empleado
            document_number = employee_data.get('document_number', 'N/A') if employee_data else 'N/A'
            employee_name = PayrollDocumentGenerator._format_user_name(employee_data) if employee_data else 'N/A'
            charge_name = getattr(contract.id_employee_charge, 'name', 'N/A') if contract else 'N/A'
            contract_code = getattr(contract, 'contract_code', 'N/A') if contract else 'N/A'

            employee_rows = [
                ["Número de identificación", str(document_number)],
                ["Nombre completo", str(employee_name)],
                ["Cargo", str(charge_name)],
                ["Período de nómina", f"{PayrollDocumentGenerator._format_date(payroll.start_date)} - {PayrollDocumentGenerator._format_date(payroll.end_date)}"],
                ["Contrato asociado", str(contract_code)],
                ["Fecha de generación", PayrollDocumentGenerator._format_datetime(payroll.creation_date)],
                ["Autor", str(author_name or 'N/A')],
            ]

            employee_table = Table(employee_rows, colWidths=[available_width * 0.35, available_width * 0.65], hAlign='LEFT')
            employee_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ]))
            story.append(employee_table)
            story.append(Spacer(1, 0.5 * cm))

            # ==========================================
            # Sección 2: Devengados
            # ==========================================
            story.append(Paragraph("2. DEVENGADOS", styles['Heading2']))
            story.append(Spacer(1, 0.2 * cm))

            # Devengos fijos del contrato
            story.append(Paragraph("Fijos del contrato:", small))
            story.append(Spacer(1, 0.1 * cm))

            contract_inc_list = list(contract_increases) if contract_increases else []
            if contract_inc_list:
                inc_header = [
                    Paragraph("Tipo", table_cell_style),
                    Paragraph("Descripción", table_cell_style),
                    Paragraph("Valor", table_cell_style),
                ]
                inc_table_data = [inc_header]
                for inc in contract_inc_list:
                    type_name = getattr(inc.increase_type, 'name', 'N/A') if inc.increase_type else 'N/A'
                    amount = inc.amount if inc.amount is not None else inc.amount_value
                    inc_table_data.append([
                        Paragraph(str(type_name), table_cell_style),
                        Paragraph(str(inc.description or '-'), table_cell_style),
                        Paragraph(PayrollDocumentGenerator._format_currency(amount, currency_symbol), table_cell_style),
                    ])
                inc_table = Table(inc_table_data, colWidths=[available_width * 0.3, available_width * 0.45, available_width * 0.25], hAlign='LEFT', repeatRows=1)
                inc_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
                ]))
                story.append(inc_table)
            else:
                story.append(Paragraph("Sin devengos fijos del contrato", table_cell_style))
            story.append(Spacer(1, 0.3 * cm))

            # Devengos adicionales (ajustes de nómina)
            story.append(Paragraph("Adicionales (ajustes):", small))
            story.append(Spacer(1, 0.1 * cm))

            payroll_inc_list = list(payroll.payroll_increases.all()) if hasattr(payroll, 'payroll_increases') else []
            if payroll_inc_list:
                adj_inc_header = [
                    Paragraph("Tipo", table_cell_style),
                    Paragraph("Descripción", table_cell_style),
                    Paragraph("Valor", table_cell_style),
                ]
                adj_inc_table_data = [adj_inc_header]
                for inc in payroll_inc_list:
                    type_name = getattr(inc.increase_type, 'name', 'N/A') if inc.increase_type else 'N/A'
                    amount = inc.calculated_amount if inc.calculated_amount is not None else (inc.amount if inc.amount is not None else inc.amount_value)
                    adj_inc_table_data.append([
                        Paragraph(str(type_name), table_cell_style),
                        Paragraph(str(inc.description or '-'), table_cell_style),
                        Paragraph(PayrollDocumentGenerator._format_currency(amount, currency_symbol), table_cell_style),
                    ])
                adj_inc_table = Table(adj_inc_table_data, colWidths=[available_width * 0.3, available_width * 0.45, available_width * 0.25], hAlign='LEFT', repeatRows=1)
                adj_inc_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
                ]))
                story.append(adj_inc_table)
            else:
                story.append(Paragraph("Sin ajustes adicionales de devengos", table_cell_style))
            story.append(Spacer(1, 0.3 * cm))

            # Total devengado
            total_devengado = PayrollDocumentGenerator._format_currency(payroll.total_increments, currency_symbol)
            story.append(Paragraph(f"<b>TOTAL DEVENGADO: {total_devengado}</b>", small))
            story.append(Spacer(1, 0.5 * cm))

            # ==========================================
            # Sección 3: Deducciones
            # ==========================================
            story.append(Paragraph("3. DEDUCCIONES", styles['Heading2']))
            story.append(Spacer(1, 0.2 * cm))

            # Deducciones fijas del contrato
            story.append(Paragraph("Fijas del contrato:", small))
            story.append(Spacer(1, 0.1 * cm))

            contract_ded_list = list(contract_deductions) if contract_deductions else []
            if contract_ded_list:
                ded_header = [
                    Paragraph("Tipo", table_cell_style),
                    Paragraph("Descripción", table_cell_style),
                    Paragraph("Valor", table_cell_style),
                ]
                ded_table_data = [ded_header]
                for ded in contract_ded_list:
                    type_name = getattr(ded.deduction_type, 'name', 'N/A') if ded.deduction_type else 'N/A'
                    amount = ded.amount if ded.amount is not None else ded.amount_value
                    ded_table_data.append([
                        Paragraph(str(type_name), table_cell_style),
                        Paragraph(str(ded.description or '-'), table_cell_style),
                        Paragraph(PayrollDocumentGenerator._format_currency(amount, currency_symbol), table_cell_style),
                    ])
                ded_table = Table(ded_table_data, colWidths=[available_width * 0.3, available_width * 0.45, available_width * 0.25], hAlign='LEFT', repeatRows=1)
                ded_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
                ]))
                story.append(ded_table)
            else:
                story.append(Paragraph("Sin deducciones fijas del contrato", table_cell_style))
            story.append(Spacer(1, 0.3 * cm))

            # Deducciones adicionales (ajustes de nómina)
            story.append(Paragraph("Adicionales (ajustes):", small))
            story.append(Spacer(1, 0.1 * cm))

            payroll_ded_list = list(payroll.payroll_deductions.all()) if hasattr(payroll, 'payroll_deductions') else []
            if payroll_ded_list:
                adj_ded_header = [
                    Paragraph("Tipo", table_cell_style),
                    Paragraph("Descripción", table_cell_style),
                    Paragraph("Valor", table_cell_style),
                ]
                adj_ded_table_data = [adj_ded_header]
                for ded in payroll_ded_list:
                    type_name = getattr(ded.deduction_type, 'name', 'N/A') if ded.deduction_type else 'N/A'
                    amount = ded.calculated_amount if ded.calculated_amount is not None else (ded.amount if ded.amount is not None else ded.amount_value)
                    adj_ded_table_data.append([
                        Paragraph(str(type_name), table_cell_style),
                        Paragraph(str(ded.description or '-'), table_cell_style),
                        Paragraph(PayrollDocumentGenerator._format_currency(amount, currency_symbol), table_cell_style),
                    ])
                adj_ded_table = Table(adj_ded_table_data, colWidths=[available_width * 0.3, available_width * 0.45, available_width * 0.25], hAlign='LEFT', repeatRows=1)
                adj_ded_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
                ]))
                story.append(adj_ded_table)
            else:
                story.append(Paragraph("Sin ajustes adicionales de deducciones", table_cell_style))
            story.append(Spacer(1, 0.3 * cm))

            # Total deducciones
            total_deducciones = PayrollDocumentGenerator._format_currency(payroll.total_deductions, currency_symbol)
            story.append(Paragraph(f"<b>TOTAL DEDUCCIONES: {total_deducciones}</b>", small))
            story.append(Spacer(1, 0.5 * cm))

            # ==========================================
            # Sección 4: Neto a Pagar
            # ==========================================
            story.append(Paragraph("4. NETO A PAGAR", styles['Heading2']))
            story.append(Spacer(1, 0.2 * cm))

            # Obtener tipo de salario para la etiqueta
            salary_type = getattr(contract, 'salary_type', 'Mensual fijo') if contract else 'Mensual fijo'
            time_unit = PayrollDocumentGenerator._get_salary_type_label(salary_type)

            summary_rows = [
                ["Salario base", PayrollDocumentGenerator._format_currency(payroll.base_salary, currency_symbol)],
                [f"Tiempo trabajado ({time_unit})", f"{payroll.time_worked:.2f}"],
                ["(+) Total devengados", PayrollDocumentGenerator._format_currency(payroll.total_increments, currency_symbol)],
                ["(-) Total deducciones", PayrollDocumentGenerator._format_currency(payroll.total_deductions, currency_symbol)],
            ]

            summary_table = Table(summary_rows, colWidths=[available_width * 0.6, available_width * 0.4], hAlign='LEFT')
            summary_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 0.3 * cm))

            # Total a pagar destacado
            net_pay = PayrollDocumentGenerator._format_currency(payroll.net_pay, currency_symbol)
            total_row = [["TOTAL A PAGAR", net_pay]]
            total_table = Table(total_row, colWidths=[available_width * 0.6, available_width * 0.4], hAlign='LEFT')
            total_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#E8F5E9')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#4CAF50')),
                ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(total_table)

            return story

        # Primera pasada: construir para contar páginas
        doc.build(create_story(doc.width), onFirstPage=on_page_first, onLaterPages=on_page_first)

        # Obtener el total de páginas
        total_pages = page_info[0]

        # Reconstruir con el total conocido usando un nuevo buffer
        if total_pages > 0:
            buffer_final = BytesIO()
            doc_final = SimpleDocTemplate(
                buffer_final,
                pagesize=A4,
                leftMargin=left_margin,
                rightMargin=right_margin,
                topMargin=top_margin,
                bottomMargin=bottom_margin,
            )
            doc_final.build(create_story(doc_final.width), onFirstPage=on_page_final, onLaterPages=on_page_final)
            pdf_bytes = buffer_final.getvalue()
            buffer_final.close()
        else:
            pdf_bytes = buffer.getvalue()

        buffer.close()
        return pdf_bytes

