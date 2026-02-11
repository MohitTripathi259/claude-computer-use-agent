"""
Output Formatters
Converts report structure to final formats (PDF, PPTX, DOCX)
Uses reportlab for PDF generation - FREE, no API cost
"""

import io
from typing import Dict, List
from datetime import datetime

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class PDFFormatter:
    """Formats reports as professional PDF using reportlab"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Create custom styles for the report"""
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=6,
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#616161'),
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1565c0'),
            spaceBefore=16,
            spaceAfter=8,
            borderWidth=1,
            borderColor=colors.HexColor('#1565c0'),
            borderPadding=4
        ))
        self.styles.add(ParagraphStyle(
            name='MetricValue',
            parent=self.styles['Normal'],
            fontSize=18,
            textColor=colors.HexColor('#1a237e'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='MetricLabel',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#757575'),
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='FindingItem',
            parent=self.styles['Normal'],
            fontSize=10,
            leftIndent=20,
            spaceBefore=4,
            spaceAfter=4
        ))

    def format(self, report_structure: Dict, settings: Dict) -> bytes:
        """Generate professional PDF from report structure"""
        print("    Rendering PDF...")

        buffer = io.BytesIO()

        page_size = A4 if settings.get('page_size', 'A4') == 'A4' else letter

        doc = SimpleDocTemplate(
            buffer,
            pagesize=page_size,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )

        elements = []

        # Title section
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(settings.get('title', 'Report'), self.styles['ReportTitle']))

        template_name = report_structure.get('template', 'generic').replace('_', ' ').title()
        now = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        elements.append(Paragraph(
            f"{template_name} | Generated: {now}",
            self.styles['ReportSubtitle']
        ))

        # Divider line
        elements.append(HRFlowable(
            width="100%", thickness=2,
            color=colors.HexColor('#1565c0'),
            spaceAfter=20
        ))

        # Process each section from template
        for section in report_structure.get('sections', []):
            # Support both 'name' (new) and 'type' (older templates)
            section_name = section.get('name') or section.get('type', '')
            section_title = section.get('title', section_name.replace('_', ' ').title())
            content = section.get('content', {})

            if section_name == 'header':
                # Already handled above
                continue

            elif section_name == 'kpi_dashboard':
                elements.extend(self._build_kpi_section(content))

            elif section_name in ['key_findings', 'analysis']:
                elements.extend(self._build_findings_section(section_title, content))

            elif section_name == 'recommendations':
                elements.extend(self._build_recommendations_section(content))

            elif section_name in ['financial_summary', 'revenue_breakdown', 'data_tables']:
                elements.extend(self._build_data_section(section_title, content))

            else:
                elements.extend(self._build_generic_section(section_title, content))

        # Footer
        elements.append(Spacer(1, 30))
        elements.append(HRFlowable(
            width="100%", thickness=1,
            color=colors.HexColor('#e0e0e0'),
            spaceAfter=8
        ))
        elements.append(Paragraph(
            "Generated by Retail MCP Intelligence System",
            self.styles['ReportSubtitle']
        ))

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    def _build_kpi_section(self, content: Dict) -> list:
        """Build KPI dashboard with metric cards"""
        elements = []
        elements.append(Paragraph("Key Metrics", self.styles['SectionHeader']))

        metrics = content.get('metrics', [])
        if not metrics:
            elements.append(Paragraph("No metrics available", self.styles['Normal']))
            return elements

        # Build metric cards in a table (3 per row)
        rows = []
        current_row = []

        for metric in metrics:
            label = str(metric.get('label', 'N/A'))
            value = metric.get('value', 0)

            # Format value
            if isinstance(value, float):
                if value > 10000:
                    formatted = f"Rs. {value:,.2f}"
                else:
                    formatted = f"{value:,.2f}"
            elif isinstance(value, int):
                if value > 1000:
                    formatted = f"{value:,}"
                else:
                    formatted = str(value)
            else:
                formatted = str(value)

            # Show label first, then value on next line for clarity
            cell_content = [
                Paragraph(f"{label}:", self.styles['MetricLabel']),
                Paragraph(formatted, self.styles['MetricValue'])
            ]
            current_row.append(cell_content)

            if len(current_row) == 3:
                rows.append(current_row)
                current_row = []

        if current_row:
            while len(current_row) < 3:
                current_row.append([Paragraph("", self.styles['Normal'])])
            rows.append(current_row)

        if rows:
            col_width = 160
            table = Table(rows, colWidths=[col_width] * 3)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f5f5')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 12))

        return elements

    def _build_findings_section(self, title: str, content: Dict) -> list:
        """Build key findings section"""
        elements = []
        elements.append(Paragraph(title, self.styles['SectionHeader']))

        findings = content.get('findings', [])
        if not findings:
            # Try to extract from raw data
            raw = content.get('raw', {})
            if isinstance(raw, dict):
                for key, val in raw.items():
                    if isinstance(val, list):
                        findings = [str(item) for item in val[:5]]
                        break

        if findings:
            for i, finding in enumerate(findings, 1):
                elements.append(Paragraph(
                    f"<b>{i}.</b>  {finding}",
                    self.styles['FindingItem']
                ))
        else:
            elements.append(Paragraph("No findings generated.", self.styles['Normal']))

        elements.append(Spacer(1, 8))
        return elements

    def _build_recommendations_section(self, content: Dict) -> list:
        """Build recommendations section"""
        elements = []
        elements.append(Paragraph("Recommendations", self.styles['SectionHeader']))

        items = content.get('items', [])
        if items:
            for i, rec in enumerate(items, 1):
                elements.append(Paragraph(
                    f"<b>{i}.</b>  {rec}",
                    self.styles['FindingItem']
                ))
        else:
            elements.append(Paragraph("No recommendations available.", self.styles['Normal']))

        elements.append(Spacer(1, 8))
        return elements

    def _build_data_section(self, title: str, content: Dict) -> list:
        """Build data table section from raw retail data"""
        elements = []
        elements.append(Paragraph(title, self.styles['SectionHeader']))

        data = content.get('data', content.get('raw', {}))

        if isinstance(data, dict):
            # Extract key-value pairs as a summary table
            table_data = []

            # Handle nested structures like sales summary
            totals = data.get('totals') or data.get('global_stats', {})
            if totals:
                elements.append(Paragraph(
                    "<b>Summary</b>", self.styles['Normal']
                ))
                elements.append(Spacer(1, 4))

                summary_rows = [['Metric', 'Value']]
                for key, val in totals.items():
                    label = key.replace('_', ' ').title()
                    if isinstance(val, float):
                        formatted = f"Rs. {val:,.2f}" if val > 100 else f"{val:,.2f}"
                    elif isinstance(val, int):
                        formatted = f"{val:,}"
                    else:
                        formatted = str(val)
                    summary_rows.append([label, formatted])

                if len(summary_rows) > 1:
                    table = Table(summary_rows, colWidths=[200, 200])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565c0')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fafafa')),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
                        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ]))
                    elements.append(table)
                    elements.append(Spacer(1, 10))

            # Handle breakdown data
            breakdown = data.get('breakdown', {})
            if breakdown:
                elements.append(Paragraph(
                    "<b>Breakdown</b>", self.styles['Normal']
                ))
                elements.append(Spacer(1, 4))

                bd_rows = [['Category', 'Revenue', 'Transactions']]
                for key, val in list(breakdown.items())[:10]:
                    if isinstance(val, dict):
                        rev = val.get('revenue', val.get('value', 'N/A'))
                        txn = val.get('transactions', val.get('count', 'N/A'))
                        rev_str = f"Rs. {rev:,.2f}" if isinstance(rev, (int, float)) else str(rev)
                        txn_str = f"{txn:,}" if isinstance(txn, (int, float)) else str(txn)
                        bd_rows.append([str(key), rev_str, txn_str])

                if len(bd_rows) > 1:
                    table = Table(bd_rows, colWidths=[160, 160, 120])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565c0')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
                        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ]))
                    elements.append(table)
                    elements.append(Spacer(1, 10))

            # Handle product lists
            products = data.get('top_products', data.get('products', []))
            if products and isinstance(products, list):
                elements.append(Paragraph(
                    "<b>Products</b>", self.styles['Normal']
                ))
                elements.append(Spacer(1, 4))

                prod_rows = [['SKU', 'Name', 'Brand', 'Price']]
                for p in products[:10]:
                    if isinstance(p, dict):
                        prod_rows.append([
                            str(p.get('sku', 'N/A')),
                            str(p.get('name', 'N/A'))[:30],
                            str(p.get('brand', 'N/A')),
                            f"Rs. {p.get('mrp', 0):,.2f}" if isinstance(p.get('mrp'), (int, float)) else str(p.get('mrp', 'N/A'))
                        ])

                if len(prod_rows) > 1:
                    table = Table(prod_rows, colWidths=[70, 180, 100, 90])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565c0')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
                        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
                        ('TOPPADDING', (0, 0), (-1, -1), 5),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ]))
                    elements.append(table)
                    elements.append(Spacer(1, 10))

            # Handle tables from processed data
            tables = content.get('tables', [])
            for tbl in tables:
                if isinstance(tbl, dict) and tbl.get('data'):
                    tbl_title = tbl.get('title', 'Data')
                    elements.append(Paragraph(
                        f"<b>{tbl_title}</b>", self.styles['Normal']
                    ))
                    elements.append(Spacer(1, 4))

                    tbl_data = tbl['data']
                    if tbl_data and isinstance(tbl_data[0], dict):
                        headers = list(tbl_data[0].keys())[:5]
                        rows = [headers]
                        # Show all available rows (up to reasonable page length)
                        for row in tbl_data:
                            rows.append([str(row.get(h, ''))[:25] for h in headers])

                        col_w = min(100, int(440 / len(headers)))
                        table = Table(rows, colWidths=[col_w] * len(headers))
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565c0')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, -1), 8),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
                            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
                            ('TOPPADDING', (0, 0), (-1, -1), 4),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                            ('LEFTPADDING', (0, 0), (-1, -1), 4),
                        ]))
                        elements.append(table)
                        elements.append(Spacer(1, 10))

        else:
            elements.append(Paragraph("No data available for this section.", self.styles['Normal']))

        return elements

    def _build_generic_section(self, title: str, content: Dict) -> list:
        """Build a generic section from content"""
        elements = []
        elements.append(Paragraph(title, self.styles['SectionHeader']))

        # Content can be dict, list, or primitive depending on template
        if isinstance(content, dict):
            raw = content.get('raw', content)
        else:
            raw = content

        if isinstance(raw, dict):
            for key, val in raw.items():
                label = key.replace('_', ' ').title()
                if isinstance(val, (str, int, float)):
                    elements.append(
                        Paragraph(f"<b>{label}:</b> {val}", self.styles['Normal'])
                    )
                elif isinstance(val, list) and val:
                    elements.append(Paragraph(f"<b>{label}:</b>", self.styles['Normal']))
                    for item in val[:5]:
                        text = (
                            item
                            if isinstance(item, str)
                            else str(item)[:80]
                        )
                        elements.append(
                            Paragraph(f"  - {text}", self.styles['FindingItem'])
                        )
        elif isinstance(raw, list) and raw:
            # Render list items directly
            for item in raw[:8]:
                text = item if isinstance(item, str) else str(item)[:120]
                elements.append(
                    Paragraph(f"  - {text}", self.styles['FindingItem'])
                )
        else:
            elements.append(Paragraph(str(raw)[:500], self.styles['Normal']))

        elements.append(Spacer(1, 8))
        return elements


class PPTXFormatter:
    """Formats reports as PowerPoint"""

    def format(self, report_structure: Dict, settings: Dict) -> bytes:
        """Generate PPTX from report structure"""
        print("    Rendering PowerPoint...")
        # Placeholder - in production would use python-pptx
        content = f"PPTX Report: {settings['title']}\n"
        return content.encode('utf-8')


class DOCXFormatter:
    """Formats reports as Word document"""

    def format(self, report_structure: Dict, settings: Dict) -> bytes:
        """Generate DOCX from report structure"""
        print("    Rendering Word document...")
        # Placeholder - in production would use python-docx
        content = f"DOCX Report: {settings['title']}\n"
        return content.encode('utf-8')
