from io import BytesIO
from datetime import datetime, timezone
from typing import Any, Dict, List
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader


def _resolve_logo_path() -> str | None:
    try:
        current_dir = Path(__file__).resolve().parent
        core_dir = current_dir
        project_root = core_dir.parent
        candidates = [
            core_dir / "assets" / "logo.jpg",
            core_dir / "assets" / "logo.png",
            project_root / "core" / "assets" / "logo.jpg",
            project_root / "core" / "assets" / "logo.png",
        ]
        for c in candidates:
            if c.exists():
                return str(c)
    except Exception:
        return None
    return None


def _header(canvas, doc, logo_path: str | None, employee_ident: str | None):
    canvas.saveState()
    width, height = A4

    if logo_path:
        try:
            img_width = 2.5 * cm
            ir = ImageReader(logo_path)
            iw, ih = ir.getSize()
            ratio = ih / float(iw) if iw else 1.0
            img_height = img_width * ratio
            top_padding = 0.5 * cm
            x = getattr(doc, "leftMargin", 1.5 * cm)
            y = height - img_height - top_padding
            canvas.drawImage(logo_path, x, y, width=img_width, height=img_height, preserveAspectRatio=True, mask="auto")
        except Exception:
            pass

    title_text = "Informe de Historial de Nóminas"
    ident_text = f"Empleado: {employee_ident or 'N/D'}"
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawRightString(width - 1.5 * cm, height - 1 * cm, title_text)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(width - 1.5 * cm, height - 1.5 * cm, ident_text)

    canvas.restoreState()


