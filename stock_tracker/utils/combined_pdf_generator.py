"""
Combined PDF Report Generator for Stock Tracker
Generates a single PDF containing both Stocktake and Period reports
"""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from decimal import Decimal
from datetime import datetime


def generate_combined_report_pdf(stocktake, period, include_cocktails=True):
    """
    Generate a combined PDF report with both stocktake and period data.
    
    Args:
        stocktake: Stocktake model instance
        period: StockPeriod model instance
        include_cocktails: Include cocktail data in period section
    
    Returns:
        BytesIO: PDF file buffer
    """
    buffer = BytesIO()
    
    # Use landscape for better table display
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=30,
        leftMargin=30,
        topMargin=50,
        bottomMargin=30
    )
    
    # Container for PDF elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
        spaceBefore=15
    )
    
    # ===== PART 1: STOCKTAKE REPORT =====
    elements.append(Paragraph("COMBINED STOCK REPORT", title_style))
    elements.append(Paragraph(f"Hotel: {stocktake.hotel.name}", styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))
    
    # Stocktake Header
    elements.append(Paragraph("PART 1: STOCKTAKE REPORT", section_style))
    
    # Stocktake info table
    stocktake_info = [
        ['Period:', f"{stocktake.period_start} to {stocktake.period_end}"],
        ['Status:', stocktake.get_status_display()],
        ['Created:', stocktake.created_at.strftime('%Y-%m-%d %H:%M')],
    ]
    
    if stocktake.is_locked and stocktake.approved_by:
        approval_text = (
            f"{stocktake.approved_at.strftime('%Y-%m-%d %H:%M')} "
            f"by {stocktake.approved_by.user.get_full_name() or stocktake.approved_by.user.username}"
        )
        stocktake_info.append(['Approved:', approval_text])
    
    info_table = Table(stocktake_info, colWidths=[1.5*inch, 6*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#555555')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.3 * inch))
    
    # Stocktake Summary
    summary = stocktake.get_summary()
    
    summary_data = [
        ['Total Items:', str(summary['total_items'])],
        ['Expected Stock Value:', f"€{summary['expected_value']:,.2f}"],
        ['Counted Stock Value:', f"€{summary['counted_value']:,.2f}"],
        ['Variance:', f"€{summary['variance_value']:,.2f}"],
    ]
    
    # Add profitability metrics if available
    if 'total_cogs' in summary:
        summary_data.extend([
            ['', ''],
            ['Total COGS:', f"€{summary['total_cogs']:,.2f}"],
            ['Total Revenue:', f"€{summary['total_revenue']:,.2f}"],
            ['GP%:', f"{summary['gross_profit_percentage']:.2f}%"],
            ['Pour Cost%:', f"{summary['pour_cost_percentage']:.2f}%"],
        ])
    
    summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('TEXTCOLOR', (1, 3), (1, 3), colors.red if summary['variance_value'] < 0 else colors.green),
        ('FONTNAME', (1, 3), (1, 3), 'Helvetica-Bold'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3 * inch))
    
    # Category Totals
    elements.append(Paragraph("Category Summary", section_style))
    
    category_totals = stocktake.get_category_totals()
    cat_headers = [['Category', 'Opening', 'Purchases', 'Expected', 'Counted', 'Variance', 'Value €']]
    cat_data = []
    
    for cat in category_totals:
        cat_data.append([
            cat['category_name'],
            f"{cat['opening_qty']:.2f}",
            f"{cat['purchases']:.2f}",
            f"{cat['expected_qty']:.2f}",
            f"{cat['counted_qty']:.2f}",
            f"{cat['variance_qty']:.2f}",
            f"€{cat['variance_value']:.2f}"
        ])
    
    cat_table = Table(cat_headers + cat_data, colWidths=[1.8*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch])
    cat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
    ]))
    elements.append(cat_table)
    
    # Page break before period report
    elements.append(PageBreak())
    
    # ===== PART 2: PERIOD REPORT =====
    elements.append(Paragraph("PART 2: PERIOD CLOSING STOCK REPORT", section_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    # Period info
    period_info = [
        ['Period Name:', period.period_name],
        ['Dates:', f"{period.start_date} to {period.end_date}"],
        ['Type:', period.get_period_type_display()],
        ['Status:', period.get_status_display()],
    ]
    
    period_info_table = Table(period_info, colWidths=[1.5*inch, 6*inch])
    period_info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#555555')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(period_info_table)
    elements.append(Spacer(1, 0.3 * inch))
    
    # Period Summary
    period_summary = period.get_summary()
    
    period_summary_data = [
        ['Total Items:', str(period_summary.get('total_items', 0))],
        ['Closing Stock Value:', f"€{period_summary.get('closing_value', 0):,.2f}"],
    ]
    
    if include_cocktails and 'cocktail_sales_count' in period_summary:
        period_summary_data.extend([
            ['', ''],
            ['Cocktails Sold:', str(period_summary['cocktail_sales_count'])],
            ['Cocktail Revenue:', f"€{period_summary['cocktail_revenue']:,.2f}"],
        ])
    
    period_summary_table = Table(period_summary_data, colWidths=[2.5*inch, 2*inch])
    period_summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(period_summary_table)
    elements.append(Spacer(1, 0.3 * inch))
    
    # Period Category Breakdown
    elements.append(Paragraph("Period Category Breakdown", section_style))
    
    category_breakdown = period.get_category_breakdown()
    period_cat_headers = [['Category', 'Items', 'Value €', '% of Total']]
    period_cat_data = []
    
    for cat in category_breakdown:
        period_cat_data.append([
            cat['category_name'],
            str(cat['item_count']),
            f"€{cat['value']:.2f}",
            f"{cat['percentage']:.1f}%"
        ])
    
    period_cat_table = Table(
        period_cat_headers + period_cat_data,
        colWidths=[2*inch, 1.5*inch, 2*inch, 1.5*inch]
    )
    period_cat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
    ]))
    elements.append(period_cat_table)
    elements.append(Spacer(1, 0.3 * inch))
    
    # Period Stock Snapshots (closing stock)
    elements.append(Paragraph("Closing Stock Details", section_style))
    
    snapshots = period.snapshots.select_related('item', 'item__category').order_by('item__category__code', 'item__name')
    
    if snapshots.exists():
        snapshot_headers = [['SKU', 'Name', 'Category', 'Full', 'Partial', 'Total Qty', 'Value €']]
        snapshot_data = []
        
        for snapshot in snapshots[:50]:  # Limit to first 50 for PDF
            total_servings = snapshot.full_units * snapshot.item.servings_per_unit + snapshot.partial_units
            value = total_servings * snapshot.item.cost_price
            
            snapshot_data.append([
                snapshot.item.sku,
                snapshot.item.name[:30],  # Truncate long names
                snapshot.item.category.code,
                str(snapshot.full_units),
                f"{snapshot.partial_units:.1f}",
                f"{total_servings:.1f}",
                f"€{value:.2f}"
            ])
        
        snapshot_table = Table(
            snapshot_headers + snapshot_data,
            colWidths=[0.8*inch, 2.5*inch, 0.8*inch, 0.7*inch, 0.7*inch, 0.9*inch, 1*inch]
        )
        snapshot_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8e44ad')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (2, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ]))
        elements.append(snapshot_table)
        
        if snapshots.count() > 50:
            elements.append(Spacer(1, 0.2 * inch))
            elements.append(Paragraph(
                f"<i>Note: Showing first 50 of {snapshots.count()} items. "
                f"Download Excel for complete list.</i>",
                styles['Normal']
            ))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