def build_payroll_history_pdf(
    employee_info: Dict[str, Any],
    payroll_items: List[Dict[str, Any]],
    downloader_user: str | None = None,
    date_from=None,
    date_to=None,

) -> bytes:
    """Genera PDF del historial de nóminas de un empleado.

    employee_info:
      - id_employee
      - identification
      - full_name
      - department_name
      - charge_name

    payroll_items: lista de dicts con la estructura construida por PayrollHistoryService.
    """
    buffer = BytesIO()

    logo_path = _resolve_logo_path()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=3 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    # Versión compacta: fuentes un poco más pequeñas y leading ajustado
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, leading=9.5)
    table_cell_style = ParagraphStyle("table_cell", parent=styles["Normal"], fontSize=7, leading=8.5, wordWrap="LTR")

    story = []

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    ident = employee_info.get("identification") or "N/D"
    full_name = employee_info.get("full_name") or "N/D"
    department_name = employee_info.get("department_name") or "N/D"
    charge_name = employee_info.get("charge_name") or "N/D"
    currency_symbol = employee_info.get("currency_symbol") or ""
    global_summary = employee_info.get("global_summary") or {}

    story.append(Paragraph("Informe de Historial de Nóminas", styles["Title"]))
    story.append(Spacer(1, 3))
    story.append(Paragraph(f"Fecha de generación: {now_str}", small))
    if downloader_user:
        story.append(Paragraph(f"Usuario que descarga: {downloader_user}", small))

    story.append(Spacer(1, 4))
    story.append(Paragraph("Datos del Empleado", styles["Heading2"]))

    emp_rows = [
        ["Nombre completo", Paragraph(str(full_name), table_cell_style)],
        ["Identificación", Paragraph(str(ident), table_cell_style)],
        ["Departamento", Paragraph(str(department_name), table_cell_style)],
        ["Cargo", Paragraph(str(charge_name), table_cell_style)],
    ]

    if date_from or date_to:
        df = date_from.strftime("%Y-%m-%d") if date_from else "N/D"
        dt = date_to.strftime("%Y-%m-%d") if date_to else "N/D"
        emp_rows.append(["Rango consultado", Paragraph(f"{df} - {dt}", table_cell_style)])

    emp_table = Table(emp_rows, colWidths=[3.5 * cm, 12.5 * cm], hAlign="LEFT")
    emp_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(emp_table)
    story.append(Spacer(1, 6))

    if payroll_items:
        story.append(Paragraph("Resumen General", styles["Heading2"]))
        inc_total = float(global_summary.get("total_increments") or 0)
        ded_total = float(global_summary.get("total_deductions") or 0)
        net_total = float(global_summary.get("total_net") or 0)

        symbol_paren = f" ({currency_symbol})" if currency_symbol else ""

        story.append(
            Paragraph(
                f"Total devengado en el rango: {currency_symbol}{inc_total:,.2f}{symbol_paren}",
                small,
            )
        )
        story.append(
            Paragraph(
                f"Total deducciones en el rango: {currency_symbol}{ded_total:,.2f}{symbol_paren}",
                small,
            )
        )
        story.append(
            Paragraph(
                f"Total neto pagado en el rango: {currency_symbol}{net_total:,.2f}{symbol_paren}",
                small,
            )
        )
        story.append(Spacer(1, 6))

        story.append(Paragraph("Índice de Nóminas", styles["Heading2"]))
        index_header = [
            Paragraph("ID", table_cell_style),
            Paragraph("Fecha generación", table_cell_style),
            Paragraph("Período", table_cell_style),
            Paragraph("Contrato", table_cell_style),
            Paragraph("Neto final", table_cell_style),
        ]
        index_rows = [index_header]

        for item in payroll_items:
            gen_dt = item.get("generation_date")
            if hasattr(gen_dt, "strftime"):
                gen_str = gen_dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                gen_str = str(gen_dt) if gen_dt is not None else "N/D"

            period_from = item.get("period_from")
            pf_str = period_from.strftime("%Y-%m-%d") if hasattr(period_from, "strftime") else str(period_from or "N/D")
            period_to = item.get("period_to")
            pt_str = period_to.strftime("%Y-%m-%d") if hasattr(period_to, "strftime") else str(period_to or "N/D")

            summary = item.get("summary") or {}
            net_final = float(summary.get("net_final") or 0)

            index_rows.append(
                [
                    Paragraph(str(item.get("id_payroll") or "N/D"), table_cell_style),
                    Paragraph(gen_str, table_cell_style),
                    Paragraph(f"{pf_str} - {pt_str}", table_cell_style),
                    Paragraph(str(item.get("contract_code") or "N/D"), table_cell_style),
                    Paragraph(f"{currency_symbol}{net_final:,.2f}", table_cell_style),
                ]
            )

        index_table = Table(
            index_rows,
            colWidths=[1.7 * cm, 3.5 * cm, 5.3 * cm, 4.0 * cm, 3.0 * cm],
            hAlign="LEFT",
            repeatRows=1,
        )
        index_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
                ]
            )
        )
        story.append(index_table)
        story.append(Spacer(1, 8))

    if not payroll_items:
        story.append(Paragraph("No se encontraron nóminas generadas para el rango seleccionado.", small))
        def on_page(canvas, d):
            _header(canvas, d, logo_path, ident)
        doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    story.append(Paragraph("Detalle de Nóminas", styles["Heading2"]))
    story.append(Spacer(1, 6))

    for idx, item in enumerate(payroll_items, start=1):
        # Sección básica por nómina
        story.append(Paragraph(f"Nómina #{idx}", styles["Heading3"]))

        gen_dt = item.get("generation_date")
        if hasattr(gen_dt, "strftime"):
            gen_str = gen_dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            gen_str = str(gen_dt) if gen_dt is not None else "N/D"

        period_from = item.get("period_from")
        pf_str = period_from.strftime("%Y-%m-%d") if hasattr(period_from, "strftime") else str(period_from or "N/D")
        period_to = item.get("period_to")
        pt_str = period_to.strftime("%Y-%m-%d") if hasattr(period_to, "strftime") else str(period_to or "N/D")

        base_salary = item.get("base_salary") or 0
        contract_code = item.get("contract_code") or "N/D"
        author = item.get("author") or "N/D"
        status = item.get("status") or "N/D"

        basic_rows = [
            ["ID Nómina", str(item.get("id_payroll") or "N/D")],
            ["Fecha de generación", gen_str],
            ["Período", f"{pf_str} - {pt_str}"],
            ["Contrato/Otro Sí", str(contract_code)],
            ["Salario base", f"{base_salary:,.2f}"],
            ["Autor", str(author)],
            ["Estado", str(status)],
        ]

        basic_table = Table(basic_rows, colWidths=[3.5 * cm, 12.5 * cm], hAlign="LEFT")
        basic_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ]
            )
        )
        story.append(basic_table)
        story.append(Spacer(1, 5))

        # Resumen económico
        story.append(Paragraph("Resumen", styles["Heading4"]))
        summary = item.get("summary") or {}
        total_inc = summary.get("total_increments") or 0
        total_ded = summary.get("total_deductions") or 0
        net_pay = summary.get("net_pay") or 0
        net_final = summary.get("net_final") or 0

        summary_rows = [
            ["Total devengado", f"{currency_symbol}{total_inc:,.2f}"],
            ["Total deducciones", f"{currency_symbol}{total_ded:,.2f}"],
            ["Neto a pagar", f"{currency_symbol}{net_pay:,.2f}"],
            ["Neto final pagado", f"{currency_symbol}{net_final:,.2f}"],
        ]

        summary_table = Table(summary_rows, colWidths=[5.5 * cm, 10.5 * cm], hAlign="LEFT")
        summary_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ]
            )
        )
        story.append(summary_table)
        story.append(Spacer(1, 5))

        # Devengados
        story.append(Paragraph("Detalle Devengados", styles["Heading4"]))
        inc = item.get("increases") or {}
        inc_fixed = inc.get("fixed") or []
        inc_add = inc.get("additional") or []

        def _build_inc_table(title: str, rows_data: List[Dict[str, Any]]):
            story.append(Paragraph(title, small))
            if not rows_data:
                story.append(Paragraph("Sin registros", small))
                story.append(Spacer(1, 4))
                return

            header = [
                Paragraph("Concepto", table_cell_style),
                Paragraph("Tipo monto", table_cell_style),
                Paragraph("Aplicación", table_cell_style),
                Paragraph("Valor", table_cell_style),
                Paragraph("Valor calculado", table_cell_style),
            ]
            data_rows = [header]
            for r in rows_data:
                data_rows.append(
                    [
                        Paragraph(str(r.get("type_name") or "N/D"), table_cell_style),
                        Paragraph(str(r.get("amount_type") or "N/D"), table_cell_style),
                        Paragraph(str(r.get("application_type") or "N/D"), table_cell_style),
                        Paragraph(f"{(r.get('amount') or 0):,.2f}", table_cell_style),
                        Paragraph(f"{(r.get('calculated_amount') or 0):,.2f}", table_cell_style),
                    ]
                )

            t = Table(data_rows, colWidths=[5.5 * cm, 3.0 * cm, 3.0 * cm, 2.25 * cm, 2.25 * cm], hAlign="LEFT")
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            story.append(t)
            story.append(Spacer(1, 3))

        _build_inc_table("Devengados fijos del contrato", inc_fixed)
        _build_inc_table("Devengados adicionales", inc_add)

        # Deducciones
        story.append(Paragraph("Detalle Deducciones", styles["Heading4"]))
        ded = item.get("deductions") or {}
        ded_fixed = ded.get("fixed") or []
        ded_add = ded.get("additional") or []

        def _build_ded_table(title: str, rows_data: List[Dict[str, Any]]):
            story.append(Paragraph(title, small))
            if not rows_data:
                story.append(Paragraph("Sin registros", small))
                story.append(Spacer(1, 4))
                return

            header = [
                Paragraph("Concepto", table_cell_style),
                Paragraph("Tipo monto", table_cell_style),
                Paragraph("Aplicación", table_cell_style),
                Paragraph("Valor", table_cell_style),
                Paragraph("Valor calculado", table_cell_style),
            ]
            data_rows = [header]
            for r in rows_data:
                data_rows.append(
                    [
                        Paragraph(str(r.get("type_name") or "N/D"), table_cell_style),
                        Paragraph(str(r.get("amount_type") or "N/D"), table_cell_style),
                        Paragraph(str(r.get("application_type") or "N/D"), table_cell_style),
                        Paragraph(f"{(r.get('amount') or 0):,.2f}", table_cell_style),
                        Paragraph(f"{(r.get('calculated_amount') or 0):,.2f}", table_cell_style),
                    ]
                )

            t = Table(data_rows, colWidths=[6 * cm, 3 * cm, 3 * cm, 2 * cm, 2 * cm], hAlign="LEFT")
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            story.append(t)
            story.append(Spacer(1, 6))

        _build_ded_table("Deducciones fijas del contrato", ded_fixed)
        _build_ded_table("Deducciones adicionales", ded_add)

        if idx < len(payroll_items):
            story.append(PageBreak())

    def on_page(canvas, d):
        _header(canvas, d, logo_path, ident)

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
